from dash import Dash, html, dcc, Input, Output, State
import dash_bootstrap_components as dbc

from io import BytesIO

from ._page import AbstractPage
from src.compute import compute_centroid_and_mean, RAG


class IndexPage(AbstractPage):
    def __init__(self, app: Dash):
        layout = [
            dbc.Container([
                html.H1("Hierarchical Segmentation Selector"),
                html.Hr(),
                dbc.Card(
                    dbc.Row([
                        dbc.Col(dcc.Upload(children=[dbc.Button("Open Image")], id="upload-image", accept="image/*")),
                        dbc.Col(dbc.Button("Download Segmentation", id="download-segmentation-button")),
                        dbc.Col([dbc.Input(type="color", id="selection-color", value="#FF0000")])
                    ]),
                    body=True),
                html.Hr(),
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.Label("Number of segments"),
                            dbc.Input(id="n-segments-input", type="number", value=10)
                        ],
                        body=True)
                    ]),
                    dbc.Col([
                        dbc.Card([
                            dbc.Label("Compactness"),
                            dbc.Input(id="compactness-input", type="number", value=10)
                        ],
                        body=True)
                    ])
                ]),
                dbc.Row([
                    dbc.Col(dcc.Graph(id="image-graph", style={'width': '100%', 'height': 'calc(100vh - 400px)'})),
                    dbc.Col(html.H3("TODO ! (Dendrogram)"))
                ]),
                
            ], style={'display': 'flex', 'flexDirection': 'column', 'height': '100vh'}),
            dcc.Download(id="segmentation-download")
        ]

        stores = [
            dcc.Store(id="image-data"),
            dcc.Store(id="label-map-data"),
            dcc.Store(id="selected-regions-data"),
            dcc.Store(id="border-data"),
        ]
        super().__init__(app, "Index", layout, stores)

    def _register_callbacks(self):
        from src.ui.callbacks.index import (
            load_image,
            compute_label_map,
            display_image,
            select_region,
            download_segmentation
        )

        @self._app.callback(
            Output("image-data", "data"),
            Input("upload-image", "contents"),
            prevent_initial_call=True
        )
        def load_image_callback(contents):
            return load_image(contents)

        @self._app.callback(
            Output("label-map-data", "data"),
            Output("border-data", "data"),
            Input("image-data", "data"),
            Input("n-segments-input", "value"),
            Input("compactness-input", "value"),
            prevent_initial_call=True
        )
        def compute_label_map_callback(image_data, n_segments, compactness):
            return compute_label_map(image_data, n_segments, compactness)

        @self._app.callback(
            Output("image-graph", "figure"),
            Input("image-data", "data"),
            Input("label-map-data", "data"),
            Input("selected-regions-data", "data"),
            Input("border-data", "data"),
            Input("selection-color", "value")
        )
        def display_image_callback(image_data, label_map, selected_regions, border, selected_color):
            return display_image(image_data, label_map, selected_regions, border, selected_color)

        @self._app.callback(
            Output("selected-regions-data", "data"),
            Input("image-graph", "clickData"),
            Input("border-data", "data"),
            State("selected-regions-data", "data"),
            State("label-map-data", "data"),
            prevent_initial_call=True
        )
        def select_region_callback(click, borders, selected_regions, label_map):
            return select_region(click, borders, selected_regions, label_map)

        @self._app.callback(
            Output("segmentation-download", "data"),
            Input("download-segmentation-button", "n_clicks"),
            State("selected-regions-data", "data"),
            prevent_initial_call=True
        )
        def download_segmentation_callback(click, selected_regions_data):
            return download_segmentation(click, selected_regions_data)
