import base64
import json
import os
import time
import uuid

import boto3


ddb = boto3.resource("dynamodb").Table(os.environ["JOBS_TABLE"])
ecs = boto3.client("ecs")
s3 = boto3.client("s3")
bucket = os.environ["OUTPUT_BUCKET"]
cluster_arn = os.environ["ECS_CLUSTER_ARN"]
task_definition_arn = os.environ["TASK_DEFINITION_ARN"]
container_name = os.environ["CONTAINER_NAME"]
subnets = os.environ["TASK_SUBNETS"].split(",")
security_groups = os.environ["TASK_SECURITY_GROUPS"].split(",")

ALLOWED_LAYERS = {
    "dark-transit", "modern-light", "city-lights", "ocean-tan",
    "eco", "blue-print", "ruby-routes",
}


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
    """Validate the native Tile Engine contract: a list containing one map."""
    if not isinstance(payload, list) or len(payload) != 1 or not isinstance(payload[0], dict):
        raise ValueError("Tile Engine payload must be a list containing one map object.")
    item = payload[0]
    required = {
        "id", "orientation", "textPrimary", "textSecondary", "textCoordinates",
        "tileLayer", "bbox", "zoom", "size", "styling", "pinList",
        "tileZoomOffset", "mapDimensionsIn", "text_styling_specs",
        "isTransparentTextBlock",
    }
    missing = sorted(required.difference(item))
    if missing:
        raise ValueError(f"Missing Tile Engine fields: {', '.join(missing)}")
    if item["tileLayer"] not in ALLOWED_LAYERS:
        raise ValueError("Unknown map style.")
    if item["orientation"] not in ("portrait", "landscape"):
        raise ValueError("Orientation must be portrait or landscape.")
    if not 4 <= int(item["zoom"]) <= 13:
        raise ValueError("Zoom must be between 4 and 13.")
    if int(item["tileZoomOffset"]) not in (1, 2):
        raise ValueError("Tile zoom offset must be 1 or 2.")

    bbox = json.loads(item["bbox"])
    sw, ne = bbox["_southWest"], bbox["_northEast"]
    south, west = float(sw["lat"]), float(sw["lng"])
    north, east = float(ne["lat"]), float(ne["lng"])
    if not (-85 <= south < north <= 85 and -180 <= west < east <= 180):
        raise ValueError("The selected Leaflet bounds are invalid.")
    if (east - west) > 12 or (north - south) > 10:
        raise ValueError("The selected area is too large for a print job.")

    dims = item["mapDimensionsIn"]
    width, height = float(dims["map_width"]), float(dims["map_height"])
    if sorted((width, height)) != [24.0, 36.0]:
        raise ValueError("This public demo supports the original 24 × 36 inch format.")
    if len(item["pinList"]) > 5:
        raise ValueError("This public demo supports up to five pins.")
    return payload


def start_task(job_id):
    result = ecs.run_task(
        cluster=cluster_arn,
        taskDefinition=task_definition_arn,
        launchType="FARGATE",
        count=1,
        platformVersion="LATEST",
        networkConfiguration={
            "awsvpcConfiguration": {
                "subnets": subnets,
                "securityGroups": security_groups,
                "assignPublicIp": "ENABLED",
            }
        },
        overrides={
            "containerOverrides": [{
                "name": container_name,
                "environment": [{"name": "JOB_ID", "value": job_id}],
            }]
        },
        tags=[{"key": "PortfolioDemo", "value": "LyfeCapturesTileEngine"}],
    )
    if result.get("failures"):
        raise RuntimeError(result["failures"][0].get("reason", "ECS task did not start"))
    return result["tasks"][0]["taskArn"]


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
        input_key = f"jobs/{job_id}/input.json"
        s3.put_object(
            Bucket=bucket, Key=input_key, Body=json.dumps(payload).encode("utf-8"),
            ContentType="application/json", ServerSideEncryption="AES256",
        )
        ddb.put_item(Item={
            "jobId": job_id, "status": "starting", "createdAt": now,
            "expiresAt": now + 86400, "inputKey": input_key,
        })
        try:
            task_arn = start_task(job_id)
            ddb.update_item(
                Key={"jobId": job_id},
                UpdateExpression="SET taskArn = :task, #status = :status",
                ExpressionAttributeNames={"#status": "status"},
                ExpressionAttributeValues={":task": task_arn, ":status": "queued"},
            )
        except Exception as exc:
            ddb.update_item(
                Key={"jobId": job_id},
                UpdateExpression="SET #status = :status, #error = :error",
                ExpressionAttributeNames={"#status": "status", "#error": "error"},
                ExpressionAttributeValues={":status": "failed", ":error": str(exc)[:500]},
            )
            return response(500, {"error": "The Tile Engine task could not be started."})
        return response(202, {"jobId": job_id, "status": "queued"})

    if method == "GET" and "/jobs/" in path:
        job_id = path.rsplit("/", 1)[-1]
        item = ddb.get_item(Key={"jobId": job_id}).get("Item")
        if not item:
            return response(404, {"error": "Map job not found or expired."})
        result = {"jobId": job_id, "status": item["status"]}
        if item["status"] == "complete":
            result["downloadUrl"] = s3.generate_presigned_url(
                "get_object", Params={"Bucket": bucket, "Key": item["outputKey"]}, ExpiresIn=900,
            )
            result.update({
                "expiresIn": 900, "format": "png", "width": int(item.get("width", 0)),
                "height": int(item.get("height", 0)),
            })
        if item["status"] == "failed":
            result["error"] = item.get("error", "Map generation failed.")
        return response(200, result)
    return response(404, {"error": "Not found"})
