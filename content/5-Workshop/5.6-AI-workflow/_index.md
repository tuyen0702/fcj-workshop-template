---
title : "Build AI Workflow with EventBridge, Step Functions, Bedrock, and PDF Generator"
date : 2026-07-08
weight : 6
chapter : false
pre : " <b> 5.6. </b> "
---

#### AI Workflow overview

In this section, the **AI Workflow** of the **AI AWS Architecture Reviewer** project is built using **Amazon EventBridge**, **AWS Step Functions**, **AWS Lambda**, **Amazon Bedrock**, **AWS Price List API**, **Amazon S3**, **Amazon DynamoDB**, **Amazon CloudWatch**, and **AWS IAM**.

After the user uploads an AWS architecture diagram through the upload backend, the file is stored in the **S3 Input Bucket**. The S3 object creation event is sent to **Amazon EventBridge**. EventBridge then automatically triggers **AWS Step Functions** to start the architecture analysis process.

The AI Workflow is responsible for analyzing the uploaded architecture image, detecting AWS services, estimating monthly cost, generating the final review report, storing the report in S3, and updating the review history in DynamoDB.

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
Lambda Layer
```

In this section, short configurations such as **environment variables**, **EventBridge pattern**, **Step Functions definition**, **IAM permissions**, and **test commands** are written directly in the workshop page. The long source code of the Lambda functions is stored separately in the README folder to keep the workshop page clean.

<details>
<summary><strong>README folder structure for Lambda source code</strong></summary>

```text
README/
└── ai-workflow/
    └── lambdas/
        ├── ai-analyzer/
        │   └── lambda_function.py
        ├── cost-tool/
        │   └── lambda_function.py
        └── pdf-generator/
            └── lambda_function.py
```

</details>

---

<details>
<summary><strong>Step 1: Enable EventBridge notification for the S3 Input Bucket</strong></summary>

The AI Workflow starts when a new architecture diagram is uploaded to the S3 Input Bucket. The upload backend stores the file in the input bucket using an object key that includes the `reviewId`, so the later steps can use this `reviewId` to track the entire analysis process.

The S3 Input Bucket used in this project is:

```text
ai-aws-reviewer-input-bucket-tiersteam
```

Uploaded architecture files are stored using the following key structure:

```text
uploads/{reviewId}/{fileName}
```

Example:

```text
uploads/REV-0491BC4A/architecture-diagram.jpg
```

Configure this in the AWS Console:

```text
1. Select the ap-southeast-1 region.
2. Go to Amazon S3.
3. Open the bucket ai-aws-reviewer-input-bucket-tiersteam.
4. Select the Properties tab.
5. Find the Amazon EventBridge section.
6. Choose Edit.
7. Enable Send notifications to Amazon EventBridge for all events in this bucket.
8. Choose Save changes.
```

After enabling this option, new object creation events in the bucket can be routed to EventBridge.

![S3 EventBridge](/images/5-Workshop/5.6-AI-workflow/s3-input-bucket-eventbridge.png)

</details>

---

<details>
<summary><strong>Step 2: Create an EventBridge rule for the S3 Object Created event</strong></summary>

The EventBridge rule is used to capture the event when a new file is uploaded to the S3 Input Bucket. When a new object is created, the rule triggers Step Functions to start the AI Workflow.

Configure this in the AWS Console:

```text
1. Go to Amazon EventBridge.
2. Select Rules.
3. Choose Create rule.
4. Enter the rule name.
5. Select default as the event bus.
6. Select Rule with an event pattern as the rule type.
7. Choose Next.
```

The rule name used in this project is:

```text
ai-aws-reviewer-s3-object-created-rule
```

In the Event source section, select:

```text
AWS events or EventBridge partner events
```

In the Creation method section, select:

```text
Custom pattern JSON editor
```

Paste the following event pattern:

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

Meaning of the pattern:

```text
source = aws.s3:
Only receive events from Amazon S3.

detail-type = Object Created:
Only receive events when a new object is created.

bucket.name:
Only receive events from the project input bucket.
```

After completing the configuration, choose:

```text
Next
```

![EventBridge Rule](/images/5-Workshop/5.6-AI-workflow/eventbridge-rule.png)

</details>

---

<details>
<summary><strong>Step 3: Configure the EventBridge target as Step Functions</strong></summary>

The target of the EventBridge rule is the Step Functions state machine. When a new file is uploaded to S3, EventBridge calls `StartExecution` to run the state machine.

The Step Functions workflow used in this project is:

```text
Architecture-review-workflow
```

Configure the target:

```text
1. In the Select target step of the EventBridge rule, set Target type to AWS service.
2. In Select a target, choose Step Functions state machine.
3. Select the state machine Architecture-review-workflow.
4. In Execution role, create a new role or select an existing role with states:StartExecution permission.
5. Open Additional settings.
6. Select Configure target input.
7. Select Input transformer.
```

The input transformer extracts the bucket name and object key from the S3 event, then passes a cleaner JSON input to Step Functions.

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

Example input received by Step Functions:

```json
{
  "bucket": "ai-aws-reviewer-input-bucket-tiersteam",
  "key": "uploads/REV-0491BC4A/architecture-diagram.jpg",
  "region": "ap-southeast-1"
}
```

This input allows the AI Analyzer Lambda to identify the correct bucket and object key to read the uploaded architecture diagram from S3.

![EventBridge Target](/images/5-Workshop/5.6-AI-workflow/eventbridge-target-step-functions.png)

</details>

---

<details>
<summary><strong>Step 4: Create the Step Functions AI Workflow</strong></summary>

Step Functions is used to orchestrate the entire architecture analysis process. Instead of manually invoking each Lambda function, Step Functions allows the workflow to run in the correct order and makes it easier to monitor the status of each step.

The workflow name is:

```text
Architecture-review-workflow
```

Create the state machine:

```text
1. Go to AWS Step Functions.
2. Select State machines.
3. Choose Create state machine.
4. Select Write your workflow in code.
5. Set Type to Standard.
6. Set Definition language to JSON.
7. Name the state machine Architecture-review-workflow.
8. Select or create an IAM role for Step Functions.
9. Enable logging if you want to monitor executions in CloudWatch.
10. Choose Create state machine.
```

The workflow contains three main processing stages:

```text
AnalyzeArchitectureWithAI
EstimateCost
GenerateReport
```

The role of each state:

```text
AnalyzeArchitectureWithAI:
Read the architecture diagram from S3 and use Amazon Bedrock to analyze the architecture.

EstimateCost:
Use the detected AWS services to estimate cost with AWS Price List API.

GenerateReport:
Generate the final review report, store the report in S3, and update the review history in DynamoDB.
```

The workflow also includes a Choice state named `HasDetectedServices`. If the AI Analyzer does not detect any AWS service, the workflow skips the cost estimation step and moves directly to report generation with cost set to 0.

![Step Functions](/images/5-Workshop/5.6-AI-workflow/architecture-review-workflow.png)

</details>

---

<details>
<summary><strong>Step 5: Configure the Step Functions definition</strong></summary>

After creating the state machine, paste the Amazon States Language definition into the Step Functions code editor.

Configure this in the AWS Console:

```text
1. Open the state machine Architecture-review-workflow.
2. Choose Edit.
3. Select Definition.
4. Remove the sample definition if it exists.
5. Paste the JSON definition below.
6. Check the ARNs of the three Lambda functions.
7. Choose Save.
```

The workflow definition used in this project is:

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

After saving, check the graph view. A correct graph should include the following states:

```text
AnalyzeArchitectureWithAI
HasDetectedServices
SetEmptyCost
EstimateCost
GenerateReport
```

![Step Functions Definition](/images/5-Workshop/5.6-AI-workflow/step-functions-definition.png)

</details>

---

<details>
<summary><strong>Step 6: Create the AI Analyzer Lambda</strong></summary>

The AI Analyzer Lambda is the first step in Step Functions. This Lambda receives the bucket and object key from EventBridge, reads the architecture image in S3, and sends the image to Amazon Bedrock for analysis.

The Lambda function name is:

```text
aws-reviewer-ai-analyzer
```

Create the Lambda function:

```text
1. Go to AWS Lambda.
2. Choose Create function.
3. Select Author from scratch.
4. Enter aws-reviewer-ai-analyzer as the function name.
5. Select Python 3.14 or the runtime used in the project.
6. Select x86_64 as the architecture.
7. Select an execution role with S3 GetObject, Bedrock InvokeModel, and CloudWatch Logs permissions.
8. Choose Create function.
```

After creating the function, configure general settings:

```text
Memory: 1024 MB
Timeout: 120 seconds
```

Configure environment variables:

```text
MODEL_ID = global.amazon.nova-2-lite-v1:0
BEDROCK_REGION = ap-southeast-1
```

The long Lambda source code is stored in:

```text
README/ai-workflow/lambdas/ai-analyzer/lambda_function.py
```

After copying the code into Lambda, choose:

```text
Deploy
```

This function is responsible for:

```text
Receiving the S3 bucket and object key from Step Functions.
Reading the uploaded architecture diagram from S3.
Sending the architecture image to Amazon Bedrock.
Detecting AWS services and connections in the diagram.
Creating an initial AWS Well-Architected Framework assessment.
Returning structured JSON data to Step Functions.
```

The main output of this Lambda includes:

```text
Review ID
Source bucket
Source object key
Detected AWS services
Service connections
Well-Architected assessment result
Analysis limitations
```

You can test the Lambda with this sample event:

```json
{
  "bucket": "ai-aws-reviewer-input-bucket-tiersteam",
  "key": "uploads/REV-0491BC4A/architecture-diagram.jpg",
  "region": "ap-southeast-1"
}
```

![AI Analyzer Lambda](/images/5-Workshop/5.6-AI-workflow/aws-reviewer-ai-analyzer.png)

</details>

---

<details>
<summary><strong>Step 7: Create the Cost Tool Lambda</strong></summary>

The Cost Tool Lambda is the second step in the workflow. This Lambda receives the list of AWS services detected by the AI Analyzer and calculates the estimated monthly cost.

The Lambda function name is:

```text
aws-reviewer-cost-tool
```

Create the Lambda function:

```text
1. Go to AWS Lambda.
2. Choose Create function.
3. Select Author from scratch.
4. Enter aws-reviewer-cost-tool as the function name.
5. Select Python 3.14 or the runtime used in the project.
6. Select x86_64 as the architecture.
7. Select an execution role with Pricing API, Bedrock InvokeModel, and CloudWatch Logs permissions.
8. Choose Create function.
```

Configure general settings:

```text
Memory: 1024 MB
Timeout: 120 seconds
```

Configure environment variables:

```text
MODEL_ID = global.amazon.nova-2-lite-v1:0
BEDROCK_REGION = ap-southeast-1
DEFAULT_REGION = ap-southeast-1
```

The long Lambda source code is stored in:

```text
README/ai-workflow/lambdas/cost-tool/lambda_function.py
```

After copying the code into Lambda, choose:

```text
Deploy
```

This function is responsible for:

```text
Receiving the detected services from the AI Analyzer Lambda.
Mapping detected services to corresponding AWS Pricing products.
Calling AWS Price List API to retrieve pricing information.
Calculating estimated monthly cost based on default assumptions.
Using Amazon Bedrock to generate cost analysis and optimization recommendations.
Returning the cost result to Step Functions.
```

The Cost Tool does not allow AI to invent pricing values. The numeric cost is calculated from AWS Price List API data, while Amazon Bedrock is only used to explain the cost result and provide optimization recommendations.

You can test the Lambda with this sample event:

```json
{
  "review_id": "REV-0491BC4A",
  "region": "ap-southeast-1",
  "services": [
    {
      "name": "Amazon EC2",
      "category": "Compute",
      "confidence": 0.95,
      "evidence": "Detected from architecture diagram"
    },
    {
      "name": "Amazon S3",
      "category": "Storage",
      "confidence": 0.93,
      "evidence": "Detected from architecture diagram"
    }
  ]
}
```

The main output of this Lambda includes:

```text
Estimated monthly cost
Currency
Cost breakdown by service
Pricing data source
Default usage assumptions
Cost optimization recommendations
```

![Cost Tool Lambda](/images/5-Workshop/5.6-AI-workflow/aws-reviewer-cost-tool.png)

</details>

---

<details>
<summary><strong>Step 8: Create the S3 Report Bucket</strong></summary>

The S3 Report Bucket is used to store the report files after the AI Workflow is completed. The PDF Generator Lambda uploads `report-data.json`, `report.html`, and `report.pdf` to this bucket.

The S3 Report Bucket used in this project is:

```text
ai-aws-reviewer-report-bucket-tiersteam
```

Create the bucket:

```text
1. Go to Amazon S3.
2. Choose Create bucket.
3. Select ap-southeast-1 as the region.
4. Enter ai-aws-reviewer-report-bucket-tiersteam as the bucket name.
5. Keep Object Ownership as ACLs disabled.
6. Keep Block Public Access enabled if reports are accessed only through the backend or presigned URLs.
7. Enable Bucket Versioning if you want to keep multiple report versions.
8. Set Encryption to Server-side encryption with Amazon S3 managed keys (SSE-S3).
9. Choose Create bucket.
```

Reports are stored using this key structure:

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

Meaning of each file:

```text
report-data.json:
Stores structured review data in JSON format.

report.html:
Stores the HTML report, which is easy to open in a browser.

report.pdf:
Stores the final PDF report for download or submission.
```

![S3 Report Bucket](/images/5-Workshop/5.6-AI-workflow/s3-report-bucket.png)

</details>

---

<details>
<summary><strong>Step 9: Create the PDF Generator Lambda</strong></summary>

The PDF Generator Lambda is the final step in the AI Workflow. This Lambda receives the architecture analysis result and cost result from Step Functions, then generates the final report and updates the review history in DynamoDB.

The Lambda function name is:

```text
aws-reviewer-pdf-generator
```

Create the Lambda function:

```text
1. Go to AWS Lambda.
2. Choose Create function.
3. Select Author from scratch.
4. Enter aws-reviewer-pdf-generator as the function name.
5. Select Python 3.14 as the runtime.
6. Select x86_64 as the architecture.
7. Select an execution role with S3 PutObject, DynamoDB UpdateItem, Bedrock InvokeModel, and CloudWatch Logs permissions.
8. Choose Create function.
```

Configure general settings:

```text
Memory: 1024 MB
Timeout: 180 seconds
```

Configure environment variables:

```text
REPORT_BUCKET = ai-aws-reviewer-report-bucket-tiersteam
TABLE_NAME = AIArchitectureReviews
MODEL_ID = global.amazon.nova-2-lite-v1:0
BEDROCK_REGION = ap-southeast-1
```

The long Lambda source code is stored in:

```text
README/ai-workflow/lambdas/pdf-generator/lambda_function.py
```

After copying the code into Lambda, choose:

```text
Deploy
```

This function is responsible for:

```text
Receiving the architecture analysis result and cost result from Step Functions.
Using Amazon Bedrock to generate the final review content.
Creating report-data.json.
Creating report.html.
Creating report.pdf with ReportLab.
Uploading the report files to the S3 Report Bucket.
Updating the review history in DynamoDB.
Returning the report file locations to Step Functions.
```

You can test the Lambda with this sample event:

```json
{
  "analysis": {
    "status": "ANALYZED",
    "review_id": "REV-TEST-PDF",
    "source": {
      "region": "ap-southeast-1"
    },
    "architecture_json": {
      "services": [
        {
          "name": "Amazon S3",
          "category": "Storage",
          "confidence": 0.95,
          "evidence": "Detected from architecture diagram"
        }
      ],
      "connections": []
    },
    "well_architected_review": {
      "overall_score": 80,
      "pillar_scores": {},
      "findings": []
    }
  },
  "cost": {
    "status": "COST_ESTIMATED",
    "review_id": "REV-TEST-PDF",
    "currency": "USD",
    "estimated_monthly_cost": 1.25,
    "breakdown": [],
    "cost_ai_review": {
      "summary": "Estimated demo cost is low.",
      "cost_level": "Low",
      "main_cost_drivers": [],
      "optimization_recommendations": []
    }
  }
}
```

The PDF Generator Lambda is the final state of the AI Workflow.

![PDF Generator Lambda](/images/5-Workshop/5.6-AI-workflow/aws-reviewer-pdf-generator.png)

</details>

---

<details>
<summary><strong>Step 10: Configure the ReportLab Layer for PDF generation</strong></summary>

To generate PDF files inside Lambda, the system uses a **Lambda Layer** to provide **ReportLab**, **Pillow**, and Vietnamese-supported fonts. This layer is attached to the `aws-reviewer-pdf-generator` Lambda so the function can import ReportLab and generate the `report.pdf` file.

In this project, the PDF Generator Lambda uses:

```text
Region: ap-southeast-1
Runtime: Python 3.14
Architecture: x86_64
Layer name: reportlab-layer-py314-vn
```

##### 10.1. Open CloudShell in the correct region

In the AWS Console, select the region:

```text
ap-southeast-1
```

Then open:

```text
CloudShell
```

CloudShell is used to install ReportLab, Pillow, and package them into a `.zip` file using the correct Lambda Layer structure.

##### 10.2. Create the layer folder and install ReportLab

Run the following commands in CloudShell:

```bash
mkdir -p reportlab-layer-py314/python

python3 -m pip install --upgrade pip

python3 -m pip install \
  --platform manylinux2014_x86_64 \
  --implementation cp \
  --python-version 3.14 \
  --abi cp314 \
  --only-binary=:all: \
  --target reportlab-layer-py314/python \
  reportlab pillow
```

Meaning of the main options:

```text
--platform manylinux2014_x86_64 : builds packages for the Lambda Linux x86_64 environment
--python-version 3.14          : builds for the Python 3.14 runtime
--abi cp314                    : uses the ABI that matches Python 3.14
--target                       : installs the libraries into the python/ folder of the Lambda Layer
```

After the installation is completed, move into the layer folder:

```bash
cd reportlab-layer-py314
```

##### 10.3. Create the fonts folder and add Vietnamese fonts

ReportLab does not display Vietnamese text correctly when using only the default fonts. Therefore, the layer needs a Unicode font such as **DejaVuSans**.

Create the `fonts` folder:

```bash
mkdir -p fonts
```

Copy DejaVuSans fonts into the `fonts` folder:

```bash
cp /usr/share/fonts/dejavu-sans-fonts/DejaVuSans.ttf fonts/
cp /usr/share/fonts/dejavu-sans-fonts/DejaVuSans-Bold.ttf fonts/
```

After copying the fonts, check the folder:

```bash
ls -l fonts
```

Expected result:

```text
DejaVuSans.ttf
DejaVuSans-Bold.ttf
```

If CloudShell cannot find the font path above, search for the fonts again:

```bash
find /usr/share/fonts -iname "DejaVuSans*.ttf"
```

Then use the correct path returned by the `find` command to copy the fonts into the `fonts` folder.

##### 10.4. Package the Lambda Layer

After the `python` and `fonts` folders are ready, create the zip file:

```bash
zip -r reportlab-layer-py314-vn.zip python fonts
```

The zip file structure should look like this:

```text
python/
  reportlab/
  PIL/
  ...
fonts/
  DejaVuSans.ttf
  DejaVuSans-Bold.ttf
```

When Lambda attaches this layer, the font files will be available at:

```text
/opt/fonts/DejaVuSans.ttf
/opt/fonts/DejaVuSans-Bold.ttf
```

The PDF Generator Lambda uses these paths to register Vietnamese fonts in ReportLab.

##### 10.5. Download the layer file from CloudShell

In CloudShell, choose:

```text
Actions → Download file
```

Enter the file path:

```text
reportlab-layer-py314/reportlab-layer-py314-vn.zip
```

Then choose:

```text
Download
```

The file to download is:

```text
reportlab-layer-py314-vn.zip
```

##### 10.6. Create a new Lambda Layer

Go to the AWS Console:

```text
Lambda → Layers → Create layer
```

Enter the layer information:

```text
Name: reportlab-layer-py314-vn
Upload: reportlab-layer-py314-vn.zip
Compatible runtime: Python 3.14
Compatible architecture: x86_64
```

Then choose:

```text
Create
```

![ReportLab Layer](/images/5-Workshop/5.6-AI-workflow/reportlab-layer.png)

##### 10.7. Attach the layer to the PDF Generator Lambda

Open the PDF Generator Lambda:

```text
Lambda → aws-reviewer-pdf-generator → Code → Layers
```

Choose:

```text
Add a layer
```

Then select:

```text
Custom layers → reportlab-layer-py314-vn → Latest version → Add
```

After attaching the layer, save the Lambda configuration.

##### 10.8. Configure the code to use Vietnamese fonts

In the `aws-reviewer-pdf-generator` Lambda, ReportLab must register the font before building the PDF.

The font paths in Lambda are:

```text
/opt/fonts/DejaVuSans.ttf
/opt/fonts/DejaVuSans-Bold.ttf
```

Example code to register the fonts:

```python
def register_vietnamese_fonts():
    regular_font_path = "/opt/fonts/DejaVuSans.ttf"
    bold_font_path = "/opt/fonts/DejaVuSans-Bold.ttf"

    pdfmetrics.registerFont(TTFont("DejaVuSans", regular_font_path))
    pdfmetrics.registerFont(TTFont("DejaVuSans-Bold", bold_font_path))

    return {
        "regular": "DejaVuSans",
        "bold": "DejaVuSans-Bold"
    }
```

ReportLab styles should use this font instead of the default font:

```python
styles.add(ParagraphStyle(
    name="VNBody",
    parent=styles["BodyText"],
    fontName="DejaVuSans",
    fontSize=10,
    leading=14
))
```

##### 10.9. Verify the PDF after attaching the layer

After attaching the layer and deploying the code, test the `aws-reviewer-pdf-generator` Lambda again.

Expected output:

```json
{
  "reportlab_available": true,
  "pdf_status": "PDF_GENERATED",
  "pdf_report_s3_uri": "s3://ai-aws-reviewer-report-bucket-tiersteam/reports/REV-TEST-PDF/report.pdf"
}
```

Then open the S3 Report Bucket and check the PDF file:

```text
reports/{reviewId}/report.pdf
```

If the PDF displays Vietnamese characters such as `đ`, `ư`, `ế`, `ệ`, and `ộ` correctly, the Vietnamese font configuration is successful.

</details>

---

<details>
<summary><strong>Step 11: Update review history in DynamoDB</strong></summary>

After the report is generated successfully, the PDF Generator Lambda updates the review item in DynamoDB. This update allows the frontend to display the review result instead of only showing the `uploaded` status.

The DynamoDB table used in this project is:

```text
AIArchitectureReviews
```

The partition key is:

```text
reviewId
```

DynamoDB update process:

```text
1. Upload Lambda creates a new item with status = uploaded.
2. EventBridge triggers Step Functions.
3. Step Functions runs AI Analyzer, Cost Tool, and PDF Generator.
4. PDF Generator generates the report successfully.
5. PDF Generator calls DynamoDB UpdateItem.
6. The item is updated with status = completed.
```

When the upload backend creates a new review item, the initial status is:

```text
uploaded
```

After the AI Workflow is completed, the PDF Generator Lambda updates the status to:

```text
completed
```

Fields updated after completion:

```text
status
completedDate
updatedAt
score
architectureType
detectedServices
wellArchitectedResult
costResult
recommendations
risks
bestPractices
reportFiles
htmlReportS3Key
pdfReportS3Key
finalReview
analysisStatus
```

Example DynamoDB item after completion:

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
    "jsonReportS3Key": "reports/REV-0491BC4A/report-data.json",
    "htmlReportS3Key": "reports/REV-0491BC4A/report.html",
    "pdfReportS3Key": "reports/REV-0491BC4A/report.pdf",
    "pdfStatus": "PDF_GENERATED"
  }
}
```

Check this in DynamoDB:

```text
1. Go to Amazon DynamoDB.
2. Select Tables.
3. Open the AIArchitectureReviews table.
4. Select Explore table items.
5. Search for the corresponding reviewId, for example REV-0491BC4A.
6. Check that the status has changed to completed.
7. Check the reportFiles, score, costResult, and recommendations fields.
```

This update allows the React frontend to display review history and completed analysis results.

![DynamoDB Updated Review](/images/5-Workshop/5.6-AI-workflow/dynamodb-review-completed.png)

</details>

---

<details>
<summary><strong>Step 12: Configure IAM permissions</strong></summary>

Each Lambda function, Step Functions workflow, and EventBridge target needs an IAM role with the correct permissions. IAM is important because if a permission is missing, the workflow may run until a certain step and then fail with `AccessDenied`.

How to add an inline policy to each role:

```text
1. Go to IAM.
2. Select Roles.
3. Open the role that needs to be configured.
4. Choose Add permissions.
5. Choose Create inline policy.
6. Select the JSON tab.
7. Paste the corresponding policy.
8. Choose Next.
9. Enter a policy name.
10. Choose Create policy.
```

##### 12.1. IAM policy for AI Analyzer Lambda

The AI Analyzer Lambda needs permission to read files from the S3 Input Bucket, invoke Amazon Bedrock, and write logs to CloudWatch.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ReadInputBucket",
      "Effect": "Allow",
      "Action": [
        "s3:GetObject"
      ],
      "Resource": "arn:aws:s3:::ai-aws-reviewer-input-bucket-tiersteam/*"
    },
    {
      "Sid": "InvokeBedrockModel",
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel"
      ],
      "Resource": "*"
    },
    {
      "Sid": "WriteCloudWatchLogs",
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "*"
    }
  ]
}
```

##### 12.2. IAM policy for Cost Tool Lambda

The Cost Tool Lambda needs permission to call AWS Price List API, invoke Amazon Bedrock, and write logs to CloudWatch.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowPricingApi",
      "Effect": "Allow",
      "Action": [
        "pricing:GetProducts",
        "pricing:DescribeServices",
        "pricing:GetAttributeValues"
      ],
      "Resource": "*"
    },
    {
      "Sid": "InvokeBedrockModel",
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel"
      ],
      "Resource": "*"
    },
    {
      "Sid": "WriteCloudWatchLogs",
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "*"
    }
  ]
}
```

##### 12.3. IAM policy for PDF Generator Lambda

The PDF Generator Lambda needs permission to write reports to the S3 Report Bucket, update DynamoDB, invoke Amazon Bedrock, and write logs to CloudWatch.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "WriteReportBucket",
      "Effect": "Allow",
      "Action": [
        "s3:PutObject"
      ],
      "Resource": "arn:aws:s3:::ai-aws-reviewer-report-bucket-tiersteam/*"
    },
    {
      "Sid": "UpdateReviewHistory",
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:UpdateItem"
      ],
      "Resource": "arn:aws:dynamodb:ap-southeast-1:675492141438:table/AIArchitectureReviews"
    },
    {
      "Sid": "InvokeBedrockModel",
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel"
      ],
      "Resource": "*"
    },
    {
      "Sid": "WriteCloudWatchLogs",
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "*"
    }
  ]
}
```

##### 12.4. IAM policy for Step Functions role

The Step Functions role needs permission to invoke the three Lambda functions in the AI Workflow.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "InvokeWorkflowLambdas",
      "Effect": "Allow",
      "Action": [
        "lambda:InvokeFunction"
      ],
      "Resource": [
        "arn:aws:lambda:ap-southeast-1:675492141438:function:aws-reviewer-ai-analyzer",
        "arn:aws:lambda:ap-southeast-1:675492141438:function:aws-reviewer-cost-tool",
        "arn:aws:lambda:ap-southeast-1:675492141438:function:aws-reviewer-pdf-generator"
      ]
    },
    {
      "Sid": "WriteStepFunctionsLogs",
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogDelivery",
        "logs:GetLogDelivery",
        "logs:UpdateLogDelivery",
        "logs:DeleteLogDelivery",
        "logs:ListLogDeliveries",
        "logs:PutResourcePolicy",
        "logs:DescribeResourcePolicies",
        "logs:DescribeLogGroups"
      ],
      "Resource": "*"
    }
  ]
}
```

##### 12.5. IAM policy for EventBridge target role

EventBridge needs permission to start execution of the Step Functions state machine.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "StartAIWorkflowExecution",
      "Effect": "Allow",
      "Action": [
        "states:StartExecution"
      ],
      "Resource": "arn:aws:states:ap-southeast-1:675492141438:stateMachine:Architecture-review-workflow"
    }
  ]
}
```

![IAM Roles](/images/5-Workshop/5.6-AI-workflow/ai-workflow-iam-roles.png)

</details>

---

<details>
<summary><strong>Step 13: Test the AI Workflow</strong></summary>

To test the full AI Workflow, upload an architecture diagram from the frontend or use the upload API. When the upload succeeds, S3 generates an Object Created event, EventBridge captures the event, and Step Functions starts automatically.

Prepare an architecture image file on your local machine:

```text
D:\Learning\AWS\test-files\architecture-1.png
```

Test upload with PowerShell:

```powershell
curl.exe -X POST "https://031hqksomd.execute-api.ap-southeast-1.amazonaws.com/upload" -F "file=@D:\Learning\AWS\test-files\architecture-1.png"
```

If the upload succeeds, the API returns a review ID:

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

After receiving the review ID, check the workflow in this order:

```text
1. Go to the S3 Input Bucket.
2. Check that the file exists under uploads/{reviewId}/.
3. Go to the EventBridge rule and check the Matched events metric.
4. Go to Step Functions.
5. Open the state machine Architecture-review-workflow.
6. Select the latest execution.
7. Check the Graph view.
```

The following states should complete successfully:

```text
AnalyzeArchitectureWithAI
EstimateCost
GenerateReport
```

If a state fails, open the `Input` and `Output` tabs of that state to inspect the input data and returned error.

![Step Functions Success](/images/5-Workshop/5.6-AI-workflow/step-functions-execution-success.png)

</details>

---

<details>
<summary><strong>Step 14: Verify generated reports in S3</strong></summary>

After the Step Functions execution is completed, the PDF Generator Lambda stores the report files in the S3 Report Bucket.

Open the S3 Report Bucket:

```text
ai-aws-reviewer-report-bucket-tiersteam
```

The report files are stored under this prefix:

```text
reports/{reviewId}/
```

Example:

```text
reports/REV-0491BC4A/report-data.json
reports/REV-0491BC4A/report.html
reports/REV-0491BC4A/report.pdf
```

Verify the files:

```text
1. Go to Amazon S3.
2. Open the bucket ai-aws-reviewer-report-bucket-tiersteam.
3. Open the reports folder.
4. Open the folder with the reviewId, for example REV-0491BC4A.
5. Check that report-data.json, report.html, and report.pdf are all available.
6. Open or download report.pdf to check the report content.
```

Meaning of each file:

```text
report-data.json:
Stores structured review data, suitable for frontend or backend reuse.

report.html:
Stores the HTML report, which displays well in the browser.

report.pdf:
Stores the final PDF report, which can be downloaded or used in the demo result.
```

![Generated Reports](/images/5-Workshop/5.6-AI-workflow/s3-generated-reports.png)

</details>

---

<details>
<summary><strong>Step 15: Verify the completed review in DynamoDB</strong></summary>

DynamoDB stores the review history and processing status. After the workflow is completed, the PDF Generator Lambda must update the item that matches the `reviewId`.

Open the DynamoDB table:

```text
AIArchitectureReviews
```

Verify the item:

```text
1. Go to Amazon DynamoDB.
2. Select Tables.
3. Open the AIArchitectureReviews table.
4. Select Explore table items.
5. Search for the reviewId you just uploaded, for example REV-0491BC4A.
6. Check the status field.
7. Check completedDate and updatedAt.
8. Check reportFiles, costResult, detectedServices, and recommendations.
```

The review status should change from:

```text
uploaded
```

to:

```text
completed
```

Important fields that should exist:

```text
status = completed
score
architectureType
detectedServices
wellArchitectedResult
costResult
recommendations
risks
bestPractices
reportFiles
completedDate
updatedAt
```

If the item is still in the `uploaded` state, check the CloudWatch Logs of the PDF Generator Lambda. Common causes are a missing `TABLE_NAME` environment variable or missing `dynamodb:UpdateItem` permission.

![DynamoDB Completed Review](/images/5-Workshop/5.6-AI-workflow/dynamodb-completed-review.png)

</details>

---

<details>
<summary><strong>Step 16: Verify review history on the frontend</strong></summary>

The React frontend reads review history from the upload backend API. After the PDF Generator updates DynamoDB, the frontend can display the completed review status and analysis result.

The API routes used for review history are:

```text
GET /reviews
GET /reviews/{reviewId}
GET /reviews/{reviewId}/status
```

Verify on the frontend:

```text
1. Open the React frontend.
2. Upload a new architecture diagram.
3. Record the reviewId returned by the API.
4. Wait for the AI Workflow to finish in Step Functions.
5. Refresh the review history page.
6. Check that the review status has changed to completed.
7. Open the review detail page to view score, detected services, recommendations, and report links.
```

After the AI Workflow is completed, the frontend can display:

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

This step completes the full upload and AI review process.

```text
Upload Backend → S3 Input Bucket → EventBridge → Step Functions
→ AI Analyzer → Cost Tool → PDF Generator
→ S3 Report Bucket → DynamoDB → Frontend Review History
```

![Frontend Review History](/images/5-Workshop/5.6-AI-workflow/frontend-review-history.png)

</details>

---

#### AI Workflow result

After completing this section, the system can automatically process an uploaded AWS architecture diagram and generate a complete review report.

The final result includes:

```text
AI-based architecture analysis
Detected AWS services
AWS Well-Architected Framework assessment
Estimated monthly cost
Cost optimization recommendations
HTML report
PDF report
Updated review history
```

The AI Workflow automates the entire process after upload. Users only need to upload an architecture diagram, and the backend automatically performs analysis, cost estimation, report generation, and review history update.
