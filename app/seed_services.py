
from sqlalchemy import select

from app.database import SessionLocal
from app.models import OCRService


SERVICES = [
    {
        "service_code": "aadhaar_ocr",
        "service_name": "Aadhaar OCR",
        "description": "Extract information from Aadhaar documents.",
    },
    {
        "service_code": "pan_ocr",
        "service_name": "PAN OCR",
        "description": "Extract information from PAN documents.",
    },
]


def seed_services():
    db = SessionLocal()

    try:
        for service_data in SERVICES:
            existing_service = db.scalar(
                select(OCRService).where(
                    OCRService.service_code == service_data["service_code"]
                )
            )

            if existing_service:
                print(
                    f"Already registered: {service_data['service_code']}"
                )
                continue

            service = OCRService(
                service_code=service_data["service_code"],
                service_name=service_data["service_name"],
                description=service_data["description"],
                is_active=True,
            )

            db.add(service)
            print(f"Registered: {service_data['service_code']}")

        db.commit()
        print("\nOCR SERVICES REGISTERED SUCCESSFULLY!")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    seed_services()
