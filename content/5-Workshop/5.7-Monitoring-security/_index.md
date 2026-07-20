---
title: "Monitoring with CloudWatch, SNS Alert and IAM Least Privilege"
date: 2026-07-03
weight: 7
chapter: false
pre: " <b> 5.7. </b> "
---

#### Overview

In this section, the **AI AWS Architecture Reviewer** system is enhanced with operational monitoring and alerting using **Amazon CloudWatch** and **Amazon SNS**. Amazon CloudWatch is used to record logs, monitor metrics, and create alarms for important components such as Lambda, API Gateway, Step Functions, DynamoDB, and EventBridge.

In this project, Amazon SNS is **not used to send an email when each review is completed**. Instead, SNS is integrated with CloudWatch Alarm to send alert emails when the system encounters important errors.

The system alert flow is:

```text
AWS Service Error
→ CloudWatch Metrics / Logs
→ CloudWatch Alarm
→ Amazon SNS Topic
→ Email Alert
```

The SNS Topic used in this project:

```text
Topic name: ai-aws-reviewer-notification-topic
Region: ap-southeast-1
Topic ARN: arn:aws:sns:ap-southeast-1:675492141438:ai-aws-reviewer-notification-topic
Alert recipient email: totrungkiet261023@gmail.com
```

---

#### Objectives

After completing this section, the system can:

- Record logs for Lambda functions using Amazon CloudWatch Logs.
- Monitor metrics for Lambda, API Gateway, Step Functions, DynamoDB, and EventBridge.
- Create CloudWatch Alarms to detect important errors.
- Send error alerts from CloudWatch Alarm to an Amazon SNS Topic.
- Send alert emails to the subscribed and confirmed email address.
- Review IAM permissions based on the principle of least privilege access.
- Ensure that SNS is used only for monitoring alerts and not for sending emails when a review is completed.

---

#### Step 1: Check the SNS Topic

Access Amazon SNS to check the topic:

```text
Amazon SNS
→ Topics
→ ai-aws-reviewer-notification-topic
```

Check the following information:

- The topic exists in the `ap-southeast-1` region.
- The Topic ARN matches the CloudWatch Alarm configuration.
- The topic has a confirmed email subscription.

You can also check the topic using AWS CLI:

```powershell
aws sns get-topic-attributes `
  --topic-arn arn:aws:sns:ap-southeast-1:675492141438:ai-aws-reviewer-notification-topic `
  --region ap-southeast-1
```

![SNS Topic](/images/5-Workshop/5.7-Monitoring-security/sns-topic.png)

---

#### Step 2: Subscribe an Email to the SNS Topic

Add the alert recipient email to the SNS Topic:

```powershell
aws sns subscribe `
  --topic-arn arn:aws:sns:ap-southeast-1:675492141438:ai-aws-reviewer-notification-topic `
  --protocol email `
  --notification-endpoint totrungkiet261023@gmail.com `
  --region ap-southeast-1
```

After the subscription is created, AWS sends a confirmation email to Gmail. The recipient needs to open the email and click **Confirm subscription**.

If the subscription is not confirmed, its status will be:

```text
PendingConfirmation
```

An email subscription in this state will not receive alerts.

![Confirm subscription](/images/5-Workshop/5.7-Monitoring-security/confirm-subscription.png)

---

#### Step 3: Check the Subscription Status

Check the list of subscriptions for the SNS Topic:

```powershell
aws sns list-subscriptions-by-topic `
  --topic-arn arn:aws:sns:ap-southeast-1:675492141438:ai-aws-reviewer-notification-topic `
  --region ap-southeast-1
```

A valid result should include:

```text
Protocol: email
Endpoint: totrungkiet261023@gmail.com
SubscriptionArn: arn:aws:sns:...
```

If `SubscriptionArn` is a valid ARN, the email subscription has been confirmed successfully.

---

#### Step 4: Test Email Delivery with SNS

Send a test email through SNS:

```powershell
aws sns publish `
  --topic-arn arn:aws:sns:ap-southeast-1:675492141438:ai-aws-reviewer-notification-topic `
  --subject "Test AI AWS Architecture Reviewer Monitoring Alert" `
  --message "This is a test SNS monitoring alert for AI AWS Architecture Reviewer." `
  --region ap-southeast-1
```

If Gmail receives the test email, the SNS Topic is working correctly.

![Test](/images/5-Workshop/5.7-Monitoring-security/test.png)

---

#### Step 5: Create CloudWatch Alarms for Step Functions

Step Functions orchestrates the entire review processing workflow. Therefore, alarms need to be created for the main error states.

The following alarms are created:

```text
Architecture-review-workflow-Failed-Alarm
Architecture-review-workflow-TimedOut-Alarm
Architecture-review-workflow-Aborted-Alarm
```

The monitored metrics are:

| Alarm | Metric | Condition |
|---|---|---|
| Failed Alarm | ExecutionsFailed | >= 1 within 5 minutes |
| TimedOut Alarm | ExecutionsTimedOut | >= 1 within 5 minutes |
| Aborted Alarm | ExecutionsAborted | >= 1 within 5 minutes |

When the workflow fails, times out, or is aborted, CloudWatch Alarm sends an alert to the SNS Topic.

![Architecture-review-workflow](/images/5-Workshop/5.7-Monitoring-security/Architecture-review-workflow.png)

---

#### Step 6: Create CloudWatch Alarms for Lambda Functions

The main Lambda functions that need to be monitored are:

```text
ai-aws-reviewer-upload-service
aws-reviewer-ai-analyzer
aws-reviewer-cost-tool
aws-reviewer-pdf-generator
```

For each Lambda function, create the following alarms:

| Alarm | Metric | Purpose |
|---|---|---|
| Errors Alarm | Errors | Detects Lambda execution errors |
| Throttles Alarm | Throttles | Detects Lambda invocation throttling |
| Duration Alarm | Duration | Detects long-running Lambda executions or executions close to timeout |

Example alarm names:

```text
ai-aws-reviewer-upload-service-Errors-Alarm
aws-reviewer-ai-analyzer-Errors-Alarm
aws-reviewer-cost-tool-Errors-Alarm
aws-reviewer-pdf-generator-Errors-Alarm
```

Recommended thresholds:

```text
Errors >= 1 within 5 minutes
Throttles >= 1 within 5 minutes
Duration >= 80% of the Lambda timeout
```

![Errors-Alarm](/images/5-Workshop/5.7-Monitoring-security/Errors-Alarm.png)

---

#### Step 7: Create Log Metric Filters for Lambda Logs

In addition to default metrics, the system creates CloudWatch Logs Metric Filters to detect errors from log content.

The log groups to monitor are:

```text
/aws/lambda/ai-aws-reviewer-upload-service
/aws/lambda/aws-reviewer-ai-analyzer
/aws/lambda/aws-reviewer-cost-tool
/aws/lambda/aws-reviewer-pdf-generator
```

The important error keywords to detect are:

```text
ERROR
Exception
Traceback
ValidationException
AccessDenied
ThrottlingException
Timeout
Bedrock
DynamoDB
S3
```

When an important error appears in the logs, the Metric Filter creates a custom metric, and CloudWatch Alarm can send an alert through SNS.

![Log Metric Filter](/images/5-Workshop/5.7-Monitoring-security/Log-Metric-Filter.png)

---

#### Step 8: Create CloudWatch Alarms for API Gateway

API Gateway is where the frontend calls the backend APIs. If API Gateway has issues, users may not be able to upload files, view review history, or retrieve review results.

The following alarms are created:

```text
AIArchitectureReviewer-APIGateway-5XX-Alarm
AIArchitectureReviewer-APIGateway-4XX-Alarm
AIArchitectureReviewer-APIGateway-Latency-Alarm
```

Recommended configuration:

| Alarm | Metric | Condition |
|---|---|---|
| 5XX Alarm | 5XXError | >= 1 within 5 minutes |
| 4XX Alarm | 4XXError | >= 5 within 5 minutes |
| Latency Alarm | Latency | >= 5000 ms within 5 minutes |

The threshold `4XXError >= 1` should not be used because invalid user requests may also generate 4XX errors.

![AIArchitectureReviewer-APIGateway](/images/5-Workshop/5.7-Monitoring-security/AIArchitectureReviewer-APIGateway.png)

---

#### Step 9: Create CloudWatch Alarms for DynamoDB

The DynamoDB table used in the system is:

```text
AIArchitectureReviews
```

The following alarms are created:

```text
AIArchitectureReviews-DynamoDB-SystemErrors-Alarm
AIArchitectureReviews-DynamoDB-ThrottledRequests-Alarm
```

The monitored metrics are:

| Alarm | Metric | Condition |
|---|---|---|
| System Errors | SystemErrors | >= 1 within 5 minutes |
| Throttled Requests | ThrottledRequests | >= 1 within 5 minutes |

If DynamoDB has issues, the workflow may fail to update the review status, or the frontend may not be able to read review data.

![AIArchitectureReviews-DynamoDB](/images/5-Workshop/5.7-Monitoring-security/AIArchitectureReviews-DynamoDB.png)

---

#### Step 10: Create a CloudWatch Alarm for EventBridge

EventBridge receives the S3 Object Created Event and triggers the Step Functions Review Workflow.

The following alarm is created:

```text
AIArchitectureReviewer-EventBridge-FailedInvocations-Alarm
```

Metric:

```text
FailedInvocations
```

Condition:

```text
FailedInvocations >= 1 within 5 minutes
```

If EventBridge failed invocation occurs, the file may already be uploaded to S3, but the workflow may not be triggered.

![AIArchitectureReviewer-EventBridge-FailedInvocations-Alarm](/images/5-Workshop/5.7-Monitoring-security/AIArchitectureReviewer-EventBridge-FailedInvocations-Alarm.png)

---

#### Step 11: Monitor S3 and Bedrock

In this section, Amazon S3 and Amazon Bedrock are monitored indirectly through Lambda Logs, Lambda Errors, and Step Functions Failed Alarm.

Example S3 error:

```text
Lambda AI Analyzer cannot read a file from S3
→ CloudWatch Logs records the error
→ Metric Filter detects the error
→ CloudWatch Alarm sends an alert to SNS
```

Example Bedrock error:

```text
Amazon Bedrock returns ValidationException or timeout
→ Lambda AI Analyzer records the error
→ Step Functions may fail
→ CloudWatch Alarm sends an alert through SNS
```

S3 Request Metrics are not enabled in order to avoid unnecessary configuration complexity during the demo stage.

---

#### Step 12: Check Alarm Actions

All CloudWatch Alarms must point to the SNS Topic:

```text
arn:aws:sns:ap-southeast-1:675492141438:ai-aws-reviewer-notification-topic
```

Check this in the AWS Console:

```text
CloudWatch
→ Alarms
→ All alarms
→ Select an alarm
→ Actions
```

The alarm action must point to the SNS Topic `ai-aws-reviewer-notification-topic`.

---

#### Step 13: Check Alert Emails

When an alarm changes to the `ALARM` state, Gmail receives an email from AWS Notifications.

Example email subject:

```text
ALARM: "Architecture-review-workflow-Failed-Alarm" in Asia Pacific (Singapore)
```

The alert email usually includes:

- Alarm name.
- State change.
- Reason for state change.
- Metric name.
- Threshold.
- Timestamp.
- Link to open the alarm in the AWS Console.

---

#### Step 14: Review IAM Least Privilege

IAM roles need to be reviewed based on the principle of **least privilege access**. Each Lambda function should only have the permissions required for its responsibility.

**Lambda Upload Service** requires the following permissions:

![Lambda-Upload-Service](/images/5-Workshop/5.7-Monitoring-security/Lambda-Upload-Service.png)

![Lambda-Upload-Service-Policy](/images/5-Workshop/5.7-Monitoring-security/Lambda-Upload-Service-Policy.png)

**Lambda AI Analyzer** requires the following permissions:

![Lambda-AI-Analyzer](/images/5-Workshop/5.7-Monitoring-security/Lambda-AI-Analyzer.png)

![Lambda-AI-Analyzer-Policy](/images/5-Workshop/5.7-Monitoring-security/Lambda-AI-Analyzer-Policy.png)

**Lambda Cost Tool** requires the following permissions:

![Lambda-Cost-Tool](/images/5-Workshop/5.7-Monitoring-security/Lambda-Cost-Tool.png)

![Lambda-Cost-Tool-Policy](/images/5-Workshop/5.7-Monitoring-security/Lambda-Cost-Tool-Policy.png)

**Lambda PDF Generator** requires the following permissions:

![Lambda-PDF-Generator](/images/5-Workshop/5.7-Monitoring-security/Lambda-PDF-Generator.png)

![Lambda-PDF-Generator-Policy](/images/5-Workshop/5.7-Monitoring-security/Lambda-PDF-Generator-Policy.png)

---

#### Results After Completion

After completing this section, the system achieves the following results:

- The SNS Topic is configured to receive alerts from CloudWatch Alarm.
- The email `totrungkiet261023@gmail.com` has been subscribed and confirmed.
- The SNS publish test sends an email successfully.
- CloudWatch Alarms are created for Step Functions.
- CloudWatch Alarms are created for the Lambda functions.
- CloudWatch Alarms are created for API Gateway.
- CloudWatch Alarms are created for DynamoDB.
- CloudWatch Alarms are created for EventBridge.
- CloudWatch Logs Metric Filters are created to detect errors in Lambda logs.
- Errors from S3 and Bedrock are detected indirectly through Lambda and Step Functions.
- IAM permissions are reviewed based on the principle of least privilege access.

---

#### Summary

In this section, the **AI AWS Architecture Reviewer** system has been enhanced with monitoring and alerting capabilities using Amazon CloudWatch and Amazon SNS. CloudWatch records logs, monitors metrics, and creates alarms for important components such as Lambda, API Gateway, Step Functions, DynamoDB, and EventBridge.

When the system encounters an error, CloudWatch Alarm sends an alert to the SNS Topic `ai-aws-reviewer-notification-topic`. Amazon SNS then sends the alert email to the subscribed and confirmed email address.

In the current architecture, SNS is used only for monitoring alerts. The main workflow ends after Lambda PDF Generator creates the PDF report, stores it in the S3 Report Bucket, updates DynamoDB, and allows the user to download the PDF successfully.