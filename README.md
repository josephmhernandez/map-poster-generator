# Lyfe Captures Map Studio + Tile Engine

A public, working reconstruction of the map-design flow from **Lyfe Captures**, backed by a serverless high-resolution PDF tile engine on AWS.

**Live demo:** <https://josephmhernandez.com/demos/maps/>

## What is real

- Movable and zoomable Leaflet map using OpenStreetMap tiles
- Place search, exact viewport bounds, center marker, titles, and portrait/landscape formats
- Asynchronous API → SQS → Lambda rendering workflow
- Backend tile selection at a higher export zoom when the selected area allows it
- PDF composition from real map tiles, with typography and a vector center marker
- Private S3 output and a 15-minute presigned download URL

## Cost and abuse controls

- Lambda worker reserved concurrency is limited to one
- HTTP API throttling is enabled
- DynamoDB and S3 are pay-per-request
- Jobs and generated files expire after one day
- The demo has no account, cart, payment, or Stripe flow

## Deploy

```bash
sam build
sam deploy --stack-name jmh-map-poster-demo --resolve-s3 --capabilities CAPABILITY_IAM
```

Copy the `ApiUrl` stack output into `web/config.js`, then publish `web/` to static hosting.

## Attribution

Map data and tiles are © OpenStreetMap contributors. This low-volume portfolio demonstration identifies its backend requests with a descriptive user agent and does not provide bulk or offline tile access.

## License

MIT
