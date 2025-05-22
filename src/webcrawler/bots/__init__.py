"""Expose spiders as a proper Python package."""

from .wcat_pdf_spider import WcatPdfSpider  # Import the spider

__all__: list[str] = ["WcatPdfSpider"]
