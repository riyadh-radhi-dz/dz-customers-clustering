import logging
from pathlib import Path
import sys

if __package__ is None or __package__ == "":
    project_root = Path(__file__).resolve().parent
    src_dir = project_root / "src"
    if str(src_dir) not in sys.path:
        sys.path.append(str(src_dir))

from dz_customers_clustering.pipeline import run_pipeline


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    run_pipeline()


if __name__ == "__main__":
    main()
