import os
import shutil

from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, Request
from sqlalchemy.orm import Session
from time import perf_counter
from fastapi.middleware.cors import CORSMiddleware

from app.services.ocr_service import extract_text
from app.services.document_detector import detect_document
from app.services.document_quality import check_document_quality
from app.extractors.aadhaar_extractor import extract_aadhaar
from app.extractors.pan_extractor import extract_pan
from app.schemas.response import ExtractionResponse

from app.admin_auth import router as admin_auth_router
from app.admin_routes import router as admin_routes_router
from app.admin_service_routes import router as admin_service_router
from app.admin_audit_routes import router as admin_audit_router
from app.access_request_routes import router as access_request_router
from app.admin_access_routes import router as admin_access_router
from app.admin_approval_routes import router as admin_approval_router
from app.admin_api_key_routes import router as admin_api_key_router
from app.admin_dashboard_routes import router as admin_dashboard_router

from app.client_auth import get_current_client
from app.models import Client, UsageLog
from app.admin_auth import get_db


app = FastAPI(
    title="OCR Engine",
    description="PAN and Aadhaar OCR extraction API",
    version="1.0.0"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(admin_auth_router)
app.include_router(admin_routes_router)
app.include_router(access_request_router)
app.include_router(admin_access_router)
app.include_router(admin_approval_router)
app.include_router(admin_api_key_router)
app.include_router(admin_dashboard_router)
app.include_router(admin_service_router)
app.include_router(admin_audit_router)


UPLOAD_DIR = "uploads"


ALLOWED_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".pdf"
}


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def validate_aadhaar_extraction(data: dict) -> dict:
    """
    Validate whether enough Aadhaar information was extracted
    to consider the document readable.
    """

    extracted_fields = []

    if data.get("name"):
        extracted_fields.append("name")

    if data.get("date_of_birth"):
        extracted_fields.append("date_of_birth")

    if data.get("gender"):
        extracted_fields.append("gender")

    if data.get("aadhaar_number"):
        extracted_fields.append("aadhaar_number")

    if data.get("mobile"):
        extracted_fields.append("mobile")

    address = data.get("address")

    if isinstance(address, dict):

        if address.get("full_address"):
            extracted_fields.append("address")

        if address.get("district"):
            extracted_fields.append("district")

        if address.get("state"):
            extracted_fields.append("state")

        if address.get("pincode"):
            extracted_fields.append("pincode")

    # Count important/core fields
    core_fields = 0

    if data.get("name"):
        core_fields += 1

    if data.get("date_of_birth"):
        core_fields += 1

    if data.get("gender"):
        core_fields += 1

    if data.get("aadhaar_number"):
        core_fields += 1

    if isinstance(address, dict) and address.get("full_address"):
        core_fields += 1

    # If too little information was extracted,
    # consider the document unclear/incomplete.
    if core_fields < 3:
        return {
            "valid": False,
            "reason": (
                "The document is not clear enough to read. "
                "Please upload a clear image showing the complete Aadhaar card."
            )
        }

    # Special case:
    # If only Aadhaar number was detected, reject it.
    if (
        data.get("aadhaar_number")
        and not data.get("name")
        and not data.get("date_of_birth")
        and not data.get("gender")
        and not (
            isinstance(address, dict)
            and address.get("full_address")
        )
    ):
        return {
            "valid": False,
            "reason": (
                "Only the Aadhaar number could be read. "
                "Please upload a clear image showing the complete Aadhaar card."
            )
        }

    return {
        "valid": True,
        "reason": "Aadhaar extraction is valid.",
        "extracted_fields": extracted_fields
    }


def validate_pan_extraction(data: dict) -> dict:
    """
    Validate whether enough PAN information was extracted
    to consider the document readable.
    """

    extracted_fields = []

    if data.get("name"):
        extracted_fields.append("name")

    if data.get("father_name"):
        extracted_fields.append("father_name")

    if data.get("date_of_birth"):
        extracted_fields.append("date_of_birth")

    if data.get("pan_number"):
        extracted_fields.append("pan_number")

    core_fields = len(extracted_fields)

    # PAN should have enough important fields
    if core_fields < 3:
        return {
            "valid": False,
            "reason": (
                "The PAN card is not clear enough to read. "
                "Please upload a clear image showing the complete PAN card."
            )
        }

    return {
        "valid": True,
        "reason": "PAN extraction is valid.",
        "extracted_fields": extracted_fields
    }


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/")
def root():
    return {
        "message": "OCR Engine is running",
        "supported_documents": [
            "Aadhaar Card",
            "PAN Card"
        ]
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


# ============================================================
# OCR ENDPOINT
# ============================================================

@app.post(
    "/extract",
    response_model=ExtractionResponse
)
async def extract_document(
    request: Request,
    file: UploadFile = File(...),
    current_client: Client = Depends(get_current_client),
    db: Session = Depends(get_db),
):
    # Authentication is checked before OCR processing.
    # Only active organizations with valid API keys
    # can access this endpoint.

    file_path = None
    start_time = perf_counter()
    http_status = 200
    service_code = "unknown"

    try:

        # ----------------------------------------------------
        # 1. Validate filename
        # ----------------------------------------------------

        if not file.filename:
            raise HTTPException(
                status_code=400,
                detail="Please upload a document."
            )

        extension = os.path.splitext(file.filename)[1].lower()

        if extension not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Unsupported file type. "
                    "Please upload a JPG, JPEG, PNG, or PDF document."
                )
            )

        # ----------------------------------------------------
        # 2. Determine uploaded file type
        # ----------------------------------------------------

        if extension == ".pdf":
            file_type = "pdf"
        else:
            file_type = "image"

        print("Uploaded document type:", file_type)

        # ----------------------------------------------------
        # 3. Create uploads directory
        # ----------------------------------------------------

        os.makedirs(UPLOAD_DIR, exist_ok=True)

        # ----------------------------------------------------
        # 4. Save uploaded file
        # ----------------------------------------------------

        safe_filename = os.path.basename(file.filename)

        file_path = os.path.join(
            UPLOAD_DIR,
            safe_filename
        )

        # Avoid problems if a file with the same name exists
        base_name = os.path.splitext(safe_filename)[0]
        original_extension = os.path.splitext(safe_filename)[1]

        counter = 1

        while os.path.exists(file_path):

            file_path = os.path.join(
                UPLOAD_DIR,
                f"{base_name}_{counter}{original_extension}"
            )

            counter += 1

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(
                file.file,
                buffer
            )

        print("Document upload saved for OCR processing.")

        # ----------------------------------------------------
        # 5. OCR FIRST
        # ----------------------------------------------------
        #
        # We intentionally perform OCR before the image
        # quality check so that invalid documents are
        # identified correctly.
        # ----------------------------------------------------

        print("Starting OCR process.")

        extracted_text = extract_text(file_path)

        print("OCR completed.")

        # ----------------------------------------------------
        # 6. Detect document type
        # ----------------------------------------------------

        document_type = detect_document(
            extracted_text
        )

        print("Document detection completed.")
        if document_type == "aadhaar":
            service_code = "aadhaar_ocr"
        elif document_type == "pan":
            service_code = "pan_ocr"

        # ----------------------------------------------------
        # 7. Reject invalid documents
        # ----------------------------------------------------

        if document_type not in {
            "aadhaar",
            "pan"
        }:

            raise HTTPException(
                status_code=400,
                detail=(
                    "Invalid document. "
                    "Please upload a valid PAN or Aadhaar card."
                )
            )

        # ----------------------------------------------------
        # 8. Check document quality
        # ----------------------------------------------------

        quality_result = check_document_quality(
            file_path
        )

        if not quality_result["valid"]:

            raise HTTPException(
                status_code=400,
                detail=quality_result["reason"]
            )

        # ----------------------------------------------------
        # 9. Extract fields based on document type
        # ----------------------------------------------------

        print("Starting field extraction.")

        if document_type == "aadhaar":

            data = extract_aadhaar(
                extracted_text
            )

            # ------------------------------------------------
            # 10. Validate Aadhaar extraction
            # ------------------------------------------------

            validation_result = validate_aadhaar_extraction(
                data
            )

            if not validation_result["valid"]:

                raise HTTPException(
                    status_code=400,
                    detail=validation_result["reason"]
                )

            # Make sure PAN-only fields are empty
            data["father_name"] = None
            data["pan_number"] = None

        elif document_type == "pan":

            data = extract_pan(
                extracted_text
            )

            # ------------------------------------------------
            # 10. Validate PAN extraction
            # ------------------------------------------------

            validation_result = validate_pan_extraction(
                data
            )

            if not validation_result["valid"]:

                raise HTTPException(
                    status_code=400,
                    detail=validation_result["reason"]
                )

            # Make sure Aadhaar-only fields are empty
            data["gender"] = None
            data["aadhaar_number"] = None
            data["mobile"] = None
            data["address"] = None

        else:

            raise HTTPException(
                status_code=400,
                detail=(
                    "Invalid document. "
                    "Please upload a valid PAN or Aadhaar card."
                )
            )

        # ----------------------------------------------------
        # 11. Return successful response
        # ----------------------------------------------------

        response = ExtractionResponse(
            success=True,
            document_type=document_type,
            file_type=file_type,
            data=data
        )

        # Never print extracted personal information.
        print("OCR extraction completed successfully.")

        return response

    # --------------------------------------------------------
    # HTTP errors
    # --------------------------------------------------------

    except HTTPException as exc:
        http_status = exc.status_code
        raise
    

    # --------------------------------------------------------
    # Unexpected errors
    # --------------------------------------------------------

    except Exception:
        http_status = 500

        # Avoid logging sensitive OCR data or exception details.
        print("An unexpected OCR processing error occurred.")

        raise HTTPException(
            status_code=500,
            detail=(
                "An error occurred while processing the document. "
                "Please try again with a valid PAN or Aadhaar card."
            )
        )

    # --------------------------------------------------------
    # Always delete uploaded temporary file
    # --------------------------------------------------------

    finally:
                # Record OCR API usage
        try:
            duration_ms = int(
                (perf_counter() - start_time) * 1000
            )

            usage_record = UsageLog(
                client_id=current_client.id,
                api_key_id=getattr(
                    request.state,
                    "api_key_id",
                    None
                ),
                service_code=service_code,
                endpoint="/extract",
                http_status=http_status,
                duration_ms=duration_ms,
            )

            db.add(usage_record)
            db.commit()

        except Exception:
            db.rollback()
            print("Could not save OCR usage record.")

        if file_path and os.path.exists(file_path):

            try:

                os.remove(file_path)

                print("Temporary uploaded file deleted.")

            except Exception:

                print("Could not delete temporary uploaded file.")