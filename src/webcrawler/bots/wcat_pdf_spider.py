from __future__ import annotations

import pathlib
from typing import Any, ClassVar, Final  # NEW
from urllib.parse import urljoin

import scrapy
from scrapy.http import Response

from webcrawler.core.items import PdfItem


class WcatPdfSpider(scrapy.Spider):
    """Spider that crawls WCAT "search-past-decisions" pages for PDFs."""

    name: Final[str] = "wcat_pdf_spider"

    # --------------------------- LINT: RUF012 --------------------------- #
    allowed_domains: ClassVar[list[str]] = ["wcat.bc.ca"]

    custom_settings: ClassVar[dict[str, Any]] = {  # type: ignore[assignment]
        # Spider-local politeness - can still be overridden by YAML
        "DOWNLOAD_DELAY": 0.3,
        "ROBOTSTXT_OBEY": True,
    }
    # ------------------------------------------------------------------- #

    def __init__(
        self,
        *args,
        start_urls: list[str] | None = None,
        output_dir: str | pathlib.Path | None = None,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        if not start_urls:
            raise ValueError("start_urls must be supplied via YAML config")

        self.start_urls = start_urls
        self.output_dir = (
            pathlib.Path(output_dir).expanduser().resolve() if output_dir else None
        )

    # ------------------------------------------------------------------ #
    def parse(self, response: Response):  # type: ignore[override]
        """Yield :class:`PdfItem` for every PDF, then follow pagination."""
        for href in response.css('a[href$=".pdf"]::attr(href)').getall():
            yield PdfItem(
                file_urls=[urljoin(response.url, href)],
                original_url=response.url,
            )

        # Pagination - robust to glyph or aria-label
        next_href = (
            response.css('a[rel="next"]::attr(href)').get()
            or response.css('a[aria-label*="Next"]::attr(href)').get()
            or response.xpath('//a[normalize-space(text())=">"]/@href').get()
        )
        if next_href:
            yield response.follow(next_href, callback=self.parse)
