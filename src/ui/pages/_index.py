from typing import Any

import dash_bootstrap_components as dbc
from dash import Dash, Input, Output, State, ctx, dcc, html

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
            Input("image-graph", "clickData"),
            Input("border-data", "data"),
            Input("image-data", "data"),
            Input("n-segments-input", "value"),
            Input("compactness-input", "value"),
            State("selected-regions-data", "data"),
            State("label-map-data", "data"),
            prevent_initial_call=True,
        )
        def select_region_callback(
            click: dict[str, Any] | None,
            borders: list[list[bool]] | None,
            image_data: list[list[list[int]]] | None,
            n_segments: int | None,
            compactness: float | None,
            selected_regions: list[list[bool]] | None,
            label_map: list[list[int]] | None,
        ) -> list[list[bool]] | None:
            return select_region(
                click=click,
                borders=borders,
                selected_regions=selected_regions,
                label_map=label_map,
                image_data=image_data,
                triggered_id=ctx.triggered_id,
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
            prevent_initial_call=True,
        )
        def plot_dendrogram_callback(
            parent: list[int] | None, altitude: list[Any] | None
        ) -> Any:
            return plot_dendrogram(parent, altitude)
