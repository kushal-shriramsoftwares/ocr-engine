from app.services.ocr_service import OCRService


ocr_service = OCRService()

text = ocr_service.extract_text(
    "samples/test.jpg"
)

print("\n========== RAW TEXT ==========\n")

print(text)