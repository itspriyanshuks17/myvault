# Complete Configuration Guide: AWS Amplify + Amazon S3 Vault

This guide walks you through connecting your **Amplify-hosted CloudVault** website to your **Amazon S3** bucket so that you can upload, access, and manage personal documents from anywhere securely.

---

## Architecture Overview

```
[ User Browser ]  <--- HTTPS --->  [ AWS Amplify Hosting ] (Hosts index.html)
       |
       | Direct Encrypted S3 Upload / Download
       v
[ Amazon S3 Bucket ] (Stores your actual documents)
```

---

## Step 1: Create Your Amazon S3 Bucket

1. Log in to the [AWS Management Console](https://console.aws.amazon.com/s3/).
2. In the search bar at the top, type **S3** and select it.
3. Click **Create bucket**.
4. Configure bucket settings:
   - **Bucket name**: Choose a globally unique name (e.g. `my-cloudvault-docs-2026`).
   - **AWS Region**: Select the region closest to you (e.g. `us-east-1` for N. Virginia or `ap-south-1` for Mumbai).
   - **Block Public Access**: Keep **"Block all public access" ENABLED (Checked)**. *(Your files stay private and safe; the app accesses them using authenticated API keys or signed URLs).*
   - **Bucket Versioning**: *(Optional)* Enable if you want version history for changed files.
   - **Encryption**: Keep default (Amazon S3-managed keys - SSE-S3).
5. Click **Create bucket** at the bottom.

---

## Step 2: Configure S3 CORS (Cross-Origin Resource Sharing)

Because your website is served from Amplify (e.g. `https://main.xxxx.amplifyapp.com`), modern browsers block web requests to S3 unless S3 explicitly permits your domain.

1. Click on your newly created bucket name in the S3 console.
2. Go to the **Permissions** tab.
3. Scroll down to the **Cross-origin resource sharing (CORS)** card and click **Edit**.
4. Paste the following configuration:

```json
[
  {
    "AllowedHeaders": [
      "*"
    ],
    "AllowedMethods": [
      "GET",
      "PUT",
      "POST",
      "DELETE",
      "HEAD"
    ],
    "AllowedOrigins": [
      "https://*.amplifyapp.com",
      "http://localhost:*"
    ],
    "ExposeHeaders": [
      "ETag",
      "x-amz-meta-custom-header"
    ],
    "MaxAgeSeconds": 3000
  }
]
```

> **Note**: If you have a custom domain on Amplify (e.g. `vault.yourdomain.com`), also add `"https://vault.yourdomain.com"` into the `"AllowedOrigins"` array.

5. Click **Save changes**.

---

## Step 3: Create an IAM User with S3 Access

To allow your browser to securely upload and download documents from your bucket, create a dedicated IAM user with minimal necessary permissions.

1. Open the [AWS IAM Console](https://console.aws.amazon.com/iam/).
2. In the left navigation, click **Users** &rarr; **Create user**.
3. **User details**:
   - Username: `cloudvault-app-user`
   - Do NOT check the console access checkbox. Click **Next**.
4. **Set permissions**:
   - Choose **Attach policies directly**.
   - Click **Create policy** (opens in a new tab).
   - In the Policy editor, click **JSON** and paste this scoped policy (replace `YOUR-BUCKET-NAME` with your actual bucket name):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ListBucketContents",
      "Effect": "Allow",
      "Action": [
        "s3:ListBucket",
        "s3:GetBucketLocation"
      ],
      "Resource": "arn:aws:s3:::YOUR-BUCKET-NAME"
    },
    {
      "Sid": "ReadWriteObjects",
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:DeleteObject"
      ],
      "Resource": "arn:aws:s3:::YOUR-BUCKET-NAME/*"
    }
  ]
}
```

5. Click **Next**, name the policy `CloudVaultS3Policy`, and click **Create policy**.
6. Switch back to the **Create user** tab, click the refresh icon on the policies list, search for `CloudVaultS3Policy`, select its checkbox, and click **Next**.
7. Click **Create user**.

### Generate Access Key & Secret Key:
8. Click on your newly created user (`cloudvault-app-user`).
9. Go to the **Security credentials** tab.
10. Scroll down to **Access keys** and click **Create access key**.
11. Choose **Application running outside AWS** (or Other) and click **Next** &rarr; **Create access key**.
12. **Copy and save**:
    - **Access Key ID** (e.g. `AKIAIOSFODNN7EXAMPLE`)
    - **Secret Access Key** (e.g. `wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY`)

---

## Step 4: Configure CloudVault in Your Browser

1. Open your deployed website on Amplify (e.g., `https://main.xxxx.amplifyapp.com`).
2. Click the **Gear icon (⚙️)** in the top right, or click the **Local Vault (Ready)** pill.
3. In the modal:
   - Change **Storage Backend Mode** to **AWS S3 Direct Bucket Sync**.
   - Enter your **S3 Bucket Name** (e.g. `my-cloudvault-docs-2026`).
   - Select your **AWS Region** (e.g. `us-east-1` or `ap-south-1`).
   - Enter your **Access Key ID**.
   - Enter your **Secret Access Key**.
4. Click **Test S3 Connection**.
   - If connected, you will see a green **"Connected to S3 Successfully!"** notice.
5. Click **Save Configuration**.

---

## Step 5: Test Upload & Retrieval

1. Drag and drop any document (PDF, PNG, docx, etc.) into the upload zone.
2. The document is uploaded directly to your Amazon S3 bucket.
3. Test **Search**, **Filter pills**, **Preview**, and **Download**.
4. Open the AWS S3 Console in another tab &rarr; view your bucket &rarr; your uploaded files will be listed there!

---

## Security Notes

- **Credential Storage**: Your AWS credentials are saved strictly in your own browser's private `localStorage` and never transmitted to any third party server.
- **Bucket Privacy**: Because "Block all public access" is enabled on your bucket, your files cannot be accessed by anyone on the internet without valid AWS credentials or signed links generated by your app.
