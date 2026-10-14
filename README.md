# Hierarchical Segmentation Selector

This project is a research-oriented image segmentation tool built with Python and [Dash](https://dash.plotly.com/). It helps users segment an image into superpixels, explore a hierarchical merge tree, and interactively select regions of interest before exporting the resulting mask.

The application combines:

- SLIC superpixel generation via `scikit-image`
- a region adjacency graph (RAG) built from the superpixel partition
- agglomerative clustering through a binary partition tree (BPT)
- a Plotly dendrogram to inspect the merge hierarchy
- interactive region selection and parent-cluster expansion in the image view
- JSON+gzip tree import/export for preserving the hierarchy between sessions

## Highlights

- Open an image and compute a segmentation in a few clicks.
- Tune the `n_segments` and `compactness` parameters in real time.
- Click a region in the image to select it and click again to toggle it off.
- Expand the current selection to its parent cluster in the hierarchy.
- Export the segmentation mask as a PNG-style image payload or a saved hierarchical tree.
- Import a previously exported tree to continue editing without recomputing the entire graph.

## Getting started

### Requirements

- Python 3.13
- `uv` for dependency management
- optional: Docker or Nix for containerized and reproducible environments

### Run the app locally

```bash
uv run app.py
```

This installs the dependencies and starts the Dash application in debug mode.

### Run with Nix

The project is developed and tested on Nix-based systems.

```bash
nix develop
```

If you use `direnv`, you can enable the shell automatically:

```bash
direnv allow
```

### Run with Docker

```bash
docker build . -t baptisteesteban/hierarchical-segmentation-selector
docker run --rm -p 8000:8000 baptisteesteban/hierarchical-segmentation-selector
```

Or pull the prebuilt image:

```bash
docker run --rm -p 8000:8000 ghcr.io/baptisteesteban/hierarchical-segmentation-selector:latest
```

## Typical workflow

1. Load an image with the Open Image button.
2. Adjust the number of segments and compactness.
3. Inspect the image and the dendrogram side by side.
4. Click a region to select it.
5. Use Parent region to move up the hierarchy and refine the region of interest.
6. Reset the selection to start over.
7. Download the resulting mask or export the hierarchy tree.

## User interface

The main view contains:

- an image panel on the left
- a dendrogram panel on the right
- an action bar with image upload, reset, download, import/export, and color selection controls
- parameter controls for `Number of segments` and `Compactness`
- a Parent region button to expand a selected cluster to its parent node in the merge tree

Selection is highlighted directly on the image with a configurable color overlay, and border pixels are shown in a stronger tone so the user can see the region boundary clearly.

## Project structure

```text
.
├── app.py                  # application entry point
├── README.md               # overview and quickstart guide
├── mkdocs.yml              # MkDocs configuration
├── doc/                    # documentation pages
├── src/
│   ├── compute/             # segmentation, RAG, clustering, hierarchy utilities
│   └── ui/
│       ├── callbacks/      # Dash callback logic
│       └── pages/          # Dash page definitions
├── tests/                  # unit and integration tests
├── Dockerfile              # container definition
├── flake.nix               # Nix development shell
├── pyproject.toml          # project metadata and dependencies
└── site/                   # generated documentation output
```

## Building the documentation

```bash
uv run --extra doc mkdocs build
```

The generated site is written to the `site/` directory and can be opened locally in a browser.

## Running the tests

```bash
uv run pytest
```

Browser-driven Dash tests are skipped by default. To run them, install a WebDriver such as ChromeDriver and use:

```bash
uv run pytest --run-dash-e2e --headless -m dash_e2e
```

## Development notes

This project uses a layered architecture:

- UI layer: Dash components and callback orchestration
- computation layer: SLIC segmentation, centroid statistics, region graphs, and hierarchy construction
- persistence layer: JSON+gzip export/import for saved analysis states

The code favors explicitly typed Python data structures and uses `numpy` and `scikit-image` for computational work. The hierarchy is represented as parent arrays, which makes it easy to query ancestor relations via the `LCA` utilities.

## Roadmap

- [x] Graphical interface
- [x] SLIC superpixel segmentation
- [x] Superpixel selection
- [x] Region adjacency graph computation
- [x] Hierarchical clustering and dendrogram
- [x] Selection mask overlay improvements
- [x] Lab-based RAG and BPT hierarchy improvements
- [x] Production server setup

## License and repository status

This repository is currently a research tool rather than a packaged application. The code is designed to be run from source or through the provided Docker stack.

For more complete project details, see the documentation under the `doc/` directory and the developer guide in [doc/development/index.md](doc/development/index.md).