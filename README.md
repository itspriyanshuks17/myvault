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

### Step 2: Deploy the Lambda Backend Function

You can deploy the Lambda backend using either the **AWS Management Console (Recommended / Easiest)** or via the **AWS CLI**.

---

#### Method A: Deploy via AWS Management Console (Easiest)

1. Open the [AWS Lambda Console](https://console.aws.amazon.com/lambda/).
2. Make sure you are in the same AWS Region as your S3 bucket (e.g. `us-east-1` or `ap-south-1`).
3. Click **Create function**:
   - Select **Author from scratch**.
   - **Function name**: `myvault-backend`
   - **Runtime**: **Python 3.12**
   - **Architecture**: `x86_64`
   - **Execution role**: Leave default (*"Create a new role with basic Lambda permissions"*).
   - Click **Create function**.
4. **Paste the Code**:
   - Scroll down to the **Code source** section.
   - Double-click `lambda_function.py` in the file tree.
   - Select all existing placeholder code and delete it.
   - Copy the complete content from [`lambda_function.py`](./lambda_function.py) in this repo and paste it into the editor.
   - Click the orange **Deploy** button above the code editor.
5. **Configure Environment Variables**:
   - Go to the **Configuration** tab &rarr; **Environment variables** (in the left sub-menu) &rarr; Click **Edit**.
   - Click **Add environment variable**:
     - **Key**: `BUCKET_NAME`
     - **Value**: `myvaultbypriyanshu-documents` *(replace with your actual bucket name)*
   - Click **Save**.
6. **Increase Function Timeout**:
   - Under the **Configuration** tab &rarr; **General configuration** &rarr; Click **Edit**.
   - Change **Timeout** from `0 min 3 sec` to `0 min 15 sec` (prevents timeouts when listing large buckets).
   - Click **Save**.

---

#### Method B: Deploy via AWS CLI (PowerShell / Command Line)

If you have the [AWS CLI](https://aws.amazon.com/cli/) installed and configured:

1. **Package the code into a ZIP archive**:
   ```powershell
   Compress-Archive -Path lambda_function.py -DestinationPath lambda_function.zip -Force
   ```

2. **Create the IAM Execution Role (if you don't already have one)**:
   ```powershell
   # Create trust policy file
   @'
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Principal": { "Service": "lambda.amazonaws.com" },
         "Action": "sts:AssumeRole"
       }
     ]
   }
   '@ | Out-File -Encoding ascii trust-policy.json

   # Create the role
   aws iam create-role --role-name myvault-lambda-role --assume-role-policy-document file://trust-policy.json

   # Attach basic CloudWatch logging
   aws iam attach-role-policy --role-name myvault-lambda-role --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
   ```

3. **Deploy the Lambda Function**:
   ```powershell
   # Replace YOUR_ACCOUNT_ID with your 12-digit AWS Account ID
   aws lambda create-function `
     --function-name myvault-backend `
     --runtime python3.12 `
     --role arn:aws:iam::YOUR_ACCOUNT_ID:role/myvault-lambda-role `
     --handler lambda_function.lambda_handler `
     --zip-file fileb://lambda_function.zip `
     --timeout 15 `
     --environment "Variables={BUCKET_NAME=myvaultbypriyanshu-documents}"
   ```

4. **To update the function later when you make changes**:
   ```powershell
   Compress-Archive -Path lambda_function.py -DestinationPath lambda_function.zip -Force
   aws lambda update-function-code --function-name myvault-backend --zip-file fileb://lambda_function.zip
   ```

---

#### Attach S3 Permissions to the Lambda Execution Role:

Your Lambda function must be allowed to read and write to your private S3 bucket:

1. In your Lambda function, click the **Configuration** tab &rarr; **Permissions**.
2. Under **Execution role**, click on the Role Name link (e.g. `myvault-backend-role-...`), which opens AWS IAM in a new tab.
3. In IAM, click **Add permissions** &rarr; **Create inline policy**.
4. Click the **JSON** tab in the top right of the policy editor.
5. Paste this policy:

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
*(Replace `myvaultbypriyanshu-documents` with your actual bucket name if different)*.
6. Click **Next**, enter `LambdaS3VaultPolicy` as the policy name, and click **Create policy**.

---

#### Test Your Lambda Function (Verification):

You can test that Lambda can talk to your S3 bucket directly from the AWS Console before even touching API Gateway!

1. In the Lambda function, click the **Test** tab (next to Code).
2. **Event name**: `TestListFiles`
3. In the **Event JSON** editor, paste:
   ```json
   {
     "rawPath": "/files",
     "requestContext": {
       "http": {
         "method": "GET"
       }
     }
   }
   ```
4. Click **Test** (orange button at top right).
5. You should see a green **"Execution result: succeeded"** banner with `statusCode: 200` and `"files": []`. If you see that, your Lambda function is 100% working and ready!

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
