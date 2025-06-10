class ExceptionLoggingMixin:
    """Mixin providing optional exception logging."""
    def log_exception(self, context: str, exc: Exception):
        if hasattr(self, "logger"):
            self.logger.error(f"[{context}] {type(exc).__name__}: {exc}")
        else:
            print(f"[{context}] {type(exc).__name__}: {exc}")
