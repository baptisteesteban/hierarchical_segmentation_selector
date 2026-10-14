import pytest

from app import app


@pytest.mark.dash_e2e
def test_001_index_page_renders_without_browser_errors(dash_duo) -> None:
    dash_duo.start_server(app)

    dash_duo.wait_for_text_to_equal("h1", "Hierarchical Segmentation Selector", timeout=10)

    assert dash_duo.find_element("#upload-image") is not None
    assert dash_duo.find_element("#download-segmentation-button") is not None
    assert dash_duo.find_element("#download-tree-button") is not None

    # The export action should stay disabled until a session state is available.
    export_button = dash_duo.find_element("#download-tree-button")
    assert export_button.get_attribute("disabled") in {"true", "disabled"}

    assert dash_duo.get_logs() == []
