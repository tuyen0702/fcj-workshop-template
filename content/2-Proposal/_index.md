---
title: "Proposal"
date: 2026-07-03
weight: 2
chapter: false
pre: " <b> 2. </b> "
---

This section summarizes the workshop project topic, including the problem statement, solution architecture, AWS services used, technical implementation plan, roadmap, risks, and expected outcomes.

# AI AWS Architecture Reviewer

## A Serverless AI-Powered Platform for Reviewing AWS Architecture Diagrams

### 1. Executive Summary

AI AWS Architecture Reviewer is a serverless web platform designed to help users automatically review AWS architecture diagrams using AI and the AWS Well-Architected Framework. The platform allows users to upload architecture diagrams through a React web application, securely store uploaded files in Amazon S3, record metadata for each review in Amazon DynamoDB, and trigger an automated review workflow.

The solution uses Amazon CloudFront and Amazon S3 to distribute the React frontend, Amazon API Gateway and AWS Lambda to handle upload requests, Amazon S3 Input Bucket to store uploaded architecture diagrams, and Amazon EventBridge with AWS Step Functions to start and manage the automated review workflow.

In the processing workflow, AWS Lambda Diagram Extractor reads the uploaded diagram from the Amazon S3 Input Bucket and prepares the input data to send to Amazon Bedrock. Amazon Bedrock identifies AWS services, connections, text notes, and architectural components from the diagram, then returns a structured architecture JSON. This architecture JSON becomes the central data source for the next analysis steps.

After the architecture JSON is generated, the system sends this data to AWS Lambda Cost Tool to estimate monthly costs based on the AWS services detected in the diagram. Lambda Cost Tool generates a cost estimation result, including the list of services, pricing units, usage assumptions, and estimated monthly costs.

Finally, the architecture JSON and cost estimation result are sent back to Amazon Bedrock to perform a comprehensive architecture review based on the AWS Well-Architected Framework. Amazon Bedrock analyzes aspects such as Security, Reliability, Performance Efficiency, Cost Optimization, Operational Excellence, and Sustainability, while also explaining costs and recommending optimization improvements.

After the analysis is completed, AWS Lambda PDF Generator creates a PDF report that includes the architecture review, cost estimation, cost explanation, and optimization recommendations. The report is stored in the Amazon S3 Report Bucket, the review history is updated in Amazon DynamoDB, and a completion notification is sent to the user through Amazon SNS. Amazon CloudWatch is used for logging and monitoring, while AWS IAM applies least privilege access across the system.

The goal of this project is to provide a practical, scalable, and cost-optimized AWS serverless solution that helps students, learners, and cloud project teams review AWS architectures more consistently, reduce manual review effort, and improve their understanding of best practices in cloud architecture design.

---

### 2. Problem Statement

### Current Problem

Manually reviewing an AWS architecture requires knowledge of multiple AWS services, cloud design patterns, security best practices, reliability strategies, performance optimization, cost optimization, and system operations. For students, cloud beginners, or project teams, identifying whether an AWS architecture follows the AWS Well-Architected Framework is often challenging.

Common challenges include:

- AWS architecture diagrams are usually reviewed manually and may lack consistency.
- Students may not know which important services are missing from their architecture or which design risks exist.
- Manual review requires cloud architecture experience and takes a significant amount of time.
- There is no centralized system for uploading, reviewing, storing, and tracking architecture review history.
- Creating a structured review report manually is time-consuming.
- Teams need an automated solution that can analyze architecture diagrams and provide improvement recommendations.

### Solution

AI AWS Architecture Reviewer provides an automated serverless workflow for reviewing AWS architecture diagrams. Users access the web application through Amazon CloudFront. The React frontend is distributed from an S3 Static Website bucket. Users upload architecture diagrams through the frontend, and the request is sent to Amazon API Gateway.

API Gateway forwards the upload request to AWS Lambda Upload Service. The Lambda function validates the uploaded file, stores the diagram in the Amazon S3 Input Bucket, and records the initial metadata in Amazon DynamoDB. After an object is created in the input bucket, Amazon S3 publishes an object-created event. This event is routed through Amazon EventBridge to start the AWS Step Functions review workflow.

AWS Step Functions orchestrates the entire review process. First, Step Functions calls AWS Lambda Diagram Extractor to read the uploaded diagram from the S3 Input Bucket. Lambda Diagram Extractor prepares the input data and sends the diagram to Amazon Bedrock. Amazon Bedrock analyzes the diagram to identify AWS services, connections, text notes, and important architectural components, then returns a structured architecture JSON.

After receiving the architecture JSON, Lambda Diagram Extractor sends this data to AWS Lambda Cost Tool. Lambda Cost Tool uses the list of AWS services in the architecture JSON to estimate monthly costs. The result of this step is a cost estimation result, including detected services, usage assumptions, estimated costs, and components that may have a significant impact on the budget.

Next, the architecture JSON and cost estimation result are sent back to Amazon Bedrock to perform a comprehensive architecture review. At this step, Amazon Bedrock analyzes the architecture based on the AWS Well-Architected Framework, explains design risks, evaluates costs, suggests cost optimization improvements, and provides recommendations for improvement.

After Bedrock completes the comprehensive review, AWS Lambda PDF Generator creates a PDF report from the AI review result. The report is stored in the Amazon S3 Report Bucket, the review history is updated in Amazon DynamoDB, and Amazon SNS sends a review notification to the user.

Overall system flow:

User → Amazon CloudFront → S3 Static Website React App → API Gateway → Lambda Upload Service → S3 Input Bucket → EventBridge → Step Functions → Lambda Diagram Extractor → Amazon Bedrock generates architecture JSON → Lambda Cost Tool estimates monthly cost → Amazon Bedrock performs comprehensive architecture review and cost optimization → Lambda PDF Generator → S3 Report Bucket + DynamoDB + SNS Email Notification.

### Benefits and Return on Investment

The solution provides a practical tool for learning and reviewing AWS architecture design. The system helps reduce manual review effort, improve consistency in architecture evaluation, and support users in understanding AWS Well-Architected principles more clearly.

Key benefits include:

- Automatically reviews AWS architectures based on Well-Architected best practices.
- Provides faster feedback for students and project teams.
- Centrally stores uploaded diagrams and review metadata.
- Tracks review history through DynamoDB.
- Generates PDF reports for documentation and presentation purposes.
- Sends email notifications when the review process is completed.
- Uses a serverless architecture to reduce operational effort.
- Optimizes cost because most services follow a pay-per-use model.
- Can be easily extended through EventBridge, Step Functions, Lambda, S3, and DynamoDB.

The project also creates long-term value as a reusable educational platform for learning cloud architecture, reviewing AWS projects, and developing AI-powered cloud architecture evaluation tools in the future.

---

### 3. Solution Architecture

The platform uses an event-driven AWS serverless architecture. The frontend layer is hosted on Amazon S3 and distributed through Amazon CloudFront. The API layer is built with Amazon API Gateway and AWS Lambda. Uploaded files are stored in the Amazon S3 Input Bucket, while review metadata is stored in Amazon DynamoDB. The review workflow is triggered by Amazon EventBridge and orchestrated by AWS Step Functions.

In the Processing Layer, AWS Lambda Diagram Extractor reads the uploaded diagram from the S3 Input Bucket and sends the diagram to Amazon Bedrock for analysis. Amazon Bedrock returns an architecture JSON that includes detected AWS services, connections, text notes, and architectural components. The architecture JSON is then sent to AWS Lambda Cost Tool to estimate monthly costs. The cost estimation result, together with the architecture JSON, is sent back to Amazon Bedrock to perform a comprehensive architecture review based on the AWS Well-Architected Framework and generate the final analysis content. AWS Lambda PDF Generator uses this result to create the PDF report.

The architecture includes the following main steps:

1. The user accesses the web application through Amazon CloudFront.
2. CloudFront delivers the React frontend from the S3 Static Website bucket.
3. The user submits an architecture diagram through the frontend.
4. API Gateway receives the upload request and sends it to AWS Lambda Upload Service.
5. Lambda Upload Service validates the upload request and stores the uploaded diagram in the Amazon S3 Input Bucket.
6. Amazon S3 publishes an object-created event after the diagram is uploaded.
7. Amazon EventBridge receives the object-created event and starts the AWS Step Functions review workflow.
8. AWS Step Functions orchestrates the review workflow and calls AWS Lambda Diagram Extractor.
9. AWS Lambda Diagram Extractor sends the uploaded diagram to Amazon Bedrock so Bedrock can identify AWS services, connections, text notes, and generate architecture JSON.
10. AWS Lambda Diagram Extractor sends the architecture JSON to AWS Lambda Cost Tool to estimate monthly costs.
11. AWS Lambda Cost Tool sends the cost estimation result together with the architecture JSON to Amazon Bedrock to review the entire architecture, explain costs, and provide optimization recommendations.
12. AWS Lambda PDF Generator creates a PDF report from the final AI review result.
13. AWS Lambda PDF Generator updates the review history and review status in Amazon DynamoDB.
14. AWS Lambda PDF Generator stores the generated PDF report in the Amazon S3 Report Bucket.
15. Amazon SNS sends a review notification to the user after the review process is completed.
16. Amazon CloudWatch records logs and metrics and supports troubleshooting for Lambda, Step Functions, API Gateway, and workflow execution.
17. AWS IAM applies least privilege access between services.

![AI AWS Architecture Reviewer Architecture](/images/2-Proposal/ai-aws-architecture-reviewer-proposal.png)

### AWS Services Used

- **Amazon CloudFront**: Distributes the React web application and improves frontend performance.
- **Amazon S3 Static Website Bucket**: Stores the React production build, including `index.html` and static assets.
- **Amazon API Gateway**: Provides API endpoints for upload, review history, review detail, and review status.
- **AWS Lambda Upload Service**: Validates upload requests, stores uploaded diagrams, records metadata, and handles review data APIs.
- **Amazon S3 Input Bucket**: Stores the original architecture diagrams uploaded by users.
- **Amazon DynamoDB**: Stores review metadata, upload information, review status, and review history.
- **Amazon EventBridge**: Captures S3 object-created events and triggers the review workflow.
- **AWS Step Functions**: Orchestrates the review workflow with retry and error handling.
- **AWS Lambda Diagram Extractor**: Reads the uploaded architecture diagram from the Amazon S3 Input Bucket, prepares the input data, and sends the diagram to Amazon Bedrock to identify AWS services, connections, text notes, and generate architecture JSON.
- **Amazon Bedrock**: Used in two main stages. In the first stage, Bedrock analyzes the diagram and generates a structured architecture JSON. In the second stage, Bedrock receives the architecture JSON and cost estimation result to perform a comprehensive architecture review based on the AWS Well-Architected Framework, explain costs, and suggest optimization improvements.
- **AWS Lambda Cost Tool**: Receives the architecture JSON from Lambda Diagram Extractor, analyzes the AWS services detected in the diagram, and estimates monthly costs. The cost estimation result is sent back to Amazon Bedrock to support the comprehensive review and cost optimization step.
- **AWS Lambda PDF Generator**: Creates PDF reports from the final AI review result, including architecture review, cost estimation, cost explanation, and optimization recommendations.
- **Amazon S3 Report Bucket**: Stores generated PDF reports with server-side encryption.
- **Amazon SNS**: Sends email notifications when the review process is completed.
- **Amazon CloudWatch**: Provides logging, monitoring, and troubleshooting for Lambda and workflow execution.
- **AWS IAM**: Controls service access using least privilege access.

### Component Design

- **Frontend Layer**: The React application is hosted in Amazon S3 and distributed through Amazon CloudFront. The frontend includes Dashboard, Upload Diagram, Review Progress, Review History, Report Detail, and Settings pages.
- **API Layer**: Amazon API Gateway provides endpoints such as `POST /upload`, `GET /reviews`, `GET /reviews/{reviewId}`, and `GET /reviews/{reviewId}/status`.
- **Upload Processing Layer**: AWS Lambda Upload Service validates uploaded files, creates a unique review ID, stores the file in S3, and records metadata in DynamoDB.
- **Storage Layer**: Amazon S3 Input Bucket stores uploaded diagrams, Amazon S3 Report Bucket stores generated PDF reports, and DynamoDB stores metadata and review history.
- **Workflow Layer**: EventBridge receives object-created events from S3 and starts Step Functions to orchestrate the review process.
- **AI Processing Layer**: AWS Lambda Diagram Extractor reads the uploaded diagram from the S3 Input Bucket and sends the diagram to Amazon Bedrock to extract architecture information. Amazon Bedrock identifies AWS services, connections, text notes, and returns the architecture JSON. The architecture JSON is then used as input for cost estimation and comprehensive architecture review.
- **Cost Analysis Component**: AWS Lambda Cost Tool receives the architecture JSON, identifies AWS services in the diagram, and estimates monthly costs based on demo-level usage assumptions. The cost estimation result helps the report provide not only architecture evaluation but also an overview of expected operational costs.
- **Final AI Review Component**: Amazon Bedrock receives the architecture JSON and cost estimation result to review the entire architecture based on the AWS Well-Architected Framework. The analysis result includes strengths, risks, issues to improve, cost explanations, and optimization recommendations.
- **Reporting Layer**: AWS Lambda PDF Generator receives the final AI review result from Amazon Bedrock, creates a PDF report, and stores it in the Amazon S3 Report Bucket.
- **Notification Layer**: Amazon SNS sends email notifications after the review process is completed.
- **Monitoring and Security Layer**: CloudWatch monitors logs and workflow execution, while IAM applies least privilege access.

---

### 4. Technical Implementation

**Implementation Phases**

The project is implemented in multiple phases, starting with frontend development and the basic upload feature, then expanding into an event-driven AI workflow and PDF reporting.

- **Frontend Development and Hosting**: Build the React frontend with Vite, create the main pages, generate production build files, upload them to Amazon S3, and distribute the frontend through Amazon CloudFront.
- **Upload Backend Implementation**: Create the S3 Input Bucket, DynamoDB review table, Lambda execution role, and Lambda Upload Service to handle file uploads and store metadata.
- **API Gateway and Review Data API**: Create API Gateway routes for uploading diagrams and retrieving review data. Configure CORS to allow requests from the deployed CloudFront frontend.
- **Event-Driven Review Workflow**: Configure S3 object-created events, route events through EventBridge, and start a Step Functions workflow to process uploaded architecture diagrams.
- **AI Analysis and Reporting**: Use Lambda Diagram Extractor to read the uploaded diagram and send it to Amazon Bedrock to generate architecture JSON. Then, send the architecture JSON to Lambda Cost Tool to estimate monthly costs. The architecture JSON and cost estimation result are sent back to Amazon Bedrock to perform a comprehensive architecture review based on the AWS Well-Architected Framework. Finally, Lambda PDF Generator creates the PDF report and stores it in the S3 Report Bucket.
- **Notification, Monitoring, and Security**: Send review notifications through SNS, monitor logs and workflow execution with CloudWatch, and apply IAM least privilege permissions.

### Technical Requirements

- React frontend using Vite.
- Amazon S3 frontend bucket for static hosting.
- Amazon CloudFront distribution with Origin Access Control.
- API Gateway for backend APIs.
- AWS Lambda for upload handling and review API logic.
- Amazon S3 Input Bucket for uploaded diagrams.
- Amazon DynamoDB for metadata and review history.
- Amazon EventBridge for event-driven workflow triggering.
- AWS Step Functions for review orchestration.
- AWS Lambda Diagram Extractor for diagram parsing.
- Amazon Bedrock for diagram-to-JSON extraction and final AI architecture review.
- AWS Lambda Cost Tool for monthly cost estimation based on architecture JSON.
- AWS Lambda PDF Generator for report generation.
- Amazon S3 Report Bucket for PDF storage.
- Amazon SNS for email notification.
- CloudWatch for monitoring and troubleshooting.
- IAM for least privilege access control.

---

### 5. Roadmap and Implementation Milestones

**Project Timeline**

The project is planned and implemented over four internship weeks, from Week 9 to Week 12. The roadmap focuses on architecture design, frontend development, AWS backend configuration, system deployment, AI workflow integration, testing, and documentation completion.

- **Week 9: Project Planning and Architecture Design**
  - Define the project topic: AI AWS Architecture Reviewer.
  - Analyze system requirements and the main user workflow.
  - Study the AWS Well-Architected Framework.
  - Select the AWS services needed for the solution.
  - Design the overall AWS serverless architecture diagram.
  - Plan the main application features, including Dashboard, Upload Diagram, Review Progress, Review History, Report Detail, and Settings.

- **Week 10: Frontend Development**
  - Create the React project with Vite.
  - Build the main frontend layout with Header, Sidebar, and Main Content.
  - Develop the Dashboard page.
  - Develop the Upload Diagram page.
  - Develop the Review Progress page.
  - Develop the Review History page.
  - Develop the Report Detail and Settings pages.
  - Prepare the frontend structure for integration with AWS backend APIs.

- **Week 11: AWS Backend Development and Frontend Deployment**
  - Create the S3 Frontend Bucket to store the React production build.
  - Build and upload the React production files to Amazon S3.
  - Create the Amazon CloudFront Distribution.
  - Configure Origin Access Control, S3 bucket policy, default root object, SPA fallback, and CloudFront invalidation.
  - Create the S3 Input Bucket to store architecture diagrams uploaded by users.
  - Create the DynamoDB Review Table to store metadata for each review.
  - Create the Lambda Execution Role with the required permissions for S3, DynamoDB, and CloudWatch.
  - Create the Lambda Upload Service.
  - Create API Gateway routes, including `POST /upload`, `GET /reviews`, `GET /reviews/{reviewId}`, and `GET /reviews/{reviewId}/status`.
  - Configure CORS for localhost and the CloudFront frontend domain.
  - Test the upload function from the frontend to S3 and verify metadata recording in DynamoDB.

- **Week 12: AI Workflow Integration, Reporting, Testing, and Completion**
  - Create the AWS Step Functions Review Workflow.
  - Create Lambda Diagram Extractor to read uploaded diagrams from the S3 Input Bucket.
  - Integrate Amazon Bedrock in the first stage to analyze diagrams and generate architecture JSON.
  - Create Lambda Cost Tool to estimate monthly costs based on architecture JSON.
  - Integrate Amazon Bedrock in the final review stage to evaluate the entire architecture based on the AWS Well-Architected Framework, explain costs, and suggest optimizations.
  - Create Lambda PDF Generator to generate review reports from the final AI review result.
  - Store generated PDF reports in the S3 Report Bucket.
  - Send completion notifications through Amazon SNS.
  - Monitor logs and execution status with Amazon CloudWatch.
  - Review IAM permissions according to the least privilege principle.
  - Perform end-to-end testing for upload, diagram extraction, cost estimation, AI review, report generation, and notification.

---

### 6. Budget Estimation

The project uses AWS serverless services, so costs mainly depend on usage. In the MVP and medium-scale demo phase, expected traffic is not high, but the system still includes key components such as frontend hosting, API backend, file storage, metadata database, event-driven workflow, AI analysis, PDF report generation, email notification, and monitoring.

### Calculation Assumptions

The budget estimation is based on a medium-scale demo with the following assumptions:

- Number of users: around 5–10 users.
- Number of diagram uploads: around 200–300 diagrams per month.
- Average diagram size: around 3–5 MB.
- Number of PDF reports generated: around 200–300 reports per month.
- Number of review workflow executions: around 200–300 executions per month.
- Number of API requests: around 5,000–15,000 requests per month.
- Each workflow includes the following steps: upload diagram, store metadata, trigger workflow, send diagram to Bedrock to generate architecture JSON, estimate monthly cost with Lambda Cost Tool, send architecture JSON and cost estimation result to Bedrock for comprehensive review, create PDF report, store the report, and send notification.
- Amazon Bedrock is used for architecture analysis at demo scale, not for large production traffic.

### Estimated Infrastructure Costs

- **Amazon S3**: around **0.10–0.50 USD/month**  
  Used to store React frontend build files, uploaded diagrams, and generated PDF reports. With a few GB of storage during the demo phase, S3 cost remains very low.

- **Amazon CloudFront**: around **0.00–1.00 USD/month**  
  Used to distribute the frontend web application. With medium demo traffic, CloudFront cost is usually low because data transfer volume is not high.

- **Amazon API Gateway**: around **0.05–0.20 USD/month**  
  Used to process API requests such as `POST /upload`, `GET /reviews`, `GET /reviews/{reviewId}`, and `GET /reviews/{reviewId}/status`.

- **AWS Lambda**: around **0.00–0.70 USD/month**  
  Used to handle uploads, validate files, record metadata, read uploaded diagrams, coordinate architecture JSON data, estimate monthly costs through Lambda Cost Tool, and generate PDF reports. With demo-level request volume, Lambda cost remains very low.

- **AWS Lambda Cost Tool**: around **0.00–0.20 USD/month**  
  Used to receive architecture JSON, identify AWS services in the diagram, and estimate monthly costs. With 200–300 diagrams per month in the demo phase, the cost of running Lambda Cost Tool remains very low. Actual cost depends on Lambda runtime duration, the number of services to calculate, and the complexity of the cost estimation logic.

- **Amazon DynamoDB**: around **0.05–0.30 USD/month**  
  Used to store review metadata, review history, and review status. Since each review record is small, DynamoDB cost is low during the demo phase.

- **Amazon EventBridge**: around **0.01–0.05 USD/month**  
  Used to route S3 object-created events and trigger the workflow after users upload diagrams.

- **AWS Step Functions**: around **0.00–0.30 USD/month**  
  Used to orchestrate the review workflow. With around 200–300 workflow executions per month, Step Functions cost remains very low if the number of state transitions is not high.

- **Amazon SNS**: around **0.00–0.10 USD/month**  
  Used to send email notifications when the review process is completed.

- **Amazon CloudWatch**: around **0.50–2.00 USD/month**  
  Used to store logs and support monitoring for Lambda, API Gateway, and Step Functions. CloudWatch cost depends on the amount of logs generated during testing and debugging.

- **Amazon Bedrock**: around **5.00–35.00 USD/month**  
  Used in two stages: analyzing diagrams to generate architecture JSON and performing comprehensive architecture review based on the architecture JSON and cost estimation result. This is the most variable cost component because it depends on the selected model, input/output tokens, diagram size, architecture JSON length, cost estimation detail, and number of AI calls. If a smaller model is used, prompt length is limited, and input data is reduced, the cost will be lower.

### Total Estimated Cost

With a medium-scale demo, the total estimated infrastructure cost is around:

**10–40 USD/month**

Equivalent to approximately:

**120–480 USD/year**

In this estimate, basic serverless services such as S3, CloudFront, API Gateway, Lambda, DynamoDB, EventBridge, Step Functions, SNS, and Lambda Cost Tool account for a relatively small cost. The largest cost factor is Amazon Bedrock because the system uses Bedrock for both the diagram-to-architecture-JSON generation step and the final AI architecture review step.

### Notes

To control costs, the system should limit upload file size, limit the number of AI calls, choose a suitable Bedrock model, reduce diagram data before sending it to Bedrock, standardize the architecture JSON at the necessary level, send only important cost estimation results instead of all raw data, reduce unnecessary logs, and use AWS Budgets to monitor monthly costs.

---

### 7. Risk Assessment

#### Risk Matrix

- Invalid or unsupported diagram file: Medium impact, medium probability.
- AI review result is inaccurate or incomplete: High impact, medium probability.
- Workflow fails during extraction or report generation: Medium impact, medium probability.
- CORS error between CloudFront and API Gateway: Medium impact, medium probability.
- CloudFront cache still serves an old frontend build: Low to medium impact, medium probability.
- IAM permissions are too broad or too restrictive: High impact, medium probability.
- Amazon Bedrock cost increases due to high token usage: Medium impact, low probability.
- Bedrock incorrectly identifies AWS services or connections from the diagram: High impact, medium probability.
- Generated architecture JSON is incomplete or does not follow the expected structure: High impact, medium probability.
- Cost estimation is inaccurate due to missing usage assumptions: Medium impact, medium probability.
- Amazon Bedrock cost increases because AI is called in both the JSON generation step and the final review step: Medium impact, medium probability.

#### Mitigation Strategies

- Validate file type and file size before storing uploads.
- Use structured prompts for Amazon Bedrock.
- Use Step Functions retry and error handling.
- Store workflow status in DynamoDB.
- Configure CORS correctly for localhost and the CloudFront frontend domain.
- Create CloudFront invalidation after each frontend deployment.
- Apply least privilege IAM policies.
- Monitor Lambda, API Gateway, Step Functions, and Bedrock usage through CloudWatch.
- Use AWS Budgets to track expected monthly costs.
- Standardize the prompt for the diagram-to-JSON extraction step.
- Validate architecture JSON before sending it to Lambda Cost Tool.
- Use clear default usage assumptions for cost estimation.
- Limit diagram size and the length of data sent to Bedrock.
- Separate the architecture JSON generation prompt from the final architecture review prompt to better control the output.

#### Contingency Plan

- If AI analysis fails, mark the review status as failed in DynamoDB.
- If PDF generation fails, keep the AI review result and retry the PDF generation process.
- If SNS email delivery fails, allow the user to view the report directly from the web application.
- If CloudFront still serves old files, create an invalidation and redeploy the frontend.
- If Bedrock usage becomes too expensive, limit input size or reduce the number of review requests.

---

### 8. Expected Outcomes

#### Technical Improvements

The project is expected to create a working AWS serverless platform that allows users to upload architecture diagrams and receive AI-supported architecture review results.

Expected technical outcomes include:

- A React web application running on S3 and distributed through CloudFront.
- Secure frontend delivery using CloudFront OAC and private S3 bucket access.
- API Gateway routes for uploading diagrams and retrieving review data.
- Lambda Upload Service for file validation, S3 storage, and DynamoDB metadata.
- S3 Input Bucket for uploaded architecture diagrams.
- DynamoDB Review Database for review history and status tracking.
- EventBridge and Step Functions workflow for automated review processing.
- Lambda Diagram Extractor reads uploaded diagrams and sends them to Amazon Bedrock.
- Amazon Bedrock generates architecture JSON from uploaded diagrams.
- Lambda Cost Tool estimates monthly costs based on architecture JSON.
- Amazon Bedrock performs final AI architecture review based on architecture JSON and cost estimation result.
- PDF report generation includes architecture review, cost estimation, cost explanation, and optimization recommendations.
- PDF reports are stored in the S3 Report Bucket.
- SNS email notification when the review is completed.
- CloudWatch monitoring and IAM least privilege security.

#### Long-Term Value

The platform can be reused as a learning tool for AWS architecture design and Well-Architected review practice. The system can also be extended into a more advanced cloud architecture evaluation platform with features such as user authentication, multi-user review history, architecture scoring, advanced report templates, and support for more diagram formats.

The project provides practical experience with important AWS services, including CloudFront, S3, API Gateway, Lambda, DynamoDB, EventBridge, Step Functions, Amazon Bedrock, SNS, CloudWatch, and IAM.