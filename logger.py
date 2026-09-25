"""
Structured Production Logging for KameraPh.
Provides JSON formatting, sensitive field sanitization (API keys, passwords, tokens),
and standard request context tracking.
"""

import os
import re
import sys
import json
import logging
from datetime import datetime

# Regex pattern for sensitive tokens/keys
SENSITIVE_PATTERNS = [
    (re.compile(r'(?i)(api[_-]?key|secret|password|token|authorization)\s*[:=]\s*["\']?([^"\'\s,]+)'), r'\1="[REDACTED]"'),
    (re.compile(r'AIzaSy[A-Za-z0-9_-]{33}'), '[REDACTED_GEMINI_KEY]'),
    (re.compile(r'AQ\.[A-Za-z0-9_-]{50,}'), '[REDACTED_GEMINI_KEY]'),
]

class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Extra metadata if provided
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        if hasattr(record, "studio_id"):
            log_data["studio_id"] = record.studio_id
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        msg_str = json.dumps(log_data)

        # Sanitize sensitive patterns
        for pattern, repl in SENSITIVE_PATTERNS:
            msg_str = pattern.sub(repl, msg_str)

        return msg_str

def setup_logger(name: str = "kameraph") -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    logger.setLevel(getattr(logging, log_level, logging.INFO))

    handler = logging.StreamHandler(sys.stdout)
    if os.getenv("LOG_FORMAT", "json").lower() == "json":
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))

    logger.addHandler(handler)
    return logger

logger = setup_logger()
