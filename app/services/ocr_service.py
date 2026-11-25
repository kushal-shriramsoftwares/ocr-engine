import os

# MUST be set before importing PaddleOCR/Paddle
os.environ["FLAGS_use_mkldnn"] = "0"
os.environ["FLAGS_enable_pir_api"] = "0"
os.environ["PADDLE_PDX_ENABLE_MKLDNN_BYDEFAULT"] = "0"
os.environ["PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK"] = "True"

import cv2
import fitz  # PyMuPDF

from paddleocr import PaddleOCR


print("Loading PaddleOCR...")

ocr = PaddleOCR(
    text_detection_model_name="PP-OCRv5_mobile_det",
    text_recognition_model_name="PP-OCRv5_mobile_rec",

    # Disable document preprocessing models
    use_doc_orientation_classify=False,
    use_doc_unwarping=False,
    use_textline_orientation=False,

    # IMPORTANT: Disable MKLDNN / oneDNN
    enable_mkldnn=False,

    # Use CPU
    device="cpu"
)

print("PaddleOCR loaded successfully")


def preprocess_image(image_path: str):

    image = cv2.imread(image_path)

    if image is None:
        raise ValueError(f"Could not read image: {image_path}")

    height, width = image.shape[:2]

    max_width = 1600

    if width > max_width:

        scale = max_width / width

        new_width = int(width * scale)
        new_height = int(height * scale)

        image = cv2.resize(
            image,
            (new_width, new_height),
            interpolation=cv2.INTER_AREA
        )

    processed_path = image_path.rsplit(".", 1)[0] + "_processed.jpg"

    cv2.imwrite(
        processed_path,
        image,
        [cv2.IMWRITE_JPEG_QUALITY, 90]
    )

    return processed_path


def pdf_to_images(pdf_path: str):

    print("Converting PDF to images:", pdf_path)

    document = fitz.open(pdf_path)

    image_paths = []

    try:

        for page_number in range(len(document)):

            page = document.load_page(page_number)

            # 2x resolution gives OCR a better image to work with
            matrix = fitz.Matrix(2, 2)

            pixmap = page.get_pixmap(
                matrix=matrix,
                alpha=False
            )

            image_path = (
                pdf_path.rsplit(".", 1)[0]
                + f"_page_{page_number + 1}.png"
            )

            pixmap.save(image_path)

            image_paths.append(image_path)

            print(
                f"PDF page {page_number + 1} converted:",
                image_path
            )

        return image_paths

    finally:

        document.close()


def extract_text_from_image(image_path: str) -> str:

    processed_path = None

    try:

        processed_path = preprocess_image(image_path)

        print("Processed image:", processed_path)

        result = ocr.predict(processed_path)

        print("OCR prediction completed")

        extracted_text = []

        for res in result:

            data = res.json

            if "res" in data:

                texts = data["res"].get(
                    "rec_texts",
                    []
                )

                for text in texts:

                    if text and text.strip():

                        extracted_text.append(
                            text.strip()
                        )

        return "\n".join(extracted_text)

    finally:

        if (
            processed_path
            and os.path.exists(processed_path)
        ):

            os.remove(processed_path)


def extract_text(image_path: str) -> str:

    print("OCR started:", image_path)

    extension = os.path.splitext(image_path)[1].lower()

    # ---------------------------------------------------------
    # PDF
    # ---------------------------------------------------------

    if extension == ".pdf":

        pdf_image_paths = []

        try:

            pdf_image_paths = pdf_to_images(image_path)

            all_text = []

            for page_number, page_image in enumerate(
                pdf_image_paths,
                start=1
            ):

                print(
                    f"OCR processing PDF page {page_number}"
                )

                page_text = extract_text_from_image(
                    page_image
                )

                if page_text:

                    all_text.append(page_text)

            final_text = "\n".join(all_text)

            print("PDF OCR finished")
            print(
                "Characters extracted:",
                len(final_text)
            )

            return final_text

        finally:

            # Delete converted PDF page images
            for page_image in pdf_image_paths:

                if os.path.exists(page_image):

                    os.remove(page_image)

                    print(
                        "Temporary PDF image deleted:",
                        page_image
                    )

    # ---------------------------------------------------------
    # IMAGE
    # ---------------------------------------------------------

    else:

        try:

            final_text = extract_text_from_image(
                image_path
            )

            print("OCR finished")
            print(
                "Characters extracted:",
                len(final_text)
            )

            return final_text

        except Exception:

            raise