import logging
import sys

class DefaultStageFilter(logging.Filter):
    """Injects a default 'stage' so third-party logs don't crash the formatter."""
    def filter(self, record):
        if not hasattr(record, 'stage'):
            # Grabs the root module name of the third-party library
            record.stage = record.name.split('.')[0].upper()
        return True

def configure_logging():
    """Initializes the global logging singleton."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(stage)s | %(message)s",
        handlers=[
            logging.FileHandler("pipeline.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )

    for handler in logging.getLogger().handlers:
        handler.addFilter(DefaultStageFilter())