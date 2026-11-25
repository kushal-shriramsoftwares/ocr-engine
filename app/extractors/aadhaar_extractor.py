import re

def extract_mobile_number(text: str):
    """
    Extract Indian mobile number from OCR text.

    Handles:
    - Mobile: 9876543210
    - Mobile : 98765 43210
    - Mobile number followed by number on next line
    - Standalone 10-digit Indian mobile number

    Returns:
        str | None
    """

    if not text:
        return None

    # ---------------------------------------------------------
    # Normalize OCR text
    # ---------------------------------------------------------

    normalized_text = re.sub(r"[ \t]+", " ", text)

    # ---------------------------------------------------------
    # Priority 1:
    # Mobile label followed by number
    # ---------------------------------------------------------

    patterns = [
        r"(?:mobile|mob|phone|contact)\s*(?:no|number|num)?\s*[:\-]?\s*(?:\+91[\s\-]*)?([6-9]\d{4}[\s\-]?\d{5})",

        # Handles:
        # Mobile:
        # 98765 43210
        r"(?:mobile|mob|phone|contact)\s*(?:no|number|num)?\s*[:\-]?\s*\n?\s*(?:\+91[\s\-]*)?([6-9]\d{4}[\s\-]?\d{5})",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if match:

            number = match.group(1)

            number = re.sub(
                r"[\s\-]",
                "",
                number
            )

            if len(number) == 10 and number[0] in "6789":
                return number

    # ---------------------------------------------------------
    # Priority 2:
    # Search line immediately after Mobile-related text
    # ---------------------------------------------------------

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    for index, line in enumerate(lines):

        if re.search(
            r"\b(?:mobile|mob|phone|contact)\b",
            line,
            re.IGNORECASE
        ):

            # Check current line and next 3 lines
            for candidate in lines[index:index + 4]:

                # Find 10 digit number, allowing OCR spaces
                matches = re.findall(
                    r"(?<!\d)([6-9]\d{4}[\s\-]?\d{5})(?!\d)",
                    candidate
                )

                for number in matches:

                    number = re.sub(
                        r"[\s\-]",
                        "",
                        number
                    )

                    if len(number) == 10:
                        return number

    # ---------------------------------------------------------
    # Priority 3:
    # Standalone Indian mobile number
    # ---------------------------------------------------------

    matches = re.findall(
        r"(?<!\d)([6-9]\d{4}[\s\-]?\d{5})(?!\d)",
        text
    )

    for number in matches:

        number = re.sub(
            r"[\s\-]",
            "",
            number
        )

        if len(number) == 10:
            return number

    return None


def extract_aadhaar(text: str) -> dict:

    details = {
        "name": None,
        "date_of_birth": None,
        "gender": None,
        "aadhaar_number": None,
        "mobile":None,
        "address": {
            "full_address": None,
            "district": None,
            "state": None,
            "pincode": None
        }
    }

    # Clean OCR lines
    lines = [
        re.sub(r"\s+", " ", line).strip()
        for line in text.split("\n")
        if line.strip()
    ]

    # =========================================================
    # AADHAAR NUMBER
    # =========================================================

    # Priority 1:
    # Aadhaar number near "Your Aadhaar No"
    aadhaar_match = re.search(
        r"Your\s+Aadhaar\s+No\.?\s*:?\s*([0-9]{4}\s*[0-9]{4}\s*[0-9]{4})",
        text,
        re.IGNORECASE
    )

    if aadhaar_match:

        details["aadhaar_number"] = re.sub(
            r"\s+",
            "",
            aadhaar_match.group(1)
        )

    else:

        # Find all Aadhaar-style 12 digit numbers
        all_matches = list(
            re.finditer(
                r"\b\d{4}\s?\d{4}\s?\d{4}\b",
                text
            )
        )

        valid_numbers = []

        for match in all_matches:

            start = match.start()

            # Check text before the number
            previous_text = text[
                max(0, start - 50):start
            ].upper()

            # Ignore VID related numbers
            if "VID" not in previous_text:
                valid_numbers.append(
                    re.sub(
                        r"\s+",
                        "",
                        match.group()
                    )
                )

        if valid_numbers:
            details["aadhaar_number"] = valid_numbers[-1]

    # =========================================================
    # DATE OF BIRTH
    # =========================================================

    dob_patterns = [

        # DOB:27/05/1995
        r"DOB\s*[:\-]?\s*([0-3]?\d\s*[/\-.]\s*[0-1]?\d\s*[/\-.]\s*\d{4})",

        # /DOB:27/05/1995
        r"[/|]?\s*DOB\s*[:\-]?\s*([0-3]?\d\s*[/\-.]\s*[0-1]?\d\s*[/\-.]\s*\d{4})",

        # Date of Birth: 27/05/1995
        r"Date\s+of\s+Birth\s*[:\-]?\s*([0-3]?\d\s*[/\-.]\s*[0-1]?\d\s*[/\-.]\s*\d{4})",

        # Fallback: any date format
        r"\b([0-3]?\d\s*[/\-.]\s*[0-1]?\d\s*[/\-.]\s*\d{4})\b"
    ]

    for pattern in dob_patterns:

        dob_match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if dob_match:

            dob = dob_match.group(1)

            # Remove spaces
            dob = re.sub(r"\s+", "", dob)

            # Convert - or . to /
            dob = dob.replace("-", "/")
            dob = dob.replace(".", "/")

            details["date_of_birth"] = dob

            break

    # =========================================================
    # GENDER
    # =========================================================

    gender_match = re.search(
        r"\b(MALE|FEMALE|TRANSGENDER)\b",
        text,
        re.IGNORECASE
    )

    if gender_match:
        details["gender"] = gender_match.group(1).capitalize()

    # =========================================================
    # NAME VALIDATION
    # =========================================================

    invalid_name_words = [
        "government",
        "india",
        "authority",
        "unique",
        "identification",
        "aadhaar",
        "address",
        "district",
        "state",
        "mobile",
        "download",
        "authentication",
        "security",
        "documents",
        "benefits",
        "services",
        "information",
        "enrolment",
        "sub district",
        "pin code",
        "your aadhaar",
        "proof of identity",
        "date of birth",
        "male",
        "female",
        "vid",
        "dob"
    ]

    def is_valid_name(candidate):

        candidate = re.sub(
            r"\s+",
            " ",
            candidate
        ).strip()

        # Only English letters, spaces and dots
        if not re.match(
            r"^[A-Za-z][A-Za-z .]{2,60}$",
            candidate
        ):
            return False

        # No digits
        if re.search(
            r"\d",
            candidate
        ):
            return False

        candidate_lower = candidate.lower()

        # Reject document-related words
        if any(
            word in candidate_lower
            for word in invalid_name_words
        ):
            return False

        words = re.findall(
            r"[A-Za-z]+",
            candidate
        )

        # Aadhaar name should have at least 2 words
        if len(words) < 2:
            return False

        # Reject too many tiny OCR words
        short_words = sum(
            1
            for word in words
            if len(word) <= 2
        )

        if short_words >= 2:
            return False

        return True

    # =========================================================
    # NAME EXTRACTION
    # PRIORITY 1: NAME BEFORE S/O, D/O, W/O
    # =========================================================

    for index, line in enumerate(lines):

        if re.match(
            r"^(S/O|D/O|W/O)\s*:",
            line,
            re.IGNORECASE
        ):

            for i in range(
                index - 1,
                max(-1, index - 5),
                -1
            ):

                candidate = lines[i]

                if is_valid_name(candidate):

                    details["name"] = candidate
                    break

            if details["name"]:
                break

    # =========================================================
    # PRIORITY 2: NAME BEFORE DOB
    # =========================================================

    if not details["name"]:

        for index, line in enumerate(lines):

            if re.search(
                r"(?:DOB|Date\s+of\s+Birth)",
                line,
                re.IGNORECASE
            ):

                for i in range(
                    index - 1,
                    max(-1, index - 5),
                    -1
                ):

                    candidate = lines[i]

                    if is_valid_name(candidate):

                        details["name"] = candidate
                        break

                if details["name"]:
                    break

    # =========================================================
    # PRIORITY 3: NAME AFTER "TO"
    # =========================================================

    if not details["name"]:

        for index, line in enumerate(lines):

            if line.strip().lower() == "to":

                for i in range(
                    index + 1,
                    min(index + 8, len(lines))
                ):

                    candidate = lines[i]

                    if is_valid_name(candidate):

                        details["name"] = candidate
                        break

                if details["name"]:
                    break

    # =========================================================
    # PINCODE
    # =========================================================

    pincode_matches = re.findall(
        r"\b\d{6}\b",
        text
    )

    if pincode_matches:

        # Prefer last pincode because Aadhaar card address
        # often appears near the end
        details["address"]["pincode"] = pincode_matches[-1]

    # =========================================================
    # STATE
    # =========================================================

    indian_states = [
        "Andhra Pradesh",
        "Arunachal Pradesh",
        "Assam",
        "Bihar",
        "Chhattisgarh",
        "Goa",
        "Gujarat",
        "Haryana",
        "Himachal Pradesh",
        "Jharkhand",
        "Karnataka",
        "Kerala",
        "Madhya Pradesh",
        "Maharashtra",
        "Manipur",
        "Meghalaya",
        "Mizoram",
        "Nagaland",
        "Odisha",
        "Punjab",
        "Rajasthan",
        "Sikkim",
        "Tamil Nadu",
        "Telangana",
        "Tripura",
        "Uttar Pradesh",
        "Uttarakhand",
        "West Bengal",
        "Delhi"
    ]

    for state in indian_states:

        if re.search(
            rf"\b{re.escape(state)}\b",
            text,
            re.IGNORECASE
        ):

            details["address"]["state"] = state
            break

    # =========================================================
    # DISTRICT
    # =========================================================

    district = None

    # First try line-by-line extraction.
    # This is more reliable for PDF OCR because the
    # "District:" field normally appears on its own line.

    for line in lines:

        # Normalize OCR spacing
        normalized_line = re.sub(
            r"\s+",
            " ",
            line
        ).strip()

        # Match "District:" but NOT "Sub District:"
        district_match = re.search(
            r"^\s*District\s*[:\-]?\s*(.+?)\s*$",
            normalized_line,
            re.IGNORECASE
        )

        if district_match:

            candidate = district_match.group(1).strip()

            # Remove trailing punctuation
            candidate = candidate.rstrip(".,;:")

            # Make sure we didn't accidentally capture
            # another field
            candidate = re.split(
                r"\b(?:State|PIN|PIN\s+Code|Pincode|VTC|PO|Sub\s+District)\b",
                candidate,
                maxsplit=1,
                flags=re.IGNORECASE
            )[0].strip()

            candidate = candidate.rstrip(".,;:")

            if candidate:
                district = candidate
                break

    # Fallback: search the complete OCR text
    if not district:

        district_match = re.search(
            r"\bDistrict\s*[:\-]\s*([A-Za-z][A-Za-z .'-]*?)(?=\s*(?:,|State|PIN|PIN\s+Code|Pincode|VTC|PO|Sub\s+District|$))",
            text,
            re.IGNORECASE
        )

        if district_match:

            district = district_match.group(1).strip()
            district = district.rstrip(".,;:")

    if district:

        details["address"]["district"] = district

    # =========================================================
    # ADDRESS EXTRACTION
    # =========================================================

    address_candidates = []

    address_keywords = [
        "road",
        "street",
        "building",
        "house",
        "layout",
        "nagar",
        "colony",
        "village",
        "main",
        "cross",
        "lane",
        "floor",
        "block",
        "sector",
        "apartment",
        "apartments",
        "vtc:",
        "po:",
        "sub district",
        "district:"
    ]

    skip_keywords = [
        "government",
        "unique identification",
        "aadhaar is proof",
        "date of birth",
        "verified",
        "enrolment",
        "mobile",
        "download",
        "security",
        "entities seeking",
        "consent",
        "your aadhaar",
        "vid:",
        "help@",
        "uidai.gov",
        "authentication",
        "government benefits",
        "keep your",
        "documents to support",
        "scanning using",
        "app stores"
    ]

    for line in lines:

        line_lower = line.lower()

        # Skip unwanted text
        if any(
            keyword in line_lower
            for keyword in skip_keywords
        ):
            continue

        # Skip Aadhaar number
        if re.search(
            r"\b\d{4}\s?\d{4}\s?\d{4}\b",
            line
        ):
            continue

        # Skip mobile number
        if re.search(
            r"\b[6-9]\d{9}\b",
            line
        ):
            continue

        # Skip extracted name
        if (
            details["name"]
            and line.strip() == details["name"]
        ):
            continue

        # Skip DOB and gender lines
        if re.search(
            r"\b(DOB|MALE|FEMALE|TRANSGENDER)\b",
            line,
            re.IGNORECASE
        ):
            continue

        # Address keyword lines
        if any(
            keyword in line_lower
            for keyword in address_keywords
        ):

            address_candidates.append(line)

        # House number lines
        elif re.search(
            r"(#\s*\d+|House\s*No\.?\s*\d+)",
            line,
            re.IGNORECASE
        ):

            address_candidates.append(line)

        # Parent/spouse information
        elif re.match(
            r"^(S/O|D/O|W/O)\s*:",
            line,
            re.IGNORECASE
        ):

            address_candidates.append(line)

    # =========================================================
    # REMOVE DUPLICATES
    # =========================================================

    clean_address = []

    for line in address_candidates:

        line = re.sub(
            r"\s+",
            " ",
            line
        ).strip()

        # Remove repeated commas
        line = re.sub(
            r",\s*,+",
            ",",
            line
        )

        if (
            line
            and line not in clean_address
        ):
            clean_address.append(line)

    if clean_address:

        details["address"]["full_address"] = ", ".join(
            clean_address
        )
           
    # =========================================================
    # MOBILE NUMBER
    # =========================================================

    details["mobile"] = extract_mobile_number(text)

    # =========================================================
    # DEBUG OUTPUT
    # =========================================================

    print("\n========== EXTRACTED AADHAAR DETAILS ==========")
    print(details)
    print("===============================================\n")

    return details