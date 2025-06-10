class CollectorMetadataValidator:
    """Utility to validate collector output metadata."""

    def validate_metadata(self, metadata: dict) -> bool:
        required_keys = ["title", "source_url", "domain"]
        missing = [k for k in required_keys if k not in metadata]
        if missing:
            print(f"Missing metadata keys: {missing}")
            return False
        return True
