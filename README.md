# PII Redaction Tool

A structured, class-based PII redaction tool built with Microsoft Presidio, python-docx, and Faker. It reads a `.docx` file, identifies personally identifiable information (PII), replaces it with realistic fake data, and writes a clean redacted `.docx` file — preserving all text formatting such as bold, italics, and font sizes.

## Setup Instructions

1. **System Dependencies** — Install Tesseract OCR and the OpenGL library required by OpenCV:
   ```bash
   sudo apt-get install tesseract-ocr libgl1
   ```

2. **Python Environment** — Create a virtual environment and install dependencies:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   python -m spacy download en_core_web_lg
   ```

3. **Run the Tool**:
   ```bash
   python main.py "Red Herring Prospectus.docx" "Redacted_Output.docx"
   ```

## PII Coverage

| PII Type | Detected By | Fake Replacement |
|---|---|---|
| Full names | SpaCy NER (`PERSON`) | `faker.name()` |
| Email addresses | Presidio built-in (`EMAIL_ADDRESS`) | `faker.email()` |
| Phone numbers | Presidio built-in (`PHONE_NUMBER`) | `faker.phone_number()` |
| Company names | SpaCy NER (`ORGANIZATION`) | `faker.company()` |
| Physical addresses | SpaCy NER (`LOCATION`) | `faker.city()` |
| SSNs | Presidio built-in (`US_SSN`) | `faker.ssn()` |
| Credit card numbers | Presidio built-in (`CREDIT_CARD`) | `faker.credit_card_number()` |
| Dates of birth / dates | Presidio built-in (`DATE_TIME`) | `faker.date()` |
| IP addresses | Presidio built-in (`IP_ADDRESS`) | `faker.ipv4()` |
| Indian PAN Card | Custom regex (`IN_PAN`) | Fake PAN format |
| Indian Aadhar Card | Custom regex (`IN_AADHAR`) | Fake 12-digit number |
| SEBI Registration No. | Custom regex + context (`IN_SEBI`) | Fake `IN` + 10 chars |
| CIN (Corporate Identity No.) | Custom regex (`IN_CIN`) | Fake CIN format |
| Embedded image text | Tesseract OCR via `presidio-image-redactor` | Black bar drawn over text |

## Approach

This tool uses a **hybrid strategy**:

- **NER Model**: Microsoft Presidio backed by the `en_core_web_lg` spaCy model detects semantic entities (names, locations, organisations).
- **Regex Recognizers**: Custom patterns defined in `config/presidio_config.yaml` cover structured Indian identifiers (PAN, Aadhar, SEBI, CIN).
- **Contextual Score Thresholding**: Regex patterns with a low base score (e.g., SEBI) only fire when context words like "sebi" or "registration" appear nearby, preventing false matches on regular English words.
- **Contextual Allowlisting**: A configurable allowlist prevents redaction of numbers near financial terms (Order, Revenue, Cost) and legal citations (Act, Section, Regulation), preserving critical business figures in the document.
- **Format-Preserving Replacement**: The document is parsed at paragraph level for analysis, but replacements are applied at the `run` level, preserving bold, italics, font size, and colour.
- **Consistent Fake Mapping**: A `mapping` dictionary ensures the same real name always maps to the same fake name throughout the entire document.
- **Image Redaction**: Embedded images in the `.docx` zip archive are extracted, run through `presidio-image-redactor` (Tesseract OCR), and reinjected with black bars drawn over any detected text.

## Tradeoffs and Known Limitations

### Date Redaction — Privacy-First by Design
The assignment specifies **dates of birth** as the minimum PII to redact. However, Presidio's `DATE_TIME` recognizer cannot inherently distinguish a date of birth from a document signing date, a board resolution date, or an audit period date — they are all syntactically identical.

Rather than under-redact (which risks exposing sensitive information), this tool takes a **privacy-first stance**: all specific dates are redacted by default. Document creation dates, engagement letter dates, and board resolution dates are redacted alongside dates of birth, because:
- They often reveal the timeline of confidential corporate decisions.
- A reader with partial context could use them to correlate against public filings.
- Erring on the side of privacy is safer than erring on the side of readability.

A targeted allowlist mitigates the most disruptive false positives:
- **Legal citations** (`Act`, `Section`, `Regulation`) — years in phrases like "Companies Act, 1956" are preserved.
- **Fiscal calendar structure** (`fiscal`, `commences`, `calendar year`, `period`, `month`) — structural phrases like "financial year commences on April 1" and "three-month period" are preserved.
- **Reporting dates** (`March 31, 2024`) near clearly structural context (Fiscal Year references) are largely preserved.

### SpaCy NER Inconsistency on Names and Entities
The `en_core_web_lg` spaCy model can inconsistently detect person and company names depending on surrounding grammatical context or structural phrasing.
- **Person Names:** Names followed by short role abbreviations (e.g. "Sandesh Bhagwat, CEO") are sometimes missed, while names followed by longer descriptors ("Ganesh Prasad, Technical Director") are caught. Specific surnames like "Hegde" can also be inconsistently classified depending on their position in a sentence.
- **Company / Trust Entities:** Organizations containing words like "Trust" or family names are sometimes redacted and sometimes missed by the `ORGANIZATION` classifier, as the model struggles with non-standard corporate entity names. 

This is a known limitation of general-purpose NER models applied to domain-specific legal text. A fine-tuned model trained on Indian corporate prospectuses would improve recall significantly.

### Country and Acronym Allowlist
Country names (`India`, `US`, `EU`, `Sweden`) and financial/regulatory acronyms (`GAAP`, `IFRS`, `SEBI`, `SCRR`, `ICAI`) are explicitly allowlisted to prevent the SpaCy LOCATION/PERSON classifiers from replacing them with fake city names. These terms carry structural or regulatory meaning in the document that must be preserved.

### Bank Name Preservation
Bank names are explicitly excluded from `ORGANIZATION` redaction (any entity containing the word "bank"). Their physical addresses, however, are still caught by the `LOCATION` recognizer and redacted. This preserves the institution's identity while hiding specific branch locations.

### Cross-Run Formatting Consistency
The `Faker` library is seeded and all replacements are stored in a persistent mapping dictionary for each document run. This means the same real name will always map to the same fake name **within a single run**. However, the mapping is not persisted across separate runs, so running the tool twice on the same document will produce different fake names each time.

### Cross-Run Span Handling
Presidio detects entities over the full paragraph text, but `python-docx` stores text in `Run` fragments (each with its own formatting). When an entity spans multiple runs, the tool maps character indices back to individual runs and reconstructs the replacement correctly in the first run while clearing the others. Complex nested formatting in large tables can occasionally cause minor alignment shifts.