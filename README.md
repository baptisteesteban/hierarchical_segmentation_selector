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

It has to be noted that the Nix development shell is handled by a Nix flake
using [flake-parts](https://flake.parts/) but it only handles a `x86_64-linux`
system. If you wish to add a new system, please make a pull request to add the
system in the `flake.nix` file.

### Using Docker

You can build and run a Docker image from this repository. At the root of the
project, use the following commands:

```
$ docker build . -t baptisteesteban/hierarchical-segmentation-selector
$ docker run --rm -p 8050:8050 baptisteesteban/hierarchical-segmentation-selector
```

A built image is also available in the Github Container registry and may be used
using the following command:

```
$ docker run --rm -p 8050:8050 ghcr.io/baptisteesteban/hierarchical-segmentation-selector:latest
```

## How to build the documentation

In order to build the documentation, use the following command:

```
$ uv run --extra doc mkdocs build
```

It will create a directory named `site`, at the root of which the file
`index.html` is the entry point and may be opened by your favorite web browser.

## TODOs

- [X] Design graphical interface (version 0.1)
- [X] SLIC Superpixel segmentation (version 0.1)
- [X] Superpixel selector (version 0.1)
- [X] Compute Region Adjacency Graph (version 0.1)
- [X] Hierarchical clustering (version 0.1)
- [X] Dendrogram display (version 0.1)
- [X] Changement of mask display (using opaque mask instead of colored image) (version 0.1)
- [ ] Improving hierarchical segmentation (Lab based rag + hierarchy)
- [ ] Production server
- [ ] Nix flake packaging
- [ ] uv application packaging