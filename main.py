import argparse
import sys
from src.config import ConfigManager
from src.analyzer import RedactionAnalyzer
from src.anonymizer import FakeDataAnonymizer
from src.document_processor import DocxProcessor
from src.image_processor import ImageProcessor

def main():
    parser = argparse.ArgumentParser(description="PII Redaction Tool using Presidio")
    parser.add_argument("input_file", help="Path to the input .docx file")
    parser.add_argument("output_file", help="Path for the output redacted .docx file")
    args = parser.parse_args()

    print("Loading configuration...")
    config_manager = ConfigManager()
    
    print("Initializing Analyzer...")
    analyzer = RedactionAnalyzer(config_manager.analyzer_config)
    
    print("Initializing Anonymizer...")
    anonymizer = FakeDataAnonymizer(config_manager.anonymizer_config)
    
    print("Initializing Document Processor...")
    docx_processor = DocxProcessor(analyzer, anonymizer)
    
    print("Processing Document Text...")
    try:
        docx_processor.process_document(args.input_file, args.output_file)
    except Exception as e:
        print(f"Error processing document text: {e}")
        sys.exit(1)
        
    print("Processing Document Images...")
    try:
        image_processor = ImageProcessor(analyzer.analyzer)
        image_processor.process_images_in_docx(args.output_file)
    except Exception as e:
        print(f"Error processing document images: {e}")
        
    print(f"Redaction complete. Output saved to {args.output_file}")

if __name__ == "__main__":
    main()
