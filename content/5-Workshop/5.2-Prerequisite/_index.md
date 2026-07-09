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

For a workshop, the following IAM policy can be attached to the IAM user or role used for deployment.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "S3Permissions",
      "Effect": "Allow",
      "Action": [
        "s3:CreateBucket",
        "s3:DeleteBucket",
        "s3:ListAllMyBuckets",
        "s3:ListBucket",
        "s3:GetBucketLocation",
        "s3:GetBucketPolicy",
        "s3:PutBucketPolicy",
        "s3:DeleteBucketPolicy",
        "s3:GetBucketPublicAccessBlock",
        "s3:PutBucketPublicAccessBlock",
        "s3:GetBucketWebsite",
        "s3:PutBucketWebsite",
        "s3:DeleteBucketWebsite",
        "s3:GetBucketVersioning",
        "s3:PutBucketVersioning",
        "s3:GetEncryptionConfiguration",
        "s3:PutEncryptionConfiguration",
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject",
        "s3:DeleteObjectVersion",
        "s3:ListBucketMultipartUploads",
        "s3:AbortMultipartUpload"
      ],
      "Resource": "*"
    },
    {
      "Sid": "CloudFrontPermissions",
      "Effect": "Allow",
      "Action": [
        "cloudfront:CreateDistribution",
        "cloudfront:GetDistribution",
        "cloudfront:GetDistributionConfig",
        "cloudfront:UpdateDistribution",
        "cloudfront:DeleteDistribution",
        "cloudfront:ListDistributions",
        "cloudfront:CreateInvalidation",
        "cloudfront:GetInvalidation",
        "cloudfront:ListInvalidations",
        "cloudfront:CreateOriginAccessControl",
        "cloudfront:GetOriginAccessControl",
        "cloudfront:UpdateOriginAccessControl",
        "cloudfront:DeleteOriginAccessControl",
        "cloudfront:ListOriginAccessControls"
      ],
      "Resource": "*"
    },
    {
      "Sid": "APIGatewayPermissions",
      "Effect": "Allow",
      "Action": [
        "apigateway:*"
      ],
      "Resource": "*"
    },
    {
      "Sid": "LambdaPermissions",
      "Effect": "Allow",
      "Action": [
        "lambda:CreateFunction",
        "lambda:DeleteFunction",
        "lambda:GetFunction",
        "lambda:GetFunctionConfiguration",
        "lambda:UpdateFunctionCode",
        "lambda:UpdateFunctionConfiguration",
        "lambda:InvokeFunction",
        "lambda:AddPermission",
        "lambda:RemovePermission",
        "lambda:ListFunctions",
        "lambda:TagResource",
        "lambda:UntagResource"
      ],
      "Resource": "*"
    },
    {
      "Sid": "DynamoDBPermissions",
      "Effect": "Allow",
      "Action": [
        "dynamodb:CreateTable",
        "dynamodb:DeleteTable",
        "dynamodb:DescribeTable",
        "dynamodb:UpdateTable",
        "dynamodb:ListTables",
        "dynamodb:PutItem",
        "dynamodb:GetItem",
        "dynamodb:UpdateItem",
        "dynamodb:DeleteItem",
        "dynamodb:Scan",
        "dynamodb:Query"
      ],
      "Resource": "*"
    },
    {
      "Sid": "EventBridgePermissions",
      "Effect": "Allow",
      "Action": [
        "events:PutRule",
        "events:DeleteRule",
        "events:DescribeRule",
        "events:EnableRule",
        "events:DisableRule",
        "events:PutTargets",
        "events:RemoveTargets",
        "events:ListRules",
        "events:ListTargetsByRule"
      ],
      "Resource": "*"
    },
    {
      "Sid": "StepFunctionsPermissions",
      "Effect": "Allow",
      "Action": [
        "states:CreateStateMachine",
        "states:DeleteStateMachine",
        "states:DescribeStateMachine",
        "states:UpdateStateMachine",
        "states:StartExecution",
        "states:StopExecution",
        "states:DescribeExecution",
        "states:ListExecutions",
        "states:ListStateMachines"
      ],
      "Resource": "*"
    },
    {
      "Sid": "BedrockPermissions",
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream",
        "bedrock:ListFoundationModels",
        "bedrock:GetFoundationModel"
      ],
      "Resource": "*"
    },
    {
      "Sid": "SNSPermissions",
      "Effect": "Allow",
      "Action": [
        "sns:CreateTopic",
        "sns:DeleteTopic",
        "sns:GetTopicAttributes",
        "sns:SetTopicAttributes",
        "sns:ListTopics",
        "sns:Subscribe",
        "sns:Unsubscribe",
        "sns:ListSubscriptionsByTopic",
        "sns:Publish"
      ],
      "Resource": "*"
    },
    {
      "Sid": "CloudWatchLogsPermissions",
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:DeleteLogGroup",
        "logs:DescribeLogGroups",
        "logs:DescribeLogStreams",
        "logs:PutLogEvents",
        "logs:GetLogEvents",
        "logs:FilterLogEvents",
        "logs:PutRetentionPolicy"
      ],
      "Resource": "*"
    },
    {
      "Sid": "IAMPermissions",
      "Effect": "Allow",
      "Action": [
        "iam:CreateRole",
        "iam:DeleteRole",
        "iam:GetRole",
        "iam:ListRoles",
        "iam:PassRole",
        "iam:AttachRolePolicy",
        "iam:DetachRolePolicy",
        "iam:PutRolePolicy",
        "iam:DeleteRolePolicy",
        "iam:GetRolePolicy",
        "iam:CreatePolicy",
        "iam:DeletePolicy",
        "iam:GetPolicy",
        "iam:ListPolicies",
        "iam:ListAttachedRolePolicies"
      ],
      "Resource": "*"
    }
  ]
}
```
This policy is suitable for a workshop. In a production environment, the permissions should be restricted to specific resources and follow the principle of least privilege.

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