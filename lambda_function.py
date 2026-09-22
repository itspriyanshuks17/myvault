import json
import boto3
import os
from botocore.exceptions import ClientError

# Name of your private S3 bucket
BUCKET_NAME = os.environ.get("BUCKET_NAME", "myvaultbypriyanshu-documents")
s3_client = boto3.client("s3")

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, DELETE, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Authorization",
}

def lambda_handler(event, context):
    http_method = event.get("httpMethod") or event.get("requestContext", {}).get("http", {}).get("method")
    path = event.get("path") or event.get("rawPath", "")

    # Handle CORS preflight OPTIONS request
    if http_method == "OPTIONS":
        return {
            "statusCode": 200,
            "headers": CORS_HEADERS,
            "body": json.dumps({"message": "CORS preflight OK"})
        }

    try:
        # 1. LIST FILES: GET /files
        if http_method == "GET" and (path.endswith("/files") or path == "/files"):
            response = s3_client.list_objects_v2(Bucket=BUCKET_NAME)
            files = []
            for item in response.get("Contents", []):
                files.append({
                    "name": item["Key"],
                    "size": item["Size"],
                    "date": int(item["LastModified"].timestamp() * 1000)
                })
            return respond(200, {"files": files})

        # 2. GENERATE PRESIGNED UPLOAD URL: POST /upload-url
        elif http_method == "POST" and (path.endswith("/upload-url") or path == "/upload-url"):
            body = json.loads(event.get("body", "{}"))
            file_name = body.get("fileName")
            content_type = body.get("contentType", "application/octet-stream")

            if not file_name:
                return respond(400, {"error": "fileName is required"})

            # Generate S3 presigned URL for direct browser PUT upload
            presigned_url = s3_client.generate_presigned_url(
                ClientMethod="put_object",
                Params={
                    "Bucket": BUCKET_NAME,
                    "Key": file_name,
                    "ContentType": content_type
                },
                ExpiresIn=300 # 5 minutes
            )

            return respond(200, {
                "uploadUrl": presigned_url,
                "key": file_name
            })

        # 3. GENERATE PRESIGNED DOWNLOAD/VIEW URL: GET /download-url?key=filename
        elif http_method == "GET" and (path.endswith("/download-url") or path == "/download-url"):
            params = event.get("queryStringParameters") or {}
            key = params.get("key")

            if not key:
                return respond(400, {"error": "key query parameter is required"})

            presigned_url = s3_client.generate_presigned_url(
                ClientMethod="get_object",
                Params={
                    "Bucket": BUCKET_NAME,
                    "Key": key
                },
                ExpiresIn=3600 # 1 hour
            )

            return respond(200, {"url": presigned_url})

        # 4. DELETE FILE: DELETE /delete?key=filename
        elif http_method == "DELETE" and (path.endswith("/delete") or path == "/delete"):
            params = event.get("queryStringParameters") or {}
            key = params.get("key")

            if not key:
                return respond(400, {"error": "key query parameter is required"})

            s3_client.delete_object(Bucket=BUCKET_NAME, Key=key)
            return respond(200, {"message": f"File '{key}' deleted successfully"})

        else:
            return respond(404, {"error": f"Route not found: {http_method} {path}"})

    except ClientError as e:
        return respond(500, {"error": str(e)})
    except Exception as e:
        return respond(500, {"error": f"Internal error: {str(e)}"})


def respond(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            **CORS_HEADERS,
            "Content-Type": "application/json"
        },
        "body": json.dumps(body)
    }
