import scrapy


class PdfItem(scrapy.Item):
    """
    Represents a PDF item to be downloaded and its metadata.
    """

    file_urls = (
        scrapy.Field()
    )  # URL(s) of the file(s) to download (used by FilesPipeline)
    original_url = scrapy.Field()  # The URL of the page where the PDF link was found
    local_path = scrapy.Field()  # The local path where the PDF is stored after download
    # Add any other metadata fields you might need, e.g.:
    # title = scrapy.Field()
    # publication_date = scrapy.Field()
