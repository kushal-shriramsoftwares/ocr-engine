import re


def detect_document(text: str) -> str:

    if not text:
        return "unknown"

    text_lower = text.lower()

    # =========================================================
    # AADHAAR
    # =========================================================

    aadhaar_keywords = [
        "unique identification authority",
        "uidai",
        "aadhaar",
        "your aadhaar"
    ]

    aadhaar_score = 0

    for keyword in aadhaar_keywords:

        if keyword in text_lower:
            aadhaar_score += 1

    # Aadhaar number pattern
    # Example: 1234 5678 9012
    aadhaar_number_match = re.search(
        r"\b\d{4}\s?\d{4}\s?\d{4}\b",
        text
    )

    if aadhaar_number_match:
        aadhaar_score += 1

    # =========================================================
    # PAN
    # =========================================================

    pan_keywords = [
        "income tax department",
        "permanent account number",
        "income tax",
        "govt. of india",
        "government of india"
    ]

    pan_score = 0

    for keyword in pan_keywords:

        if keyword in text_lower:
            pan_score += 1

    # PAN number pattern
    #
    # Standard PAN format:
    # ABCDE1234F
    #
    # 5 letters + 4 digits + 1 letter

    pan_number_match = re.search(
        r"\b[A-Z]{5}[0-9]{4}[A-Z]\b",
        text.upper()
    )

    if pan_number_match:
        pan_score += 2

    # =========================================================
    # DOCUMENT DECISION
    # =========================================================

    # Aadhaar
    if aadhaar_score >= 1:

        return "aadhaar"

    # PAN
    if pan_score >= 2:

        return "pan"

    return "unknown"