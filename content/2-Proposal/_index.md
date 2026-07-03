---
title: "Proposal"
date: 2026-07-03
weight: 2
chapter: false
pre: " <b> 2. </b> "
---

In this section, the proposed workshop project is summarized, including the problem statement, solution architecture, AWS services, technical implementation plan, timeline, risks, and expected outcomes.

# AI AWS Architecture Reviewer
## A Serverless AI-Powered Platform for Reviewing AWS Architecture Diagrams

### 1. Executive Summary

AI AWS Architecture Reviewer is a serverless web platform designed to help users review AWS architecture diagrams automatically using AI and the AWS Well-Architected Framework. The platform allows users to upload architecture diagrams through a React web application, stores the uploaded files securely in Amazon S3, records review metadata in Amazon DynamoDB, and triggers an automated review workflow.

The solution uses Amazon CloudFront and Amazon S3 to deliver the React frontend, Amazon API Gateway and AWS Lambda to handle upload and review API requests, Amazon S3 Input Bucket to store uploaded architecture diagrams, Amazon EventBridge and AWS Step Functions to start and manage the review workflow, AWS Lambda Diagram Extractor to extract AWS services and connections from the uploaded diagram, and Amazon Bedrock to analyze the architecture based on AWS Well-Architected best practices.

After the AI analysis is completed, AWS Lambda PDF Generator creates a PDF report, stores it in Amazon S3 Report Bucket, updates the review history in Amazon DynamoDB, and sends a review notification through Amazon SNS. Amazon CloudWatch is used for logging and monitoring, while AWS IAM is used to enforce least privilege access across the system.

This project aims to provide a practical, scalable, and cost-optimized AWS serverless solution that helps students, learners, and cloud project teams review AWS architectures more consistently, reduce manual review effort, and improve their understanding of cloud architecture best practices.

---

### 2. Problem Statement

### What’s the Problem?

Reviewing an AWS architecture manually requires knowledge of many AWS services, cloud design patterns, security best practices, reliability strategies, performance considerations, cost optimization methods, and operational practices. For students, beginners, or project teams, it can be difficult to determine whether an AWS architecture follows the AWS Well-Architected Framework.

Common challenges include:

- AWS architecture diagrams are often reviewed manually and inconsistently.
- Students may not know whether their architecture is missing important services or contains design risks.
- Manual review requires cloud architecture experience and takes time.
- There is no centralized system to upload, review, store, and track architecture review history.
- Creating a structured review report manually can be time-consuming.
- Teams need an automated solution that can analyze architecture diagrams and provide improvement suggestions.

### The Solution

AI AWS Architecture Reviewer provides an automated serverless workflow for reviewing AWS architecture diagrams. Users access the web application through Amazon CloudFront. The React frontend is delivered from an Amazon S3 Static Website bucket. Users upload an architecture diagram through the frontend, and the request is submitted to Amazon API Gateway.

API Gateway forwards the upload request to AWS Lambda Upload Service. The Lambda function validates the uploaded file, stores the diagram in Amazon S3 Input Bucket, and records metadata in Amazon DynamoDB. After the object is created in the input bucket, an event is published and routed through Amazon EventBridge to start an AWS Step Functions review workflow.

Step Functions coordinates the review process. AWS Lambda Diagram Extractor extracts AWS services and connections from the uploaded architecture diagram. The extracted information is then sent to Amazon Bedrock, which analyzes the architecture using the AWS Well-Architected Framework. After the analysis, AWS Lambda PDF Generator creates a PDF report. The report is stored in Amazon S3 Report Bucket, review history is updated in Amazon DynamoDB, and Amazon SNS sends a review notification to the user.

The overall system flow is:

User → Amazon CloudFront → S3 Static Website React App → API Gateway → Lambda Upload Service → S3 Input Bucket → EventBridge → Step Functions → Lambda Diagram Extractor → Amazon Bedrock → Lambda PDF Generator → DynamoDB + S3 Report Bucket + SNS Email Notification.

### Benefits and Return on Investment

The solution provides a practical tool for learning and reviewing AWS architecture designs. It helps reduce manual review effort, improves consistency in architecture assessment, and supports better understanding of AWS Well-Architected principles.

Key benefits include:

- Automated AWS architecture review based on Well-Architected best practices.
- Faster feedback for students and project teams.
- Centralized storage for uploaded diagrams and review metadata.
- Review history tracking through DynamoDB.
- PDF report generation for documentation and presentation.
- Email notification when the review is completed.
- Serverless architecture with low operational overhead.
- Cost-efficient design because most services are pay-per-use.
- Easy scalability through EventBridge, Step Functions, Lambda, S3, and DynamoDB.

The project also creates long-term value as a reusable educational platform for cloud architecture learning, AWS project review, and future AI-powered cloud assessment tools.

---

### 3. Solution Architecture

The platform uses an AWS serverless event-driven architecture. The frontend layer is hosted using Amazon S3 and distributed through Amazon CloudFront. The API layer is built with Amazon API Gateway and AWS Lambda. Uploaded files are stored in Amazon S3 Input Bucket, while review metadata is stored in Amazon DynamoDB. The AI review workflow is triggered by Amazon EventBridge and orchestrated by AWS Step Functions. Amazon Bedrock performs AI-based analysis, and AWS Lambda PDF Generator produces the final report.

The architecture contains the following main steps:

1. User accesses the web application through Amazon CloudFront.
2. CloudFront delivers the React frontend from the S3 Static Website bucket.
3. User submits an architecture diagram through the frontend.
4. API Gateway receives the upload request and sends it to AWS Lambda Upload Service.
5. Lambda validates the upload request and stores the uploaded diagram in Amazon S3 Input Bucket.
6. Amazon S3 publishes an object-created event.
7. Amazon EventBridge starts the review workflow.
8. AWS Step Functions coordinates the review workflow and invokes Lambda Diagram Extractor.
9. Lambda Diagram Extractor extracts AWS services and connections from the uploaded diagram.
10. Amazon Bedrock analyzes the architecture using the AWS Well-Architected Framework.
11. Lambda PDF Generator creates a PDF report.
12. Amazon DynamoDB stores review history and metadata.
13. Amazon S3 Report Bucket stores the generated PDF report.
14. Amazon SNS sends a review notification.
15. Amazon CloudWatch monitors logs, metrics, and workflow execution.
16. AWS IAM enforces least privilege access between services.

![AI AWS Architecture Reviewer Architecture](/images/2-Proposal/ai-aws-architecture-reviewer.jpg)

### AWS Services Used

- **Amazon CloudFront**: Distributes the React web application and improves frontend performance.
- **Amazon S3 Static Website Bucket**: Stores the React production build, including `index.html` and static assets.
- **Amazon API Gateway**: Provides API endpoints for upload, review history, review detail, and review status.
- **AWS Lambda Upload Service**: Validates upload requests, stores uploaded diagrams, writes metadata, and handles review data APIs.
- **Amazon S3 Input Bucket**: Stores original architecture diagrams uploaded by users.
- **Amazon DynamoDB**: Stores review metadata, upload information, review status, and review history.
- **Amazon EventBridge**: Captures S3 object-created events and triggers the review workflow.
- **AWS Step Functions**: Orchestrates the review workflow with retry and error handling.
- **AWS Lambda Diagram Extractor**: Extracts AWS services and connections from uploaded architecture diagrams.
- **Amazon Bedrock**: Performs AI-powered architecture analysis based on the AWS Well-Architected Framework.
- **AWS Lambda PDF Generator**: Generates PDF reports from AI review results.
- **Amazon S3 Report Bucket**: Stores generated PDF reports with server-side encryption.
- **Amazon SNS**: Sends email notifications when the review is completed.
- **Amazon CloudWatch**: Provides logging, monitoring, and troubleshooting for Lambda and workflow execution.
- **AWS IAM**: Controls service permissions using least privilege access.

### Component Design

- **Frontend Layer**: A React application hosted in Amazon S3 and delivered through Amazon CloudFront. It includes Dashboard, Upload Diagram, Review Progress, Review History, Report Detail, and Settings pages.
- **API Layer**: Amazon API Gateway exposes endpoints such as `POST /upload`, `GET /reviews`, `GET /reviews/{reviewId}`, and `GET /reviews/{reviewId}/status`.
- **Upload Processing Layer**: AWS Lambda Upload Service validates uploaded files, generates a unique review ID, stores files in S3, and writes metadata to DynamoDB.
- **Storage Layer**: Amazon S3 Input Bucket stores uploaded diagrams, Amazon S3 Report Bucket stores generated PDF reports, and DynamoDB stores metadata and review history.
- **Workflow Layer**: EventBridge receives object-created events from S3 and starts Step Functions to coordinate the review process.
- **AI Processing Layer**: Lambda Diagram Extractor extracts architecture information, and Amazon Bedrock analyzes the design based on the AWS Well-Architected Framework.
- **Reporting Layer**: Lambda PDF Generator creates a PDF report and stores it in S3 Report Bucket.
- **Notification Layer**: Amazon SNS sends email notifications after review completion.
- **Monitoring and Security Layer**: CloudWatch monitors logs and workflow execution, while IAM enforces least privilege access.

---

### 4. Technical Implementation

**Implementation Phases**

The project is implemented in multiple phases, starting from frontend development and basic upload functionality, then extending to event-driven AI workflow and PDF reporting.

- **Frontend Development and Hosting**: Build the React frontend using Vite, create the main pages, build the production files, upload them to Amazon S3, and distribute the frontend through Amazon CloudFront.
- **Upload Backend Implementation**: Create the S3 Input Bucket, DynamoDB review table, Lambda execution role, and Lambda Upload Service to handle file uploads and metadata storage.
- **API Gateway and Review Data API**: Create API Gateway routes for uploading diagrams and retrieving review data. Configure CORS to allow requests from the deployed CloudFront frontend.
- **Event-Driven Review Workflow**: Configure S3 object-created events, route them through EventBridge, and start a Step Functions workflow to process the uploaded architecture diagram.
- **AI Analysis and Reporting**: Use Lambda Diagram Extractor and Amazon Bedrock to analyze the architecture, then generate a PDF report and store it in the S3 Report Bucket.
- **Notification, Monitoring, and Security**: Send review notifications through SNS, monitor logs and workflow execution using CloudWatch, and apply IAM least privilege permissions.

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
- Amazon Bedrock for AI architecture review.
- AWS Lambda PDF Generator for report generation.
- Amazon S3 Report Bucket for PDF storage.
- Amazon SNS for email notification.
- CloudWatch for monitoring and troubleshooting.
- IAM for least privilege access control.

---

### 5. Timeline & Milestones

**Project Timeline**

The project is planned and implemented within four internship weeks, from Week 9 to Week 12. The timeline focuses on architecture design, frontend development, AWS backend setup, deployment, AI workflow integration, and final testing.

- **Week 9: Project Planning and Architecture Design**
  - Define the project topic: AI AWS Architecture Reviewer.
  - Analyze the system requirements and main user flow.
  - Study the AWS Well-Architected Framework.
  - Select the required AWS services for the solution.
  - Design the overall AWS serverless architecture diagram.
  - Plan the main application features, including Dashboard, Upload Diagram, Review Progress, Review History, Report Detail, and Settings.

- **Week 10: Frontend Development**
  - Create the React project using Vite.
  - Build the main frontend layout with Header, Sidebar, and Main Content.
  - Develop the Dashboard page.
  - Develop the Upload Diagram page.
  - Develop the Review Progress page.
  - Develop the Review History page.
  - Develop the Report Detail and Settings pages.
  - Prepare the frontend structure for API integration with the AWS backend.

- **Week 11: AWS Backend and Frontend Deployment**
  - Create the S3 frontend bucket for hosting the React production build.
  - Build and upload React production files to Amazon S3.
  - Create the Amazon CloudFront distribution.
  - Configure Origin Access Control, S3 bucket policy, default root object, SPA fallback, and CloudFront invalidation.
  - Create the S3 Input Bucket for uploaded architecture diagrams.
  - Create the DynamoDB review table for storing review metadata.
  - Create the Lambda execution role with required S3, DynamoDB, and CloudWatch permissions.
  - Create the Lambda Upload Service.
  - Create API Gateway routes, including `POST /upload`, `GET /reviews`, `GET /reviews/{reviewId}`, and `GET /reviews/{reviewId}/status`.
  - Configure CORS for localhost and the CloudFront frontend domain.
  - Test file upload from the frontend to S3 and DynamoDB.

- **Week 12: AI Workflow, Reporting, Testing, and Finalization**
  - Configure Amazon EventBridge to trigger the review workflow after file upload.
  - Create the AWS Step Functions Review Workflow.
  - Create Lambda Diagram Extractor to extract AWS services and connections from uploaded diagrams.
  - Integrate Amazon Bedrock to analyze architectures using the AWS Well-Architected Framework.
  - Create Lambda PDF Generator to generate review reports.
  - Store generated PDF reports in the S3 Report Bucket.
  - Send review completion notifications through Amazon SNS.
  - Monitor logs and execution status using Amazon CloudWatch.
  - Review IAM permissions based on least privilege access.
  - Perform end-to-end testing for upload, review workflow, report generation, and notification.
  - Finalize documentation, architecture diagram, and project presentation.o

---

### 6. Budget Estimation

The project uses AWS serverless services, so the cost mainly depends on actual usage. In the MVP and medium-scale demo stage, the expected traffic is not too high, but the system still includes all key components such as frontend hosting, API backend, file storage, metadata database, event-driven workflow, AI analysis, PDF report generation, email notification, and monitoring.

### Calculation Assumptions

The budget estimation is calculated based on a medium-scale demo as follows:

- Number of users: approximately 5–10 users.
- Number of diagram uploads: approximately 200–300 diagrams/month.
- Average diagram size: approximately 3–5 MB.
- Number of generated PDF reports: approximately 200–300 reports/month.
- Number of review workflow executions: approximately 200–300 executions/month.
- Number of API requests: approximately 5,000–15,000 requests/month.
- Each workflow includes the following steps: upload diagram, store metadata, trigger workflow, extract diagram information, analyze using AI, generate PDF report, store report, and send notification.
- Amazon Bedrock is used for architecture analysis at a demo level, not for large production traffic.

### Estimated Infrastructure Costs

- **Amazon S3**: approximately **0.10–0.50 USD/month**  
  Used to store React frontend build files, uploaded diagrams, and generated PDF reports. With only a few GB of storage in the demo stage, S3 cost remains very low.

- **Amazon CloudFront**: approximately **0.00–1.00 USD/month**  
  Used to distribute the frontend web application. With medium demo traffic, CloudFront cost is usually low because data transfer volume is limited.

- **Amazon API Gateway**: approximately **0.05–0.20 USD/month**  
  Used to handle API requests such as `POST /upload`, `GET /reviews`, `GET /reviews/{reviewId}`, and `GET /reviews/{reviewId}/status`.

- **AWS Lambda**: approximately **0.00–0.50 USD/month**  
  Used to process uploads, validate files, write metadata, extract diagram information, and generate PDF reports. With demo-level request volume, Lambda cost is very low.

- **Amazon DynamoDB**: approximately **0.05–0.30 USD/month**  
  Used to store review metadata, review history, and review status. Since each review record is small, DynamoDB cost remains low during the demo stage.

- **Amazon EventBridge**: approximately **0.01–0.05 USD/month**  
  Used to route S3 object-created events and trigger the workflow after a user uploads a diagram.

- **AWS Step Functions**: approximately **0.00–0.30 USD/month**  
  Used to orchestrate the review workflow. With approximately 200–300 workflow executions per month, Step Functions cost remains very low if the number of state transitions is not too high.

- **Amazon SNS**: approximately **0.00–0.10 USD/month**  
  Used to send email notifications when the review process is completed.

- **Amazon CloudWatch**: approximately **0.50–2.00 USD/month**  
  Used to store logs and support monitoring for Lambda, API Gateway, and Step Functions. CloudWatch cost depends on the amount of logs generated during testing and debugging.

- **Amazon Bedrock**: approximately **5.00–30.00 USD/month**  
  Used to analyze AWS architecture diagrams using AI. This is the most variable cost component because it depends on the selected model, the number of input/output tokens, and the number of AI requests. If a smaller model is used or prompt length is limited, the cost will be lower. If a stronger model is used or the generated analysis report is detailed and long, the cost may increase significantly.

### Total Estimated Cost

For a medium-scale demo, the estimated total infrastructure cost is approximately:

**10–35 USD/month**

Equivalent to approximately:

**120–420 USD/year**

The basic serverless services such as S3, CloudFront, API Gateway, Lambda, DynamoDB, EventBridge, Step Functions, and SNS contribute relatively low costs. The main cost driver is **Amazon Bedrock**, because AI cost directly depends on the selected model, token usage, and number of reviews.

### Notes

The estimated cost above is only for the MVP and medium demo stage. In a real deployment, the final budget should be recalculated using AWS Pricing Calculator based on the selected AWS Region, number of uploads, file size, number of workflow executions, number of Amazon Bedrock requests, Lambda execution duration, Step Functions state transitions, and CloudWatch Logs retention period.

To control cost, the system should limit upload file size, limit the number of AI requests, select an appropriate Bedrock model, reduce prompt length, minimize unnecessary logs, and use AWS Budgets to monitor monthly spending.

---

### 7. Risk Assessment

#### Risk Matrix

- Invalid or unsupported diagram format: Medium impact, medium probability.
- AI review result is inaccurate or incomplete: High impact, medium probability.
- Workflow failure during extraction or report generation: Medium impact, medium probability.
- CORS issues between CloudFront and API Gateway: Medium impact, medium probability.
- CloudFront cache serving an old frontend build: Low to medium impact, medium probability.
- IAM permissions are too broad or too restrictive: High impact, medium probability.
- Amazon Bedrock cost increases due to high token usage: Medium impact, low probability.

#### Mitigation Strategies

- Validate file type and file size before storing uploads.
- Use structured prompts for Amazon Bedrock.
- Use Step Functions retry and error handling.
- Store workflow status in DynamoDB.
- Configure CORS correctly for localhost and CloudFront domain.
- Create CloudFront invalidation after each frontend deployment.
- Apply least privilege IAM policies.
- Monitor Lambda, API Gateway, Step Functions, and Bedrock usage through CloudWatch.
- Use AWS Budgets to track estimated monthly cost.

#### Contingency Plans

- If AI analysis fails, mark the review status as failed in DynamoDB.
- If PDF generation fails, keep the AI review result and retry PDF generation.
- If SNS email fails, allow users to view the report directly from the web application.
- If CloudFront serves old files, create invalidation and redeploy the frontend.
- If Bedrock usage becomes expensive, limit input size or reduce the number of review requests.

---

### 8. Expected Outcomes

#### Technical Improvements

The project is expected to deliver a working AWS serverless platform that allows users to upload architecture diagrams and receive AI-assisted architecture review results.

Expected technical outcomes include:

- A working React web application hosted on S3 and delivered through CloudFront.
- Secure frontend delivery using CloudFront OAC and private S3 bucket access.
- API Gateway routes for upload and review data retrieval.
- Lambda Upload Service for file validation, S3 storage, and DynamoDB metadata.
- S3 Input Bucket for uploaded architecture diagrams.
- DynamoDB Review Database for review history and status tracking.
- EventBridge and Step Functions workflow for automated review processing.
- Lambda Diagram Extractor for extracting AWS services and connections.
- Amazon Bedrock integration for AI-based review using AWS Well-Architected Framework.
- PDF report generation and storage in S3 Report Bucket.
- SNS email notification when the review is completed.
- CloudWatch monitoring and IAM least privilege security.

#### Long-term Value

The platform can be reused as a learning tool for AWS architecture design and Well-Architected review practice. It can also be extended into a more advanced cloud architecture assessment system with features such as user authentication, multi-user review history, architecture scoring, advanced report templates, and support for more diagram formats.

The project provides practical experience with important AWS services, including CloudFront, S3, API Gateway, Lambda, DynamoDB, EventBridge, Step Functions, Amazon Bedrock, SNS, CloudWatch, and IAM.