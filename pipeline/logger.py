"""
logger.py — Cấu hình logging tập trung.

Trong production, log được gửi đến:
  - Console (stdout)  → để Docker/K8s/Airflow capture
  - File              → để debug khi cần

Dùng thư viện logging chuẩn của Python thay vì print().
Lý do: log có timestamp, level, và có thể route đến nhiều nơi.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path

from pipeline.config import LOG_DIR


def get_logger(name: str) -> logging.Logger:
    """
    Tạo logger cho một module.

    Usage (trong mỗi file):
        from pipeline.logger import get_logger
        logger = get_logger(__name__)
        logger.info("Starting extract...")

    Args:
        name: thường là __name__ của module gọi

    Returns:
        Logger đã được cấu hình
    """
    logger = logging.getLogger(name)

    # Tránh thêm handler trùng nếu logger đã được tạo
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    # ── Format ────────────────────────────────────────────────────────
    fmt = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # ── Handler 1: Console (stdout) ───────────────────────────────────
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(fmt)
    logger.addHandler(console_handler)

    # ── Handler 2: File ───────────────────────────────────────────────
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    log_file = LOG_DIR / f"pipeline_{today}.log"

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)   # File ghi cả DEBUG
    file_handler.setFormatter(fmt)
    logger.addHandler(file_handler)

    return logger
