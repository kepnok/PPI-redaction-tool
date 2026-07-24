import docx
import sys

def get_text(filename):
    doc = docx.Document(filename)
    fullText = []
    for para in doc.paragraphs:
        fullText.append(para.text)
    return '\n'.join(fullText)

orig_text = get_text(sys.argv[1])
redacted_text = get_text(sys.argv[2])

print(f"Original length: {len(orig_text)}")
print(f"Redacted length: {len(redacted_text)}")

# Sample 5 differences
orig_lines = orig_text.split('\n')
redact_lines = redacted_text.split('\n')

diff_count = 0
for o, r in zip(orig_lines, redact_lines):
    if o != r:
        print(f"ORIGINAL: {o}")
        print(f"REDACTED: {r}")
        print("---")
        diff_count += 1
        if diff_count >= 15:
            break
