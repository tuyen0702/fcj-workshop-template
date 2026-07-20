---
title: "Monitoring với CloudWatch, SNS Alert và IAM Least Privilege"
date: 2026-07-03
weight: 7
chapter: false
pre: " <b> 5.7. </b> "
---

#### Tổng quan

Trong phần này, hệ thống **AI AWS Architecture Reviewer** được bổ sung khả năng giám sát và cảnh báo vận hành bằng **Amazon CloudWatch** và **Amazon SNS**. Amazon CloudWatch được sử dụng để ghi logs, theo dõi metrics và tạo alarm cho các thành phần quan trọng như Lambda, API Gateway, Step Functions, DynamoDB và EventBridge.

Amazon SNS trong dự án này **không được sử dụng để gửi email khi từng review hoàn tất**. Thay vào đó, SNS được tích hợp với CloudWatch Alarm để gửi email cảnh báo khi hệ thống phát sinh lỗi quan trọng.

Luồng cảnh báo của hệ thống:

```text
AWS Service Error
→ CloudWatch Metrics / Logs
→ CloudWatch Alarm
→ Amazon SNS Topic
→ Email Alert
```

SNS Topic được sử dụng:

```text
Topic name: ai-aws-reviewer-notification-topic
Region: ap-southeast-1
Topic ARN: arn:aws:sns:ap-southeast-1:675492141438:ai-aws-reviewer-notification-topic
Email nhận cảnh báo: totrungkiet261023@gmail.com
```

---

#### Mục tiêu

Sau khi hoàn thành phần này, hệ thống có thể:

- Ghi logs cho các Lambda functions bằng Amazon CloudWatch Logs.
- Theo dõi metrics của Lambda, API Gateway, Step Functions, DynamoDB và EventBridge.
- Tạo CloudWatch Alarm để phát hiện lỗi quan trọng.
- Gửi cảnh báo lỗi từ CloudWatch Alarm đến Amazon SNS Topic.
- Gửi email cảnh báo đến địa chỉ đã đăng ký và xác nhận subscription.
- Kiểm tra IAM permissions theo nguyên tắc least privilege access.
- Đảm bảo SNS chỉ phục vụ monitoring alert, không gửi email khi review hoàn tất.

---

#### Bước 1: Kiểm tra SNS Topic

Truy cập Amazon SNS để kiểm tra topic:

```text
Amazon SNS
→ Topics
→ ai-aws-reviewer-notification-topic
```

Cần kiểm tra:

- Topic tồn tại trong region `ap-southeast-1`.
- Topic ARN đúng với cấu hình CloudWatch Alarm.
- Topic có email subscription đã confirmed.

Có thể kiểm tra bằng AWS CLI:

```powershell
aws sns get-topic-attributes `
  --topic-arn arn:aws:sns:ap-southeast-1:675492141438:ai-aws-reviewer-notification-topic `
  --region ap-southeast-1
```

![SNS Topic](/images/5-Workshop/5.7-Monitoring-security/sns-topic.png)

---

#### Bước 2: Subscribe email vào SNS Topic

Thêm email nhận cảnh báo vào SNS Topic:

```powershell
aws sns subscribe `
  --topic-arn arn:aws:sns:ap-southeast-1:675492141438:ai-aws-reviewer-notification-topic `
  --protocol email `
  --notification-endpoint totrungkiet261023@gmail.com `
  --region ap-southeast-1
```

Sau khi subscribe, AWS sẽ gửi email xác nhận đến Gmail. Người nhận cần mở email và bấm **Confirm subscription**.

Nếu chưa xác nhận, subscription sẽ có trạng thái:

```text
PendingConfirmation
```

Email ở trạng thái này sẽ chưa nhận được cảnh báo.

![Confirm subscription](/images/5-Workshop/5.7-Monitoring-security/confirm-subscription.png)

---

#### Bước 3: Kiểm tra trạng thái subscription

Kiểm tra danh sách subscription của SNS Topic:

```powershell
aws sns list-subscriptions-by-topic `
  --topic-arn arn:aws:sns:ap-southeast-1:675492141438:ai-aws-reviewer-notification-topic `
  --region ap-southeast-1
```

Kết quả hợp lệ cần có:

```text
Protocol: email
Endpoint: totrungkiet261023@gmail.com
SubscriptionArn: arn:aws:sns:...
```

Nếu `SubscriptionArn` là ARN hợp lệ, email đã confirmed thành công.

---

#### Bước 4: Test gửi email bằng SNS

Gửi thử một email test thông qua SNS:

```powershell
aws sns publish `
  --topic-arn arn:aws:sns:ap-southeast-1:675492141438:ai-aws-reviewer-notification-topic `
  --subject "Test AI AWS Architecture Reviewer Monitoring Alert" `
  --message "This is a test SNS monitoring alert for AI AWS Architecture Reviewer." `
  --region ap-southeast-1
```

Nếu Gmail nhận được email test, SNS Topic đã hoạt động đúng.

![Test](/images/5-Workshop/5.7-Monitoring-security/test.png)

---

#### Bước 5: Tạo CloudWatch Alarm cho Step Functions

Step Functions điều phối toàn bộ workflow xử lý review. Vì vậy, cần tạo alarm cho các trạng thái lỗi chính.

Các alarm được tạo:

```text
Architecture-review-workflow-Failed-Alarm
Architecture-review-workflow-TimedOut-Alarm
Architecture-review-workflow-Aborted-Alarm
```

Các metric giám sát:

| Alarm | Metric | Điều kiện |
|---|---|---|
| Failed Alarm | ExecutionsFailed | >= 1 trong 5 phút |
| TimedOut Alarm | ExecutionsTimedOut | >= 1 trong 5 phút |
| Aborted Alarm | ExecutionsAborted | >= 1 trong 5 phút |

Khi workflow bị failed, timed out hoặc aborted, CloudWatch Alarm sẽ gửi cảnh báo đến SNS Topic.

![Architecture-review-workflow](/images/5-Workshop/5.7-Monitoring-security/Architecture-review-workflow.png)

---

#### Bước 6: Tạo CloudWatch Alarm cho Lambda Functions

Các Lambda chính cần giám sát:

```text
ai-aws-reviewer-upload-service
aws-reviewer-ai-analyzer
aws-reviewer-cost-tool
aws-reviewer-pdf-generator
```

Với mỗi Lambda, tạo các alarm sau:

| Alarm | Metric | Mục đích |
|---|---|---|
| Errors Alarm | Errors | Phát hiện Lambda chạy lỗi |
| Throttles Alarm | Throttles | Phát hiện Lambda bị giới hạn invocation |
| Duration Alarm | Duration | Phát hiện Lambda chạy quá lâu hoặc gần timeout |

Ví dụ tên alarm:

```text
ai-aws-reviewer-upload-service-Errors-Alarm
aws-reviewer-ai-analyzer-Errors-Alarm
aws-reviewer-cost-tool-Errors-Alarm
aws-reviewer-pdf-generator-Errors-Alarm
```

Ngưỡng đề xuất:

```text
Errors >= 1 trong 5 phút
Throttles >= 1 trong 5 phút
Duration >= 80% timeout của Lambda
```
![Errors-Alarm](/images/5-Workshop/5.7-Monitoring-security/Errors-Alarm.png)

---

#### Bước 7: Tạo Log Metric Filter cho Lambda Logs

Ngoài metric mặc định, hệ thống tạo thêm CloudWatch Logs Metric Filter để phát hiện lỗi trong log.

Các log group cần theo dõi:

```text
/aws/lambda/ai-aws-reviewer-upload-service
/aws/lambda/aws-reviewer-ai-analyzer
/aws/lambda/aws-reviewer-cost-tool
/aws/lambda/aws-reviewer-pdf-generator
```

Các từ khóa lỗi cần phát hiện:

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

Khi log có lỗi quan trọng, Metric Filter tạo custom metric và CloudWatch Alarm có thể gửi cảnh báo qua SNS.

![Log Metric Filter](/images/5-Workshop/5.7-Monitoring-security/Log-Metric-Filter.png)

---

#### Bước 8: Tạo CloudWatch Alarm cho API Gateway

API Gateway là nơi frontend gọi backend API. Nếu API Gateway lỗi, người dùng có thể không upload được file, không xem được review history hoặc không tải được kết quả review.

Các alarm được tạo:

```text
AIArchitectureReviewer-APIGateway-5XX-Alarm
AIArchitectureReviewer-APIGateway-4XX-Alarm
AIArchitectureReviewer-APIGateway-Latency-Alarm
```

Cấu hình đề xuất:

| Alarm | Metric | Điều kiện |
|---|---|---|
| 5XX Alarm | 5XXError | >= 1 trong 5 phút |
| 4XX Alarm | 4XXError | >= 5 trong 5 phút |
| Latency Alarm | Latency | >= 5000 ms trong 5 phút |

Không nên đặt ngưỡng `4XXError >= 1`, vì người dùng gửi request sai cũng có thể tạo ra lỗi 4XX.

![AIArchitectureReviewer-APIGateway](/images/5-Workshop/5.7-Monitoring-security/AIArchitectureReviewer-APIGateway.png)

---

#### Bước 9: Tạo CloudWatch Alarm cho DynamoDB

DynamoDB table được sử dụng trong hệ thống:

```text
AIArchitectureReviews
```

Các alarm được tạo:

```text
AIArchitectureReviews-DynamoDB-SystemErrors-Alarm
AIArchitectureReviews-DynamoDB-ThrottledRequests-Alarm
```

Các metric giám sát:

| Alarm | Metric | Điều kiện |
|---|---|---|
| System Errors | SystemErrors | >= 1 trong 5 phút |
| Throttled Requests | ThrottledRequests | >= 1 trong 5 phút |

Nếu DynamoDB lỗi, workflow có thể không cập nhật được review status hoặc frontend không đọc được dữ liệu review.

![AIArchitectureReviews-DynamoDB](/images/5-Workshop/5.7-Monitoring-security/AIArchitectureReviews-DynamoDB.png)

---

#### Bước 10: Tạo CloudWatch Alarm cho EventBridge

EventBridge nhận S3 Object Created Event và kích hoạt Step Functions Review Workflow.

Alarm được tạo:

```text
AIArchitectureReviewer-EventBridge-FailedInvocations-Alarm
```

Metric:

```text
FailedInvocations
```

Điều kiện:

```text
FailedInvocations >= 1 trong 5 phút
```

Nếu EventBridge failed invocation, file có thể đã upload vào S3 nhưng workflow không được kích hoạt.

![AIArchitectureReviewer-EventBridge-FailedInvocations-Alarm](/images/5-Workshop/5.7-Monitoring-security/AIArchitectureReviewer-EventBridge-FailedInvocations-Alarm.png)

---

#### Bước 11: Giám sát S3 và Bedrock

Trong phần này, Amazon S3 và Amazon Bedrock được giám sát gián tiếp thông qua Lambda Logs, Lambda Errors và Step Functions Failed Alarm.

Ví dụ lỗi S3:

```text
Lambda AI Analyzer không đọc được file từ S3
→ CloudWatch Logs ghi lỗi
→ Metric Filter phát hiện lỗi
→ CloudWatch Alarm gửi cảnh báo đến SNS
```

Ví dụ lỗi Bedrock:

```text
Amazon Bedrock trả về ValidationException hoặc timeout
→ Lambda AI Analyzer ghi lỗi
→ Step Functions có thể failed
→ CloudWatch Alarm gửi cảnh báo qua SNS
```

S3 Request Metrics chưa được bật để tránh cấu hình phức tạp không cần thiết trong giai đoạn demo.

---

#### Bước 12: Kiểm tra Alarm Action

Tất cả CloudWatch Alarm cần trỏ về SNS Topic:

```text
arn:aws:sns:ap-southeast-1:675492141438:ai-aws-reviewer-notification-topic
```

Kiểm tra trong AWS Console:

```text
CloudWatch
→ Alarms
→ All alarms
→ Chọn alarm
→ Actions
```

Alarm action phải trỏ đến SNS Topic `ai-aws-reviewer-notification-topic`.

---

#### Bước 13: Kiểm tra email cảnh báo

Khi alarm chuyển sang trạng thái `ALARM`, Gmail sẽ nhận được email từ AWS Notifications.

Ví dụ tiêu đề email:

```text
ALARM: "Architecture-review-workflow-Failed-Alarm" in Asia Pacific (Singapore)
```

Email cảnh báo thường bao gồm:

- Alarm name.
- State change.
- Reason for state change.
- Metric name.
- Threshold.
- Timestamp.
- Link mở alarm trong AWS Console.

---

#### Bước 14: Kiểm tra IAM Least Privilege

Các IAM Role cần được kiểm tra theo nguyên tắc **least privilege access**. Mỗi Lambda chỉ nên có quyền cần thiết cho nhiệm vụ của nó.

**Lambda Upload Service** cần quyền:
![Lambda-Upload-Service](/images/5-Workshop/5.7-Monitoring-security/Lambda-Upload-Service.png)
![Lambda-Upload-Service-Policy](/images/5-Workshop/5.7-Monitoring-security/Lambda-Upload-Service-Policy.png)

**Lambda AI Analyzer** cần quyền:

![Lambda-AI-Analyzer](/images/5-Workshop/5.7-Monitoring-security/Lambda-AI-Analyzer.png)
![Lambda-AI-Analyzer-Policy](/images/5-Workshop/5.7-Monitoring-security/Lambda-AI-Analyzer-Policy.png)

**Lambda Cost Tool** cần quyền:

![Lambda-Cost-Tool](/images/5-Workshop/5.7-Monitoring-security/Lambda-Cost-Tool.png)
![Lambda-Cost-Tool-Policy](/images/5-Workshop/5.7-Monitoring-security/Lambda-Cost-Tool-Policy.png)

**Lambda PDF Generator** cần quyền:

![Lambda-PDF-Generator](/images/5-Workshop/5.7-Monitoring-security/Lambda-PDF-Generator.png)
![Lambda-PDF-Generator-Policy](/images/5-Workshop/5.7-Monitoring-security/Lambda-PDF-Generator-Policy.png)

---

#### Kết quả sau khi hoàn thành

Sau khi hoàn thành phần này, hệ thống đạt được các kết quả sau:

- SNS Topic được cấu hình để nhận cảnh báo từ CloudWatch Alarm.
- Email `totrungkiet261023@gmail.com` đã subscribe và confirmed.
- SNS publish test gửi email thành công.
- CloudWatch Alarm được tạo cho Step Functions.
- CloudWatch Alarm được tạo cho các Lambda functions.
- CloudWatch Alarm được tạo cho API Gateway.
- CloudWatch Alarm được tạo cho DynamoDB.
- CloudWatch Alarm được tạo cho EventBridge.
- CloudWatch Logs Metric Filter được tạo để phát hiện lỗi trong Lambda logs.
- Các lỗi từ S3 và Bedrock được phát hiện gián tiếp thông qua Lambda và Step Functions.
- IAM permissions được kiểm tra theo nguyên tắc least privilege access.

---

#### Tổng kết

Trong phần này, hệ thống **AI AWS Architecture Reviewer** đã được bổ sung khả năng monitoring và alerting bằng Amazon CloudWatch và Amazon SNS. CloudWatch ghi logs, theo dõi metrics và tạo alarms cho các thành phần quan trọng như Lambda, API Gateway, Step Functions, DynamoDB và EventBridge.

Khi hệ thống phát sinh lỗi, CloudWatch Alarm sẽ gửi cảnh báo đến SNS Topic `ai-aws-reviewer-notification-topic`. Amazon SNS sau đó gửi email cảnh báo đến địa chỉ đã đăng ký và xác nhận subscription.

Trong kiến trúc hiện tại, SNS chỉ phục vụ monitoring alert. Workflow chính kết thúc sau khi Lambda PDF Generator tạo báo cáo PDF, lưu báo cáo vào S3 Report Bucket, cập nhật DynamoDB và cho phép người dùng tải PDF thành công.