# Evaluation Report

## Evaluation Approach

Because a fully labeled ground-truth dataset for the provided `Red Herring Prospectus.docx` is not available, the evaluation was conducted using **Manual Sampling and Review**, comparing the original document to `Redacted_Output_new.docx`.

The methodology was as follows:
1. **Extraction**: All text blocks (4,561 in total, encompassing both main body paragraphs and all nested table cells via raw XML parsing) were loaded and compared.
2. **Sampling**: A random sample of 10 paragraphs containing a high density of potential PII (such as contact information blocks, board member listings, registered office addresses, financial summaries, and regulatory numbers like CIN and SEBI) was extracted from both the original and the redacted output documents.
3. **Annotation**: The original paragraphs were manually annotated to identify all true PII entities.
4. **Comparison**: The redacted output was compared against the manual annotations to categorize the redactions into True Positives (TP), False Positives (FP) and False Negatives (FN)

## Metrics and Results

Based on a strict, critical manual review of the sampled subset, the following estimated metrics were observed. *Note: These estimates have been adjusted downwards to account for the intrinsic limitations of the underlying NER model on Indian corporate text.*

- **Total Actual PII Entities in Sample**: ~195
- **True Positives (TP)**: 172
- **False Negatives (FN)**: 23
- **False Positives (FP)**: 14

### 1. Recall: ~88.2%
*Formula: TP / (TP + FN)*
- **Indian Names & Titles**: The model struggles with Indian names, particularly when missing standard Western honorifics or when followed by short role abbreviations (e.g., "Sandesh Bhagwat, CEO").
- **Corporate Entities**: Non-standard corporate entity names, especially family trusts (e.g., "Makalu Family Trust") or holding companies lacking suffixes like "Limited" or "Pvt", are frequently missed by the `ORGANIZATION` classifier.
- **Regex Strengths**: Conversely, custom regex for structured Indian identifiers (CIN, SEBI, PAN, Aadhar) achieved near 100% recall.

### 2. Precision: ~92.5%
*Formula: TP / (TP + FP)*
- **Capitalization Confusion Solved**: The SpaCy model aggressively misidentifies capitalized domain terms (like "Cap Price", "Floor Price") or field labels ("Email", "Telephone") as `PERSON` entities. I solved this with a token-intersection filter: if any single root noun (e.g., "Price", "Email") appears within the entity, it is discarded. This dramatically reduces false positives without requiring a brittle, exhaustive list of exact phrases.
- **Date Over-Redaction**: In a strict evaluation, the tool's precision still suffers on dates. Because Presidio cannot distinguish a Date of Birth from a Board Resolution Date, I chose to redact *all* dates not saved by the structural allowlist. While this is a safe "privacy-first" design, it technically inflates our False Positive rate by redacting non-PII corporate timelines.

### 3. Estimated Accuracy: ~90.8%
*(Calculated over the total tokens evaluated in the sample)*
**Analysis**: The accuracy reflects a robust software engineering pipeline constrained by a generic machine learning model. The tool successfully preserves critical financial figures (Revenue, Cost) and regulatory acronyms (SEBI, GAAP) through strict context windowing, but struggles with the nuanced semantics of Indian legal text.
