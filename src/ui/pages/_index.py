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
            dcc.Store(id="image-data"),
            dcc.Store(id="label-map-data"),
            dcc.Store(id="selected-regions-data"),
            dcc.Store(id="border-data"),
            dcc.Store(id="hierarchy-parent-data"),
            dcc.Store(id="hierarchy-altitude-data"),
            dcc.Store(id="tree-import-mode", data=False),
        ]
        super().__init__(app, "Index", layout, stores)

    def _register_callbacks(self) -> None:
        from src.ui.callbacks.index import (
            compute_clustering,
            compute_label_map,
            download_tree_information,
            display_image,
            download_segmentation,
            load_image,
            plot_dendrogram,
            select_region,
            upload_tree_information,
        )

        @self._app.callback(
            Output("image-data", "data"),
            Output("tree-import-mode", "data"),
            Input("upload-image", "contents"),
            prevent_initial_call=True,
        )
        def load_image_callback(contents: str) -> tuple[list[list[list[int]]], bool]:
            return load_image(contents), False

        @self._app.callback(
            Output("download-tree-button", "disabled"),
            Input("image-data", "data"),
        )
        def toggle_tree_export_button(
            image_data: list[list[list[int]]] | None,
        ) -> bool:
            return image_data is None

        @self._app.callback(
            Output("label-map-data", "data"),
            Output("border-data", "data"),
            Output("tree-import-mode", "data", allow_duplicate=True),
            Input("image-data", "data"),
            Input("n-segments-input", "value"),
            Input("compactness-input", "value"),
            State("tree-import-mode", "data"),
            prevent_initial_call=True,
        )
        def compute_label_map_callback(
            image_data: list[list[list[int]]] | None,
            n_segments: int,
            compactness: float,
            tree_import_mode: bool | None,
        ) -> tuple[list[list[int]] | None, list[list[bool]] | None, bool]:
            if tree_import_mode and ctx.triggered_id == "image-data":
                return no_update, no_update, no_update
            label_map, border = compute_label_map(image_data, n_segments, compactness)
            return label_map, border, False

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
            State("tree-import-mode", "data"),
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
            tree_import_mode: bool | None,
        ) -> tuple[list[list[bool]] | None, str, bool]:
            if tree_import_mode and ctx.triggered_id in {
                "image-data",
                "border-data",
            }:
                return no_update, "", False

            return select_region(
                click=click,
                selected_regions=selected_regions,
                label_map=label_map,
                image_data=image_data,
                triggered_id=ctx.triggered_id,
                parents=hierarchy_parent,
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
            Output("tree-download", "data"),
            Input("download-tree-button", "n_clicks"),
            State("hierarchy-parent-data", "data"),
            State("hierarchy-altitude-data", "data"),
            State("label-map-data", "data"),
            State("image-data", "data"),
            State("selected-regions-data", "data"),
            prevent_initial_call=True,
        )
        def download_tree_callback(
            click: int | None,
            hierarchy_parent: list[int] | None,
            hierarchy_altitude: list[float] | None,
            label_map_data: list[list[int]] | None,
            image_data: list[list[list[int]]] | None,
            selected_regions_data: list[list[bool]] | None,
        ) -> dict[str, Any] | None:
            return download_tree_information(
                click=click,
                hierarchy_parent=hierarchy_parent,
                hierarchy_altitude=hierarchy_altitude,
                label_map_data=label_map_data,
                image_data=image_data,
                selected_regions_data=selected_regions_data,
            )

        @self._app.callback(
            Output("image-data", "data", allow_duplicate=True),
            Output("label-map-data", "data", allow_duplicate=True),
            Output("selected-regions-data", "data", allow_duplicate=True),
            Output("border-data", "data", allow_duplicate=True),
            Output("hierarchy-parent-data", "data", allow_duplicate=True),
            Output("hierarchy-altitude-data", "data", allow_duplicate=True),
            Output("tree-import-mode", "data", allow_duplicate=True),
            Input("upload-tree", "contents"),
            prevent_initial_call=True,
        )
        def upload_tree_callback(
            content: str | None,
        ) -> tuple[
            list[list[list[int]]],
            list[list[int]],
            list[list[bool]],
            list[list[bool]],
            list[int],
            list[float] | None,
            bool,
        ]:
            imported = upload_tree_information(content)
            return (*imported, True)


        @self._app.callback(
            Output("hierarchy-parent-data", "data"),
            Output("hierarchy-altitude-data", "data"),
            Input("label-map-data", "data"),
            State("image-data", "data"),
            State("tree-import-mode", "data"),
            prevent_initial_call=True,
        )
        def compute_clustering_callback(
            label_map: list[list[int]] | None,
            img: list[list[list[int]]] | None,
            tree_import_mode: bool | None,
        ) -> tuple[list[int] | None, list[float] | None]:
            if tree_import_mode:
                return no_update, no_update
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
            return plot_dendrogram(
                parent,
                altitude,
                selected_regions=selected_regions,
                label_map=label_map,
            )
