from typing import Any

from ._select_region import select_region
from ._session_state import SessionState


def reduce_selection_state(
    triggered_id: str | None,
    click: dict[str, Any] | None,
    selected_regions: list[list[bool]] | None,
    session_state: SessionState | None,
) -> tuple[list[list[bool]] | None, str, bool]:
    if triggered_id == "session-state-data":
        if session_state is None:
            return None, "", False
        return session_state["initial_selected_regions"], "", False

    if session_state is None:
        return None, "", False

    return select_region(
        click=click,
        selected_regions=selected_regions,
        label_map=session_state["label_map"],
        image_data=session_state["image_data"],
        triggered_id=triggered_id,
        parents=session_state["hierarchy_parent"],
    )
