"""
utils/logger.py — Logger dùng chung cho toàn pipeline.

Mỗi module gọi:
    from pipeline.utils.logger import get_logger
    logger = get_logger(__name__)
"""

import logging
import sys
from datetime import datetime

from pipeline.utils.config import LOG_DIR


def get_logger(name: str) -> logging.Logger:
    """
    Tạo logger ghi ra cả console lẫn file.

    Args:
        name: thường truyền __name__ để biết log từ module nào

    Returns:
        Logger đã cấu hình
    """
    logger = logging.getLogger(name)
    if logger.handlers:          # Tránh thêm handler trùng
        return logger

    logger.setLevel(logging.DEBUG)
    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)-35s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console — INFO trở lên
    sh = logging.StreamHandler(sys.stdout)
    sh.setLevel(logging.INFO)
    sh.setFormatter(fmt)
    logger.addHandler(sh)

    # File — DEBUG trở lên (ghi tất cả)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    fh = logging.FileHandler(
        LOG_DIR / f"pipeline_{datetime.now():%Y-%m-%d}.log",
        encoding="utf-8",
    )
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    return logger
