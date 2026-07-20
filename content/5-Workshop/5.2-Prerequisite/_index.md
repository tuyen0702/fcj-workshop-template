---
title : "Prerequisite"
date : 2026-07-03 
weight : 2 
chapter : false
pre : " <b> 5.2. </b> "
---

#### Required AWS Region

In this workshop, the main AWS Region used for backend services is:

```text
Asia Pacific (Singapore) - ap-southeast-1
```

#### Required Tools
Before starting this workshop, make sure the following tools are installed and configured on your local machine:

+ An AWS account is required to create and manage the services used in this project.

+ Node.js and npm are required to run, build, and deploy the React frontend application.

+ The frontend application is built using React and Vite.

+ Antigravity can be used to edit frontend source code and documentation files.

+ A browser is required to access the deployed CloudFront website and test the application.

#### Local Project Folder

The project source code is stored in the following local directory:

```text
D:\Learning\AWS\ai-aws-architecture-reviewer
```

This folder contains the React frontend source code, configuration files, and build output.

The main frontend build command is:

```text
npm run build
```

After the build is completed, the production files are generated in the dist folder.

#### IAM Permissions

The IAM user or role used in this workshop needs permissions to create, configure, deploy, test, and clean up the AWS services used by the AI AWS Architecture Reviewer project.

The required AWS services include:

+ Amazon S3,
+ Amazon CloudFront,
+ Amazon API Gateway,
+ AWS Lambda,
+ Amazon DynamoDB,
+ Amazon EventBridge,
+ AWS Step Functions,
+ Amazon Bedrock,
+ Amazon SNS,
+ Amazon CloudWatch,
+ IAM.

#### Frontend Hosting Resources

The frontend application is deployed using Amazon S3 and Amazon CloudFront.
The S3 frontend bucket is used to store the React production build files:
```text
ai-aws-reviewer-frontend-tiersteam
```

The CloudFront distribution is used to deliver the website to users.
The frontend deployment command is:
```text
aws s3 sync dist s3://ai-aws-reviewer-frontend-tiersteam --delete
```
The deployed CloudFront domain is:
```text
https://d9353ayez9zar.cloudfront.net
```

After uploading a new build, create a CloudFront invalidation:
```text
/*
```
This ensures that CloudFront serves the latest version of the React application.


#### Backend API Resources

The backend API is exposed through Amazon API Gateway.

The API Gateway endpoint is:
```text
https://031hqksomd.execute-api.ap-southeast-1.amazonaws.com
```
The following API routes are required:
```text
POST /upload
GET /reviews
GET /reviews/{reviewId}
GET /reviews/{reviewId}/status
```
These routes are integrated with the Lambda Upload Service.


#### Storage Resources

The system uses Amazon S3 and Amazon DynamoDB for storage.

The S3 Input Bucket stores uploaded architecture diagrams:
```text
ai-aws-reviewer-input-bucket-tiersteam
```

Uploaded diagrams are stored using the following key pattern:

```text
uploads/{reviewId}/{fileName}
```

The DynamoDB table stores review metadata and review history:
```text
AIArchitectureReviews
```

The partition key is:
```text
reviewId
```

#### Lambda Upload Service

The upload backend is implemented using AWS Lambda.

The Lambda function name is:

```text
ai-aws-reviewer-upload-service
```

This function handles:

+ Upload request validation
+ File type and file size validation
+ Review ID generation
+ Uploading architecture diagrams to S3 Input Bucket
+ Writing review metadata to DynamoDB
+ Returning review information to the frontend
+ Retrieving review history and review status


The required Lambda environment variables are:
```text
INPUT_BUCKET = ai-aws-reviewer-input-bucket-tiersteam
TABLE_NAME = AIArchitectureReviews
MAX_FILE_SIZE_MB = 5
ALLOWED_ORIGINS = http://localhost:5173,https://d9353ayez9zar.cloudfront.net
```

#### Test Files

Prepare one or more test architecture diagram files for upload testing.

Example folder:
```text
D:\Learning\AWS\test-files
```

Example files:
```text
architecture-1.png
architecture-2.jpg
```
To test upload using PowerShell, run:
```text
curl.exe -X POST "https://031hqksomd.execute-api.ap-southeast-1.amazonaws.com/upload" -F "file=@D:\Learning\AWS\test-files\architecture-1.png"
```

If the upload is successful, the API returns a response containing a reviewId.

Example response:
```text
{
  "reviewId": "REV-5E57628D",
  "status": "uploaded",
  "fileName": "architecture-1.png",
  "fileType": "image/png",
  "fileSize": 17755,
  "message": "Upload successful"
}
```