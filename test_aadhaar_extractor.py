from app.services.ocr_service import OCRService
from app.extractors.aadhaar_extractor import extract_aadhaar


ocr_service = OCRService()


text = ocr_service.extract_text(
    "samples/test.jpg"
)


details = extract_aadhaar(text)


print("\n========== AADHAAR DETAILS ==========\n")

for key, value in details.items():

    print(f"{key}: {value}")