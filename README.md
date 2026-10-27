# Lyfe Captures Map Studio + Tile Engine

The original Lyfe Captures map payload and Python Tile Engine, deployed as a working public portfolio demo.

**Live demo:** <https://josephmhernandez.com/demos/maps/>

## What runs

- Movable and zoomable Leaflet editor using the original `tileZoomOffset` behavior
- Current MapTiler raster styles replacing the retired custom style IDs
- The original list payload, including Leaflet bounds, 24×36 dimensions, styling, text, and pin list
- The original Python download, tile assembly, exact-bounds crop, pin placement, and typography code
- A one-off ECS Fargate task for each high-resolution render
- Native 7200×10800, 300-DPI PNG output in private S3
- A 15-minute presigned download link; inputs and outputs expire after one day

The original pin PNGs were restored from the Lyfe Captures web repository because the Tile Engine referenced them but its `.gitignore` excluded them.

## Architecture

```text
Leaflet editor → HTTP API/Lambda → ECS RunTask
                                      │
                    original Python Tile Engine
                                      │
                          DynamoDB + private S3
```

There is no always-on render worker. The public endpoint is throttled, supports up to five pins, and only accepts the original 24×36 format. No cart, payment, or Stripe code is deployed.

## Deploy

`template.yaml` provisions the API, job table, private bucket, ECR repository, build project, and Fargate task definition. The image source is `engine/`, which contains the original repository as a Git subtree plus the ECS worker wrapper.

## Attribution

Map data is © OpenStreetMap contributors and rendered with MapTiler.

## License

MIT
