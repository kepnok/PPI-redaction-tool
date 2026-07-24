from presidio_analyzer import AnalyzerEngine, PatternRecognizer, Pattern
from typing import List, Dict, Any

class RedactionAnalyzer:
    """Wrapper class for Presidio AnalyzerEngine."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.analyzer = AnalyzerEngine()
        self.default_entities = self.config.get("default_entities", [])
        self.allow_list = self.config.get("allow_list", [])
        
        self._register_custom_recognizers()

    def _register_custom_recognizers(self):
        """Registers custom regex recognizers defined in the YAML config."""
        custom_recognizers_config = self.config.get("custom_recognizers", [])
        for rec_conf in custom_recognizers_config:
            patterns = []
            for pat_conf in rec_conf.get("patterns", []):
                pattern = Pattern(
                    name=pat_conf["name"],
                    regex=pat_conf["pattern"],
                    score=pat_conf["score"]
                )
                patterns.append(pattern)
                
            recognizer = PatternRecognizer(
                supported_entity=rec_conf["supported_entity"],
                patterns=patterns,
                context=rec_conf.get("context", [])
            )
            self.analyzer.registry.add_recognizer(recognizer)

    def analyze_text(self, text: str) -> List[Any]:
        """Analyzes text for PII entities."""
        if not text.strip():
            return []
            
        entities = self.default_entities + [
            rec["supported_entity"] for rec in self.config.get("custom_recognizers", [])
        ]
        
        results = self.analyzer.analyze(
            text=text,
            entities=entities,
            language='en',
            score_threshold=0.5
        )

        allow_list_lower = set(w.lower() for w in self.allow_list)

        import re
        
        filtered_results = []
        for res in results:
            matched_text = text[res.start:res.end]
            clean_match = matched_text.lower()
            
            should_allow = False
            for allowed in self.allow_list:
                if re.search(r'\b' + re.escape(allowed.lower()) + r'\b', clean_match):
                    should_allow = True
                    break
                    
            if should_allow:
                continue
                
            if res.entity_type == "ORGANIZATION" and re.search(r'\bbank\b', clean_match):
                continue
                
            filtered_results.append(res)
       
        ALWAYS_REDACT = {
            "PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER",
            "US_SSN", "CREDIT_CARD", "IP_ADDRESS",
            "IN_PAN", "IN_AADHAR", "IN_SEBI", "IN_CIN",
            "ORGANIZATION",
        }

        final_results = []
        for res in filtered_results:
            if res.entity_type in ALWAYS_REDACT:
                final_results.append(res)
                continue

            start_context = max(0, res.start - 30)
            end_context = min(len(text), res.end + 30)
            context_window = text[start_context:end_context].lower()

            should_allow = False
            for allowed in self.allow_list:
                if re.search(r'\b' + re.escape(allowed.lower()) + r'\b', context_window):
                    should_allow = True
                    break

            if not should_allow:
                final_results.append(res)

        return final_results
