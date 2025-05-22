from __future__ import annotations

import pathlib
from urllib.parse import urljoin

import scrapy
from scrapy.http import Response

from webcrawler.core.items import PdfItem


class WcatPdfSpider(scrapy.Spider):
    """
    Crawl WCAT `search-past-decisions` result pages and yield one
    :class:`core.items.PdfItem` per decision PDF.

    The spider relies on two run-time arguments set by *main.py*
    (loaded from YAML):
      • ``start_urls`` – list[str]
      • ``output_dir`` – str | pathlib.Path  (forwarded to pipelines)

    Pagination uses the `/page/<n>/` pattern that WCAT renders when a
    “>`” link is present in the pager block:contentReference[oaicite:0]{index=0}.
    """

    name = "wcat_pdf_spider"
    custom_settings = {
        # throttle politely – override per-run in YAML if needed
        "DOWNLOAD_DELAY": 0.3,
        "ROBOTSTXT_OBEY": True,
    }

    def __init__(
        self,
        *args: object,
        start_urls: list[str] | None = None,
        output_dir: str | pathlib.Path | None = None,
        **kwargs: object,
    ) -> None:
        super().__init__(*args, **kwargs)
        if not start_urls:
            raise ValueError("start_urls must be supplied via YAML config.")
        self.start_urls = start_urls
        # Pipelines look for this attribute
        self.output_dir = (
            pathlib.Path(output_dir).expanduser().resolve() if output_dir else None
        )

    # --------------------------------------------------------------------- #
    # PARSING
    # --------------------------------------------------------------------- #
    def parse(self, response: Response) -> scrapy.Request | PdfItem | None:  # type: ignore[override]
        """Extract every “Download the decision” link and follow pagination."""
        # -- Grab PDF links ------------------------------------------------ #
        for href in response.css('a[href$=".pdf"]::attr(href)').getall():
            full_url = urljoin(response.url, href)
            yield PdfItem(file_urls=[full_url], original_url=response.url)

        # -- Follow “next page” ------------------------------------------- #
        next_href = (
            response.css('a[rel="next"]::attr(href)').get()
            or response.xpath('//a[normalize-space(text())=">"]/@href').get()
        )
        if next_href:
            yield response.follow(next_href, callback=self.parse)
