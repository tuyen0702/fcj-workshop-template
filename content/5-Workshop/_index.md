---
title: "Workshop"
date: 2026-07-03
weight: 5
chapter: false
pre: " <b> 5. </b> "
---

# AI AWS Architecture Reviewer

#### Overview

**AI AWS Architecture Reviewer** is a serverless web platform that allows users to upload AWS architecture diagrams and receive AI-supported architecture review results based on the **AWS Well-Architected Framework**.

In this workshop, the system is implemented in stages, starting with frontend development, deploying the React website to Amazon S3 and Amazon CloudFront, building the upload backend using Amazon API Gateway and AWS Lambda, storing architecture diagrams in Amazon S3, storing review metadata and status in Amazon DynamoDB, and then expanding to an automated processing workflow using Amazon EventBridge and AWS Step Functions.

In the AI processing stage, the system uses AWS Lambda AI Analyze to read the uploaded diagram from the Amazon S3 Input Bucket. Lambda AI Analyze sends the diagram to Amazon Bedrock so that Bedrock can identify AWS services, connections, text notes, and generate a structured architecture JSON. Then, the architecture JSON is sent to AWS Lambda Cost Tool to estimate the monthly cost. The cost estimation result together with the architecture JSON is sent back to Amazon Bedrock to perform a comprehensive architecture review based on the AWS Well-Architected Framework, explain the cost, and recommend optimizations.

After the analysis is completed, AWS Lambda PDF Generator creates a PDF report from the final review result, stores the report in the Amazon S3 Report Bucket, and updates the review history in Amazon DynamoDB. Amazon CloudWatch is used to record logs, monitor metrics, and create alarms for important components such as Lambda, API Gateway, Step Functions, EventBridge, and DynamoDB. When an important error affects the system, CloudWatch Alarm sends an alert to an Amazon SNS Topic. Amazon SNS then distributes the alert email to the email addresses that have been subscribed and confirmed. AWS IAM is used to control access between services based on the principle of least privilege access.

The project uses the following main AWS services: **Amazon S3, Amazon CloudFront, Amazon API Gateway, AWS Lambda, Amazon DynamoDB, Amazon EventBridge, AWS Step Functions, Amazon Bedrock, Amazon SNS, Amazon CloudWatch, and AWS IAM**.

The main goal of this workshop is to document the process of deploying the website and backend services, explain how to configure each AWS service, and complete the AI-powered AWS architecture review workflow, including diagram analysis, architecture JSON generation, cost estimation, final architecture review, PDF report generation, CloudWatch monitoring, SNS alert notification, and security.

---

#### Overall System Architecture

The architecture of **AI AWS Architecture Reviewer** is designed using a **serverless event-driven architecture** model. Users access the web application through Amazon CloudFront. The React frontend is stored in an Amazon S3 Static Website bucket and distributed through CloudFront to improve access performance.

When a user uploads an AWS architecture diagram, the request is sent from the frontend to Amazon API Gateway. API Gateway forwards the request to AWS Lambda Upload Service. Lambda Upload Service validates the uploaded file, creates a review ID, stores the diagram in the Amazon S3 Input Bucket, and writes the initial metadata to the Amazon DynamoDB Review Database.

After the diagram file is stored in the S3 Input Bucket, Amazon S3 generates an Object Created Event. This event is sent to Amazon EventBridge. EventBridge uses the configured rule to start the AWS Step Functions Review Workflow. Step Functions is responsible for orchestrating the entire review processing flow, including extraction, cost estimation, AI review, PDF generation, result storage, and error handling.

In the Processing Layer, Step Functions calls AAWS Lambda AI Analyze. Lambda AI Analyze reads the uploaded diagram from the S3 Input Bucket, then sends the diagram to Amazon Bedrock. At this step, Amazon Bedrock performs the initial diagram analysis to identify AWS services, connections, text notes, and architectural components. The returned result is a structured architecture JSON.

After the architecture JSON is generated, Lambda AI Analyze sends this data to AWS Lambda Cost Tool. Lambda Cost Tool analyzes the list of AWS services detected in the architecture JSON and estimates the monthly cost based on demo-level usage assumptions. The cost estimation result includes the list of services, usage assumptions, estimated costs, and components that may have a significant impact on the budget.

Next, the architecture JSON and cost estimation result are sent back to Amazon Bedrock to perform the final AI review. At this step, Amazon Bedrock evaluates the entire architecture based on the AWS Well-Architected Framework, including the pillars of Security, Reliability, Performance Efficiency, Cost Optimization, Operational Excellence, and Sustainability. Bedrock also explains the cost, identifies risks, and recommends architecture optimization improvements.

After the final AI review is completed, AWS Lambda PDF Generator creates a PDF report from the analysis result. The report is stored in the Amazon S3 Report Bucket. Lambda PDF Generator also updates the review history, review status, and report information in Amazon DynamoDB. Amazon SNS is not used to send an email when each review is completed. Instead, Amazon SNS is integrated with Amazon CloudWatch Alarm to send operational alert emails when the system encounters errors, such as Step Functions failed executions, Lambda errors, API Gateway 5XX errors, DynamoDB throttling, or EventBridge failed invocations.

![AI AWS Architecture Reviewer Workshop](/images/5-Workshop/ai-aws-architecture-reviewer.png)

---

#### Main Workflow

The system workflow includes the following steps:

1. The user accesses the web application through Amazon CloudFront.
2. Amazon CloudFront delivers the React frontend from the Amazon S3 Static Website bucket.
3. The user submits an architecture diagram through the frontend.
4. Amazon API Gateway receives the upload request and sends the request to AWS Lambda Upload Service.
5. AWS Lambda Upload Service validates the upload request and stores the uploaded diagram in the Amazon S3 Input Bucket.
6. Amazon S3 publishes an Object Created Event after the diagram is successfully uploaded.
7. Amazon EventBridge receives the event and starts the AWS Step Functions Review Workflow.
8. AWS Step Functions orchestrates the workflow and calls AWS Lambda AI Analyze to process the diagram.
9. AWS Lambda AI Analyze sends the uploaded diagram to Amazon Bedrock so that Bedrock can identify AWS services, connections, text notes, and generate architecture JSON.
10. AWS Lambda AI Analyze sends the architecture JSON to AWS Lambda Cost Tool to estimate the monthly cost.
11. AWS Lambda Cost Tool sends the cost estimation result together with the architecture JSON to Amazon Bedrock to review the entire architecture, explain the cost, and recommend optimizations.
12. AWS Lambda PDF Generator creates a PDF report from the final AI review result.
13. AWS Lambda PDF Generator updates the review history and review status in the Amazon DynamoDB Review Database.
14. AWS Lambda PDF Generator stores the generated PDF report in the Amazon S3 Report Bucket.
15. Amazon CloudWatch records logs, monitors metrics, and creates alarms for important components such as Lambda, API Gateway, Step Functions, EventBridge, and DynamoDB.
16. When CloudWatch Alarm detects an important error in the system, the alarm sends an alert to an Amazon SNS Topic.
17. Amazon SNS sends error alert emails to the email addresses that have been subscribed and confirmed.

---

#### AWS Services Used in the Workshop

The main AWS services used in this workshop include:

- **Amazon CloudFront**: Distributes the React web application to users with better performance and lower latency.
- **Amazon S3 Static Website Bucket**: Stores the production build of the React frontend, including `index.html` and static assets.
- **Amazon API Gateway**: Provides API endpoints for uploading diagrams, retrieving review history, viewing review details, and checking review status.
- **AWS Lambda Upload Service**: Handles upload requests, validates files, creates review IDs, stores diagrams in the S3 Input Bucket, and writes metadata to DynamoDB.
- **Amazon S3 Input Bucket**: Stores the original AWS architecture diagrams uploaded by users.
- **Amazon DynamoDB Review Database**: Stores metadata, review status, review history, uploaded file information, and PDF report paths.
- **Amazon EventBridge**: Receives S3 Object Created Events and triggers the Step Functions Review Workflow.
- **AWS Step Functions**: Orchestrates the entire review workflow, including diagram extraction, cost estimation, final AI review, PDF generation, and error handling.
- **AWS Lambda AI Analyze**: Reads the uploaded diagram from the S3 Input Bucket and sends the diagram to Amazon Bedrock to generate architecture JSON.
- **Amazon Bedrock**: Used in two stages. The first stage analyzes the diagram and generates architecture JSON. The second stage reviews the entire architecture based on the architecture JSON and cost estimation result.
- **AWS Lambda Cost Tool**: Receives the architecture JSON, identifies AWS services in the diagram, and estimates monthly costs.
- **AWS Lambda PDF Generator**: Creates a PDF report from the final AI review result, including architecture review, cost estimation, cost explanation, and optimization recommendations.
- **Amazon S3 Report Bucket**: Stores PDF reports generated after the review process is completed.
- **Amazon SNS**: Receives alerts from Amazon CloudWatch Alarm and sends system error notification emails to the email addresses that have been subscribed and confirmed. In this project, SNS is not used to send an email when each review is completed.
- **Amazon CloudWatch**: Records logs, monitors metrics, creates CloudWatch Alarms, and supports troubleshooting for Lambda, API Gateway, Step Functions, EventBridge, and DynamoDB. When an alarm detects an important error, CloudWatch sends the alert to an Amazon SNS Topic.
- **AWS IAM**: Controls access between services based on the principle of least privilege access.

---

#### Current Implementation Status

The following parts have been implemented in the project:

1. **Frontend Development**
   - Created the React frontend using Vite.
   - Built the main user interface of the application.
   - Developed the main pages, including Dashboard, Upload Diagram, Review Progress, Review History, Report Detail, and Settings.
   - Prepared the frontend structure for integration with the AWS backend APIs.
   - Implemented routing using React Router.
   - Prepared the interface to display review status, review history, and review details.

2. **Frontend Deployment with Amazon S3 and Amazon CloudFront**
   - Created an S3 bucket to store the React production build.
   - Built the frontend using the `npm run build` command.
   - Uploaded the contents of the `dist` folder to Amazon S3.
   - Created an Amazon CloudFront distribution to distribute the React website.
   - Configured Origin Access Control so that CloudFront can securely access the private S3 bucket.
   - Added an S3 bucket policy to allow CloudFront to read frontend files.
   - Configured the default root object as `index.html`.
   - Configured custom error responses for React Router:
     - 403 → `/index.html` → 200
     - 404 → `/index.html` → 200
   - Created CloudFront invalidation after each frontend deployment to prevent CloudFront from serving an old build.

3. **Upload Backend Development**
   - Created an Amazon S3 Input Bucket to store architecture diagrams uploaded by users.
   - Enabled server-side encryption for the S3 Input Bucket using SSE-S3.
   - Configured a lifecycle rule to automatically delete uploaded diagrams after 30 days to reduce storage costs.
   - Created an Amazon DynamoDB table named `AIArchitectureReviews`.
   - Used `reviewId` as the partition key.
   - Designed the DynamoDB item structure to store information such as review ID, file name, S3 key, upload time, status, report path, and metadata.
   - Created a Lambda execution role with the required permissions for S3, DynamoDB, and CloudWatch Logs.
   - Created the Lambda Upload Service.
   - Configured Lambda environment variables such as input bucket name, table name, maximum file size, and allowed origins.
   - Implemented upload logic to validate files, create review IDs, store diagrams in S3, and store metadata in DynamoDB.
   - Updated the initial review status, such as `uploaded` or `pending`.

4. **Amazon API Gateway Integration**
   - Created an Amazon API Gateway endpoint.
   - Created and integrated the following routes with Lambda:
     - `POST /upload`
     - `GET /reviews`
     - `GET /reviews/{reviewId}`
     - `GET /reviews/{reviewId}/status`
   - Configured CORS for localhost and the CloudFront frontend domain.
   - Tested file upload from the frontend.
   - Confirmed that the file was stored in the S3 Input Bucket.
   - Confirmed that metadata was stored in DynamoDB.
   - Confirmed that the frontend could successfully call API Gateway.

5. **Review Data Integration with Frontend**
   - Connected frontend pages with real API data.
   - Used `GET /reviews` to display Review History.
   - Used `GET /reviews/{reviewId}` to display Review Detail.
   - Used `GET /reviews/{reviewId}/status` to display Review Progress.
   - Fixed issues related to mock data, CORS, React Router, and review ID handling.
   - Prepared the interface to display processing statuses such as uploaded, processing, analyzed, completed, and failed.

---

#### Next Implementation Steps

The following parts will be implemented in the next phase of the project:

1. **Build the Event-Driven Review Workflow**
   - Configure S3 Object Created Event after a diagram is uploaded.
   - Route the event from Amazon S3 to Amazon EventBridge.
   - Create an EventBridge rule to capture events from the S3 Input Bucket.
   - Configure the EventBridge target as the AWS Step Functions Review Workflow.
   - Create an AWS Step Functions workflow to orchestrate the review process.
   - Configure retry and error handling in Step Functions.
   - Update the review status in DynamoDB when the workflow starts processing.

2. **Build Lambda AI Analyze**
   - Create AWS Lambda AI Analyze.
   - Receive bucket name, object key, and review ID from the Step Functions input.
   - Read the uploaded diagram from the Amazon S3 Input Bucket.
   - Check the diagram file type, such as image or draw.io XML.
   - If the file is an image, Lambda prepares the data to send to Amazon Bedrock.
   - If the file is draw.io XML, Lambda can parse the XML to support diagram information extraction.
   - Send the diagram to Amazon Bedrock so that Bedrock can analyze the diagram.
   - Receive architecture JSON from Amazon Bedrock.
   - Validate the architecture JSON before sending it to the cost estimation step.
   - Update the review status in DynamoDB if extraction fails.

3. **Integrate Amazon Bedrock to Generate Architecture JSON**
   - Select a suitable Bedrock model that can process both images and text.
   - Prepare the prompt for the diagram-to-JSON extraction step.
   - Send the uploaded diagram to Amazon Bedrock.
   - Ask Bedrock to identify components in the diagram, including:
     - AWS services.
     - Connections between services.
     - Data flow.
     - Text notes.
     - Security components.
     - Storage components.
     - Monitoring components.
     - Notification components.
   - Ask Bedrock to return a clearly structured architecture JSON.
   - Check the JSON output to ensure it follows the expected format.
   - Standardize the architecture JSON data for use in the next steps.

4. **Build Lambda Cost Tool**
   - Create AWS Lambda Cost Tool.
   - Receive architecture JSON from Lambda AI Analyze.
   - Read the list of AWS services detected in the diagram.
   - Assign default usage assumptions for each service at demo scale.
   - Estimate monthly costs for key services such as S3, CloudFront, API Gateway, Lambda, DynamoDB, EventBridge, Step Functions, Bedrock, SNS, and CloudWatch.
   - Create a cost estimation result that includes:
     - Service name.
     - Usage assumption.
     - Pricing unit.
     - Estimated monthly cost.
     - Cost notes.
     - Optimization hints.
   - Return the cost estimation result to Step Functions or send it to the final AI review step.

5. **Integrate Amazon Bedrock for Final AI Architecture Review**
   - Send the architecture JSON and cost estimation result to Amazon Bedrock.
   - Prepare the architecture review prompt based on the AWS Well-Architected Framework.
   - Ask Bedrock to analyze the architecture according to the following pillars:
     - Security.
     - Reliability.
     - Performance Efficiency.
     - Cost Optimization.
     - Operational Excellence.
     - Sustainability.
   - Ask Bedrock to evaluate the strengths of the architecture.
   - Ask Bedrock to identify risks and areas for improvement.
   - Ask Bedrock to explain the cost based on the cost estimation result.
   - Ask Bedrock to provide cost optimization recommendations.
   - Return the final AI review result for use in the PDF report generation step.
   - Update the review status in DynamoDB to `analyzed` after the AI review is completed.

6. **Generate PDF Report**
   - Create AWS Lambda PDF Generator.
   - Receive the final AI review result from Amazon Bedrock.
   - Generate a clearly structured PDF report.
   - The PDF report should include:
     - Review ID.
     - Upload information.
     - Detected AWS services.
     - Architecture JSON summary.
     - Cost estimation.
     - Cost explanation.
     - Well-Architected review result.
     - Risks.
     - Recommendations.
     - Optimization suggestions.
     - Conclusion.
   - Create an Amazon S3 Report Bucket to store PDF reports.
   - Enable server-side encryption using SSE-S3 for the Report Bucket.
   - Configure a lifecycle rule to manage the report lifecycle if needed.
   - Store the PDF report in the S3 Report Bucket.
   - Update the report URL or report S3 key in DynamoDB.
   - Update the review status to `completed`.

7. **Configure CloudWatch Alarm and SNS Alert Notification**
   - Configure an Amazon SNS Topic to receive alerts from CloudWatch Alarm.
   - Add email subscriptions to the SNS Topic.
   - Confirm email subscriptions to ensure that the emails can receive alerts.
   - Configure CloudWatch Alarm for AWS Step Functions to detect failed, timed out, or aborted workflow executions.
   - Configure CloudWatch Alarm for AWS Lambda functions to detect errors, throttles, and high duration.
   - Configure CloudWatch Alarm for API Gateway to detect 5XX errors, 4XX errors, and high latency.
   - Configure CloudWatch Alarm for DynamoDB to detect system errors and throttled requests.
   - Configure CloudWatch Alarm for EventBridge to detect failed invocations.
   - When CloudWatch Alarm changes to the ALARM state, the alert is sent to the SNS Topic.
   - Amazon SNS then sends alert emails to the email addresses that have been subscribed and confirmed.
   - SNS is used only for monitoring alerts, not for sending emails when each review is completed.

8. **Monitoring and Security**
   - Use Amazon CloudWatch to monitor Lambda logs.
   - Monitor API Gateway requests.
   - Monitor Step Functions executions.
   - Check errors in each workflow step.
   - Configure CloudWatch logs for Lambda functions.
   - Review IAM permissions according to the principle of least privilege access.
   - Enable server-side encryption for S3 buckets.
   - Limit S3 access permissions to the correct Lambda functions that need them.
   - Limit DynamoDB permissions to the specific table.
   - Limit Bedrock invoke model permissions to the Lambda functions that need to call AI.
   - Add retry logic and error handling in Step Functions.
   - Update the DynamoDB review status when the workflow fails.

---

#### Expected Results After the Workshop

After completing the workshop, the system is expected to achieve the following results:

- The React website is successfully deployed to Amazon S3 and distributed through Amazon CloudFront.
- The frontend can upload architecture diagrams through API Gateway.
- Lambda Upload Service can validate files, store diagrams in the S3 Input Bucket, and write metadata to DynamoDB.
- The frontend can display review history, review detail, and review progress from real APIs.
- S3 Object Created Event can trigger EventBridge.
- EventBridge can start the Step Functions Review Workflow.
- Step Functions can orchestrate the entire review processing flow.
- Lambda AI Analyze can read uploaded diagrams and send them to Amazon Bedrock.
- Amazon Bedrock can generate architecture JSON from uploaded diagrams.
- Lambda Cost Tool can estimate monthly costs based on architecture JSON.
- Amazon Bedrock can review the overall architecture based on architecture JSON and cost estimation result.
- Lambda PDF Generator can create a PDF report from the final AI review result.
- The PDF report is stored in the Amazon S3 Report Bucket.
- DynamoDB is updated with review history, review status, and report information.
- Amazon SNS sends alert emails when Amazon CloudWatch Alarm detects important errors in the system.
- Amazon CloudWatch records logs, monitors metrics, creates alarms, and sends error alerts to the Amazon SNS Topic.
- IAM permissions are reviewed based on the principle of least privilege access.
- The system can run end-to-end from uploading a diagram to generating a PDF report, storing the report in S3, updating DynamoDB, and allowing users to download the PDF successfully.

---

#### Workshop Contents

1. [Workshop Overview](5.1-Workshop-overview/)
2. [Prerequisites](5.2-Prerequisite/)
3. [Deploy React Frontend with S3 and CloudFront](5.3-Frontend-hosting/)
4. [Build Upload Backend with API Gateway, Lambda, S3 and DynamoDB](5.4-Upload-backend/)
5. [Integrate Review APIs and Frontend Pages](5.5-Review-api/)
6. [Build Event-Driven AI Review Workflow](5.6-AI-workflow/)
7. [Monitoring with CloudWatch, SNS Alert and IAM Least Privilege](5.7-Monitoring-security/)