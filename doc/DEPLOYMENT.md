# Deployment Guide

This project uses **GitHub Actions** to automate the deployment of the Astro frontend to AWS S3 and CloudFront.

## How Deployment Works

The deployment workflow is defined in `.github/workflows/deploy.yml`.

1.  **Trigger**: The workflow starts automatically whenever code is pushed to the **`dev`** branch.
2.  **Build**: It installs dependencies (`npm install`) and builds the Astro project (`npm run build`) inside the `frontend` directory.
3.  **Deploy**: The built files (from `frontend/dist`) are synced to your AWS S3 bucket.
4.  **Invalidate**: The CloudFront cache is invalidated so that changes are visible immediately.

## Required GitHub Secrets

For the deployment to succeed, you **MUST** configure the following secrets in your GitHub repository.

Go to: **Settings** -> **Secrets and variables** -> **Actions** -> **New repository secret**

| Secret Name | Description | Example Value |
| :--- | :--- | :--- |
| `AWS_ACCESS_KEY_ID` | Access Key ID for the IAM User | `AKIAIOSFODNN7EXAMPLE` |
| `AWS_SECRET_ACCESS_KEY` | Secret Access Key for the IAM User | `wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY` |
| `AWS_REGION` | AWS Region where resources are deployed | `eu-central-1` |
| `S3_BUCKET_NAME` | Name of your S3 bucket | `my-astro-site-bucket` |
| `CLOUDFRONT_ID` | Distribution ID of your CloudFront distribution | `E1234567890EXAMPLE` |

> [!IMPORTANT]
> Ensure the IAM User associated with these keys has `S3FullAccess` and `CloudFrontFullAccess` permissions (or a more scoped-down policy allowing `s3:PutObject`, `s3:DeleteObject`, and `cloudfront:CreateInvalidation`).
