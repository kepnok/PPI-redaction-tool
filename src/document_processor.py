import docx
from docx.text.paragraph import Paragraph
from docx.oxml.ns import qn

from typing import List, Any, Iterator
from .analyzer import RedactionAnalyzer
from .anonymizer import FakeDataAnonymizer

class DocxProcessor:
    """Processes docx files to redact PII while preserving formatting."""
    
    def __init__(self, analyzer: RedactionAnalyzer, anonymizer: FakeDataAnonymizer):
        self.analyzer = analyzer
        self.anonymizer = anonymizer

    def _iter_all_paragraphs(self, doc: docx.Document) -> Iterator[Paragraph]:
        """
        Yield every paragraph in document order, including those inside tables
        and nested tables. python-docx's doc.paragraphs misses table-cell paragraphs;
        doc.tables misses nested tables. This walks the raw XML body to get everything.
        """
        body = doc.element.body
        for child in body.iter():
            if child.tag == qn('w:p'):
                yield Paragraph(child, doc)

    def process_document(self, input_path: str, output_path: str):
        """Main method to process the entire document."""
        doc = docx.Document(input_path)

        for para in self._iter_all_paragraphs(doc):
            self._process_paragraph(para)

        doc.save(output_path)

    def _process_paragraph(self, paragraph: Paragraph):
        """Processes a single paragraph, replacing PII at the run level."""
        text = paragraph.text
        if not text.strip():
            return
            
        # Analyze the full paragraph text
        results = self.analyzer.analyze_text(text)
        if not results:
            return
        
        results = sorted(results, key=lambda x: (x.score, x.end - x.start), reverse=True)

        deduped = []
        for res in results:
            if not any(
                res.start < kept.end and res.end > kept.start
                for kept in deduped
            ):
                deduped.append(res)

        # Now sort in reverse start order for safe in-place replacement
        results = sorted(deduped, key=lambda x: x.start, reverse=True)
        
        run_map = []
        for r_idx, run in enumerate(paragraph.runs):
            for c_idx, char in enumerate(run.text):
                run_map.append((r_idx, c_idx))

        if len(text) != len(run_map):
            self._fallback_process(paragraph, results, text)
            return

        for res in results:
            original_text = text[res.start:res.end]
            fake_text = self.anonymizer.get_fake_value(res.entity_type, original_text)
            
            # The runs involved in this span
            span_runs = run_map[res.start:res.end]
            if not span_runs:
                continue
                
            # Group by run_index
            runs_involved = {}
            for r_idx, c_idx in span_runs:
                if r_idx not in runs_involved:
                    runs_involved[r_idx] = []
                runs_involved[r_idx].append(c_idx)
                
            first_run_idx = list(runs_involved.keys())[0]
            
            for r_idx, char_indices in runs_involved.items():
                run = paragraph.runs[r_idx]
                run_text_list = list(run.text)
                
                for c_idx in sorted(char_indices, reverse=True):
                    if c_idx < len(run_text_list):
                        run_text_list.pop(c_idx)
                
                #
                if r_idx == first_run_idx:
                    min_idx = min(char_indices)
                    run_text_list.insert(min_idx, fake_text)
                    
                run.text = "".join(run_text_list)
                

    def _fallback_process(self, paragraph: Paragraph, results: List[Any], text: str):
        """Simple fallback that replaces text in runs if exact match is found."""
        for res in results:
            original_text = text[res.start:res.end]
            fake_text = self.anonymizer.get_fake_value(res.entity_type, original_text)
            for run in paragraph.runs:
                if original_text in run.text:
                    run.text = run.text.replace(original_text, fake_text)
