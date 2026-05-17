import re

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"(\+?\d[\d\s().-]{7,}\d)")
PESEL_RE = re.compile(r"\b\d{11}\b")
DATE_RE = re.compile(r"\b\d{1,2}[./-]\d{1,2}[./-]\d{2,4}\b")

SENSITIVE_LABELS = (
    "imię",
    "imie",
    "nazwisko",
    "pesel",
    "data urodzenia",
    "adres",
    "ul.",
    "ulica",
    "telefon",
    "e-mail",
    "email",
)

MEDICAL_LABELS = (
    "wiek",
    "płeć",
    "plec",
    "waga",
    "masa ciała",
)


def anonymize_text(text: str, mode: str = "full") -> str:
    """
    Anonymize text based on mode:
    - "full": Remove all personal data (default)
    - "medical": Keep medical data (age, gender, weight) but remove identifying info
    """
    selected_mode = mode if mode in {"full", "medical"} else "full"

    lines: list[str] = []
    for line in text.splitlines():
        lowered = line.lower()

        # Check if line contains sensitive personal data
        has_sensitive = any(label in lowered for label in SENSITIVE_LABELS)

        # Check if line contains medical data (only relevant for "medical" mode)
        has_medical = any(label in lowered for label in MEDICAL_LABELS)

        # Full mode removes all sensitive and medical demographic context.
        if selected_mode == "full" and (has_sensitive or has_medical):
            continue

        # Medical mode keeps medical demographics but still removes identifying lines.
        if selected_mode == "medical" and has_sensitive and not has_medical:
            continue

        # Always replace emails, phones, PESEL, dates with placeholders.
        line = EMAIL_RE.sub("[EMAIL]", line)
        line = PHONE_RE.sub("[PHONE]", line)
        line = PESEL_RE.sub("[ID]", line)
        line = DATE_RE.sub("[DATE]", line)

        lines.append(line)
    return "\n".join(lines).strip()
