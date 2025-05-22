import csv
import hashlib
import logging
import os

import scrapy
from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem
from scrapy.pipelines.files import FilesPipeline
from scrapy.utils.python import to_bytes

from .items import PdfItem  # Assuming PdfItem is defined in core.items

logger = logging.getLogger(__name__)


class PdfDownloadPipeline(FilesPipeline):
    """
    Downloads PDF files to a run-specific directory based on the spider's output_dir attribute.
    It also populates the local_path field in the item.
    """

    def get_media_requests(self, item, info):
        """Override to handle item file downloads."""
        adapter = ItemAdapter(item)
        if not adapter.get("file_urls"):
            raise DropItem(f"Item has no file_urls: {item}")

        # This will yield requests for each URL in file_urls
        # The file_path method below will determine the storage path
        return [scrapy.Request(x, meta={"item": item}) for x in adapter["file_urls"]]

    def file_path(self, request, response=None, info=None, *, item=None):
        """
        Override to define the download path relative to the spider's output_dir.
        The path will be output_dir/pdfs/filename.pdf.
        """
        if not item:
            # This can happen if the item is not passed correctly or if it's a retry
            # of a file that previously failed and the original item is not available.
            # Fallback or raise an error.
            logger.warning("Item not found in file_path, using default naming.")
            # Default Scrapy behavior uses a hash of the URL as the filename in a 'full' subdirectory.
            # We need a more predictable name, so we try to get it from the URL if possible.
            media_guid = hashlib.sha1(to_bytes(request.url)).hexdigest()
            media_ext = os.path.splitext(request.url)[1]
            if not media_ext:
                media_ext = ".pdf"  # Assume PDF if extension is missing
            return (
                f"pdfs/{media_guid}{media_ext}"  # This path is relative to FILES_STORE
            )

        spider = info.spider
        output_dir = getattr(spider, "output_dir", None)
        if not output_dir:
            logger.error(
                "output_dir not set on spider. PDFs may not be saved correctly."
            )
            # Fallback path or raise an error if output_dir is critical
            # For now, we'll let it potentially fail or use Scrapy's default store if not caught.
            # This should ideally be caught earlier.
            return os.path.join("pdfs", os.path.basename(request.url))

        # Construct the file name, e.g., from the last part of the URL
        original_filename = os.path.basename(request.url)
        if not original_filename.lower().endswith(".pdf"):
            original_filename += ".pdf"  # Ensure it has a .pdf extension

        # The path returned here is relative to the FILES_STORE setting.
        # However, we are setting FILES_STORE dynamically in main.py to be the output_dir.
        # So, this path becomes relative to output_dir.
        return os.path.join("pdfs", original_filename)

    def item_completed(self, results, item, info):
        """
        Override to update item with download path or drop if download failed.
        `results` is a list of 2-tuples (success, file_info_or_failure) for each file.
        """
        adapter = ItemAdapter(item)
        file_paths = [x["path"] for ok, x in results if ok]
        if not file_paths:
            # If only one file_url was expected, this means it failed.
            logger.error(
                f"PDF download failed for item: {item.get('original_url')}, file_urls: {item.get('file_urls')}. Results: {results}"
            )
            raise DropItem(f"Failed to download PDF for {item.get('original_url')}")

        # Assuming one PDF per item for simplicity, take the first path.
        # The path from `file_path` is relative to FILES_STORE (which is output_dir).
        # So, results[0][1]['path'] would be something like 'pdfs/filename.pdf'
        # The absolute path would be os.path.join(spider.output_dir, file_paths[0])
        adapter["local_path"] = file_paths[0]
        logger.info(
            f"PDF downloaded and path set: {adapter['local_path']} for {adapter.get('original_url')}"
        )
        return item


class MetadataCsvPipeline:
    """
    Writes metadata of downloaded items to a CSV file in the run-specific output_dir.
    """

    def __init__(self):
        self.csv_writer = None
        self.csv_file = None
        self.output_dir = None
        self.fieldnames = [
            "original_url",
            "local_path",
            "file_urls",
        ]  # Add other PdfItem fields if needed

    def open_spider(self, spider):
        """
        Called when the spider is opened. Sets up the CSV file.
        """
        self.output_dir = getattr(spider, "output_dir", None)
        if not self.output_dir:
            logger.error(
                "output_dir not set on spider for MetadataCsvPipeline. Cannot write CSV."
            )
            # Optionally, raise NotConfigured or handle as a critical error
            return

        csv_path = os.path.join(self.output_dir, "metadata.csv")

        try:
            # Ensure the directory for the CSV exists (output_dir itself should exist)
            os.makedirs(os.path.dirname(csv_path), exist_ok=True)

            # Open in append mode with newline='' to prevent blank rows
            self.csv_file = open(csv_path, "a", newline="", encoding="utf-8")
            self.csv_writer = csv.DictWriter(self.csv_file, fieldnames=self.fieldnames)

            # Write header only if the file is new/empty
            if os.path.getsize(csv_path) == 0:
                self.csv_writer.writeheader()
            logger.info(f"Opened CSV file for metadata: {csv_path}")
        except OSError as e:
            logger.error(f"Failed to open CSV file {csv_path}: {e}")
            self.csv_file = None  # Ensure it's None if open fails

    def close_spider(self, spider):
        """
        Called when the spider is closed. Closes the CSV file.
        """
        if self.csv_file:
            self.csv_file.close()
            logger.info(f"Closed CSV file for metadata in {self.output_dir}")

    def process_item(self, item, spider):
        """
        Processes the item and writes its metadata to the CSV file.
        This pipeline should run *after* the PdfDownloadPipeline has populated 'local_path'.
        """
        if not self.csv_writer or not self.csv_file:
            logger.warning(
                f"CSV writer not available. Dropping item: {item.get('original_url')}"
            )
            raise DropItem("CSV setup failed, cannot write metadata.")

        if not isinstance(item, PdfItem):
            logger.debug(
                f"Item is not a PdfItem, skipping MetadataCsvPipeline: {type(item)}"
            )
            return item  # Pass through items not relevant to this pipeline

        adapter = ItemAdapter(item)
        # Ensure local_path is present (meaning download was successful)
        if not adapter.get("local_path"):
            logger.warning(
                f"Item for {adapter.get('original_url')} has no local_path. Not writing to CSV."
            )
            # This item might have been dropped by PdfDownloadPipeline or download failed before local_path was set.
            # Depending on strictness, you might raise DropItem here or just log and skip.
            return item  # Or raise DropItem

        try:
            # Prepare data for CSV, ensuring all fieldnames are present
            row_data = {field: adapter.get(field) for field in self.fieldnames}
            self.csv_writer.writerow(row_data)
            logger.debug(f"Wrote metadata to CSV for: {adapter.get('original_url')}")
        except Exception as e:
            logger.error(f"Error writing item to CSV: {e} - Item: {item}")
            # Depending on how critical this is, you might raise DropItem

        return item
