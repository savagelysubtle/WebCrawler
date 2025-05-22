"""
Entry-point launcher that wires YAML → Scrapy.

Why not just “scrapy crawl”?  Because:
  • you want per-run output folders & log files
  • the same code can run programmatically inside other processes
"""

from __future__ import annotations

import argparse
import logging
import pathlib
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler
from typing import Any

import yaml
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

_LOG = logging.getLogger(__name__)


# --------------------------------------------------------------------- #
# Helpers                                                               #
# --------------------------------------------------------------------- #
def _load_yaml(path: pathlib.Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fp:
        return yaml.safe_load(fp)


def _prepare_output_dir(base: pathlib.Path) -> None:
    (base / "pdfs").mkdir(parents=True, exist_ok=True)
    (base / "logs").mkdir(parents=True, exist_ok=True)


def _install_rotating_log(log_file: pathlib.Path, level: str) -> None:
    handler = RotatingFileHandler(log_file, maxBytes=2_000_000, backupCount=3)
    fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    handler.setFormatter(logging.Formatter(fmt))
    logging.root.addHandler(handler)
    logging.root.setLevel(level)


# --------------------------------------------------------------------- #
# Runner                                                                #
# --------------------------------------------------------------------- #
def run(config_path: pathlib.Path) -> None:
    cfg = _load_yaml(config_path)

    try:
        start_urls = cfg["start_urls"]
        out_dir = pathlib.Path(cfg["output_dir"]).expanduser().resolve()
    except KeyError as exc:
        raise SystemExit(f"Missing required key in YAML: {exc}") from exc

    _prepare_output_dir(out_dir)

    settings = get_project_settings()
    settings.set("FILES_STORE", str(out_dir), priority="command")
    settings.set("LOG_LEVEL", cfg.get("log_level", "INFO"), priority="command")

    # Rotating file log
    log_file = out_dir / "logs" / f"{datetime.now():%Y%m%d_%H%M%S}.log"
    _install_rotating_log(log_file, settings["LOG_LEVEL"])

    crawler = CrawlerProcess(settings=settings)
    crawler.crawl(
        "wcat_pdf_spider",
        start_urls=start_urls,
        output_dir=str(out_dir),
    )
    crawler.start()


# --------------------------------------------------------------------- #
# CLI                                                                   #
# --------------------------------------------------------------------- #
def _cli() -> None:
    parser = argparse.ArgumentParser(description="Run a WebCrawler spider from YAML.")
    parser.add_argument(
        "--config", "-c", required=True, type=pathlib.Path, help="Path to YAML file."
    )
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)
    run(parser.parse_args().config)


if __name__ == "__main__":
    _cli()
