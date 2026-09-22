class SemanticExtractor:

    def extract(
        self,
        text: str,
    ):
        return {
            "status": "EXTRACTED",
            "text_length": len(text),
            "text": text,
        }