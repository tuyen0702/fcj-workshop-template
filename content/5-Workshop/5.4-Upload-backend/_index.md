---
title : "Build Upload Backend with API Gateway, Lambda, S3, and DynamoDB"
date : 2026-07-03 
weight : 4
chapter : false
pre : " <b> 5.4. </b> "
---

#### Upload backend overview

In this section, the backend upload service of the **AI AWS Architecture Reviewer** project is implemented using **Amazon API Gateway**, **AWS Lambda**, **Amazon S3**, and **Amazon DynamoDB**.

The upload backend allows users to upload AWS architecture diagrams from the React frontend. The uploaded file is stored in an S3 Input Bucket, while review metadata is saved in DynamoDB.

The upload backend flow is:

```text
React Frontend → API Gateway → Lambda Upload Service → S3 Input Bucket
                                      ↓
                                  DynamoDB
```
The main backend resources used in this section are:
```text
Amazon API Gateway
AWS Lambda Upload Service
Amazon S3 Input Bucket
Amazon DynamoDB
Amazon CloudWatch
AWS IAM
```

#### Step 1: Create the S3 Input Bucket
Create an Amazon S3 bucket to store uploaded architecture diagrams.
The S3 Input Bucket used in this project is:
```text
ai-aws-reviewer-input-bucket-tiersteam
```
Uploaded files are stored using the following key pattern:
```text
uploads/{reviewId}/{fileName}
```
Example:
```text
uploads/REV-C6A0D048/architecture-2.jpg
```
![S3 Input](/images/5-Workshop/5.4-Upload-backend/ai-aws-reviewer-input-bucket-tiersteam.png)

#### Step 2: Create the DynamoDB review table

Create a DynamoDB table to store review metadata and review history.
The DynamoDB table used in this project is:
```text
AIArchitectureReviews
```
The partition key is:
```text
reviewId
```
The table stores information such as:
```text
Review ID
File name
File type
File size
S3 input bucket
S3 object key
Upload date
Updated date
Review status
Architecture type
```

![DynamoDB](/images/5-Workshop/5.4-Upload-backend/AIArchitectureReviews.png)

#### Step 3: Create the Lambda execution role

Create an IAM role for the Lambda Upload Service.

This role allows Lambda to access the required AWS services, including:
```text
Amazon S3
Amazon DynamoDB
Amazon CloudWatch Logs
```
The Lambda function needs permission to upload files to S3, write review metadata to DynamoDB, and write logs to CloudWatch.

![Lambda Execution Role](/images/5-Workshop/5.4-Upload-backend/ai-aws-reviewer-upload-lambda-role.png)

![Lambda Execution Inline Policy](/images/5-Workshop/5.4-Upload-backend/ai-aws-reviewer-upload-lambda-role-inline-policy.png)

#### Step 4: Create the Lambda Upload Service
Create an AWS Lambda function to handle upload requests.
The Lambda function name is:
```text
ai-aws-reviewer-upload-service
```
This function is responsible for:
```text
Receiving upload requests from API Gateway.
Validating file type and file size.
Generating a unique review ID.
Uploading the diagram file to Amazon S3.
Saving review metadata to DynamoDB.
Returning upload response to the frontend.
```
![Lambda](/images/5-Workshop/5.4-Upload-backend/ai-aws-reviewer-upload-service.png)

#### Step 5: Configure Lambda environment variables

Configure the required environment variables for the Lambda Upload Service.

Example environment variables:
```text
INPUT_BUCKET = ai-aws-reviewer-input-bucket-tiersteam
TABLE_NAME = AIArchitectureReviews
MAX_FILE_SIZE_MB = 5
ALLOWED_ORIGINS = http://localhost:5173,https://d9353ayez9zar.cloudfront.net
```
These environment variables allow the Lambda function to identify the input bucket, DynamoDB table, upload size limit, and allowed frontend origins.

![Lambda](/images/5-Workshop/5.4-Upload-backend/ai-aws-reviewer-upload-service-env.png)

#### Step 6: Implement upload processing logic

The Lambda function validates the uploaded file and generates a unique review ID.

The review ID format is:
```text
REV-XXXXXXXX
```
Example:
```text
REV-C6A0D048
```
After the review ID is generated, the uploaded file is saved to Amazon S3 using this key structure:
```text
uploads/{reviewId}/{fileName}
```
Then, the Lambda function writes metadata to DynamoDB with an initial status:
```text
uploaded
```

This status means the diagram has been uploaded successfully and is ready for the next review workflow.



#### Step 7: Create API Gateway upload route

Create an API Gateway endpoint and connect it to the Lambda Upload Service.

The API Gateway endpoint used in this project is:
```text
https://031hqksomd.execute-api.ap-southeast-1.amazonaws.com
```
Create the following route:
```text
POST /upload
```
This route receives upload requests from the React frontend and forwards them to the Lambda Upload Service.

![API Gateway](/images/5-Workshop/5.4-Upload-backend/ai-aws-reviewer-api.png)

#### Step 8: Configure CORS

CORS must be configured so the React frontend can call the backend API.

Allowed origins:
```text
http://localhost:5173
https://d9353ayez9zar.cloudfront.net
```
Allowed methods:
```text
POST
OPTIONS
```
Allowed headers:
```text
content-type
authorization
```
The OPTIONS method is required because browsers send preflight requests before certain cross-origin API calls.

![API Gateway](/images/5-Workshop/5.4-Upload-backend/ai-aws-reviewer-api-cors.png)

#### Step 9: Test file upload using PowerShell

Prepare a test architecture diagram file.

Example file path:
```text
D:\Learning\AWS\test-files\architecture-1.png
```
Run the following command to test upload:
```text
curl.exe -X POST "https://031hqksomd.execute-api.ap-southeast-1.amazonaws.com/upload" -F "file=@D:\Learning\AWS\test-files\architecture-1.png"
```
If the upload is successful, the API returns a response similar to:
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

![API Gateway](/images/5-Workshop/5.4-Upload-backend/ai-aws-reviewer-upload-service-test-files.png)

#### Step 10: Verify uploaded file in S3

After testing the upload API, open the S3 Input Bucket and verify that the uploaded diagram file exists.

The file should be stored under:
```text
uploads/{reviewId}/{fileName}
```
Example:
```text
uploads/REV-C29F2778/architecture-1.png
```

![S3](/images/5-Workshop/5.4-Upload-backend/ai-aws-reviewer-input-bucket-tiersteam.png)

#### Step 11: Verify metadata in DynamoDB

Open the DynamoDB table and verify that a new review item has been created.

The item should include information such as:
```text
reviewId
fileName
fileType
fileSize
s3InputBucket
s3InputKey
status
uploadDate
updatedAt
```
![DynamoDB](/images/5-Workshop/5.4-Upload-backend/AIArchitectureReviews-verify.png)
