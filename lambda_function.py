import json
import boto3
import os
import hmac
import hashlib
import time
import base64
from botocore.exceptions import ClientError

# ==============================================================================
# CONFIGURATION & ZERO-COST AUTH SETTINGS
# ==============================================================================
BUCKET_NAME = os.environ.get("BUCKET_NAME", "myvaultbypriyanshu-documents")

# Default credentials (can be customized via Lambda Environment Variables)
DEFAULT_USERNAME = os.environ.get("VAULT_USERNAME", "priyanshu")
DEFAULT_PASSWORD = os.environ.get("VAULT_PASSWORD", "myvault@2026")
AUTH_SECRET = os.environ.get("AUTH_SECRET", "cloudvault-super-secure-token-secret-key-321").encode("utf-8")

# Token validity (7 days in seconds)
TOKEN_EXPIRY_SECONDS = 7 * 24 * 3600

s3_client = boto3.client("s3")

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, DELETE, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Authorization",
}

# ==============================================================================
# AUTHENTICATION HELPERS (Zero-cost HMAC Tokens)
# ==============================================================================
def create_auth_token(username):
    expires_at = int(time.time()) + TOKEN_EXPIRY_SECONDS
    payload = f"{username}:{expires_at}"
    signature = hmac.new(AUTH_SECRET, payload.encode("utf-8"), hashlib.sha256).hexdigest()
    raw_token = f"{payload}:{signature}"
    return base64.urlsafe_b64encode(raw_token.encode("utf-8")).decode("utf-8")

def verify_auth_token(token_string):
    if not token_string:
        return False, "Missing authorization token"
    try:
        decoded = base64.urlsafe_b64decode(token_string.encode("utf-8")).decode("utf-8")
        parts = decoded.split(":")
        if len(parts) != 3:
            return False, "Invalid token format"
        username, expires_at_str, signature = parts
        expires_at = int(expires_at_str)

        # Check token expiration
        if time.time() > expires_at:
            return False, "Token expired, please log in again"

        # Verify HMAC signature
        expected_payload = f"{username}:{expires_at}"
        expected_sig = hmac.new(AUTH_SECRET, expected_payload.encode("utf-8"), hashlib.sha256).hexdigest()
        if hmac.compare_digest(signature, expected_sig):
            return True, username
        return False, "Invalid token signature"
    except Exception as e:
        return False, f"Token validation error: {str(e)}"

def extract_bearer_token(headers):
    auth_header = headers.get("authorization") or headers.get("Authorization") or ""
    if auth_header.lower().startswith("bearer "):
        return auth_header[7:].strip()
    return auth_header.strip()

# ==============================================================================
# MAIN LAMBDA HANDLER
# ==============================================================================
def lambda_handler(event, context):
    headers = event.get("headers") or {}
    http_method = event.get("httpMethod") or event.get("requestContext", {}).get("http", {}).get("method")
    path = event.get("path") or event.get("rawPath", "")

    # 1. Handle CORS preflight OPTIONS request
    if http_method == "OPTIONS":
        return {
            "statusCode": 200,
            "headers": CORS_HEADERS,
            "body": json.dumps({"message": "CORS OK"})
        }

    try:
        # 2. PUBLIC LOGIN ROUTE: POST /login
        if http_method == "POST" and (path.endswith("/login") or path == "/login"):
            body = json.loads(event.get("body", "{}"))
            username = body.get("username", "").strip()
            password = body.get("password", "").strip()

            # Verify against configured credentials
            if username == DEFAULT_USERNAME and password == DEFAULT_PASSWORD:
                token = create_auth_token(username)
                return respond(200, {
                    "success": True,
                    "message": "Login successful",
                    "username": username,
                    "token": token,
                    "expiresIn": TOKEN_EXPIRY_SECONDS
                })
            else:
                return respond(401, {
                    "success": False,
                    "error": "Invalid username or password"
                })

        # 3. VERIFY TOKEN FOR ALL OTHER S3 ROUTES
        token = extract_bearer_token(headers)
        is_valid, user_or_err = verify_auth_token(token)
        if not is_valid:
            return respond(401, {
                "success": False,
                "error": f"Unauthorized: {user_or_err}"
            })

        # ======================================================================
        # PROTECTED S3 VAULT ROUTES (Require Valid Login Token)
        # ======================================================================

        # 4. LIST FILES: GET /files
        if http_method == "GET" and (path.endswith("/files") or path == "/files"):
            response = s3_client.list_objects_v2(Bucket=BUCKET_NAME)
            files = []
            for item in response.get("Contents", []):
                # Don't show internal system config files in the document list
                if item["Key"].startswith("_vault_internal/"):
                    continue
                files.append({
                    "name": item["Key"],
                    "size": item["Size"],
                    "date": int(item["LastModified"].timestamp() * 1000)
                })
            return respond(200, {"files": files, "authenticatedUser": user_or_err})

        # 5. GENERATE PRESIGNED UPLOAD URL: POST /upload-url
        elif http_method == "POST" and (path.endswith("/upload-url") or path == "/upload-url"):
            body = json.loads(event.get("body", "{}"))
            file_name = body.get("fileName")
            content_type = body.get("contentType", "application/octet-stream")

            if not file_name:
                return respond(400, {"error": "fileName is required"})

            presigned_url = s3_client.generate_presigned_url(
                ClientMethod="put_object",
                Params={
                    "Bucket": BUCKET_NAME,
                    "Key": file_name,
                    "ContentType": content_type
                },
                ExpiresIn=300  # 5 minutes
            )

            return respond(200, {
                "uploadUrl": presigned_url,
                "key": file_name
            })

        # 6. GENERATE PRESIGNED DOWNLOAD / PREVIEW URL: GET /download-url?key=filename
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
                ExpiresIn=3600  # 1 hour
            )

            return respond(200, {"url": presigned_url})

        # 7. DELETE FILE: DELETE /delete?key=filename
        elif http_method == "DELETE" and (path.endswith("/delete") or path == "/delete"):
            params = event.get("queryStringParameters") or {}
            key = params.get("key")

            if not key:
                return respond(400, {"error": "key query parameter is required"})

            s3_client.delete_object(Bucket=BUCKET_NAME, Key=key)
            return respond(200, {"message": f"File '{key}' deleted successfully"})

        # 8. SYNC USER PREFERENCES ACROSS ALL DEVICES: GET & POST /vault-config
        elif path.endswith("/vault-config") or path == "/vault-config":
            config_key = "_vault_internal/user_settings.json"
            if http_method == "GET":
                try:
                    obj = s3_client.get_object(Bucket=BUCKET_NAME, Key=config_key)
                    content = json.loads(obj["Body"].read().decode("utf-8"))
                    return respond(200, {"settings": content})
                except ClientError as ce:
                    if ce.response["Error"]["Code"] == "NoSuchKey":
                        return respond(200, {"settings": {}})
                    raise ce
            elif http_method == "POST":
                body = json.loads(event.get("body", "{}"))
                s3_client.put_object(
                    Bucket=BUCKET_NAME,
                    Key=config_key,
                    Body=json.dumps(body.get("settings", {})),
                    ContentType="application/json"
                )
                return respond(200, {"message": "Settings saved across all devices"})

        else:
            return respond(404, {"error": f"Route not found: {http_method} {path}"})

    except ClientError as e:
        return respond(500, {"error": str(e)})
    except Exception as e:
        return respond(500, {"error": f"Server error: {str(e)}"})


def respond(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            **CORS_HEADERS,
            "Content-Type": "application/json"
        },
        "body": json.dumps(body)
    }
