from dash import Dash
from dash_bootstrap_components.themes import BOOTSTRAP

from src.ui.pages import IndexPage

app = Dash(external_stylesheets=[BOOTSTRAP])

index = IndexPage(app)
index.display()

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)