# Architecture guide

This document explains the software design and the core algorithmic pipeline behind the segmentation workflow.

## High-level architecture

The project follows a simple layered architecture:

- UI layer: Dash pages and callbacks
- computation layer: segmentation and hierarchy building
- persistence layer: compressed hierarchy export/import

The primary entry point is `app.py`, which constructs the Dash app and displays the main page.

## UI architecture

The main page is defined in `src/ui/pages/_index.py`. It contains:

- the top action bar
- the segmentation parameter controls
- the image graph
- the dendrogram graph
- the session stores used for persistent state

The callbacks registered on the page use functions from `src/ui/callbacks/index/`.

The callback modules are responsible for:

- loading source images
- computing the label map and border mask
- materializing the session state
- plotting the dendrogram
- managing region selection and parent expansion
- importing and exporting hierarchy data
- downloading the segmentation mask

## Session state model

The session state is constructed in `src/ui/callbacks/index/_session_state.py` and is central to the app. It stores both the source image and the derived segmentation information.

The major session fields are:

- `image_data`: original image pixels
- `label_map`: superpixel labels
- `border`: border mask for overlay rendering
- `hierarchy_parent`: parent pointers for all nodes in the hierarchy
- `hierarchy_altitude`: merge cost array
- `tree_import_mode`: indicates whether the tree was restored from import
- `initial_selected_regions`: imported selection state

This design keeps the data flow explicit and makes it easy to re-render the image and dendrogram whenever a parameter or selection changes.

## Algorithmic pipeline

### Superpixel computation

The initial segmentation is computed with SLIC in `src/ui/callbacks/index/_compute_label_map.py`:

```python
segments = slic(img, n_segments=n_segments, compactness=compactness, start_label=0)
```

This produces a label map where each pixel is assigned to a superpixel region.

### Border mask generation

A border mask is created by comparing the label map to a dilated version of itself. This draws a strong outline around the region boundaries in the display.

### Region statistics

The centroid and mean region color are computed in `src/compute/_attribute.py`. These statistics feed the region adjacency graph.

### Region adjacency graph

The RAG is created in `src/compute/_rag.py`. For each pair of neighboring labels, the graph stores the Euclidean distance between their feature vectors. This works well as a locality-aware similarity measure for the merge hierarchy.

### Binary partition tree

The hierarchy is built in `src/compute/_bpt.py`. The algorithm:

1. initializes a heap of candidate merges
2. repeatedly merges the pair with the lowest cost
3. updates the parent pointers and aggregated region statistics
4. returns an array describing the parents of each merge node

This yields a valid binary tree representation over the region hierarchy.

### Lowest common ancestor

The LCA utility in `src/compute/_lca.py` gives efficient ancestor checks and is used by the region-selection logic to determine the current node and its parent cluster.

This is the mechanism behind the Parent region button: the app computes the lowest common ancestor of the selected leaves, checks whether the selection is the full subtree, and ascends one level when valid.

## Rendering and selection logic

The image render path is in `src/ui/callbacks/index/_display_image.py`.

It overlays three layers:

- the original image
- a semi-transparent selection mask
- the border mask and selected-border mask

This ensures the segmentation remains visible while the selection is clearly highlighted.

Selection itself is handled in `src/ui/callbacks/index/_select_region.py`, which converts a click on the image into a precise mask over the selected labels.

## Persistence and export

The export/import system in `src/ui/callbacks/index/_import_export.py` serializes the hierarchy into a gzip-compressed JSON payload. This contains the tree parent array, altitude data, label map, original image, and selected nodes.

This is useful because the hierarchy is often the expensive object to compute. Saving it allows quick resumption of a segmentation session without re-running the clustering pipeline.

## Why this design

The architecture is intentionally compact and transparent:

- the numerical work is isolated in `src/compute/`
- the UI and interaction logic live in `src/ui/`
- the data flow is explicit and state-based
- hierarchy operations are expressed using parent arrays and ancestor queries rather than hidden graph mutation

This makes debugging easier and keeps the code suitable for research iteration.