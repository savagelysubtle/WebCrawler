"""
Global Scrapy settings shared by *all* spiders.

Only “sensible defaults” live here.  Per-run or per-spider tweaks should be
applied via:

  • Spider.custom_settings      (highest priority after code)
  • YAML -> main.py -> settings.set(..., priority="command")
  • ENV variables               (Scrapy CONFIG precedence)

See Scrapy docs for precedence rules.
"""

from __future__ import annotations

BOT_NAME = "webcrawler"

SPIDER_MODULES = ["webcrawler.bots"]
NEWSPIDER_MODULE = "webcrawler.bots"

# ---- Polite crawling ---------------------------------------------------- #
ROBOTSTXT_OBEY: bool = True  # WCAT has no robots.txt, so this is harmless. :contentReference[oaicite:8]{index=8}
DOWNLOAD_DELAY: float = 0.3
CONCURRENT_REQUESTS_PER_DOMAIN: int = 8
AUTOTHROTTLE_ENABLED: bool = True
AUTOTHROTTLE_START_DELAY: float = 0.5
AUTOTHROTTLE_MAX_DELAY: float = 5.0

# ---- Pipelines ---------------------------------------------------------- #
ITEM_PIPELINES = {
    "webcrawler.core.pipelines.PdfDownloadPipeline": 300,
    "webcrawler.core.pipelines.MetadataCsvPipeline": 400,
}  # lower number = earlier stage  :contentReference[oaicite:9]{index=9}

# ---- Logging ------------------------------------------------------------ #
LOG_LEVEL = "INFO"
# main.py injects a RotatingFileHandler with LOG_FILE; this keeps console tidy.

# ---- Async -------------------------------------------------------------- #
TWISTED_REACTOR = (
    "twisted.internet.asyncioreactor.AsyncioSelectorReactor"  # default anyway
)
