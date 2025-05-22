from __future__ import annotations

import hashlib
import logging
from collections.abc import Iterable
from io import BytesIO
from pathlib import Path

from itemadapter import ItemAdapter
from scrapy import Request
from scrapy.exporters import CsvItemExporter
from scrapy.pipelines.files import FilesPipeline

_LOG = logging.getLogger(__name__)


class PdfDownloadPipeline(FilesPipeline):
    """Download each PDF to ``FILES_STORE/pdfs/<sha>_<basename>``."""

    FILES_RESULT_FIELD = "local_path"

    # ---------------- LINT: PTH119 & ARG002 ----------------- #
    def file_path(  # type: ignore[override]
        self,
        request: Request,
        _response=None,
        _info=None,
        *,
        _item=None,
    ) -> str:
        """
        Return a unique path for each PDF.

        Format: ``pdfs/<sha1_8>_<basename>``
        """
        basename = Path(request.url.split("?")[0]).name
        sha8 = hashlib.sha1(request.url.encode()).hexdigest()[:8]
        return f"pdfs/{sha8}_{basename}"

    # -------------------------------------------------------- #

    def item_completed(  # type: ignore[override]
        self,
        results: Iterable[tuple[bool, object]],
        item,
        _info=None,
    ):
        adapter = ItemAdapter(item)
        for success, detail in results:
            if not success:
                _LOG.warning(
                    "Failed to download %s → %s", adapter["file_urls"][0], detail
                )
                continue

            rel_path: str = detail["path"]
            abs_path = Path(self.store.basedir, rel_path).as_posix()
            adapter["local_path"] = abs_path
        return item


class MetadataCsvPipeline:
    """Export items once per crawl using Scrapy's CsvItemExporter."""

    exporter: CsvItemExporter | None = None
    file_handle: BytesIO | None = None
    files_store: Path | None = None

    def open_spider(self, _spider) -> None:
        self.files_store = Path(_spider.settings["FILES_STORE"])
        self.files_store.mkdir(exist_ok=True, parents=True)
        self.file_handle = BytesIO()
        self.exporter = CsvItemExporter(self.file_handle, include_headers_line=True)
        self.exporter.start_exporting()

    def close_spider(self, _spider) -> None:
        if self.exporter:
            self.exporter.finish_exporting()
            with open(self.files_store / "metadata.csv", "wb") as f:
                f.write(self.file_handle.getvalue())
