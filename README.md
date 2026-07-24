# PII Redaction Tool

This project provides a robust, class-based PII redaction tool using Microsoft Presidio and Python-docx.

## Setup Instructions

1. Ensure you have Python 3.9+ and `tesseract-ocr` installed on your system.
   - On Debian/Ubuntu: `sudo apt-get install tesseract-ocr libgl1`
2. Create a virtual environment and install dependencies:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   python -m spacy download en_core_web_lg
   ```
3. Run the tool:
   ```bash
   python main.py "Red Herring Prospectus.docx" "Redacted_Output.docx"
   ```

## Approach

This tool relies on a hybrid approach:
- **NER Model**: It uses Microsoft Presidio backed by the `en_core_web_lg` spaCy model to detect built-in entities like `PERSON`, `LOCATION`, `ORGANIZATION`, `DATE_TIME`, `EMAIL_ADDRESS`, and `PHONE_NUMBER`.
- **Regex-based Custom Recognizers**: It uses configurable regular expressions defined in `config/presidio_config.yaml` to detect Indian PAN cards and Aadhar cards.
- **Image Redaction**: It extracts embedded images from the `.docx` archive, passes them to `presidio-image-redactor` (powered by Tesseract OCR) to draw black bars over text, and injects them back into the document.
- **Contextual Allowlisting**: Terms related to financial figures like "Order", "Cost", and "Revenue" are configured in an allowlist. The analyzer checks the text window surrounding an entity and bypasses redaction if an allowed term is present, ensuring that actual financial figures remain intact.
- **Faker Replacements**: Entities are replaced with contextually realistic fake data (e.g. `PERSON` with a fake name, `EMAIL_ADDRESS` with a fake email) while preserving document formatting at the `run` level.

## Tradeoffs and Observations
- **False Positives**: The `DATE_TIME` recognizer can be overly aggressive, sometimes redacting phrases like "12-month" or generic years. The NER model occasionally misidentifies acronyms (e.g., "SCRR") as `PERSON` entities.
- **False Negatives**: Highly domain-specific company names might be missed if they aren't structured similarly to common organizations.
- **Formatting Constraints**: Applying redaction perfectly across `run` boundaries in `.docx` files is challenging. The current approach manages this by character index mapping, but complex tables or heavily nested text enhancements might occasionally see minor formatting shifts.