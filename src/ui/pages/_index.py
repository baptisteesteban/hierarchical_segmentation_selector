from typing import Any

import dash_bootstrap_components as dbc
from dash import Dash, Input, Output, State, ctx, dcc, html, no_update

from ._page import AbstractPage


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
                                        "Download Mask",
                                        id="download-segmentation-button",
                                    )
                                ),
                                dbc.Col(
                                    dcc.Upload(
                                        children=[dbc.Button("Import tree")],
                                        id="upload-tree",
                                        accept=".json.gz,application/gzip,application/x-gzip",
                                    )
                                ),
                                dbc.Col(
                                    dbc.Button(
                                        "Export tree",
                                        id="download-tree-button",
                                        disabled=True,
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
            dcc.Download(id="tree-download"),
        ]

        stores = [
            dcc.Store(id="session-source-data"),
            dcc.Store(id="session-state-data"),
            dcc.Store(id="selected-regions-data"),
        ]
        super().__init__(app, "Index", layout, stores)

    def _register_callbacks(self) -> None:
        from src.ui.callbacks.index import (
            display_image,
            download_segmentation,
            download_tree_information,
            load_session_source,
            materialize_session_state,
            plot_dendrogram,
            reduce_selection_state,
        )

        @self._app.callback(
            Output("session-source-data", "data"),
            Input("upload-image", "contents"),
            Input("upload-tree", "contents"),
            prevent_initial_call=True,
        )
        def load_session_source_callback(
            image_contents: str | None,
            tree_contents: str | None,
        ) -> dict[str, Any] | None:
            return load_session_source(
                ctx.triggered_id,
                image_contents,
                tree_contents,
            )

        @self._app.callback(
            Output("session-state-data", "data"),
            Input("session-source-data", "data"),
            Input("n-segments-input", "value"),
            Input("compactness-input", "value"),
            prevent_initial_call=True,
        )
        def materialize_session_state_callback(
            session_source: dict[str, Any] | None,
            n_segments: int | None,
            compactness: float | None,
        ) -> dict[str, Any] | Any:
            if (
                ctx.triggered_id in {"n-segments-input", "compactness-input"}
                and session_source is not None
                and session_source.get("kind") == "tree"
            ):
                return no_update

            return materialize_session_state(
                session_source,
                n_segments,
                compactness,
            )

        @self._app.callback(
            Output("download-tree-button", "disabled"),
            Input("session-state-data", "data"),
        )
        def toggle_tree_export_button(session_state: dict[str, Any] | None) -> bool:
            if session_state is None:
                return True
            return session_state.get("image_data") is None

        @self._app.callback(
            Output("image-graph", "figure"),
            Input("session-state-data", "data"),
            Input("selected-regions-data", "data"),
            Input("selection-color", "value"),
        )
        def display_image_callback(
            session_state: dict[str, Any] | None,
            selected_regions: list[list[bool]] | None,
            selected_color: str,
        ) -> Any:
            image_data = None if session_state is None else session_state.get("image_data")
            label_map = None if session_state is None else session_state.get("label_map")
            border = None if session_state is None else session_state.get("border")
            return display_image(
                image_data,
                label_map,
                selected_regions,
                border,
                selected_color,
            )

        @self._app.callback(
            Output("selected-regions-data", "data"),
            Output("selection-error-alert", "children"),
            Output("selection-error-alert", "is_open"),
            Input("image-graph", "clickData"),
            Input("parent-region-button", "n_clicks"),
            Input("reset-selection-button", "n_clicks"),
            Input("session-state-data", "data"),
            State("selected-regions-data", "data"),
            prevent_initial_call=True,
        )
        def select_region_callback(
            click: dict[str, Any] | None,
            _parent_clicks: int | None,
            _reset_clicks: int | None,
            session_state: dict[str, Any] | None,
            selected_regions: list[list[bool]] | None,
        ) -> tuple[list[list[bool]] | None, str, bool]:
            return reduce_selection_state(
                triggered_id=ctx.triggered_id,
                click=click,
                selected_regions=selected_regions,
                session_state=session_state,
            )

        @self._app.callback(
            Output("segmentation-download", "data"),
            Input("download-segmentation-button", "n_clicks"),
            State("selected-regions-data", "data"),
            prevent_initial_call=True,
        )
        def download_segmentation_callback(
            click: int,
            selected_regions_data: list[list[bool]] | None,
        ) -> dict[str, Any] | None:
            return download_segmentation(click, selected_regions_data)

        @self._app.callback(
            Output("tree-download", "data"),
            Input("download-tree-button", "n_clicks"),
            State("session-state-data", "data"),
            State("selected-regions-data", "data"),
            prevent_initial_call=True,
        )
        def download_tree_callback(
            click: int | None,
            session_state: dict[str, Any] | None,
            selected_regions_data: list[list[bool]] | None,
        ) -> dict[str, Any] | None:
            if session_state is None:
                return None

            return download_tree_information(
                click=click,
                hierarchy_parent=session_state.get("hierarchy_parent"),
                hierarchy_altitude=session_state.get("hierarchy_altitude"),
                label_map_data=session_state.get("label_map"),
                image_data=session_state.get("image_data"),
                selected_regions_data=selected_regions_data,
            )

        @self._app.callback(
            Output("dendrogram-graph", "figure"),
            Input("session-state-data", "data"),
            Input("selected-regions-data", "data"),
            prevent_initial_call=True,
        )
        def plot_dendrogram_callback(
            session_state: dict[str, Any] | None,
            selected_regions: list[list[bool]] | None,
        ) -> Any:
            if session_state is None:
                return plot_dendrogram(None, None)

            return plot_dendrogram(
                session_state.get("hierarchy_parent"),
                session_state.get("hierarchy_altitude"),
                selected_regions=selected_regions,
                label_map=session_state.get("label_map"),
            )
