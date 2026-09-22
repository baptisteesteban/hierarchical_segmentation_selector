# Developer guide

The project is implemented using [Dash](https://dash.plotly.com/) in Python.

The project source code is organised as follow:

```
.
├─ src/
|   ├─ ui/
|   |   ├─ callbacks/
|   |   └─ pages/
|   └─ compute/
└─ app.py
```

The `app.py` file is the entrypoint of the application. It may be run using the
`uv` package and project manager.

The `src` directory is divided into two directories:

* `compute/`: contains all the code to perform computation in the application.
  It may contains code to perform computation on the application server or to
  make external API calls.
* `ui/`: contains all the Dash related code. It is divided into a `pages/`
  directory, that contains the user interface and the Dash functionalities, and
  a `callback/` directory, that contains the whole code called by the callbacks
  (but not the callbacks theirselves).

## Callback state machine

The diagram below illustrates the chaining of the callbacks in the application.

```mermaid
graph LR
    upload-image["upload-image.contents"]
    image-data["image-data.data"]
    n-segments["n-segments-input.value"]
    compactness["compactness-input.value"]
    label-map["label-map-data.data"]
    border["border-data.data"]
    selected-regions["selected-regions-data.data"]
    selection-color["selection-color.value"]
    image-graph["image-graph.figure"]
    download-btn["download-segmentation-button.n_clicks"]
    segmentation-dl["segmentation-download.data"]
    
    load{load_image}
    compute{compute_label_map}
    display{display_image}
    select{select_region}
    download{download_segmentation}
    
    upload-image --> load
    load --> image-data
    
    image-data --> compute
    n-segments --> compute
    compactness --> compute
    compute --> label-map
    compute --> border
    
    image-data --> display
    label-map --> display
    selected-regions --> display
    border --> display
    selection-color --> display
    display --> image-graph
    
    image-graph --> select
    border --> select
    selected-regions -.-> select
    label-map -.-> select
    select --> selected-regions
    
    download-btn --> download
    selected-regions -.-> download
    download --> segmentation-dl
    
    classDef data fill:#e1f5ff
    classDef callback fill:#fff9c4
    class upload-image,image-data,n-segments,compactness,label-map,border,selected-regions,selection-color,image-graph,download-btn,segmentation-dl data
    class load,compute,display,select,download callback
```