#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import logging
import sys
from pathlib import Path

from dotenv import load_dotenv

logger = logging.getLogger(__name__)


def main() -> None:
    """Run administrative tasks."""
    load_dotenv()
    logger.info("Loading environment variables from .env")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        msg = "Couldn't import Django. Are you sure it's installed and available on your PYTHONPATH environment variable? Did you forget to activate a virtual environment?"
        raise ImportError(
            msg,
        ) from exc
    # This allows easy placement of apps within the interior
    # portal directory.
    current_path = Path(__file__).resolve().parent
    sys.path.append(current_path / "portal")

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
