from typing import Any

import dash_bootstrap_components as dbc
import numpy as np
from dash import Dash, Input, Output, State, ctx, dcc, html
from loguru import logger

from ._page import AbstractPage


def _selected_labels_from_mask(
    selected_mask: np.ndarray, label_map: np.ndarray
) -> list[int]:
    if selected_mask.shape != label_map.shape:
        raise ValueError("Selection shape does not match current label-map shape")
    return [int(label) for label in np.unique(label_map[selected_mask]).tolist()]


class IndexPage(AbstractPage):
    def __init__(self, app: Dash):
        layout = [
            dbc.Container(
                [
                    html.H1("Hierarchical Segmentation Selector"),
                    html.Hr(),
                    dbc.Card(
                        dbc.Row(
                            [
                                dbc.Col(
                                    dcc.Upload(
                                        children=[dbc.Button("Open Image")],
                                        id="upload-image",
                                        accept="image/*",
                                    )
                                ),
                                dbc.Col(
                                    dbc.Button(
                                        "Reset selection",
                                        id="reset-selection-button",
                                    )
                                ),
                                dbc.Col(
                                    dbc.Button(
                                        "Download Segmentation",
                                        id="download-segmentation-button",
                                    )
                                ),
                                dbc.Col(
                                    [
                                        dbc.Input(
                                            type="color",  # type: ignore
                                            id="selection-color",
                                            value="#FF0000",
                                        )
                                    ]
                                ),
                            ]
                        ),
                        body=True,
                    ),
                    html.Hr(),
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    dbc.Card(
                                        [
                                            dbc.Label("Number of segments"),
                                            dbc.Input(
                                                id="n-segments-input",
                                                type="number",
                                                value=10,
                                            ),
                                        ],
                                        body=True,
                                    )
                                ]
                            ),
                            dbc.Col(
                                [
                                    dbc.Card(
                                        [
                                            dbc.Label("Compactness"),
                                            dbc.Input(
                                                id="compactness-input",
                                                type="number",
                                                value=10,
                                            ),
                                        ],
                                        body=True,
                                    )
                                ]
                            ),
                            dbc.Col(
                                [
                                    dbc.Card(
                                        [
                                            dbc.Button(
                                                "Parent region",
                                                id="parent-region-button",
                                                color="primary",
                                            )
                                        ],
                                        body=True,
                                    )
                                ]
                            ),
                        ]
                    ),
                    dbc.Row(
                        [
                            dbc.Col(
                                dcc.Graph(
                                    id="image-graph",
                                    style={
                                        "width": "100%",
                                        "height": "calc(100vh - 400px)",
                                    },
                                )
                            ),
                            dbc.Col(
                                dcc.Graph(
                                    id="dendrogram-graph",
                                    style={
                                        "width": "100%",
                                        "height": "calc(100vh - 400px)",
                                    },
                                )
                            ),
                        ]
                    ),
                    dbc.Alert(
                        id="selection-error-alert",
                        color="danger",
                        is_open=False,
                        duration=4000,
                    ),
                ],
                style={"display": "flex", "flexDirection": "column", "height": "100vh"},
            ),
            dcc.Download(id="segmentation-download"),
        ]

        stores = [
            dcc.Store(id="image-data"),
            dcc.Store(id="label-map-data"),
            dcc.Store(id="selected-regions-data"),
            dcc.Store(id="border-data"),
            dcc.Store(id="hierarchy-parent-data"),
            dcc.Store(id="hierarchy-altitude-data"),
        ]
        super().__init__(app, "Index", layout, stores)

    def _register_callbacks(self) -> None:
        from src.ui.callbacks.index import (
            compute_clustering,
            compute_label_map,
            display_image,
            download_segmentation,
            load_image,
            plot_dendrogram,
            select_parent_cluster,
            select_region,
        )

        @self._app.callback(
            Output("image-data", "data"),
            Input("upload-image", "contents"),
            prevent_initial_call=True,
        )
        def load_image_callback(contents: str) -> list[list[list[int]]]:
            return load_image(contents)

        @self._app.callback(
            Output("label-map-data", "data"),
            Output("border-data", "data"),
            Input("image-data", "data"),
            Input("n-segments-input", "value"),
            Input("compactness-input", "value"),
            prevent_initial_call=True,
        )
        def compute_label_map_callback(
            image_data: list[list[list[int]]] | None,
            n_segments: int,
            compactness: float,
        ) -> tuple[list[list[int]] | None, list[list[bool]] | None]:
            return compute_label_map(image_data, n_segments, compactness)

        @self._app.callback(
            Output("image-graph", "figure"),
            Input("image-data", "data"),
            Input("label-map-data", "data"),
            Input("selected-regions-data", "data"),
            Input("border-data", "data"),
            Input("selection-color", "value"),
        )
        def display_image_callback(
            image_data: list[list[list[int]]] | None,
            label_map: list[list[int]] | None,
            selected_regions: list[list[bool]] | None,
            border: list[list[bool]] | None,
            selected_color: str,
        ) -> Any:
            return display_image(
                image_data, label_map, selected_regions, border, selected_color
            )

        @self._app.callback(
            Output("selected-regions-data", "data"),
            Output("selection-error-alert", "children"),
            Output("selection-error-alert", "is_open"),
            Input("image-graph", "clickData"),
            Input("parent-region-button", "n_clicks"),
            Input("reset-selection-button", "n_clicks"),
            Input("border-data", "data"),
            Input("image-data", "data"),
            Input("n-segments-input", "value"),
            Input("compactness-input", "value"),
            State("selected-regions-data", "data"),
            State("label-map-data", "data"),
            State("hierarchy-parent-data", "data"),
            prevent_initial_call=True,
        )
        def select_region_callback(
            click: dict[str, Any] | None,
            parent_clicks: int | None,
            reset_clicks: int | None,
            borders: list[list[bool]] | None,
            image_data: list[list[list[int]]] | None,
            n_segments: int | None,
            compactness: float | None,
            selected_regions: list[list[bool]] | None,
            label_map: list[list[int]] | None,
            hierarchy_parent: list[int] | None,
        ) -> tuple[list[list[bool]] | None, str, bool]:
            triggered = ctx.triggered_id
            if triggered == "reset-selection-button":
                if label_map is None:
                    return None, "", False
                label_map_np = np.asarray(label_map)
                return np.zeros_like(label_map_np, dtype=bool).tolist(), "", False

            if triggered == "parent-region-button" and hierarchy_parent is not None:
                if selected_regions is None or label_map is None:
                    return None, "No selection is available to expand.", True
                selected_mask = np.asarray(selected_regions, dtype=bool)
                label_map_np = np.asarray(label_map)
                try:
                    selected_labels = _selected_labels_from_mask(
                        selected_mask=selected_mask,
                        label_map=label_map_np,
                    )
                except ValueError as exc:
                    logger.warning(f"Parent-region selection rejected: {exc}")
                    return (
                        selected_regions,
                        "Selection is out of sync with the current segmentation. Recompute segmentation or reset selection.",
                        True,
                    )

                if not selected_labels:
                    return selected_regions, "Select at least one region first.", True

                try:
                    next_labels = select_parent_cluster(
                        selected_labels, hierarchy_parent
                    )
                except ValueError as exc:
                    logger.warning(f"Parent-region hierarchy error: {exc}")
                    return selected_regions, str(exc), True
                selected_regions_np = np.zeros_like(label_map_np, dtype=bool)
                for label in next_labels:
                    selected_regions_np[label_map_np == int(label)] = True
                return selected_regions_np.tolist(), "", False

            return (
                select_region(
                    click=click,
                    borders=borders,
                    selected_regions=selected_regions,
                    label_map=label_map,
                    image_data=image_data,
                    triggered_id=triggered,
                    parents=hierarchy_parent,
                ),
                "",
                False,
            )

        @self._app.callback(
            Output("segmentation-download", "data"),
            Input("download-segmentation-button", "n_clicks"),
            State("selected-regions-data", "data"),
            prevent_initial_call=True,
        )
        def download_segmentation_callback(
            click: int, selected_regions_data: list[list[bool]] | None
        ) -> dict[str, Any] | None:
            return download_segmentation(click, selected_regions_data)

        @self._app.callback(
            Output("hierarchy-parent-data", "data"),
            Output("hierarchy-altitude-data", "data"),
            Input("label-map-data", "data"),
            State("image-data", "data"),
            prevent_initial_call=True,
        )
        def compute_clustering_callback(
            label_map: list[list[int]] | None, img: list[list[list[int]]] | None
        ) -> tuple[list[int] | None, list[float] | None]:
            return compute_clustering(label_map, img)

        @self._app.callback(
            Output("dendrogram-graph", "figure"),
            Input("hierarchy-parent-data", "data"),
            Input("hierarchy-altitude-data", "data"),
            Input("selected-regions-data", "data"),
            Input("label-map-data", "data"),
            prevent_initial_call=True,
        )
        def plot_dendrogram_callback(
            parent: list[int] | None,
            altitude: list[Any] | None,
            selected_regions: list[list[bool]] | None,
            label_map: list[list[int]] | None,
        ) -> Any:
            selected_labels = None
            if selected_regions is not None and label_map is not None:
                selected_mask = np.asarray(selected_regions, dtype=bool)
                label_map_np = np.asarray(label_map)
                if selected_mask.shape == label_map_np.shape:
                    selected_labels = np.unique(label_map_np[selected_mask]).tolist()
            return plot_dendrogram(parent, altitude, selected_labels)
