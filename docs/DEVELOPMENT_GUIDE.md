# WebCrawler Development Guide

This guide provides a comprehensive overview of the `WebCrawler` project's architecture, development workflow, coding conventions, and best practices. It is intended to help current and future developers understand the project and contribute effectively.

## Table of Contents

1.  [Project Goal](#project-goal)
2.  [Core Technologies](#core-technologies)
3.  [Project Architecture](#project-architecture)
    *   [Directory Structure](#directory-structure)
    *   [Key Components and Their Roles](#key-components-and-their-roles)
4.  [Configuration Management](#configuration-management)
    *   [YAML Configuration Files](#yaml-configuration-files)
    *   [Passing Configuration to Spiders](#passing-configuration-to-spiders)
5.  [Data Flow and Output](#data-flow-and-output)
    *   [Scraping Process](#scraping-process)
    *   [PDF Downloading](#pdf-downloading)
    *   [Metadata Generation (CSV)](#metadata-generation-csv)
    *   [Logging](#logging)
6.  [Development Workflow](#development-workflow)
    *   [Setup](#setup)
    *   [Running Spiders](#running-spiders)
    *   [Adding a New Spider](#adding-a-new-spider)
    *   [Modifying Existing Spiders](#modifying-existing-spiders)
7.  [Coding Conventions and Best Practices](#coding-conventions-and-best-practices)
    *   [Python Style (Ruff)](#python-style-ruff)
    *   [Scrapy Best Practices](#scrapy-best-practices)
    *   [Error Handling](#error-handling)
    *   [Code Comments and Documentation](#code-comments-and-documentation)
8.  [Troubleshooting](#troubleshooting)

---

## 1. Project Goal

The primary goal of the `WebCrawler` project is to download PDF documents from specified web pages, initially focusing on decisions from WCAT.BC.CA. The system is designed to be configurable per crawl run, allowing users to specify target URLs and output locations easily. Each run's output (PDFs, metadata, logs) is stored in a distinct, user-defined directory.

## 2. Core Technologies

-   **Python:** The primary programming language.
-   **Scrapy:** The core web crawling and scraping framework.
-   **uv:** For Python environment and package management.
-   **PyYAML:** For parsing YAML configuration files.
-   **Ruff:** For Python linting and formatting.

## 3. Project Architecture

### Directory Structure

```
WebCrawler/
│
├── .venv/                   # Virtual environment managed by uv
├── bots/                    # Scrapy Spider classes
│   ├── __init__.py
│   └── wcat_pdf_spider.py   # Example spider
│
├── configs/                 # YAML configuration files for crawl runs
│   └── wcat_links.yaml      # Example configuration
│
├── core/                    # Main Scrapy project module
│   ├── __init__.py
│   ├── items.py             # Scrapy Item definitions
│   ├── pipelines.py         # Scrapy Item Pipeline definitions
│   ├── settings.py          # Scrapy project settings
│   └── utils.py             # Utility functions
│
├── docs/                    # Project documentation
│   └── DEVELOPMENT_GUIDE.md # This guide
│
├── outputs/                 # Base directory for all crawl run outputs
│   └── [output_dir_from_yaml]/ # Each run's output directory
│       ├── pdfs/              # Downloaded PDF files
│       ├── metadata.csv       # CSV metadata for downloaded items
│       └── logs/              # Log files for the run
│           └── [spider_name].log
│
├── .gitignore
├── main.py                  # Main script to initiate and manage crawls
├── pyproject.toml           # Project metadata and dependencies (for uv)
├── README.md                # General project overview and setup
├── ruff.toml                # Ruff linter/formatter configuration
├── scrapy.cfg               # Scrapy project configuration file
└── uv.toml                  # uv configuration
```

### Key Components and Their Roles

Refer to the `@global` project documentation or the `README.md` for a detailed breakdown of standard Scrapy components (`Spiders`, `Items`, `Pipelines`, `Settings`, `scrapy.cfg`) and their roles within this project.

**Project-Specific Components:**

-   **`main.py`**:
    -   Parses command-line arguments (e.g., path to YAML config file).
    -   Reads the specified YAML configuration.
    -   Creates the `output_dir` (and its subdirectories `pdfs/`, `logs/`) if they don't exist.
    -   Sets up Scrapy `CrawlerProcess` with project settings, potentially overriding some from the YAML (like `LOG_FILE` path and custom settings passed to spiders).
    -   Instantiates and schedules the relevant spider(s) from `WebCrawler/bots/`, passing arguments from the YAML config (e.g., `start_urls`, `output_dir`, and any other custom settings).
-   **`configs/*.yaml`**:
    -   Defines parameters for a specific crawl run.
    -   **Required fields:**
        -   `start_urls`: A list of URLs for the spider to begin crawling.
        -   `output_dir`: The path (relative to `WebCrawler/`) where all outputs for this run will be stored (e.g., `outputs/wcat_run_01`).
    -   **Optional fields:**
        -   Spider-specific arguments (e.g., `download_delay`, `user_agent`, custom parameters for a particular spider). These will be passed to the spider's `__init__` method.
-   **`core/items.py`**:
    -   Defines `scrapy.Item` classes for structured data. For PDF scraping, this will likely include fields for `file_urls` (used by Scrapy's `FilesPipeline`), `original_url` (source page of the PDF), `local_path` (where the PDF is saved), and any other metadata to be saved.
-   **`core/pipelines.py`**:
    -   **PDF Download Pipeline:** A custom or customized Scrapy `FilesPipeline` to download files (PDFs) to the run-specific `output_dir/pdfs/` directory. It should use the `output_dir` passed to the spider.
    -   **Metadata CSV Pipeline:** A custom pipeline to write metadata for each successfully downloaded item into the run-specific `output_dir/metadata.csv` file. This pipeline should also use the `output_dir`. It should open the CSV file in `open_spider` and close it in `close_spider`.
-   **`core/settings.py`**:
    -   Standard Scrapy settings.
    -   `SPIDER_MODULES = ['WebCrawler.bots']`
    -   `NEWSPIDER_MODULE = ['WebCrawler.bots']`
    -   `ITEM_PIPELINES`: Configuration to enable and order the PDF download and metadata CSV pipelines. The PDF pipeline should run before the metadata pipeline if the metadata depends on the download status/path.
    -   Logging settings can be defined here but might be overridden in `main.py` to ensure logs are directed to the run-specific `output_dir/logs/` folder.

## 4. Configuration Management

### YAML Configuration Files

-   Located in `WebCrawler/configs/`.
-   Each file defines a distinct crawl run or a set of parameters for spiders.
-   **Example (`configs/wcat_config.yaml`):**
    ```yaml
    spider_name: "wcat_pdf_spider" # Specifies which spider to run
    start_urls:
      - "https://www.wcat.bc.ca/decisions/"
      # Add more URLs as needed
    output_dir: "outputs/wcat_crawl_june_2024" # Crucial: defines the unique output folder

    # Optional spider-specific settings that will be passed to the spider
    custom_settings_for_spider:
      DOWNLOAD_DELAY: 1.5
      USER_AGENT: "MyResearchBot/1.0 (me@example.com)"
      # Any other key-value pairs needed by the spider's __init__
    ```

### Passing Configuration to Spiders

-   The `main.py` script is responsible for reading the YAML file.
-   The `output_dir` and `start_urls` are passed as arguments to the spider's `__init__` method.
-   Any other key-value pairs under a dedicated section in the YAML (e.g., `custom_settings_for_spider`) can also be passed to the spider's `__init__` method or used to update the spider's `custom_settings` attribute.
-   Spiders should be designed to accept these arguments in their `__init__` method (e.g., `def __init__(self, *args, start_urls=None, output_dir=None, **kwargs):`).

## 5. Data Flow and Output

### Scraping Process

1.  User executes `python main.py --config configs/your_config.yaml`.
2.  `main.py` loads the config, sets up the output directory (`output_dir`), and configures logging for the specified spider to `output_dir/logs/[spider_name].log`.
3.  `main.py` instantiates the spider (e.g., `wcat_pdf_spider`), passing `start_urls`, `output_dir`, and other config parameters.
4.  The spider starts requests to `start_urls`.
5.  The spider's `parse` method (and other callbacks) process responses, identify PDF links, and yield `PdfItem` objects.
    -   A `PdfItem` should contain at least `file_urls` (a list with the PDF URL) and any other metadata to be saved (e.g., source page URL).

### PDF Downloading

-   A customized `FilesPipeline` (or a pipeline using it) in `core/pipelines.py` handles items with `file_urls`.
-   This pipeline must be configured to save files into the `[output_dir]/pdfs/` directory specific to the current run. The `output_dir` should be accessible to the pipeline, likely via `spider.output_dir` (an attribute set on the spider by `main.py`).
-   The pipeline updates the item with information about the download (e.g., local path, status).

### Metadata Generation (CSV)

-   A separate custom pipeline in `core/pipelines.py` receives processed items (after PDF download).
-   This pipeline appends a new row to `[output_dir]/metadata.csv` for each item.
-   The CSV should include: PDF URL, local path of the downloaded PDF, source page URL, timestamp of download, and any other relevant extracted metadata.
-   The pipeline should handle CSV file creation (with headers if it's the first item) in `open_spider` and ensure the file is properly closed in `close_spider`. The CSV path is constructed using the `output_dir`.

### Logging

-   Scrapy's logging is configured in `main.py` before starting the `CrawlerProcess`.
-   Log output for each spider is directed to a file named `[spider_name].log` within the run-specific `[output_dir]/logs/` directory.
-   `LOG_LEVEL` can be set in `core/settings.py` or overridden from the YAML config if needed. `INFO` is a good default for production, `DEBUG` for development.

## 6. Development Workflow

### Setup

1.  Clone the repository.
2.  Ensure `uv` is installed.
3.  Create and activate the virtual environment:
    ```bash
    uv venv
    # PowerShell:
    .venv\Scripts\Activate.ps1
    # bash/zsh:
    # source .venv/bin/activate
    ```
4.  Install dependencies:
    ```bash
    uv pip install -e . # Installs in editable mode, good for development
    # or
    # uv pip install .
    ```

### Running Spiders

-   Activate the virtual environment.
-   Modify or create a YAML config file in `configs/`.
-   Run: `python main.py --config configs/your_config_file.yaml`

### Adding a New Spider

1.  Create a new Python file in `WebCrawler/bots/` (e.g., `new_site_spider.py`).
2.  Define your new spider class, inheriting from `scrapy.Spider`.
    -   Give it a unique `name` attribute (e.g., `name = "new_site"`).
    -   Implement `__init__` to accept `start_urls`, `output_dir`, and any other parameters passed from `main.py` via the YAML config. Store `output_dir` as an instance attribute (e.g., `self.output_dir`).
    -   Implement the `parse` method and any other necessary callbacks to extract data and PDF links.
    -   Yield `PdfItem` objects.
3.  Define a new item type in `core/items.py` if the data structure is different, or reuse `PdfItem`.
4.  Update/create pipelines in `core/pipelines.py` if custom processing is needed for this new spider's items. Ensure existing pipelines can handle the new items or are skipped if not applicable.
5.  Create a new YAML configuration file in `configs/` for your new spider, specifying its `spider_name`, `start_urls`, and `output_dir`.
6.  Test by running `main.py` with the new config.

### Modifying Existing Spiders

1.  Locate the spider file in `WebCrawler/bots/`.
2.  Modify selectors, parsing logic, or item yielding as needed.
3.  If item structure changes, update `core/items.py` and relevant pipelines.
4.  Test thoroughly with an appropriate YAML config.

## 7. Coding Conventions and Best Practices

### Python Style (Ruff)

-   This project uses `Ruff` for linting and formatting. Configuration is in `ruff.toml`.
-   Before committing code, ensure it's formatted and passes linter checks:
    ```bash
    uv run ruff format .
    uv run ruff check . --fix
    ```
-   Adhere to PEP 8 principles.

### Scrapy Best Practices

-   **Selectors:** Use clear, robust CSS or XPath selectors. Avoid overly complex or brittle selectors.
-   **Item Loaders:** For complex item population logic, consider using Scrapy Item Loaders.
-   **Politeness:** Respect `robots.txt` ( `ROBOTSTXT_OBEY = True` in `settings.py` unless a specific reason not to). Configure `DOWNLOAD_DELAY` and `CONCURRENT_REQUESTS_PER_DOMAIN` appropriately in `settings.py` or override per spider/run via YAML config if necessary. Set a descriptive `USER_AGENT`.
-   **Efficiency:** Write efficient parsing logic. Offload data processing to pipelines where appropriate.

### Error Handling

-   Implement `try-except` blocks in spider callbacks and pipeline methods to handle potential errors gracefully (e.g., missing elements during scraping, network issues, file I/O errors).
-   Log errors clearly.
-   For critical errors in pipelines that prevent item processing, raise `DropItem`.

### Code Comments and Documentation

-   Write clear docstrings for all modules, classes, and functions, explaining their purpose, arguments, and return values.
-   Use inline comments to clarify complex or non-obvious logic.
-   Keep this `DEVELOPMENT_GUIDE.md` and the `README.md` updated with any significant changes to architecture or workflow.

## 8. Troubleshooting

-   **Spider not running:**
    -   Check `spider_name` in YAML matches the spider's `name` attribute.
    -   Ensure the spider is in `WebCrawler/bots/` and imported correctly (though `CrawlerProcess` usually handles discovery via `SPIDER_MODULES`).
    -   Check for Python syntax errors in the spider file.
-   **No data scraped:**
    -   Use `scrapy shell <url>` to test selectors.
    -   Add `self.log("Debug message here...")` or use a debugger in your spider's `parse` method.
    -   Check `LOG_LEVEL` (set to `DEBUG` for more verbose output).
-   **Files not downloaded / Metadata not written:**
    -   Verify `ITEM_PIPELINES` in `settings.py` are correctly enabled and ordered.
    -   Check for errors in pipeline code.
    -   Ensure `output_dir` is correctly passed to and used by pipelines.
    -   Confirm the spider is yielding items correctly.
-   **Configuration issues:**
    -   Validate YAML syntax.
    -   Ensure `main.py` is correctly parsing the YAML and passing arguments.