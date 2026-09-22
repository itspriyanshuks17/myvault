# CloudVault - Serverless Personal Document Vault

CloudVault is a secure, modern, serverless document storage platform. The frontend is hosted on **AWS Amplify**, interacting via **API Gateway** and **AWS Lambda** to securely store your files in a **Private Amazon S3 Bucket**.

---

## 🏛️ Architecture Overview

```text
               ┌───────────────────────┐
               │  AWS Amplify Hosting  │
               │  (Frontend Website)   │
               └──────────┬────────────┘
                          │ HTTPS
                          ▼
               ┌───────────────────────┐
               │    API Gateway        │
               │    (HTTP API)         │
               └──────────┬────────────┘
                          │ Proxy
                          ▼
               ┌───────────────────────┐
               │    AWS Lambda         │
               │  (lambda_function.py) │
               └──────────┬────────────┘
                          │ Generates Presigned URLs
                          ▼
               ┌───────────────────────┐
               │   PRIVATE S3 BUCKET   │
               │ myvaultbypriyanshu-   │
               │      documents        │
               └───────────────────────┘
```

### Why this architecture?
1. **100% Private S3 Storage**: "Block all public access" remains ON. Your personal documents are never exposed to the public internet.
2. **Zero Secrets in Browser**: No AWS Access Key ID or Secret Access Key is embedded in the frontend JavaScript.
3. **Direct Uploads/Downloads**: Lambda issues temporary S3 Presigned URLs (valid for 5–60 minutes), allowing files to stream directly between your browser and S3 with progress tracking.

---

## 📋 Step-by-Step Setup Guide

### Step 1: Create the Private S3 Document Bucket

1. Open the [AWS S3 Console](https://console.aws.amazon.com/s3/).
2. Click **Create bucket**.
3. **Bucket name**: `myvaultbypriyanshu-documents` *(or choose your own unique name)*.
4. **AWS Region**: Select your region (e.g. `us-east-1` or `ap-south-1`).
5. **Block Public Access**: Keep **"Block all public access" ENABLED (Checked)**.
6. Click **Create bucket**.

#### Configure S3 CORS:
1. In your newly created bucket, go to the **Permissions** tab.
2. Scroll down to **Cross-origin resource sharing (CORS)** and click **Edit**.
3. Paste the following JSON:

```json
[
  {
    "AllowedHeaders": ["*"],
    "AllowedMethods": ["GET", "PUT", "POST", "DELETE", "HEAD"],
    "AllowedOrigins": ["*"],
    "ExposeHeaders": ["ETag"],
    "MaxAgeSeconds": 3000
  }
]
```
4. Click **Save changes**.

---

### Step 2: Create the Lambda Backend Function

1. Open the [AWS Lambda Console](https://console.aws.amazon.com/lambda/).
2. Click **Create function**:
   - **Function name**: `myvault-backend`
   - **Runtime**: **Python 3.12** (or Python 3.11)
   - **Architecture**: `x86_64`
   - Click **Create function**.
3. Under the **Code** tab &rarr; open `lambda_function.py`:
   - Replace everything with the code from [`lambda_function.py`](./lambda_function.py).
   - *(Optional)* If your bucket name is different, change line 7:
     ```python
     BUCKET_NAME = os.environ.get("BUCKET_NAME", "myvaultbypriyanshu-documents")
     ```
   - Click **Deploy**.

#### Attach S3 Permissions to the Lambda Execution Role:
1. In the Lambda function, click the **Configuration** tab &rarr; **Permissions**.
2. Click the role name under **Execution role** (this opens AWS IAM in a new tab).
3. In IAM, click **Add permissions** &rarr; **Create inline policy**.
4. Click **JSON** and paste:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "VaultS3Access",
      "Effect": "Allow",
      "Action": [
        "s3:ListBucket",
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject"
      ],
      "Resource": [
        "arn:aws:s3:::myvaultbypriyanshu-documents",
        "arn:aws:s3:::myvaultbypriyanshu-documents/*"
      ]
    }
  ]
}
```
5. Click **Next**, name it `LambdaS3VaultPolicy`, and click **Create policy**.

---

### Step 3: Create the API Gateway (HTTP API)

1. Open the [AWS API Gateway Console](https://console.aws.amazon.com/apigateway/).
2. Click **Create API** &rarr; locate **HTTP API** and click **Build**.
3. **Integrations**:
   - Click **Add integration** &rarr; choose **Lambda**.
   - **Lambda function**: select `myvault-backend`.
   - **API name**: `myvault-api`.
   - Click **Next**.
4. **Configure routes**:
   - Leave the default route (`$default`) pointed to `myvault-backend`.
   - Click **Next**.
5. **Configure stages**:
   - Keep stage `$default` with auto-deploy enabled &rarr; Click **Next** &rarr; Click **Create**.

#### Configure API Gateway CORS:
1. In the left sidebar of your API Gateway, click **CORS** &rarr; click **Configure**.
2. Fill in:
   - **Access-Control-Allow-Origin**: `*` *(or your Amplify domain: `https://*.amplifyapp.com`)*
   - **Access-Control-Allow-Headers**: `Content-Type,Authorization`
   - **Access-Control-Allow-Methods**: `GET,POST,DELETE,OPTIONS`
3. Click **Save**.
4. Copy the **Invoke URL** shown on your API overview page (e.g. `https://xyz123.execute-api.us-east-1.amazonaws.com`).

---

### Step 4: IAM Policy for User

If you want to attach a policy to an IAM user to manage this bucket and CloudVault infrastructure:

#### Option A: Scoped Document Access Policy (Application User)
Attach this policy to an IAM user if you want to grant access strictly to this bucket:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ListVaultBucket",
      "Effect": "Allow",
      "Action": [
        "s3:ListBucket",
        "s3:GetBucketLocation"
      ],
      "Resource": "arn:aws:s3:::myvaultbypriyanshu-documents"
    },
    {
      "Sid": "ReadWriteDeleteVaultObjects",
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:DeleteObject"
      ],
      "Resource": "arn:aws:s3:::myvaultbypriyanshu-documents/*"
    }
  ]
}
```

#### Option B: Full CloudVault Stack Policy (Developer Admin)
Attach this policy if your IAM user needs to manage the S3 bucket, Lambda function, and API Gateway:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "S3VaultManagement",
      "Effect": "Allow",
      "Action": ["s3:*"],
      "Resource": [
        "arn:aws:s3:::myvaultbypriyanshu-documents",
        "arn:aws:s3:::myvaultbypriyanshu-documents/*"
      ]
    },
    {
      "Sid": "LambdaBackendManagement",
      "Effect": "Allow",
      "Action": [
        "lambda:CreateFunction",
        "lambda:UpdateFunctionCode",
        "lambda:UpdateFunctionConfiguration",
        "lambda:GetFunction",
        "lambda:InvokeFunction",
        "lambda:AddPermission"
      ],
      "Resource": "arn:aws:lambda:*:*:function:myvault-backend"
    },
    {
      "Sid": "APIGatewayManagement",
      "Effect": "Allow",
      "Action": ["apigateway:*"],
      "Resource": "arn:aws:apigateway:*::/*"
    },
    {
      "Sid": "CloudWatchLogs",
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents",
        "logs:DescribeLogStreams"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    }
  ]
}
```

---

### Step 5: Connect Your Amplify Frontend

1. Commit and push your updated files to GitHub so Amplify automatically redeploys:
   ```bash
   git add .
   git commit -m "Configure API Gateway serverless backend"
   git push
   ```
2. Open your deployed website on Amplify (e.g., `https://main.xxxx.amplifyapp.com`).
3. Click the **Gear icon (⚙️)** or the status pill in the top header.
4. Select **AWS API Gateway + Lambda** as the storage mode.
5. Paste your **API Gateway Invoke URL** (e.g. `https://xyz123.execute-api.us-east-1.amazonaws.com`).
6. Click **🔍 Test API Gateway & S3 Connection**.
7. Once verified, click **Save Configuration**.

---

## ✨ Features Available on Your Site

- 🔍 **Real-Time Search**: Search documents by keyword, file extension (`.pdf`, `.png`), or tag. Press `/` to focus.
- 📁 **Category Filters**: Instant tabs for All Files, PDFs, Images, Docs & Notes, Spreadsheets, Archives, and Code.
- 🔀 **Multi-Sort**: Sort by Date (Newest/Oldest), Name (A-Z / Z-A), and Size (Smallest/Largest).
- 👁️ **In-App Previews**: View PDFs, images, text, and code directly in a modal without downloading first.
- 📊 **Storage Analytics**: Real-time stats showing Total Documents, Storage Consumed, and Active Categories.
- 🌓 **Theme Switcher**: Dark Mode and Light Mode with instant toggle.
- ⚡ **Direct S3 Streaming**: Files stream with real-time upload progress bars directly to your private S3 bucket.
