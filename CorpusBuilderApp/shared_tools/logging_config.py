import logging


def setup_logging(level: int = logging.INFO, log_file: str | None = None) -> None:
    """Configure basic logging for the application.

    Parameters
    ----------
    level:
        The minimum logging level to capture.
    log_file:
        Optional path to a log file. If provided, logs will be written to this
        file in addition to the console.
    """
    handlers = [logging.StreamHandler()]
    if log_file:
        handlers.append(logging.FileHandler(log_file))

    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=handlers,
    )
