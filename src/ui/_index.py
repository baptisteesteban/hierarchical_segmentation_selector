from dash import Dash, html, dcc, Input, Output, State, ctx
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from imageio.v3 import imread, imwrite
from skimage.segmentation import slic
from skimage.morphology import footprint_rectangle, dilation
import numpy as np

from loguru import logger

import base64
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
            dcc.Store(id="image-data"),
            dcc.Store(id="label-map-data"),
            dcc.Store(id="selected-regions-data"),
            dcc.Store(id="border-data"),
            dcc.Download(id="segmentation-download")
        ]
        super().__init__(app, "Index", layout)

    def _register_callbacks(self):
        @self._app.callback(
            Output("image-data", "data"),
            Input("upload-image", "contents"),
            prevent_initial_call=True
        )
        def load_image(content):
            _, encoded = content.split(",", 1)
            image_bytes = base64.b64decode(encoded)
            img = imread(image_bytes)
            if img.ndim == 2:
                img = img[:, :, None]
                img = img.repeat(3, axis=2)

            return img.tolist()

        @self._app.callback(
            Output("label-map-data", "data"),
            Output("border-data", "data"),
            Input("image-data", "data"),
            Input("n-segments-input", "value"),
            Input("compactness-input", "value"),
            prevent_initial_call=True
        )
        def compute_label_map(image_data, n_segments, compactness):
            img = np.asarray(image_data)

            N = img.shape[0] * img.shape[1]
            if n_segments is None or n_segments < 1 or n_segments > N:
                logger.error(f"Invalid number of segment (Got {n_segments}, expected in [1 - {N}])")
                return None, None

            if compactness is None or compactness <= 0:
                logger.error("Compactness must be strictly positive")
                return None, None

            segments = slic(img, n_segments=n_segments, compactness=compactness)
            logger.info(f"SLIC computed with {n_segments} segments (Got {segments.max()} segments)")
            dil = dilation(segments, footprint_rectangle((3, 3)))
            borders = segments != dil

            return segments.tolist(), borders.tolist()

        @self._app.callback(
            Output("image-graph", "figure"),
            Input("image-data", "data"),
            Input("label-map-data", "data"),
            Input("selected-regions-data", "data"),
            Input("border-data", "data"),
            Input("selection-color", "value")
        )
        def display_image(image_data, label_map, selected_regions, border, selected_color):
            def hex_to_rgb(hex_color):
                hex_color = hex_color.lstrip('#')
                return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
            if image_data is None:
                return go.Figure()

            img = np.array(image_data, dtype=np.uint8)
            displayed_img = img
            if img.ndim != 3 or img.shape[2] != 3:
                logger.error("Invalid image data")
                return go.Figure()

            if selected_regions is not None:
                displayed_np = np.asarray(selected_regions)
                displayed_np = np.logical_or(displayed_np, np.asarray(border))
                displayed_img[displayed_np] = hex_to_rgb(selected_color)

            
            fig = go.Figure()
            fig.add_trace(go.Image(z=displayed_img, hoverinfo="skip"))
            if label_map is not None:
                label_map_np = np.asarray(label_map)
                fig.add_trace(go.Heatmap(z=label_map_np, opacity=0, showscale=False, hovertemplate=None))

                logger.info("Computing information for RAG")
                centroid, mean = compute_centroid_and_mean(label_map_np, img)
                logger.info("Building RAG")
                rag = RAG.build(label_map_np, mean)
                logger.info("Computing information for RAG")
                lines = rag.process_rag_for_display(centroid)

                logger.info("Displaying RAG")
                y = np.column_stack((lines[:, 0], lines[:, 2], np.full(len(lines), np.nan))).ravel()
                x = np.column_stack((lines[:, 1], lines[:, 3], np.full(len(lines), np.nan))).ravel()
                fig.add_trace(go.Scatter(x=x, y=y, mode="lines", hoverinfo="skip"))

                fig.add_trace(go.Scatter(x=centroid[1:, 1], y=centroid[1:, 0], mode='markers', hoverinfo="skip"))
            return fig

        @self._app.callback(
            Output("selected-regions-data", "data"),
            Input("image-graph", "clickData"),
            Input("border-data", "data"),
            State("selected-regions-data", "data"),
            State("label-map-data", "data"),
            prevent_initial_call=True
        )
        def select_region(click, borders, selected_regions, label_map):
            if borders is None:
                return None
    
            selected_regions_np = None
            if ctx.triggered_id == "image-graph" and click is not None:
                selected_regions_np = np.asarray(selected_regions)
                label_map_np = np.asarray(label_map)
                data = click["points"][0]
                x = int(data["x"])
                y = int(data["y"])
                lbl = int(data["z"])
                if selected_regions_np[y, x]:
                    selected_regions_np[label_map_np == lbl] = False
                else:
                    selected_regions_np[label_map_np == lbl] = True
            else:
                selected_regions_np = np.zeros_like(borders)
            
            return selected_regions_np.tolist()

        @self._app.callback(
            Output("segmentation-download", "data"),
            Input("download-segmentation-button", "n_clicks"),
            State("selected-regions-data", "data"),
            prevent_initial_call=True
        )
        def download_segmentation(click, selected_regions_data):
            if selected_regions_data is None:
                return None
            selected_regions = np.asarray(selected_regions_data)
            buffer = BytesIO()
            imwrite(buffer, selected_regions, extension=".png")
            return dcc.send_bytes(buffer.getvalue(), "segmentation.png")
