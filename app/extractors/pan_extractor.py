import re


def extract_pan(text: str) -> dict:

    details = {
        "name": None,
        "father_name": None,
        "date_of_birth": None,
        "pan_number": None
    }

    if not text:
        return details

    # =========================================================
    # CLEAN OCR TEXT
    # =========================================================

    lines = [
        re.sub(r"\s+", " ", line).strip()
        for line in text.splitlines()
        if line.strip()
    ]

    # =========================================================
    # PAN NUMBER
    # =========================================================

    # Standard PAN format:
    # ABCDE1234F
    #
    # 5 letters + 4 digits + 1 letter

    pan_matches = re.findall(
        r"\b[A-Z]{5}[0-9]{4}[A-Z]\b",
        text.upper()
    )

    if pan_matches:

        # Use the first valid PAN number
        details["pan_number"] = pan_matches[0]

    # =========================================================
    # DATE OF BIRTH
    # =========================================================

    dob_patterns = [

        # Date of Birth: 27/05/1995
        r"Date\s+of\s+Birth\s*[:\-]?\s*"
        r"([0-3]?\d\s*[/\-.]\s*[0-1]?\d\s*[/\-.]\s*\d{4})",

        # DOB: 27/05/1995
        r"\bDOB\s*[:\-]?\s*"
        r"([0-3]?\d\s*[/\-.]\s*[0-1]?\d\s*[/\-.]\s*\d{4})",

        # Fallback date
        r"\b"
        r"([0-3]?\d\s*[/\-.]\s*[0-1]?\d\s*[/\-.]\s*\d{4})"
        r"\b"
    ]

    for pattern in dob_patterns:

        dob_match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if dob_match:

            dob = dob_match.group(1)

            dob = re.sub(
                r"\s+",
                "",
                dob
            )

            dob = dob.replace(
                "-",
                "/"
            )

            dob = dob.replace(
                ".",
                "/"
            )

            details["date_of_birth"] = dob

            break

    # =========================================================
    # FATHER NAME
    # =========================================================

    father_patterns = [

        # Father's Name: XXXXX
        r"Father'?s?\s+Name\s*[:\-]?\s*(.+)",

        # Father's Name XXXXX
        r"Father'?s?\s+Name\s+(.+)"
    ]

    for pattern in father_patterns:

        father_match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if father_match:

            father_name = father_match.group(1).strip()

            # Remove accidental trailing punctuation
            father_name = father_name.rstrip(
                ".,:;-"
            )

            if father_name:

                details["father_name"] = father_name

                break

    # =========================================================
    # NAME
    # =========================================================

    # PAN cards commonly have the person's name above
    # father's name.
    #
    # We first try to find a line immediately before
    # "Father's Name".

    invalid_words = [
        "income tax",
        "government",
        "govt",
        "india",
        "department",
        "permanent account",
        "account number",
        "pan",
        "father",
        "name",
        "date of birth",
        "dob",
        "signature",
        "income"
    ]

    def is_valid_name(candidate: str) -> bool:

        candidate = re.sub(
            r"\s+",
            " ",
            candidate
        ).strip()

        if not candidate:
            return False

        # Names should contain letters/spaces/dots only
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

        if any(
            word in candidate_lower
            for word in invalid_words
        ):
            return False

        words = re.findall(
            r"[A-Za-z]+",
            candidate
        )

        # Require at least two words
        if len(words) < 2:
            return False

        return True

    # ---------------------------------------------------------
    # PRIORITY 1:
    # Name before Father's Name
    # ---------------------------------------------------------

    for index, line in enumerate(lines):

        if re.search(
            r"Father'?s?\s+Name",
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

    # ---------------------------------------------------------
    # PRIORITY 2:
    # Name before DOB
    # ---------------------------------------------------------

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

    # ---------------------------------------------------------
    # PRIORITY 3:
    # Find first valid name-like line
    # ---------------------------------------------------------

    if not details["name"]:

        for line in lines:

            if is_valid_name(line):

                details["name"] = line

                break

    # =========================================================
    # DEBUG OUTPUT
    # =========================================================

    print(
        "\n========== EXTRACTED PAN DETAILS =========="
    )

    print(details)

    print(
        "===========================================\n"
    )

    return details