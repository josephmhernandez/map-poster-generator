import base64
import json
import math
import os
import time
import uuid

import boto3


ddb = boto3.resource("dynamodb").Table(os.environ["JOBS_TABLE"])
sqs = boto3.client("sqs")
s3 = boto3.client("s3")
queue_url = os.environ["QUEUE_URL"]
bucket = os.environ["OUTPUT_BUCKET"]


def response(status, body):
    return {
        "statusCode": status,
        "headers": {"content-type": "application/json", "cache-control": "no-store"},
        "body": json.dumps(body),
    }


def body_from(event):
    raw = event.get("body") or "{}"
    if event.get("isBase64Encoded"):
        raw = base64.b64decode(raw).decode("utf-8")
    return json.loads(raw)


def validate(payload):
    bbox = payload.get("bbox") or {}
    south, west = float(bbox["south"]), float(bbox["west"])
    north, east = float(bbox["north"]), float(bbox["east"])
    zoom = int(payload.get("zoom", 12))
    if not (-85 <= south < north <= 85 and -180 <= west < east <= 180):
        raise ValueError("The selected map bounds are invalid.")
    if not 3 <= zoom <= 18:
        raise ValueError("Zoom must be between 3 and 18.")
    if (east - west) > 30 or (north - south) > 20:
        raise ValueError("The selected area is too large for a poster.")
    orientation = payload.get("orientation", "portrait")
    if orientation not in ("portrait", "landscape"):
        raise ValueError("Orientation must be portrait or landscape.")
    return {
        "bbox": {"south": south, "west": west, "north": north, "east": east},
        "zoom": zoom,
        "orientation": orientation,
        "title": str(payload.get("title") or "CUSTOM MAP")[:48],
        "subtitle": str(payload.get("subtitle") or "")[:90],
        "showPin": bool(payload.get("showPin", True)),
        "center": payload.get("center") or {"lat": (south + north) / 2, "lng": (west + east) / 2},
    }


def handler(event, _context):
    method = event.get("requestContext", {}).get("http", {}).get("method")
    path = event.get("rawPath", "")
    if method == "POST" and path.endswith("/jobs"):
        try:
            payload = validate(body_from(event))
        except (ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
            return response(400, {"error": str(exc)})
        job_id = str(uuid.uuid4())
        now = int(time.time())
        ddb.put_item(Item={"jobId": job_id, "status": "queued", "createdAt": now, "expiresAt": now + 86400})
        sqs.send_message(QueueUrl=queue_url, MessageBody=json.dumps({"jobId": job_id, "payload": payload}))
        return response(202, {"jobId": job_id, "status": "queued"})

    if method == "GET" and "/jobs/" in path:
        job_id = path.rsplit("/", 1)[-1]
        item = ddb.get_item(Key={"jobId": job_id}).get("Item")
        if not item:
            return response(404, {"error": "Map job not found or expired."})
        result = {"jobId": job_id, "status": item["status"]}
        if item["status"] == "complete":
            result["downloadUrl"] = s3.generate_presigned_url(
                "get_object",
                Params={"Bucket": bucket, "Key": item["outputKey"]},
                ExpiresIn=900,
            )
            result["expiresIn"] = 900
        if item["status"] == "failed":
            result["error"] = item.get("error", "Map generation failed.")
        return response(200, result)
    return response(404, {"error": "Not found"})
