---
title : "Build AI Workflow with EventBridge, Step Functions, Bedrock, and PDF Generator"
date : 2026-07-08
weight : 5
chapter : false
pre : " <b> 5.5. </b> "
---

#### AI workflow overview

In this section, the **AI Workflow** of the **AI AWS Architecture Reviewer** project is implemented using **Amazon EventBridge**, **AWS Step Functions**, **AWS Lambda**, **Amazon Bedrock**, **AWS Price List API**, **Amazon S3**, and **Amazon DynamoDB**.

After a user uploads an AWS architecture diagram through the upload backend, the file is stored in the S3 Input Bucket. The S3 object creation event is then sent to EventBridge, which automatically starts the Step Functions workflow.

The AI Workflow analyzes the uploaded architecture image, detects AWS services, estimates monthly cost, generates the final review report, stores the report in S3, and updates the review history in DynamoDB.

The AI Workflow flow is:

```text
S3 Input Bucket → EventBridge → Step Functions
                                      ↓
                              AI Analyzer Lambda
                                      ↓
                              Cost Tool Lambda
                                      ↓
                              PDF Generator Lambda
                                      ↓
                         S3 Report Bucket + DynamoDB
```

The main AWS resources used in this section are:

```text
Amazon S3 Input Bucket
Amazon EventBridge
AWS Step Functions
AWS Lambda AI Analyzer
AWS Lambda Cost Tool
AWS Lambda PDF Generator
Amazon Bedrock
AWS Price List API
Amazon S3 Report Bucket
Amazon DynamoDB
Amazon CloudWatch
AWS IAM
```

The source code and configuration files used in this AI Workflow are stored in the following README folder:

```text
README/ai-workflow/
```

This keeps the workshop page clean while still allowing readers to review the actual JSON definitions, Lambda environment variables, and testing commands.

<details>
<summary><strong>README folder structure</strong></summary>

```text
README/
└── ai-workflow/
    ├── eventbridge/
    │   ├── eventbridge-rule-pattern.json
    │   ├── input-transformer-paths.json
    │   └── input-transformer-template.json
    ├── step-functions/
    │   └── architecture-review-workflow.asl.json
    ├── lambdas/
    │   ├── ai-analyzer/
    │   │   ├── lambda_function.py
    │   │   └── environment.txt
    │   ├── cost-tool/
    │   │   ├── lambda_function.py
    │   │   └── environment.txt
    │   └── pdf-generator/
    │       ├── lambda_function.py
    │       └── environment.txt
    ├── layers/
    │   └── reportlab-layer-structure.txt
    ├── dynamodb/
    │   └── completed-review-example.json
    └── testing/
        └── test-upload-command.md
```

</details>

---

<details>
<summary><strong>Step 1: Enable EventBridge notification on S3 Input Bucket</strong></summary>

The AI Workflow starts when a new architecture diagram is uploaded to the S3 Input Bucket.

The S3 Input Bucket used in this project is:

```text
ai-aws-reviewer-input-bucket-tiersteam
```

Uploaded architecture diagrams are stored using the following object key pattern:

```text
uploads/{reviewId}/{fileName}
```

Example:

```text
uploads/REV-0491BC4A/architecture-diagram.jpg
```

To allow S3 events to be sent to Amazon EventBridge, enable EventBridge notification on the S3 Input Bucket.

Open the S3 Input Bucket, go to **Properties**, and enable:

```text
Amazon EventBridge
```

This allows object creation events in the bucket to be routed to EventBridge.

![S3 EventBridge](/images/5-Workshop/5.5-AI-workflow/s3-input-bucket-eventbridge.png)

</details>

---

<details>
<summary><strong>Step 2: Create EventBridge rule for S3 object creation</strong></summary>

Create an EventBridge rule to capture new uploaded files from the S3 Input Bucket.

The rule listens for the following event type:

```text
Object Created
```

The event pattern used in this project is stored in the README folder instead of being pasted directly into the workshop page.

```text
README/ai-workflow/eventbridge/eventbridge-rule-pattern.json
```

<details>
<summary><strong>View EventBridge event pattern</strong></summary>

```json
{
  "source": ["aws.s3"],
  "detail-type": ["Object Created"],
  "detail": {
    "bucket": {
      "name": ["ai-aws-reviewer-input-bucket-tiersteam"]
    }
  }
}
```

</details>

This rule is triggered whenever a new file is uploaded to the input bucket.

![EventBridge Rule](/images/5-Workshop/5.5-AI-workflow/eventbridge-rule.png)

</details>

---

<details>
<summary><strong>Step 3: Configure EventBridge target</strong></summary>

The target of the EventBridge rule is the Step Functions state machine.

The Step Functions workflow used in this project is:

```text
Architecture-review-workflow
```

EventBridge passes the uploaded file information to Step Functions by using an input transformer.

The input transformer files are stored in the README folder:

```text
README/ai-workflow/eventbridge/input-transformer-paths.json
README/ai-workflow/eventbridge/input-transformer-template.json
```

<details>
<summary><strong>View EventBridge input transformer</strong></summary>

Input paths:

```json
{
  "bucket": "$.detail.bucket.name",
  "key": "$.detail.object.key"
}
```

Input template:

```json
{
  "bucket": "<bucket>",
  "key": "<key>",
  "region": "ap-southeast-1"
}
```

</details>

This input allows the AI Analyzer Lambda to locate and read the uploaded architecture diagram from S3.

![EventBridge Target](/images/5-Workshop/5.5-AI-workflow/eventbridge-target-step-functions.png)

</details>

---

<details>
<summary><strong>Step 4: Create the Step Functions AI workflow</strong></summary>

Create an AWS Step Functions state machine to control the full AI review process.

The workflow name is:

```text
Architecture-review-workflow
```

The workflow contains three main processing stages:

```text
AnalyzeArchitectureWithAI
EstimateCost
GenerateReport
```

The responsibility of each state is:

```text
AnalyzeArchitectureWithAI:
Read the uploaded diagram from S3 and use Amazon Bedrock to analyze the architecture.

EstimateCost:
Use detected AWS services to estimate monthly cost with AWS Price List API.

GenerateReport:
Generate the final review report, save it to S3, and update DynamoDB review history.
```

![Step Functions](/images/5-Workshop/5.5-AI-workflow/architecture-review-workflow.png)

</details>

---

<details>
<summary><strong>Step 5: Configure Step Functions definition</strong></summary>

The Step Functions workflow invokes each Lambda function in order.

The main workflow definition is saved in the README folder:

```text
README/ai-workflow/step-functions/architecture-review-workflow.asl.json
```

This file contains the Amazon States Language definition used by Step Functions. During implementation, copy the content of this file into the Step Functions definition editor.

<details>
<summary><strong>View Step Functions definition</strong></summary>

```json
{
  "Comment": "AI AWS Architecture Reviewer Workflow",
  "StartAt": "AnalyzeArchitectureWithAI",
  "States": {
    "AnalyzeArchitectureWithAI": {
      "Type": "Task",
      "Resource": "arn:aws:states:::lambda:invoke",
      "Parameters": {
        "FunctionName": "arn:aws:lambda:ap-southeast-1:675492141438:function:aws-reviewer-ai-analyzer",
        "Payload.$": "$"
      },
      "ResultSelector": {
        "analysis.$": "$.Payload"
      },
      "ResultPath": "$.analysis_result",
      "Next": "HasDetectedServices"
    },
    "HasDetectedServices": {
      "Type": "Choice",
      "Choices": [
        {
          "Variable": "$.analysis_result.analysis.status",
          "StringEquals": "NO_SERVICES_DETECTED",
          "Next": "SetEmptyCost"
        }
      ],
      "Default": "EstimateCost"
    },
    "SetEmptyCost": {
      "Type": "Pass",
      "Result": {
        "cost": {
          "status": "SKIPPED",
          "message": "No AWS services were detected for cost estimation.",
          "estimated_monthly_cost": 0,
          "currency": "USD",
          "breakdown": []
        }
      },
      "ResultPath": "$.cost_result",
      "Next": "GenerateReport"
    },
    "EstimateCost": {
      "Type": "Task",
      "Resource": "arn:aws:states:::lambda:invoke",
      "Parameters": {
        "FunctionName": "arn:aws:lambda:ap-southeast-1:675492141438:function:aws-reviewer-cost-tool",
        "Payload": {
          "review_id.$": "$.analysis_result.analysis.review_id",
          "region.$": "$.analysis_result.analysis.source.region",
          "services.$": "$.analysis_result.analysis.architecture_json.services"
        }
      },
      "ResultSelector": {
        "cost.$": "$.Payload"
      },
      "ResultPath": "$.cost_result",
      "Next": "GenerateReport"
    },
    "GenerateReport": {
      "Type": "Task",
      "Resource": "arn:aws:states:::lambda:invoke",
      "Parameters": {
        "FunctionName": "arn:aws:lambda:ap-southeast-1:675492141438:function:aws-reviewer-pdf-generator",
        "Payload": {
          "analysis.$": "$.analysis_result.analysis",
          "cost.$": "$.cost_result.cost"
        }
      },
      "ResultSelector": {
        "report.$": "$.Payload"
      },
      "ResultPath": "$.report_result",
      "End": true
    }
  }
}
```

</details>

![Step Functions Definition](/images/5-Workshop/5.5-AI-workflow/step-functions-definition.png)

</details>

---

<details>
<summary><strong>Step 6: Create the AI Analyzer Lambda</strong></summary>

Create a Lambda function to analyze the uploaded architecture diagram.

The Lambda function name is:

```text
aws-reviewer-ai-analyzer
```

This function is responsible for:

```text
Receiving S3 bucket and object key from Step Functions.
Reading the uploaded architecture diagram from S3.
Sending the image to Amazon Bedrock.
Detecting AWS services and connections from the diagram.
Generating an initial AWS Well-Architected assessment.
Returning structured JSON output to Step Functions.
```

The AI Analyzer Lambda uses Amazon Bedrock Nova model to analyze the architecture image.

Example environment variables are stored in:

```text
README/ai-workflow/lambdas/ai-analyzer/environment.txt
```

<details>
<summary><strong>View AI Analyzer environment variables</strong></summary>

```text
MODEL_ID = global.amazon.nova-2-lite-v1:0
BEDROCK_REGION = ap-southeast-1
```

</details>

The Lambda source code can be stored in:

```text
README/ai-workflow/lambdas/ai-analyzer/lambda_function.py
```

The output of this Lambda includes:

```text
Review ID
Source bucket
Source object key
Detected AWS services
Detected service connections
Well-Architected review result
Limitations
```

![AI Analyzer Lambda](/images/5-Workshop/5.5-AI-workflow/aws-reviewer-ai-analyzer.png)

</details>

---

<details>
<summary><strong>Step 7: Create the Cost Tool Lambda</strong></summary>

Create a Lambda function to estimate monthly cost based on the detected AWS services.

The Lambda function name is:

```text
aws-reviewer-cost-tool
```

This function is responsible for:

```text
Receiving detected services from the AI Analyzer Lambda.
Mapping detected services to AWS pricing products.
Calling AWS Price List API to retrieve pricing information.
Calculating estimated monthly cost using default assumptions.
Using Amazon Bedrock to generate cost analysis and optimization suggestions.
Returning cost result to Step Functions.
```

The Cost Tool does not allow AI to invent pricing values. Instead, the numeric cost is calculated from AWS Price List API data, while Amazon Bedrock is only used to explain the cost result and provide optimization recommendations.

Example environment variables are stored in:

```text
README/ai-workflow/lambdas/cost-tool/environment.txt
```

<details>
<summary><strong>View Cost Tool environment variables</strong></summary>

```text
MODEL_ID = global.amazon.nova-2-lite-v1:0
BEDROCK_REGION = ap-southeast-1
DEFAULT_REGION = ap-southeast-1
```

</details>

The Lambda source code can be stored in:

```text
README/ai-workflow/lambdas/cost-tool/lambda_function.py
```

The output of this Lambda includes:

```text
Estimated monthly cost
Currency
Cost breakdown by service
Pricing source
Default usage assumptions
Cost optimization recommendations
```

![Cost Tool Lambda](/images/5-Workshop/5.5-AI-workflow/aws-reviewer-cost-tool.png)

</details>

---

<details>
<summary><strong>Step 8: Create the S3 Report Bucket</strong></summary>

Create an S3 bucket to store generated review reports.

The S3 Report Bucket used in this project is:

```text
ai-aws-reviewer-report-bucket-tiersteam
```

The generated reports are stored using the following key pattern:

```text
reports/{reviewId}/report-data.json
reports/{reviewId}/report.html
reports/{reviewId}/report.pdf
```

Example:

```text
reports/REV-0491BC4A/report-data.json
reports/REV-0491BC4A/report.html
reports/REV-0491BC4A/report.pdf
```

The report bucket stores the final output of the AI Workflow.

![S3 Report Bucket](/images/5-Workshop/5.5-AI-workflow/s3-report-bucket.png)

</details>

---

<details>
<summary><strong>Step 9: Create the PDF Generator Lambda</strong></summary>

Create a Lambda function to generate the final architecture review report.

The Lambda function name is:

```text
aws-reviewer-pdf-generator
```

This function is responsible for:

```text
Receiving analysis result and cost result from Step Functions.
Using Amazon Bedrock to generate the final review content.
Creating report-data.json.
Creating report.html.
Creating report.pdf using ReportLab.
Uploading generated reports to the S3 Report Bucket.
Updating review history in DynamoDB.
Returning report file locations to Step Functions.
```

Example environment variables are stored in:

```text
README/ai-workflow/lambdas/pdf-generator/environment.txt
```

<details>
<summary><strong>View PDF Generator environment variables</strong></summary>

```text
REPORT_BUCKET = ai-aws-reviewer-report-bucket-tiersteam
TABLE_NAME = AIArchitectureReviews
MODEL_ID = global.amazon.nova-2-lite-v1:0
BEDROCK_REGION = ap-southeast-1
```

</details>

The Lambda source code can be stored in:

```text
README/ai-workflow/lambdas/pdf-generator/lambda_function.py
```

The PDF Generator Lambda is the final state of the AI Workflow.

![PDF Generator Lambda](/images/5-Workshop/5.5-AI-workflow/aws-reviewer-pdf-generator.png)

</details>

---

<details>
<summary><strong>Step 10: Configure ReportLab layer for PDF generation</strong></summary>

To generate PDF reports inside Lambda, a Lambda Layer is used to provide the ReportLab library.

The layer includes:

```text
ReportLab library
Required Python dependencies
Vietnamese-supported fonts
```

The layer structure is stored in:

```text
README/ai-workflow/layers/reportlab-layer-structure.txt
```

<details>
<summary><strong>View ReportLab layer structure</strong></summary>

```text
python/
  reportlab/
  ...
fonts/
  DejaVuSans.ttf
  DejaVuSans-Bold.ttf
```

</details>

The fonts are used to display Vietnamese text correctly in PDF reports.

After creating the layer, attach it to the PDF Generator Lambda.

![ReportLab Layer](/images/5-Workshop/5.5-AI-workflow/reportlab-layer.png)

</details>

---

<details>
<summary><strong>Step 11: Update DynamoDB review history</strong></summary>

After the report is generated successfully, the PDF Generator Lambda updates the review item in DynamoDB.

The DynamoDB table used in this project is:

```text
AIArchitectureReviews
```

The partition key is:

```text
reviewId
```

When the upload backend creates a new review item, the initial status is:

```text
uploaded
```

After the AI Workflow finishes, the PDF Generator Lambda updates the status to:

```text
completed
```

The updated review item includes:

```text
Review status
Completed date
Updated date
Architecture score
Detected AWS services
Well-Architected result
Cost result
Recommendations
Risks
Best practices
Report file locations
```

The example updated item is stored in:

```text
README/ai-workflow/dynamodb/completed-review-example.json
```

<details>
<summary><strong>View completed DynamoDB item example</strong></summary>

```json
{
  "reviewId": "REV-0491BC4A",
  "status": "completed",
  "score": 82,
  "architectureType": "Serverless Architecture",
  "completedDate": "2026-07-08T03:49:31.000000",
  "detectedServices": [],
  "recommendations": [],
  "risks": [],
  "bestPractices": [],
  "costResult": {},
  "reportFiles": {
    "htmlReportS3Key": "reports/REV-0491BC4A/report.html",
    "pdfReportS3Key": "reports/REV-0491BC4A/report.pdf"
  }
}
```

</details>

This update allows the React frontend to display review history and completed analysis results.

![DynamoDB Updated Review](/images/5-Workshop/5.5-AI-workflow/dynamodb-review-completed.png)

</details>

---

<details>
<summary><strong>Step 12: Configure IAM permissions</strong></summary>

Each Lambda function and Step Functions workflow requires an IAM role with the correct permissions.

The AI Analyzer Lambda requires permission to:

```text
Read objects from S3 Input Bucket
Invoke Amazon Bedrock model
Write logs to CloudWatch
```

The Cost Tool Lambda requires permission to:

```text
Call AWS Price List API
Invoke Amazon Bedrock model
Write logs to CloudWatch
```

The PDF Generator Lambda requires permission to:

```text
Write reports to S3 Report Bucket
Update DynamoDB review history
Invoke Amazon Bedrock model
Write logs to CloudWatch
```

The Step Functions role requires permission to:

```text
Invoke AI Analyzer Lambda
Invoke Cost Tool Lambda
Invoke PDF Generator Lambda
Write execution logs to CloudWatch
```

![IAM Roles](/images/5-Workshop/5.5-AI-workflow/ai-workflow-iam-roles.png)

</details>

---

<details>
<summary><strong>Step 13: Test the AI Workflow</strong></summary>

To test the full AI Workflow, upload an architecture diagram from the frontend or use the upload API.

The test upload command is stored in:

```text
README/ai-workflow/testing/test-upload-command.md
```

<details>
<summary><strong>View test upload command</strong></summary>

```powershell
curl.exe -X POST "https://031hqksomd.execute-api.ap-southeast-1.amazonaws.com/upload" -F "file=@D:\Learning\AWS\test-files\architecture-1.png"
```

</details>

If the upload is successful, the API returns a review ID:

```json
{
  "reviewId": "REV-0491BC4A",
  "status": "uploaded",
  "fileName": "architecture-1.png",
  "fileType": "image/png",
  "fileSize": 17755,
  "message": "Upload successful"
}
```

After the file is uploaded to S3, EventBridge automatically starts the Step Functions workflow.

Open Step Functions and verify that all states are completed successfully:

```text
AnalyzeArchitectureWithAI
EstimateCost
GenerateReport
```

![Step Functions Success](/images/5-Workshop/5.5-AI-workflow/step-functions-execution-success.png)

</details>

---

<details>
<summary><strong>Step 14: Verify generated reports in S3</strong></summary>

After the Step Functions execution is completed, open the S3 Report Bucket.

The generated files should be stored under:

```text
reports/{reviewId}/
```

Example:

```text
reports/REV-0491BC4A/report-data.json
reports/REV-0491BC4A/report.html
reports/REV-0491BC4A/report.pdf
```

The `report-data.json` file stores structured review data.

The `report.html` file stores a browser-readable report.

The `report.pdf` file stores the final PDF report.

![Generated Reports](/images/5-Workshop/5.5-AI-workflow/s3-generated-reports.png)

</details>

---

<details>
<summary><strong>Step 15: Verify completed review in DynamoDB</strong></summary>

Open the DynamoDB table and verify that the review item has been updated.

The review status should change from:

```text
uploaded
```

to:

```text
completed
```

The item should also include report file information, cost result, detected services, recommendations, risks, and best practices.

![DynamoDB Completed Review](/images/5-Workshop/5.5-AI-workflow/dynamodb-completed-review.png)

</details>

---

<details>
<summary><strong>Step 16: Verify review history on frontend</strong></summary>

The React frontend reads review history from the backend API.

The review history API routes are:

```text
GET /reviews
GET /reviews/{reviewId}
GET /reviews/{reviewId}/status
```

After the AI Workflow completes, the frontend can display:

```text
Review ID
File name
Upload date
Review status
Architecture score
Detected services
Recommendations
Risks
Report links
```

This completes the full upload and AI review process.

```text
Upload Backend → S3 Input Bucket → EventBridge → Step Functions
→ AI Analyzer → Cost Tool → PDF Generator
→ S3 Report Bucket → DynamoDB → Frontend Review History
```

![Frontend Review History](/images/5-Workshop/5.5-AI-workflow/frontend-review-history.png)

</details>

---

#### AI Workflow result

After completing this section, the system can automatically process an uploaded AWS architecture diagram and generate a complete architecture review.

The final result includes:

```text
AI-based architecture analysis
Detected AWS services
AWS Well-Architected assessment
Estimated monthly cost
Cost optimization suggestions
HTML report
PDF report
Updated review history
```

The AI Workflow makes the system fully automated after upload. Users only need to upload an architecture diagram, and the backend automatically performs analysis, cost estimation, report generation, and history update.
