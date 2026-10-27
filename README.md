# Map Poster Generator

An interactive, client-side map-poster renderer adapted from the product design and rendering concepts behind **Lyfe Captures** and the Python **Tile Engine**.

**Live demo:** <https://josephmhernandez.com/demos/maps/>

## Features

- Six coordinate-seeded city compositions
- Four visual themes
- Portrait and landscape rendering
- Editable location typography
- Optional location marker
- Deterministic procedural road graph
- Local PNG export
- No accounts, cart, payments, or uploaded data

## Rendering pipeline

```text
Location seed → procedural road graph → style pass → typography → PNG export
```

The original Python engine downloaded map tiles, assembled and cropped them to a geographic bounding box, added pins and backgrounds, applied transparency/style transforms, and rendered print typography. This public demo uses an original procedural road network so it has no private map-provider key, tile-service dependency, or per-render backend cost.

## Run locally

```bash
python3 -m http.server 8080 --directory web
```

Then open <http://localhost:8080>.

## Privacy and cost

Rendering happens entirely inside the visitor's browser. No location or image is uploaded, and the deployed demo requires only static hosting.

## License

MIT
