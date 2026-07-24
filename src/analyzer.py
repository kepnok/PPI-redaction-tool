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
        
        # We pass allow_list if there are specific strings to never redact
        # presidio-analyzer doesn't have an built-in allowlist parameter for contextual exclusion,
        # but we can filter results after the fact if they match our allow_list.
        results = self.analyzer.analyze(
            text=text,
            entities=entities,
            language='en',
            score_threshold=0.5
        )
        
        # Filter out results that are in the allow_list (exact match or substring)
        filtered_results = []
        for res in results:
            matched_text = text[res.start:res.end]
            
            if matched_text.strip() in self.allow_list:
                continue
                
            # Hide the bank addresses (LOCATION) but leave the bank name (ORGANIZATION)
            if res.entity_type == "ORGANIZATION" and "bank" in matched_text.lower():
                continue
                
            filtered_results.append(res)
                
        # To handle the requirement "figures related to orders/costs/revenue are allowlisted",
        # if Presidio mistakenly flags a cost or revenue number as a phone number or something else,
        # we can check if the context window around the match contains our allow_list keywords.
        final_results = []
        for res in filtered_results:
            start_context = max(0, res.start - 30)
            end_context = min(len(text), res.end + 30)
            context_window = text[start_context:end_context].lower()
            
            # Check if any allow_list keyword is in the context window around the entity
            should_allow = False
            for allowed_word in self.allow_list:
                if allowed_word.lower() in context_window:
                    # If it's a date or person, maybe we still redact, but for numbers we allowlist.
                    # Since requirements state allowlisting these figures, we skip redaction.
                    should_allow = True
                    break
            
            if not should_allow:
                final_results.append(res)
                
        return final_results
