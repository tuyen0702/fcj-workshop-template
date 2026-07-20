---
title : "Workshop Overview"
date : 2026-07-03 
weight : 1 
chapter : false
pre : " <b> 5.1. </b> "
---

#### AI AWS Architecture Reviewer

+ **AI AWS Architecture Reviewer** is a serverless web application that helps users upload AWS architecture diagrams and receive AI-supported architecture review results based on the **AWS Well-Architected Framework**.
+ The system allows users to submit architecture diagrams through a React frontend, store uploaded files in Amazon S3, store metadata and review status for each review in Amazon DynamoDB, and process the review workflow using serverless services on AWS.
+ The system is designed using a **serverless event-driven architecture**, where AWS services work together through events, workflows, and Lambda functions to automate the architecture review process.
+ The key point of the AI workflow is that the system not only analyzes architecture diagrams, but also generates **architecture JSON**, estimates **monthly cost**, evaluates the architecture based on the pillars of the AWS Well-Architected Framework, and creates a PDF report for the user.
+ The main goal of this workshop is to document the process of deploying the website and backend services on AWS, including frontend hosting, upload processing, review data integration, event-driven workflow, AI analysis, cost estimation, report generation, notification, monitoring, and security.

---

#### Workshop Overview

In this workshop, the **AI AWS Architecture Reviewer** system will be built and deployed step by step, from frontend, upload backend, data storage, automated processing workflow, AI review, cost estimation, PDF report generation, to email notification.

+ **Frontend Layer** uses Amazon S3 and Amazon CloudFront to host and distribute the React web application. Users access the website through CloudFront, while the React production build is stored in the S3 frontend bucket.
+ **API and Upload Layer** uses Amazon API Gateway and AWS Lambda Upload Service to receive upload requests, validate architecture diagram files, create review IDs, store uploaded diagrams in the Amazon S3 Input Bucket, and store metadata in Amazon DynamoDB.
+ **Review Data Layer** uses Amazon DynamoDB to store review information such as review ID, file name, file type, file size, upload date, review status, S3 input bucket, S3 object key, report path, and review result information.
+ **Event-Driven Workflow Layer** uses Amazon EventBridge and AWS Step Functions to start the review workflow after a diagram is uploaded to the S3 Input Bucket. When S3 generates an Object Created Event, EventBridge captures this event and triggers the Step Functions Review Workflow.
+ **AI Processing Layer** uses AWS Lambda AI Analyze and Amazon Bedrock. Lambda AI Analyze reads the uploaded diagram from the S3 Input Bucket, then sends the diagram to Amazon Bedrock so that Bedrock can identify AWS services, connections, text notes, and generate a structured architecture JSON.
+ **Cost Analysis Layer** uses AWS Lambda Cost Tool to receive the architecture JSON, analyze the AWS services detected in the diagram, and estimate monthly cost based on demo-level usage assumptions.
+ **Final AI Review Layer** continues to use Amazon Bedrock to receive the architecture JSON and cost estimation result, then perform a comprehensive architecture review based on the AWS Well-Architected Framework, explain costs, identify risks, and recommend optimization improvements.
+ **Reporting and Notification Layer** uses AWS Lambda PDF Generator to create the PDF review report, Amazon S3 Report Bucket to store the generated report, and Amazon SNS to send an email notification after the review is completed.
+ **Monitoring and Security Layer** uses Amazon CloudWatch for logging, metrics tracking, and troubleshooting support. AWS IAM is used to apply least privilege access between AWS services.

The architecture below shows the overall workflow of the AI AWS Architecture Reviewer system, from the user accessing the website, uploading a diagram, processing AI analysis, estimating cost, generating a report, storing review history, to sending an email notification.

![AI AWS Architecture Reviewer Overview](/images/5-Workshop/5.1-Workshop-overview/ai-aws-architecture-reviewer-overview.jpg)