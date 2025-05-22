# WebCrawler Project

A Scrapy project designed to crawl websites, extract data (specifically PDFs from WCAT.BC.CA decisions initially), and manage outputs on a per-run basis.

## Project Structure

-   `main.py`: Entry point to run crawls.
-   `configs/`: YAML configuration files for defining crawl parameters (e.g., `start_urls`, `output_dir`).
-   `bots/`: Contains Scrapy spider definitions.
-   `core/`: Scrapy project module.
    -   `items.py`: Item definitions.
    -   `pipelines.py`: Item pipeline definitions (e.g., for downloading files, writing metadata).
    -   `settings.py`: Scrapy project settings.
    -   `utils.py`: Utility functions.
-   `outputs/`: Default base directory for crawl outputs. Each run, as defined by `output_dir` in a YAML config, will create a subdirectory here.
    -   `[output_dir_from_yaml]/`:
        -   `pdfs/`: Stores downloaded PDF files.
        -   `metadata.csv`: Stores metadata about scraped items.
        -   `logs/`: Contains log files for each spider run.
-   `pyproject.toml`: Project dependencies and build configuration (for `uv`).
-   `ruff.toml`: Linter and formatter configuration for `Ruff`.
-   `uv.toml`: `uv` specific configurations.
-   `scrapy.cfg`: Scrapy project configuration file.

## Setup and Installation

This project uses `uv` for environment and package management.

1.  **Create and activate a virtual environment:**
    ```bash
    uv venv
    # On PowerShell:
    .venv\Scripts\Activate.ps1
    # On bash/zsh:
    # source .venv/bin/activate
    ```

2.  **Install dependencies:**
    ```bash
    uv pip install -r requirements.txt
    # or if you want to install directly from pyproject.toml (uv will create/update lock file)
    # uv pip install .
    # or to install in editable mode if you are developing the package itself
    # uv pip install -e .
    ```
    *(Note: `requirements.txt` can be generated using `uv pip freeze > requirements.txt` after installing from `pyproject.toml` if needed for other environments/tools).*

## Running a Crawl

1.  Ensure your virtual environment is activated.
2.  Create or modify a YAML configuration file in the `configs/` directory (e.g., `configs/wcat_links.yaml`). Specify `start_urls` and the `output_dir` for the run.
    Example `configs/wcat_links.yaml`:
    ```yaml
    start_urls:
      - "https://www.wcat.bc.ca/recent-decisions/"
    output_dir: "outputs/wcat_run_01"
    # Optional: spider-specific settings
    # download_delay: 1.0
    # user_agent: "Mozilla/5.0 (compatible; MyScrapyBot/1.0)"
    ```
3.  Execute the main script, passing the path to your configuration file:
    ```bash
    python main.py --config configs/your_config_file.yaml
    ```

## Development

For detailed information on the project architecture, development workflow, and coding conventions, please see the [Development Guide](docs/DEVELOPMENT_GUIDE.md).

-   **Linting and Formatting:** This project uses `Ruff`.
    ```bash
    # Format
    uv run ruff format .
    # Lint
    uv run ruff check .
    # Lint and apply fixes
    uv run ruff check . --fix
    ```

This `README.md` provides a good starting point for understanding and using the project.
