# User guide

This guide explains how to use the interactive segmentation workflow in practice.

## Launching the app

From the project root:

```bash
uv run app.py
```

Once the app starts, the browser opens the main segmentation dashboard.

## Interface overview

The main interface includes:

- Open Image: load a source image
- Reset selection: clear the current region selection
- Download Mask: export the current mask selection
- Import tree: load a previously exported hierarchy
- Export tree: save the current segmentation tree
- Selection color: choose the overlay color used for selected regions
- Number of segments: controls the target superpixel count
- Compactness: balances region regularity against color similarity
- Parent region: move the selection to the parent cluster in the tree
- image panel: visual segmentation output and region selection overlay
- dendrogram panel: hierarchical merge visualization

## Step-by-step workflow

### 1. Load an image
Click Open Image and choose a raster image such as PNG, JPEG, or TIFF. The application reads the image and stores it in the session state.

### 2. Tune segmentation parameters
Use the controls on the top panel:

- `Number of segments` sets the target number of initial superpixels.
- `Compactness` tunes the SLIC regularization term.

A moderate number of segments is often easier to inspect and select interactively than an overly fine segmentation.

### 3. Inspect the segmentation
The image panel shows the original image with a colored overlay for the active selection and a border overlay for the segmentation boundaries. Each region is determined from the SLIC partition.

The dendrogram on the right shows the merge hierarchy, with altitude acting as a distance-like merge cost. Selected leaves and branch regions can be visually emphasized when a selection is active.

### 4. Select a region
Click anywhere in the image panel to select the region under the cursor. Re-click the same region to toggle it off.

The selected mask is computed by taking all pixels belonging to the clicked label and highlighting them. The chosen color is controlled by the selection color picker.

### 5. Expand to the parent cluster
When you have a meaningful subset of regions, use Parent region. The application computes the minimal enclosing cluster in the tree and moves the selection one level upward.

This is the key interaction for exploring hierarchical structure without retriggering segmentation from scratch.

### 6. Reset the selection
Use Reset selection to clear the current selection and start a new region-of-interest exploration.

### 7. Download the mask
Once the selection is suitable, click Download Mask to save the binary mask corresponding to the selected region(s).

## Import and export of hierarchy state

### Export tree
Use Export tree to save the current hierarchy to a compressed JSON archive.

This archive stores:

- the parent array
- the altitude array
- the image data
- the label map
- the selected nodes

### Import tree
Use Import tree to restore a previous hierarchy and continue editing from that state. This is particularly helpful when a segmentation session is long or when the same region needs to be refined on another pass.

## Tips for effective use

- start with a simpler segmentation and then refine the hierarchy
- use the parent-region expansion to move from a local region to a broader semantic object
- keep `compactness` moderate if the image contains fine-grained texture
- export the tree when the selection becomes important, so it can be imported later without recomputation

## Troubleshooting

### No selection appears
Check that the image has been loaded and the segmentation state is present. If the user changes the superpixel parameters, the hierarchy is rebuilt, and the current selection may need to be reset.

### Parent region is unavailable
This usually means there is no valid selection or the current hierarchy is not available. Load an image or import a saved tree before attempting the operation.

### The imported tree does not align with the current image
Ensure that the imported archive corresponds to the same source image or a compatible segmentation state. The app validates the stored hierarchy before restoring it.

## Recommended workflow for research use

For annotation-heavy experiments, the workflow is:

1. upload the image
2. choose a segmentation granularity
3. select a small region
4. expand upward to the containing object
5. export the tree and mask for downstream analysis

This keeps the interactive loop efficient while preserving a hierarchical description of the object being segmented.
