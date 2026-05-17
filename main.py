"""
main.py - CLI entry point.
Runs the full EDA pipeline (load → analyse → visualise → report) without
starting the web server. Useful for batch processing or CI pipelines.

Usage:
    python main.py
    python main.py --force-download
    python main.py --no-charts
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import LOG_LEVEL, REPORTS_DIR
from src.data_loader import load_titanic
from src.eda_analysis import full_quality_report
from src.utils import get_logger, save_json
from src.visualizations import generate_all_charts

logger = get_logger("main", LOG_LEVEL)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Titanic EDA — CLI runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--force-download",
        action="store_true",
        help="Re-download the dataset even if a local copy exists.",
    )
    parser.add_argument(
        "--no-charts",
        action="store_true",
        help="Skip chart generation (faster for CI or stats-only runs).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    logger.info("=== Titanic EDA CLI ===")

    # 1. Load data
    logger.info("Step 1/3 — Loading dataset …")
    df = load_titanic(force_download=args.force_download)

    # 2. Analysis
    logger.info("Step 2/3 — Running quality analysis …")
    report = full_quality_report(df)
    report_path = REPORTS_DIR / "quality_report.json"
    save_json(report, report_path)
    logger.info("Quality report saved to %s", report_path)

    # 3. Visualisations
    if not args.no_charts:
        logger.info("Step 3/3 — Generating visualisations …")
        charts = generate_all_charts(df)
        logger.info("Generated %d charts:", len(charts))
        for name, path in charts.items():
            logger.info("  %-25s → %s", name, path)
    else:
        logger.info("Step 3/3 — Skipped (--no-charts flag set).")

    logger.info("=== EDA pipeline complete ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
