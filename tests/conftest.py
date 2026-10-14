from collections.abc import Sequence
from pathlib import Path
import sys

import pytest
from _pytest.config import Config
from _pytest.config.argparsing import Parser
from _pytest.nodes import Item


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def pytest_addoption(parser: Parser) -> None:
    parser.addoption(
        "--run-dash-e2e",
        action="store_true",
        default=False,
        help="Run browser-based Dash end-to-end tests.",
    )


def pytest_collection_modifyitems(config: Config, items: Sequence[Item]) -> None:
    if config.getoption("--run-dash-e2e"):
        return

    skip_marker = pytest.mark.skip(reason="Pass --run-dash-e2e to run Dash browser tests")
    for item in items:
        if "dash_e2e" in item.keywords:
            item.add_marker(skip_marker)
