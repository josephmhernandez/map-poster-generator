import json
import math
import os
import struct
import time
import urllib.request
import zlib

import boto3


ddb = boto3.resource("dynamodb").Table(os.environ["JOBS_TABLE"])
s3 = boto3.client("s3")
bucket = os.environ["OUTPUT_BUCKET"]
TILE_URL = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
USER_AGENT = "Joseph-Hernandez-Portfolio-Map-Demo/1.0 (https://josephmhernandez.com)"


def mercator(lat, lng, zoom):
    scale = 2 ** zoom
    x = (lng + 180.0) / 360.0 * scale
    lat_rad = math.radians(max(-85.0511, min(85.0511, lat)))
    y = (1 - math.asinh(math.tan(lat_rad)) / math.pi) / 2 * scale
    return x, y


def select_export_zoom(payload):
    bbox, requested = payload["bbox"], payload["zoom"]
    for zoom in range(min(18, requested + 2), requested - 1, -1):
        west, north = mercator(bbox["north"], bbox["west"], zoom)
        east, south = mercator(bbox["south"], bbox["east"], zoom)
        count = (math.floor(east) - math.floor(west) + 1) * (math.floor(south) - math.floor(north) + 1)
        if count <= 80:
            return zoom
    return requested


def chunks(data):
    pos = 8
    while pos < len(data):
        length = struct.unpack(">I", data[pos:pos + 4])[0]
        kind = data[pos + 4:pos + 8]
        yield kind, data[pos + 8:pos + 8 + length]
        pos += 12 + length


def png_pdf_image(png):
    width, height, bit_depth, color_type, _, _, interlace = struct.unpack(">IIBBBBB", png[16:29])
    if bit_depth != 8 or color_type != 3 or interlace != 0:
        raise ValueError("Unexpected tile image format")
    palette, image_data = b"", b""
    for kind, data in chunks(png):
        if kind == b"PLTE":
            palette = data
        elif kind == b"IDAT":
            image_data += data
    colors = max(0, len(palette) // 3 - 1)
    dictionary = (
        f"/Type /XObject /Subtype /Image /Width {width} /Height {height} "
        f"/ColorSpace [/Indexed /DeviceRGB {colors} <{palette.hex()}>] "
        f"/BitsPerComponent 8 /Filter /FlateDecode "
        f"/DecodeParms << /Predictor 15 /Colors 1 /BitsPerComponent 8 /Columns {width} >>"
    )
    return dictionary, image_data


def fetch_tile(z, x, y):
    request = urllib.request.Request(TILE_URL.format(z=z, x=x, y=y), headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=12) as response:
        return response.read()


def escape_pdf(text):
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def build_pdf(payload):
    portrait = payload["orientation"] == "portrait"
    page_w, page_h = (24 * 72, 36 * 72) if portrait else (36 * 72, 24 * 72)
    footer_h = 240
    map_x, map_y, map_w, map_h = 0, footer_h, page_w, page_h - footer_h
    zoom = select_export_zoom(payload)
    bbox = payload["bbox"]
    west, north = mercator(bbox["north"], bbox["west"], zoom)
    east, south = mercator(bbox["south"], bbox["east"], zoom)
    x0, x1, y0, y1 = math.floor(west), math.floor(east), math.floor(north), math.floor(south)
    tile_w, tile_h = map_w / (east - west), map_h / (south - north)

    objects = [None]
    image_refs = []
    for ty in range(y0, y1 + 1):
        for tx in range(x0, x1 + 1):
            tile = fetch_tile(zoom, tx, ty)
            dictionary, stream = png_pdf_image(tile)
            obj_id = len(objects)
            objects.append((dictionary, stream))
            px = map_x + (tx - west) * tile_w
            py = map_y + map_h - (ty + 1 - north) * tile_h
            image_refs.append((f"Im{obj_id}", obj_id, px, py))

    font_id = len(objects)
    objects.append(("/Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold", None))
    content = ["q", f"{map_x} {map_y} {map_w} {map_h} re W n"]
    for name, _, px, py in image_refs:
        content.append(f"q {tile_w:.4f} 0 0 {tile_h:.4f} {px:.4f} {py:.4f} cm /{name} Do Q")
    content.append("Q")
    if payload.get("showPin"):
        center = payload.get("center") or {}
        cx, cy = mercator(float(center.get("lat", 0)), float(center.get("lng", 0)), zoom)
        pin_x = map_x + (cx - west) / (east - west) * map_w
        pin_y = map_y + map_h - (cy - north) / (south - north) * map_h
        radius = 16
        k = radius * 0.5522848
        content.extend([
            "1 0.27 0.13 rg",
            f"{pin_x + radius:.2f} {pin_y:.2f} m "
            f"{pin_x + radius:.2f} {pin_y + k:.2f} {pin_x + k:.2f} {pin_y + radius:.2f} {pin_x:.2f} {pin_y + radius:.2f} c "
            f"{pin_x - k:.2f} {pin_y + radius:.2f} {pin_x - radius:.2f} {pin_y + k:.2f} {pin_x - radius:.2f} {pin_y:.2f} c "
            f"{pin_x - radius:.2f} {pin_y - k:.2f} {pin_x - k:.2f} {pin_y - radius:.2f} {pin_x:.2f} {pin_y - radius:.2f} c "
            f"{pin_x + k:.2f} {pin_y - radius:.2f} {pin_x + radius:.2f} {pin_y - k:.2f} {pin_x + radius:.2f} {pin_y:.2f} c f",
        ])
    title = escape_pdf(payload["title"].upper())
    subtitle = escape_pdf(payload["subtitle"].upper())
    content.extend([
        "0.07 0.09 0.09 rg",
        f"BT /F1 62 Tf 72 132 Td ({title}) Tj ET",
        "0.33 0.36 0.35 rg",
        f"BT /F1 19 Tf 72 78 Td ({subtitle}) Tj ET",
        f"BT /F1 12 Tf 72 38 Td (LYFE CAPTURES / TILE ENGINE / ZOOM {zoom}) Tj ET",
    ])
    content_bytes = "\n".join(content).encode("latin-1", "replace")
    content_id = len(objects)
    objects.append(("", content_bytes))
    resources = " ".join(f"/{name} {obj_id} 0 R" for name, obj_id, _, _ in image_refs)
    page_id = len(objects)
    pages_id = page_id + 1
    objects.append((f"/Type /Page /Parent {pages_id} 0 R /MediaBox [0 0 {page_w} {page_h}] /Resources << /Font << /F1 {font_id} 0 R >> /XObject << {resources} >> >> /Contents {content_id} 0 R", None))
    objects.append((f"/Type /Pages /Kids [{page_id} 0 R] /Count 1", None))
    catalog_id = len(objects)
    objects.append((f"/Type /Catalog /Pages {pages_id} 0 R", None))

    output = bytearray(b"%PDF-1.7\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for obj_id in range(1, len(objects)):
        offsets.append(len(output))
        dictionary, stream = objects[obj_id]
        output.extend(f"{obj_id} 0 obj\n<< {dictionary}".encode())
        if stream is not None:
            output.extend(f" /Length {len(stream)} >>\nstream\n".encode())
            output.extend(stream)
            output.extend(b"\nendstream\nendobj\n")
        else:
            output.extend(b" >>\nendobj\n")
    xref = len(output)
    output.extend(f"xref\n0 {len(objects)}\n0000000000 65535 f \n".encode())
    for offset in offsets[1:]:
        output.extend(f"{offset:010d} 00000 n \n".encode())
    output.extend(f"trailer\n<< /Size {len(objects)} /Root {catalog_id} 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode())
    return bytes(output), zoom, len(image_refs)


def handler(event, _context):
    for record in event.get("Records", []):
        message = json.loads(record["body"])
        job_id, payload = message["jobId"], message["payload"]
        ddb.update_item(Key={"jobId": job_id}, UpdateExpression="SET #s=:s", ExpressionAttributeNames={"#s": "status"}, ExpressionAttributeValues={":s": "rendering"})
        try:
            pdf, export_zoom, tile_count = build_pdf(payload)
            key = f"maps/{job_id}.pdf"
            filename = "-".join(payload["title"].lower().split())[:50] or "custom-map"
            s3.put_object(Bucket=bucket, Key=key, Body=pdf, ContentType="application/pdf", ContentDisposition=f'attachment; filename="{filename}.pdf"')
            ddb.update_item(
                Key={"jobId": job_id},
                UpdateExpression="SET #s=:s, outputKey=:k, exportZoom=:z, tileCount=:t",
                ExpressionAttributeNames={"#s": "status"},
                ExpressionAttributeValues={":s": "complete", ":k": key, ":z": export_zoom, ":t": tile_count},
            )
        except Exception as exc:
            ddb.update_item(
                Key={"jobId": job_id},
                UpdateExpression="SET #s=:s, #e=:e",
                ExpressionAttributeNames={"#s": "status", "#e": "error"},
                ExpressionAttributeValues={":s": "failed", ":e": str(exc)[:300]},
            )
            raise
