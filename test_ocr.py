from pathlib import Path
from paddleocr import PaddleOCR


# Find image automatically
samples_folder = Path("samples")

image_files = list(samples_folder.glob("*.jpg"))
image_files += list(samples_folder.glob("*.jpeg"))
image_files += list(samples_folder.glob("*.png"))


if not image_files:
    print("ERROR: No image found inside samples folder.")
    print("Supported formats: JPG, JPEG, PNG")
    exit()


image_path = image_files[0]

print(f"Using image: {image_path}")

print("Loading PaddleOCR...")

ocr = PaddleOCR(
    lang="en",
    enable_mkldnn=False
)

print("Starting OCR...")

result = ocr.predict(str(image_path))

print("\n========== EXTRACTED TEXT ==========\n")

for page in result:

    if isinstance(page, dict):

        texts = page.get("rec_texts", [])

        for text in texts:
            print(text)