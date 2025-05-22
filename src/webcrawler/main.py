from __future__ import annotations

import argparse
import logging
import pathlib
import sys
from datetime import datetime
from typing import Any

import yaml
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

_LOG = logging.getLogger(__name__)


def _load_yaml(path: pathlib.Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fp:
        return yaml.safe_load(fp)


def _prepare_output_dir(base: pathlib.Path) -> None:
    (base / "pdfs").mkdir(parents=True, exist_ok=True)
    (base / "logs").mkdir(parents=True, exist_ok=True)


def run(config_path: pathlib.Path) -> None:
    cfg = _load_yaml(config_path)

    output_dir = pathlib.Path(cfg["output_dir"]).expanduser().resolve()
    _prepare_output_dir(output_dir)

    settings = get_project_settings()
    # ------------------------------------------------------------------ #
    #  Dynamically wire run-specific values into Scrapy’s settings
    # ------------------------------------------------------------------ #
    settings.set("LOG_LEVEL", cfg.get("log_level", "INFO"), priority="project")
    settings.set(
        "LOG_FILE",
        str(output_dir / "logs" / f"{datetime.now():%Y%m%d_%H%M%S}.log"),
        priority="project",
    )
    settings.set("FILES_STORE", str(output_dir), priority="project")
    # Enable pipelines if not already active
    settings.set(
        "ITEM_PIPELINES",
        {
            "core.pipelines.PdfDownloadPipeline": 300,
            "core.pipelines.MetadataCsvPipeline": 400,
        },
        priority="project",
    )

    crawler_process = CrawlerProcess(settings=settings)
    crawler_process.crawl(
        "wcat_pdf_spider",
        start_urls=cfg["start_urls"],
        output_dir=str(output_dir),
    )
    crawler_process.start()


def _cli() -> None:
    parser = argparse.ArgumentParser(description="Run a WebCrawler spider from YAML.")
    parser.add_argument("--config", "-c", required=True, type=pathlib.Path)
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)
    run(parser.parse_args().config)


if __name__ == "__main__":
    _cli()
