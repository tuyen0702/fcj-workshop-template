---
title : "Deploy React Frontend with S3 and CloudFront"
date : 2026-07-03 
weight : 3
chapter : false
pre : " <b> 5.3. </b> "
---

#### Frontend hosting overview

In this section, the React frontend of the **AI AWS Architecture Reviewer** project is deployed to AWS using **Amazon S3** and **Amazon CloudFront**.

The React application is built locally using Vite. After the production build is generated, the files inside the `dist` folder are uploaded to an Amazon S3 bucket. Amazon CloudFront is then used to securely distribute the website to users with better performance and caching.

The frontend deployment flow is:

```text
React Source Code → npm run build → dist folder → Amazon S3 Frontend Bucket → Amazon CloudFront → User
```
The frontend bucket used in this project is:
```text
ai-aws-reviewer-frontend-tiersteam
```
The CloudFront domain used to access the deployed website is:
```text
https://d9353ayez9zar.cloudfront.net
```

#### Step 1: Build the React application

Open PowerShell and go to the project folder:

```text
cd D:\Learning\AWS\ai-aws-architecture-reviewer
```
Run the build command:
```text
npm run build
```
After the build is completed, Vite generates the production files in the dist folder.

#### Step 2: Create the S3 frontend bucket

Create an Amazon S3 bucket to store the React production build files.

The bucket name used in this project is:
```text
ai-aws-reviewer-frontend-tiersteam
```
This bucket stores files such as:
```text
index.html
JavaScript assets
CSS assets
image assets
other static frontend files
```

![S3 React App](/images/5-Workshop/5.3-Frontend-hosting/ai-aws-reviewer-frontend-tiersteam.png)

#### Step 3: Upload frontend build files to S3

After the React application is built, upload the content of the dist folder to the S3 frontend bucket.

Run the following command:
```text
aws s3 sync dist s3://ai-aws-reviewer-frontend-tiersteam --delete
```
The --delete option removes old files in the S3 bucket that no longer exist in the latest build. This helps prevent CloudFront or the browser from loading outdated frontend assets.

#### Step 4: Create a CloudFront distribution

Amazon CloudFront is used to deliver the React frontend to users.

The CloudFront distribution connects to the S3 frontend bucket as its origin. Users access the frontend through the CloudFront domain instead of accessing the S3 bucket directly.

CloudFront distribution domain:
```text
https://d9353ayez9zar.cloudfront.net
```
CloudFront distribution ID:
```text
E2JHD76RIC6AML
```

![CloudFront](/images/5-Workshop/5.3-Frontend-hosting/ai-aws-reviewer-cloudfront.png)

#### Step 5: Configure Origin Access Control

The S3 frontend bucket is kept private. To allow CloudFront to read files from the private S3 bucket, Origin Access Control is configured.

This setup improves security because users cannot directly access the S3 bucket. They must access the website through CloudFront.

![CloudFront](/images/5-Workshop/5.3-Frontend-hosting/ai-aws-reviewer-cloudfront-2.png)

#### Step 6: Configure S3 bucket policy

After configuring Origin Access Control, update the S3 bucket policy to allow the CloudFront distribution to read objects from the bucket.

The bucket policy allows CloudFront to perform s3:GetObject on frontend files.

![S3 React App Policy](/images/5-Workshop/5.3-Frontend-hosting/ai-aws-reviewer-frontend-tiersteam-policy.png)

#### Step 7: Configure default root object

In CloudFront, configure the default root object as:
```text
index.html
```
This allows users to access the website by opening the CloudFront root domain without typing index.html.

Example:
```text
https://d9353ayez9zar.cloudfront.net
```

#### Step 8: Configure React Router fallback

Because the frontend is a React Single Page Application, direct access to routes such as /reviews or /settings may return an error if CloudFront cannot find a physical file with that path.

To fix this, custom error responses are configured in CloudFront:
```text
403 → /index.html → 200
404 → /index.html → 200
```
This allows React Router to handle frontend routes correctly.

![CloudFront](/images/5-Workshop/5.3-Frontend-hosting/ai-aws-reviewer-cloudfront-3.png)

#### Step 9: Create CloudFront invalidation

After uploading a new frontend build to S3, CloudFront may still serve cached files. To make CloudFront load the latest frontend version, create an invalidation.

Run the following command:

```text
aws cloudfront create-invalidation --distribution-id E2JHD76RIC6AML --paths "/*"
```

Wait until the invalidation status becomes **Completed**.

![CloudFront](/images/5-Workshop/5.3-Frontend-hosting/ai-aws-reviewer-cloudfront-4.png)

#### Step 10: Test the deployed website

Open the CloudFront domain in a browser:

```text
https://d9353ayez9zar.cloudfront.net
```

The React frontend should load successfully.

![React App](/images/5-Workshop/5.3-Frontend-hosting/Website-project.png)