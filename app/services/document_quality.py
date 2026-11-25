import os

import cv2
import fitz
import numpy as np


# ============================================================
# IMAGE QUALITY SETTINGS
# ============================================================
#
# These settings are used ONLY for JPG/JPEG/PNG images.
#
# PDFs are handled separately below because a PDF page can
# legitimately have a very bright/white background.
# ============================================================

MIN_IMAGE_WIDTH = 800
MIN_IMAGE_HEIGHT = 500

MIN_BLUR_SCORE = 120.0
MIN_CONTRAST = 35.0
MIN_BRIGHTNESS = 45.0
MAX_BRIGHTNESS = 245.0
MIN_EDGE_PERCENT = 1.5


# ============================================================
# IMAGE QUALITY ANALYSIS
# ============================================================

def analyze_image(image) -> dict:
    """
    Analyze the quality of a normal image file.

    This is intended for JPG/JPEG/PNG files captured as
    photographs or uploaded as images.
    """

    if image is None:
        return {
            "valid": False,
            "reason": "Could not read the image."
        }

    height, width = image.shape[:2]

    print(f"Image size: {width}x{height}")

    # --------------------------------------------------------
    # Resolution
    # --------------------------------------------------------

    if width < MIN_IMAGE_WIDTH or height < MIN_IMAGE_HEIGHT:

        return {
            "valid": False,
            "reason": (
                "Image resolution is too low. "
                "Please upload a clear, high-resolution document image."
            )
        }

    # --------------------------------------------------------
    # Convert to grayscale
    # --------------------------------------------------------

    gray = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY
    )

    # --------------------------------------------------------
    # Brightness
    # --------------------------------------------------------

    brightness = float(
        np.mean(gray)
    )

    print(
        "Brightness:",
        round(brightness, 2)
    )

    if brightness < MIN_BRIGHTNESS:

        return {
            "valid": False,
            "reason": (
                "Document image is too dark. "
                "Please upload a properly lit photo."
            )
        }

    if brightness > MAX_BRIGHTNESS:

        return {
            "valid": False,
            "reason": (
                "Document image is too bright or overexposed. "
                "Please upload a properly exposed photo."
            )
        }

    # --------------------------------------------------------
    # Contrast
    # --------------------------------------------------------

    contrast = float(
        np.std(gray)
    )

    print(
        "Contrast:",
        round(contrast, 2)
    )

    if contrast < MIN_CONTRAST:

        return {
            "valid": False,
            "reason": (
                "Document image has insufficient contrast. "
                "Please upload a clearer photo."
            )
        }

    # --------------------------------------------------------
    # Blur detection
    # --------------------------------------------------------

    blur_score = float(
        cv2.Laplacian(
            gray,
            cv2.CV_64F
        ).var()
    )

    print(
        "Blur score:",
        round(blur_score, 2)
    )

    if blur_score < MIN_BLUR_SCORE:

        return {
            "valid": False,
            "reason": (
                "Document image is too blurry or out of focus. "
                "Please upload a clear photo."
            )
        }

    # --------------------------------------------------------
    # Edge/detail detection
    # --------------------------------------------------------

    edges = cv2.Canny(
        gray,
        100,
        200
    )

    edge_pixels = np.count_nonzero(
        edges
    )

    total_pixels = (
        edges.shape[0] *
        edges.shape[1]
    )

    edge_percent = (
        edge_pixels /
        total_pixels
    ) * 100

    print(
        "Edge/detail percentage:",
        round(edge_percent, 2)
    )

    if edge_percent < MIN_EDGE_PERCENT:

        return {
            "valid": False,
            "reason": (
                "Document image does not contain enough visible "
                "detail for reliable OCR. Please upload a clearer photo."
            )
        }

    # --------------------------------------------------------
    # Passed
    # --------------------------------------------------------

    print(
        "Image quality: PASSED"
    )

    return {
        "valid": True,
        "reason": "Image quality is acceptable.",
        "width": width,
        "height": height,
        "brightness": round(brightness, 2),
        "contrast": round(contrast, 2),
        "blur_score": round(blur_score, 2),
        "edge_percent": round(edge_percent, 2)
    }


# ============================================================
# IMAGE FILE QUALITY CHECK
# ============================================================

def check_image_quality(image_path: str) -> dict:
    """
    Quality check for JPG/JPEG/PNG files.
    """

    print(
        "\n========== IMAGE QUALITY CHECK =========="
    )

    image = cv2.imread(
        image_path
    )

    result = analyze_image(
        image
    )

    if result["valid"]:

        print(
            "Image quality validation: PASSED"
        )

    else:

        print(
            "Image quality validation: FAILED"
        )

        print(
            "Reason:",
            result["reason"]
        )

    print(
        "=========================================\n"
    )

    return result


# ============================================================
# PDF QUALITY CHECK
# ============================================================

def check_pdf_quality(pdf_path: str) -> dict:
    """
    Quality check for PDF files.

    IMPORTANT:
    PDFs are NOT evaluated using camera-photo brightness,
    contrast, blur, or edge thresholds.

    A PDF can have a white background and therefore have a
    high average brightness even though all of its text is
    perfectly readable.

    For PDFs, we only verify that:
      1. The PDF can be opened.
      2. It contains at least one page.
      3. Every page can be rendered successfully.
      4. The rendered page contains actual pixel data.

    Whether the PDF is actually a PAN/Aadhaar document is
    determined later by OCR + document detection.
    """

    print(
        "\n========== PDF QUALITY CHECK =========="
    )

    try:

        document = fitz.open(
            pdf_path
        )

    except Exception as error:

        print(
            "Could not open PDF:",
            error
        )

        print(
            "========================================\n"
        )

        return {
            "valid": False,
            "reason": (
                "Could not read the PDF. "
                "Please upload a valid PDF document."
            )
        }

    try:

        page_count = len(
            document
        )

        print(
            "PDF pages:",
            page_count
        )

        # ----------------------------------------------------
        # Empty PDF
        # ----------------------------------------------------

        if page_count == 0:

            return {
                "valid": False,
                "reason": (
                    "PDF contains no pages. "
                    "Please upload a valid document."
                )
            }

        # ----------------------------------------------------
        # Check every page can be rendered
        # ----------------------------------------------------

        for page_number in range(
            page_count
        ):

            print(
                f"\nChecking PDF page {page_number + 1}..."
            )

            try:

                page = document.load_page(
                    page_number
                )

                # Render at 2x resolution.
                matrix = fitz.Matrix(
                    2,
                    2
                )

                pixmap = page.get_pixmap(
                    matrix=matrix,
                    alpha=False
                )

                # Make sure the rendered page actually
                # contains image data.
                if (
                    pixmap.width <= 0
                    or pixmap.height <= 0
                    or not pixmap.samples
                ):

                    return {
                        "valid": False,
                        "reason": (
                            f"PDF page {page_number + 1} "
                            "could not be rendered correctly. "
                            "Please upload a valid document."
                        )
                    }

                print(
                    f"PDF page {page_number + 1} rendered successfully: "
                    f"{pixmap.width}x{pixmap.height}"
                )

            except Exception as error:

                print(
                    f"PDF page {page_number + 1} rendering error:",
                    error
                )

                return {
                    "valid": False,
                    "reason": (
                        f"PDF page {page_number + 1} "
                        "could not be read. "
                        "Please upload a valid document."
                    )
                }

        # ----------------------------------------------------
        # PDF passed
        # ----------------------------------------------------

        print(
            "\nPDF rendering validation: PASSED"
        )

        print(
            "========================================\n"
        )

        return {
            "valid": True,
            "reason": "PDF can be read and rendered successfully.",
            "pages": page_count
        }

    finally:

        document.close()


# ============================================================
# DOCUMENT QUALITY ROUTER
# ============================================================

def check_document_quality(file_path: str) -> dict:
    """
    Select the correct quality check based on file type.

    JPG/JPEG/PNG:
        Uses image quality analysis.

    PDF:
        Uses PDF rendering validation only.
    """

    extension = os.path.splitext(
        file_path
    )[1].lower()

    # --------------------------------------------------------
    # Image files
    # --------------------------------------------------------

    if extension in {
        ".jpg",
        ".jpeg",
        ".png"
    }:

        return check_image_quality(
            file_path
        )

    # --------------------------------------------------------
    # PDF files
    # --------------------------------------------------------

    if extension == ".pdf":

        return check_pdf_quality(
            file_path
        )

    # --------------------------------------------------------
    # Unsupported file
    # --------------------------------------------------------

    return {
        "valid": False,
        "reason": (
            "Unsupported file type."
        )
    }