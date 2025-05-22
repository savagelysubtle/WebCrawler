"""
Scrapy Items shared by spiders & pipelines.
"""

from __future__ import annotations

import scrapy


class PdfItem(scrapy.Item):
    """Simple item carrying a single PDF URL and its source page."""

    file_urls: scrapy.Field = scrapy.Field()  # used by FilesPipeline
    original_url: scrapy.Field = scrapy.Field()  # WCAT result-page URL
    local_path: scrapy.Field = scrapy.Field()  # filled by pipeline
