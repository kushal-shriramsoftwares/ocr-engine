from app.services.ocr_service import OCRService
from app.services.document_detector import detect_document_type


ocr_service = OCRService()

text = ocr_service.extract_text(
    "samples/test.jpg"
)

document_type = detect_document_type(text)

print("\n========== DOCUMENT TYPE ==========\n")

print(document_type)