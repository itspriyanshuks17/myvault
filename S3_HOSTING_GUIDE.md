# Amazon S3 Hosting Guide for CloudVault

CloudVault is built as a single-page static web application. It requires **no server setup, no Node.js backend, and zero build commands**. You can deploy it to Amazon S3 in less than 5 minutes.

---

## Quick Deployment Steps

### 1. Create an S3 Bucket
1. Open the [AWS S3 Console](https://console.aws.amazon.com/s3/).
2. Click **Create bucket**.
3. Choose a unique name (e.g., `my-personal-cloudvault-101`).
4. Select your preferred AWS Region (e.g., `us-east-1` or `ap-south-1`).
5. **Block Public Access settings**:
   - If hosting directly via S3 website endpoint: Uncheck *Block all public access* and acknowledge the warning.
   - *(Recommended for production)*: Keep public access blocked and use an **AWS CloudFront** distribution with Origin Access Control (OAC).

---

### 2. Enable Static Website Hosting
1. Go to your bucket's **Properties** tab.
2. Scroll to the bottom to **Static website hosting** and click **Edit**.
3. Select **Enable**.
4. Set **Index document** to `index.html`.
5. Click **Save changes**.
6. Copy the **Bucket website endpoint** URL provided (e.g., `http://my-personal-cloudvault-101.s3-website-us-east-1.amazonaws.com`).

---

### 3. Add Bucket Policy (for Public Static Website)
Under the **Permissions** tab -> **Bucket policy**, paste this (replace `YOUR-BUCKET-NAME` with your actual bucket name):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PublicReadGetObject",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::YOUR-BUCKET-NAME/*"
    }
  ]
}
```

---

### 4. Configure CORS (Cross-Origin Resource Sharing)
Under the **Permissions** tab -> **Cross-origin resource sharing (CORS)**, paste:

```json
[
  {
    "AllowedHeaders": ["*"],
    "AllowedMethods": ["GET", "PUT", "POST", "DELETE", "HEAD"],
    "AllowedOrigins": ["*"],
    "ExposeHeaders": ["ETag"]
  }
]
```

---

### 5. Upload `index.html`
- **Via AWS Web Console**:
  - Click **Upload** -> Add `index.html` -> Click **Upload**.
- **Or via AWS CLI**:
  ```bash
  aws s3 cp index.html s3://YOUR-BUCKET-NAME/index.html --content-type text/html
  ```

Visit your S3 website endpoint URL in any browser on your computer, tablet, or phone, and your personal document vault will be live!

---

## Vault Features Summary

- **Instant Search**: Search through document names, extensions, or tags in real time. Press `/` anywhere to focus search.
- **Category Filter Pills**: Fast filtering by `PDF Documents`, `Images`, `Docs & Notes`, `Spreadsheets`, `Archives`, and `Code & JSON`.
- **Sorting Options**: Sort by Newest, Oldest, Name (A-Z / Z-A), and File Size (Smallest / Largest).
- **View Modes**: Switch between Grid Card View (with image thumbnails) and List Table View.
- **In-App Previews**: Preview PDFs, photos, text documents, and code right within the web app without downloading first.
- **Batch Management**: Multi-select documents to batch download or batch delete.
- **Storage Flexibility**:
  - **Local Vault (IndexedDB)**: Works immediately without any setup. Data persists securely inside your browser.
  - **AWS S3 Direct**: Connect your bucket credentials via the Settings gear in the header to sync directly to AWS S3.
- **Dark & Light Modes**: Beautiful themes with smooth transitions and persistent preference.
