from dash import Dash, html, dcc, Input, Output, ctx
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from imageio.v3 import imread
from skimage.segmentation import slic
from skimage.morphology import footprint_rectangle, dilation
import numpy as np

from loguru import logger

import base64
from io import BytesIO

from ._page import AbstractPage


class IndexPage(AbstractPage):
    def __init__(self, app: Dash):
        layout = [
            dbc.Container([
                html.H1("Hierarchical Segmentation Selector"),
                html.Hr(),
                dbc.Card(
                    dbc.Row([
                        dbc.Col(dcc.Upload(children=[dbc.Button("Open Image")], id="upload-image", accept="image/*")),
                        dbc.Col(dbc.Button("Reset", id="reset-button")),
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
                            dbc.Input(id="compactness-inputs", type="number", value=10)
                        ],
                        body=True)
                    ])
                ]),
                dbc.Row([
                    dbc.Col(dcc.Graph(id="image-graph", style={'width': '100%', 'height': 'calc(100vh - 400px)'})),
                    dbc.Col(html.H3("TODO ! (Dendrogram)"))
                ]),
                
            ], style={'display': 'flex', 'flexDirection': 'column', 'height': '100vh'})
        ]
        self._currently_selected = set()
        super().__init__(app, "Index", layout)

    def _register_callbacks(self):
        @self._app.callback(
            Output("image-graph", "figure"),
            Input("upload-image", "contents"),
            Input("n-segments-input", "value"),
            Input("compactness-inputs", "value"),
            Input("selection-color", "value"),
            Input("image-graph", "clickData"),
            Input("reset-button", "n_clicks")
        )
        def display_image(content, n_segments, compactness, border_color, click_data, _btn_reset):
            def hex_to_rgb(hex_color):
                hex_color = hex_color.lstrip('#')
                return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

            if ctx.triggered_id == "reset-button":
                self._currently_selected.clear()

            if not content:
                logger.info("Image content is empty")
                return go.Figure()

            logger.info("Displaying image")
            _, encoded = content.split(",", 1)
            image_bytes = base64.b64decode(encoded)
            img = imread(image_bytes)

            n_segment_max = img.shape[0] * img.shape[1]
            if n_segments is None or n_segments < 1 or n_segments >= n_segment_max:
                logger.error(f"Invalid number of segment (must be in the range [1 - {n_segment_max}])")
                return go.Figure()

            if compactness is None or compactness < 0:
                logger.error("Invalid compactness")
                return go.Figure()

            if ctx.triggered_id == "image-graph" and click_data is not None:
                lbl = int(click_data["points"][0]["z"])
                if lbl in self._currently_selected:
                    self._currently_selected.remove(lbl)
                else:
                    self._currently_selected.add(lbl)

            displayed_img = img
            if img.ndim == 2:
                displayed_img = img[:, :, None]
                displayed_img = img.repeat(3, axis=2)
            elif img.ndim == 3 and img.shape[2] == 4:
                displayed_img = img[:, :, :3]

            segments = slic(img, n_segments=n_segments, compactness=compactness)
            logger.info(f"SLIC computed with {n_segments} segments (Got {segments.max()} segments)")
            dil = dilation(segments, footprint_rectangle((3, 3)))
            borders = segments != dil
            displayed_img[borders] = hex_to_rgb(border_color)
            for lbl in self._currently_selected:
                displayed_img[segments == lbl] = hex_to_rgb(border_color)

            h, w = img.shape[:2]
            fig = go.Figure()
            fig.add_trace(go.Image(z=displayed_img, hoverinfo="skip"))
            fig.add_trace(go.Heatmap(z=segments, opacity=0, showscale=False, hovertemplate=None))
            return fig