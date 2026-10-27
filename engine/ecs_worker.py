import json
import os
import traceback

import boto3
from PIL import Image

job_id = os.environ["JOB_ID"]
bucket = os.environ["OUTPUT_BUCKET"]
table = boto3.resource("dynamodb").Table(os.environ["JOBS_TABLE"])
s3 = boto3.client("s3")


def set_status(status, **values):
    names = {"#status": "status"}
    attrs = {":status": status}
    parts = ["#status = :status"]
    for index, (key, value) in enumerate(values.items()):
        name_key, value_key = f"#n{index}", f":v{index}"
        names[name_key] = key
        attrs[value_key] = value
        parts.append(f"{name_key} = {value_key}")
    table.update_item(
        Key={"jobId": job_id}, UpdateExpression="SET " + ", ".join(parts),
        ExpressionAttributeNames=names, ExpressionAttributeValues=attrs,
    )


def run():
    from main import main

    item = table.get_item(Key={"jobId": job_id}).get("Item")
    if not item:
        raise RuntimeError("Job record does not exist")
    input_path = "/tmp/input.json"
    s3.download_file(bucket, item["inputKey"], input_path)
    set_status("rendering")
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    code = main(["main.py", input_path], verbose=False)
    if code != 0:
        raise RuntimeError(f"Tile Engine exited with status {code}")
    with open(input_path, "r", encoding="utf-8") as payload_file:
        payload = json.load(payload_file)
    output_path = f"map_{payload[0]['id']}.png"
    with Image.open(output_path) as image:
        width, height = image.size
        image.verify()
    output_key = f"jobs/{job_id}/map.png"
    s3.upload_file(
        output_path, bucket, output_key,
        ExtraArgs={
            "ContentType": "image/png",
            "ContentDisposition": f'attachment; filename="lyfe-captures-{job_id}.png"',
            "ServerSideEncryption": "AES256",
        },
    )
    set_status("complete", outputKey=output_key, width=width, height=height)


if __name__ == "__main__":
    try:
        run()
    except Exception as exc:
        traceback.print_exc()
        set_status("failed", error=str(exc)[:500])
        raise
