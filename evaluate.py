import docx
import sys
from docx.oxml.ns import qn
from docx.text.paragraph import Paragraph


def iter_all_blocks(doc):
    """
    Yield (source_tag, paragraph_text) for every paragraph in document order,
    walking the raw XML body so that nested table-cell paragraphs are included.
    Mirrors the _iter_all_paragraphs logic in document_processor.py exactly.
    """
    body = doc.element.body
    for child in body.iter():
        if child.tag == qn('w:p'):
            para = Paragraph(child, doc)
            # Determine if this paragraph lives inside a table cell
            parent = child.getparent()
            in_table = False
            while parent is not None:
                if parent.tag == qn('w:tc'):
                    in_table = True
                    break
                parent = parent.getparent()
            source = "table" if in_table else "body"
            yield source, para.text


def load_blocks(filename):
    """Load all text blocks (paragraphs + table cells) from a docx file."""
    doc = docx.Document(filename)
    return list(iter_all_blocks(doc))


def main():
    if len(sys.argv) < 3:
        print("Usage: python evaluate.py <original.docx> <redacted.docx>")
        sys.exit(1)

    orig_file = sys.argv[1]
    redacted_file = sys.argv[2]

    print(f"Loading: {orig_file}")
    orig_blocks = load_blocks(orig_file)

    print(f"Loading: {redacted_file}")
    redacted_blocks = load_blocks(redacted_file)

    orig_total_chars = sum(len(text) for _, text in orig_blocks)
    redact_total_chars = sum(len(text) for _, text in redacted_blocks)

    print(f"\n--- Document Stats ---")
    print(f"Original  : {len(orig_blocks):>6} blocks | {orig_total_chars:>8} chars")
    print(f"Redacted  : {len(redacted_blocks):>6} blocks | {redact_total_chars:>8} chars")
    print(f"Char delta: {redact_total_chars - orig_total_chars:>+8} chars")

    # Pair up blocks by position (both docs should have the same structure)
    min_len = min(len(orig_blocks), len(redacted_blocks))
    diffs = []
    for i in range(min_len):
        source, orig_text = orig_blocks[i]
        _, redact_text = redacted_blocks[i]
        if orig_text != redact_text:
            diffs.append((source, orig_text, redact_text))

    # Also flag any extra blocks in either doc
    extra_orig = len(orig_blocks) - min_len
    extra_redact = len(redacted_blocks) - min_len

    print(f"\n--- Diff Summary ---")
    print(f"Blocks compared : {min_len}")
    print(f"Blocks changed  : {len(diffs)}")
    if extra_orig:
        print(f"Extra blocks in ORIGINAL (unmatched): {extra_orig}")
    if extra_redact:
        print(f"Extra blocks in REDACTED (unmatched): {extra_redact}")

    # Print up to 20 sample diffs, flagging source (body or table cell)
    max_show = 20
    print(f"\n--- Sample Differences (up to {max_show}) ---")
    for i, (source, orig_text, redact_text) in enumerate(diffs[:max_show]):
        print(f"[{source}]")
        print(f"  ORIGINAL : {orig_text}")
        print(f"  REDACTED : {redact_text}")
        print()

    if len(diffs) > max_show:
        print(f"... and {len(diffs) - max_show} more differences not shown.")


if __name__ == "__main__":
    main()
