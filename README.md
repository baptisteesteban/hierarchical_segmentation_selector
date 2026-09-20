# Hierarchical Image Selector

This repository provides a [Dash](https://dash.plotly.com/) web application to
compute superpixels and hierarchical clustering to compute segmentation based on
the latest.

## How to launch it

### On a system equiped with uv

This project is managed by the [uv](https://docs.astral.sh/uv/) package and
project manager. If `uv` is installed, just use the following command:

```
$ uv run app.py
```

This will install the dependencies and launch the application in debug mode (from now on).

### On a Nix-based system

This project is mainly developed using a NixOS Linux distribution, and thus is
tested with it.  If you wish to develop the application with a Nix based system,
ensure you can use `nix flake` and `nix command` (see
[here](https://nixos.wiki/wiki/Flakes) for more information) and use the following command:

```
$ nix develop 
```

It will launch a development shell. Furthermore, this project can be use with
[nix-direnv](https://github.com/nix-community/nix-direnv) and you may just lauch
the nix shell automatically using direnv by using once the following command:

```
$ direnv allow
```

Then, you can develop or run the application as described in the previous
section.

### Using Docker

You can build and run a Docker image from this repository. At the root of the
project, use the following commands:

```
$ docker build . -t baptisteesteban/hierarchical-segmentation-selector
$ docker run --rm -p 8050:8050 baptisteesteban/hierarchical-segmentation-selector
```

## TODOs

- [X] Design graphical interface (version 0.1)
- [X] SLIC Superpixel segmentation (version 0.1)
- [X] Superpixel selector (version 0.1)
- [ ] Compute Region Adjacency Graph
- [ ] Hierarchical clustering
- [ ] Dendrogram display
- [ ] Choice of superpixel clustering
    - [ ] Meanshift
    - [ ] Watershed
- [ ] Choice of hierarchy on the RAG
    - [ ] Complete hierarchical clustering
    - [ ] Binary Partition Tree
    - [ ] Min / Max-tree
- [ ] Changement of mask display (using opaque mask instead of colored image)