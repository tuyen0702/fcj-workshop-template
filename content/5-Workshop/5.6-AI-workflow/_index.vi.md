---
title : "Xây dựng AI Workflow với EventBridge, Step Functions, Bedrock và PDF Generator"
date : 2026-07-08
weight : 5
chapter : false
pre : " <b> 5.5. </b> "
---

#### Tổng quan AI Workflow

Trong phần này, **AI Workflow** của dự án **AI AWS Architecture Reviewer** được xây dựng bằng **Amazon EventBridge**, **AWS Step Functions**, **AWS Lambda**, **Amazon Bedrock**, **AWS Price List API**, **Amazon S3** và **Amazon DynamoDB**.

Sau khi người dùng upload sơ đồ kiến trúc AWS thông qua upload backend, file sẽ được lưu vào S3 Input Bucket. Sự kiện tạo object mới trong S3 sau đó được gửi sang EventBridge. EventBridge sẽ tự động kích hoạt Step Functions để bắt đầu quy trình phân tích kiến trúc.

AI Workflow chịu trách nhiệm phân tích ảnh kiến trúc đã upload, nhận diện các dịch vụ AWS, ước tính chi phí hằng tháng, tạo báo cáo đánh giá cuối cùng, lưu báo cáo vào S3 và cập nhật lịch sử review trong DynamoDB.

Luồng hoạt động của AI Workflow là:

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

Các tài nguyên AWS chính được sử dụng trong phần này gồm:

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

Source code và các file cấu hình được sử dụng trong AI Workflow được lưu trong thư mục README sau:

```text
README/ai-workflow/
```

Cách tổ chức này giúp trang workshop gọn gàng hơn, đồng thời vẫn cho phép người đọc xem lại các file JSON, biến môi trường Lambda và lệnh kiểm thử thực tế.

<details>
<summary><strong>Cấu trúc thư mục README</strong></summary>

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
<summary><strong>Bước 1: Bật EventBridge notification cho S3 Input Bucket</strong></summary>

AI Workflow bắt đầu khi một sơ đồ kiến trúc mới được upload vào S3 Input Bucket.

S3 Input Bucket được sử dụng trong dự án là:

```text
ai-aws-reviewer-input-bucket-tiersteam
```

Các file kiến trúc sau khi upload được lưu theo cấu trúc key sau:

```text
uploads/{reviewId}/{fileName}
```

Ví dụ:

```text
uploads/REV-0491BC4A/architecture-diagram.jpg
```

Để cho phép sự kiện từ S3 được gửi sang Amazon EventBridge, cần bật EventBridge notification trên S3 Input Bucket.

Mở S3 Input Bucket, vào tab **Properties**, sau đó bật:

```text
Amazon EventBridge
```

Sau khi bật tùy chọn này, các sự kiện tạo object trong bucket có thể được định tuyến sang EventBridge.

![S3 EventBridge](/images/5-Workshop/5.5-AI-workflow/s3-input-bucket-eventbridge.png)

</details>

---

<details>
<summary><strong>Bước 2: Tạo EventBridge rule cho sự kiện S3 Object Created</strong></summary>

Tạo một EventBridge rule để bắt sự kiện file mới được upload vào S3 Input Bucket.

Rule này lắng nghe loại sự kiện sau:

```text
Object Created
```

Event pattern sử dụng trong dự án được lưu trong thư mục README thay vì dán trực tiếp toàn bộ vào trang workshop.

```text
README/ai-workflow/eventbridge/eventbridge-rule-pattern.json
```

<details>
<summary><strong>Xem EventBridge event pattern</strong></summary>

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

Rule này sẽ được kích hoạt mỗi khi có file mới được upload vào input bucket.

![EventBridge Rule](/images/5-Workshop/5.5-AI-workflow/eventbridge-rule.png)

</details>

---

<details>
<summary><strong>Bước 3: Cấu hình EventBridge target</strong></summary>

Target của EventBridge rule là Step Functions state machine.

Step Functions workflow được sử dụng trong dự án là:

```text
Architecture-review-workflow
```

EventBridge truyền thông tin file đã upload sang Step Functions bằng input transformer.

Các file input transformer được lưu trong thư mục README:

```text
README/ai-workflow/eventbridge/input-transformer-paths.json
README/ai-workflow/eventbridge/input-transformer-template.json
```

<details>
<summary><strong>Xem EventBridge input transformer</strong></summary>

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

Input này giúp AI Analyzer Lambda xác định đúng bucket và object key để đọc sơ đồ kiến trúc đã upload từ S3.

![EventBridge Target](/images/5-Workshop/5.5-AI-workflow/eventbridge-target-step-functions.png)

</details>

---

<details>
<summary><strong>Bước 4: Tạo Step Functions AI Workflow</strong></summary>

Tạo một AWS Step Functions state machine để điều phối toàn bộ quá trình AI review.

Tên workflow là:

```text
Architecture-review-workflow
```

Workflow gồm ba giai đoạn xử lý chính:

```text
AnalyzeArchitectureWithAI
EstimateCost
GenerateReport
```

Vai trò của từng state:

```text
AnalyzeArchitectureWithAI:
Đọc sơ đồ kiến trúc từ S3 và sử dụng Amazon Bedrock để phân tích kiến trúc.

EstimateCost:
Sử dụng danh sách dịch vụ AWS đã phát hiện để ước tính chi phí bằng AWS Price List API.

GenerateReport:
Tạo báo cáo đánh giá cuối cùng, lưu báo cáo vào S3 và cập nhật lịch sử review trong DynamoDB.
```

![Step Functions](/images/5-Workshop/5.5-AI-workflow/architecture-review-workflow.png)

</details>

---

<details>
<summary><strong>Bước 5: Cấu hình Step Functions definition</strong></summary>

Step Functions workflow gọi lần lượt từng Lambda function trong quy trình.

Workflow definition chính được lưu trong thư mục README:

```text
README/ai-workflow/step-functions/architecture-review-workflow.asl.json
```

File này chứa định nghĩa Amazon States Language được sử dụng bởi Step Functions. Khi triển khai, copy nội dung file này vào trình chỉnh sửa definition của Step Functions.

<details>
<summary><strong>Xem Step Functions definition</strong></summary>

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
<summary><strong>Bước 6: Tạo AI Analyzer Lambda</strong></summary>

Tạo một Lambda function để phân tích sơ đồ kiến trúc đã upload.

Tên Lambda function là:

```text
aws-reviewer-ai-analyzer
```

Function này chịu trách nhiệm:

```text
Nhận S3 bucket và object key từ Step Functions.
Đọc sơ đồ kiến trúc đã upload từ S3.
Gửi ảnh kiến trúc sang Amazon Bedrock.
Phát hiện các dịch vụ AWS và kết nối trong sơ đồ.
Tạo kết quả đánh giá ban đầu theo AWS Well-Architected Framework.
Trả về dữ liệu JSON có cấu trúc cho Step Functions.
```

AI Analyzer Lambda sử dụng model Amazon Bedrock Nova để phân tích ảnh kiến trúc.

Các biến môi trường mẫu được lưu tại:

```text
README/ai-workflow/lambdas/ai-analyzer/environment.txt
```

<details>
<summary><strong>Xem biến môi trường của AI Analyzer</strong></summary>

```text
MODEL_ID = global.amazon.nova-2-lite-v1:0
BEDROCK_REGION = ap-southeast-1
```

</details>

Source code của Lambda có thể được lưu tại:

```text
README/ai-workflow/lambdas/ai-analyzer/lambda_function.py
```

Output của Lambda này bao gồm:

```text
Review ID
Source bucket
Source object key
Danh sách dịch vụ AWS phát hiện được
Các kết nối giữa dịch vụ
Kết quả đánh giá Well-Architected
Các giới hạn của quá trình phân tích
```

![AI Analyzer Lambda](/images/5-Workshop/5.5-AI-workflow/aws-reviewer-ai-analyzer.png)

</details>

---

<details>
<summary><strong>Bước 7: Tạo Cost Tool Lambda</strong></summary>

Tạo một Lambda function để ước tính chi phí hằng tháng dựa trên các dịch vụ AWS đã phát hiện.

Tên Lambda function là:

```text
aws-reviewer-cost-tool
```

Function này chịu trách nhiệm:

```text
Nhận danh sách dịch vụ đã phát hiện từ AI Analyzer Lambda.
Ánh xạ các dịch vụ đã phát hiện sang sản phẩm tương ứng trong AWS Pricing.
Gọi AWS Price List API để lấy thông tin giá.
Tính toán chi phí ước tính hằng tháng dựa trên assumption mặc định.
Sử dụng Amazon Bedrock để tạo phân tích chi phí và đề xuất tối ưu.
Trả kết quả chi phí về cho Step Functions.
```

Cost Tool không cho AI tự tạo ra giá. Thay vào đó, giá trị chi phí được tính từ dữ liệu AWS Price List API, còn Amazon Bedrock chỉ được dùng để giải thích kết quả chi phí và đưa ra đề xuất tối ưu.

Các biến môi trường mẫu được lưu tại:

```text
README/ai-workflow/lambdas/cost-tool/environment.txt
```

<details>
<summary><strong>Xem biến môi trường của Cost Tool</strong></summary>

```text
MODEL_ID = global.amazon.nova-2-lite-v1:0
BEDROCK_REGION = ap-southeast-1
DEFAULT_REGION = ap-southeast-1
```

</details>

Source code của Lambda có thể được lưu tại:

```text
README/ai-workflow/lambdas/cost-tool/lambda_function.py
```

Output của Lambda này bao gồm:

```text
Chi phí ước tính hằng tháng
Đơn vị tiền tệ
Bảng phân tích chi phí theo dịch vụ
Nguồn dữ liệu giá
Assumption sử dụng mặc định
Đề xuất tối ưu chi phí
```

![Cost Tool Lambda](/images/5-Workshop/5.5-AI-workflow/aws-reviewer-cost-tool.png)

</details>

---

<details>
<summary><strong>Bước 8: Tạo S3 Report Bucket</strong></summary>

Tạo một S3 bucket để lưu các báo cáo review được tạo ra.

S3 Report Bucket được sử dụng trong dự án là:

```text
ai-aws-reviewer-report-bucket-tiersteam
```

Các báo cáo được lưu theo cấu trúc key sau:

```text
reports/{reviewId}/report-data.json
reports/{reviewId}/report.html
reports/{reviewId}/report.pdf
```

Ví dụ:

```text
reports/REV-0491BC4A/report-data.json
reports/REV-0491BC4A/report.html
reports/REV-0491BC4A/report.pdf
```

Report bucket lưu trữ kết quả cuối cùng của AI Workflow.

![S3 Report Bucket](/images/5-Workshop/5.5-AI-workflow/s3-report-bucket.png)

</details>

---

<details>
<summary><strong>Bước 9: Tạo PDF Generator Lambda</strong></summary>

Tạo một Lambda function để tạo báo cáo đánh giá kiến trúc cuối cùng.

Tên Lambda function là:

```text
aws-reviewer-pdf-generator
```

Function này chịu trách nhiệm:

```text
Nhận kết quả phân tích kiến trúc và kết quả chi phí từ Step Functions.
Sử dụng Amazon Bedrock để tạo nội dung đánh giá cuối cùng.
Tạo file report-data.json.
Tạo file report.html.
Tạo file report.pdf bằng ReportLab.
Upload các file báo cáo vào S3 Report Bucket.
Cập nhật lịch sử review trong DynamoDB.
Trả về vị trí các file báo cáo cho Step Functions.
```

Các biến môi trường mẫu được lưu tại:

```text
README/ai-workflow/lambdas/pdf-generator/environment.txt
```

<details>
<summary><strong>Xem biến môi trường của PDF Generator</strong></summary>

```text
REPORT_BUCKET = ai-aws-reviewer-report-bucket-tiersteam
TABLE_NAME = AIArchitectureReviews
MODEL_ID = global.amazon.nova-2-lite-v1:0
BEDROCK_REGION = ap-southeast-1
```

</details>

Source code của Lambda có thể được lưu tại:

```text
README/ai-workflow/lambdas/pdf-generator/lambda_function.py
```

PDF Generator Lambda là state cuối cùng của AI Workflow.

![PDF Generator Lambda](/images/5-Workshop/5.5-AI-workflow/aws-reviewer-pdf-generator.png)

</details>

---

<details>
<summary><strong>Bước 10: Cấu hình ReportLab Layer để tạo PDF</strong></summary>

Để tạo file PDF bên trong Lambda, hệ thống sử dụng Lambda Layer để cung cấp thư viện ReportLab.

Layer bao gồm:

```text
Thư viện ReportLab
Các dependency Python cần thiết
Font hỗ trợ tiếng Việt
```

Cấu trúc layer được lưu tại:

```text
README/ai-workflow/layers/reportlab-layer-structure.txt
```

<details>
<summary><strong>Xem cấu trúc ReportLab Layer</strong></summary>

```text
python/
  reportlab/
  ...
fonts/
  DejaVuSans.ttf
  DejaVuSans-Bold.ttf
```

</details>

Các font này được dùng để hiển thị tiếng Việt chính xác trong file PDF.

Sau khi tạo layer, gắn layer này vào PDF Generator Lambda.

![ReportLab Layer](/images/5-Workshop/5.5-AI-workflow/reportlab-layer.png)

</details>

---

<details>
<summary><strong>Bước 11: Cập nhật lịch sử review trong DynamoDB</strong></summary>

Sau khi báo cáo được tạo thành công, PDF Generator Lambda cập nhật review item trong DynamoDB.

DynamoDB table được sử dụng trong dự án là:

```text
AIArchitectureReviews
```

Partition key là:

```text
reviewId
```

Khi upload backend tạo review item mới, trạng thái ban đầu là:

```text
uploaded
```

Sau khi AI Workflow hoàn tất, PDF Generator Lambda cập nhật trạng thái thành:

```text
completed
```

Review item sau khi cập nhật bao gồm:

```text
Trạng thái review
Thời gian hoàn thành
Thời gian cập nhật
Điểm đánh giá kiến trúc
Danh sách dịch vụ AWS phát hiện được
Kết quả Well-Architected
Kết quả chi phí
Các khuyến nghị
Các rủi ro
Các best practice
Vị trí các file báo cáo
```

Ví dụ item đã hoàn thành được lưu tại:

```text
README/ai-workflow/dynamodb/completed-review-example.json
```

<details>
<summary><strong>Xem ví dụ DynamoDB item sau khi hoàn thành</strong></summary>

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

Việc cập nhật này giúp React frontend hiển thị được lịch sử review và kết quả phân tích đã hoàn thành.

![DynamoDB Updated Review](/images/5-Workshop/5.5-AI-workflow/dynamodb-review-completed.png)

</details>

---

<details>
<summary><strong>Bước 12: Cấu hình IAM permissions</strong></summary>

Mỗi Lambda function và Step Functions workflow cần có IAM role với các quyền phù hợp.

AI Analyzer Lambda cần quyền:

```text
Đọc object từ S3 Input Bucket
Invoke Amazon Bedrock model
Ghi log vào CloudWatch
```

Cost Tool Lambda cần quyền:

```text
Gọi AWS Price List API
Invoke Amazon Bedrock model
Ghi log vào CloudWatch
```

PDF Generator Lambda cần quyền:

```text
Ghi report vào S3 Report Bucket
Cập nhật lịch sử review trong DynamoDB
Invoke Amazon Bedrock model
Ghi log vào CloudWatch
```

Step Functions role cần quyền:

```text
Invoke AI Analyzer Lambda
Invoke Cost Tool Lambda
Invoke PDF Generator Lambda
Ghi execution log vào CloudWatch
```

![IAM Roles](/images/5-Workshop/5.5-AI-workflow/ai-workflow-iam-roles.png)

</details>

---

<details>
<summary><strong>Bước 13: Kiểm thử AI Workflow</strong></summary>

Để kiểm thử toàn bộ AI Workflow, upload một sơ đồ kiến trúc từ frontend hoặc sử dụng upload API.

Lệnh kiểm thử upload được lưu tại:

```text
README/ai-workflow/testing/test-upload-command.md
```

<details>
<summary><strong>Xem lệnh kiểm thử upload</strong></summary>

```powershell
curl.exe -X POST "https://031hqksomd.execute-api.ap-southeast-1.amazonaws.com/upload" -F "file=@D:\Learning\AWS\test-files\architecture-1.png"
```

</details>

Nếu upload thành công, API sẽ trả về review ID:

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

Sau khi file được upload vào S3, EventBridge tự động kích hoạt Step Functions workflow.

Mở Step Functions và kiểm tra tất cả state đã chạy thành công:

```text
AnalyzeArchitectureWithAI
EstimateCost
GenerateReport
```

![Step Functions Success](/images/5-Workshop/5.5-AI-workflow/step-functions-execution-success.png)

</details>

---

<details>
<summary><strong>Bước 14: Kiểm tra báo cáo được tạo trong S3</strong></summary>

Sau khi Step Functions execution hoàn tất, mở S3 Report Bucket.

Các file báo cáo sẽ được lưu dưới prefix:

```text
reports/{reviewId}/
```

Ví dụ:

```text
reports/REV-0491BC4A/report-data.json
reports/REV-0491BC4A/report.html
reports/REV-0491BC4A/report.pdf
```

File `report-data.json` lưu dữ liệu review có cấu trúc.

File `report.html` là báo cáo có thể mở bằng trình duyệt.

File `report.pdf` là báo cáo PDF cuối cùng.

![Generated Reports](/images/5-Workshop/5.5-AI-workflow/s3-generated-reports.png)

</details>

---

<details>
<summary><strong>Bước 15: Kiểm tra review đã hoàn thành trong DynamoDB</strong></summary>

Mở DynamoDB table và kiểm tra review item đã được cập nhật.

Trạng thái review sẽ được đổi từ:

```text
uploaded
```

thành:

```text
completed
```

Item cũng cần có thông tin file báo cáo, kết quả chi phí, dịch vụ phát hiện được, khuyến nghị, rủi ro và best practice.

![DynamoDB Completed Review](/images/5-Workshop/5.5-AI-workflow/dynamodb-completed-review.png)

</details>

---

<details>
<summary><strong>Bước 16: Kiểm tra lịch sử review trên frontend</strong></summary>

React frontend đọc lịch sử review từ backend API.

Các API route dùng cho lịch sử review là:

```text
GET /reviews
GET /reviews/{reviewId}
GET /reviews/{reviewId}/status
```

Sau khi AI Workflow hoàn tất, frontend có thể hiển thị:

```text
Review ID
Tên file
Ngày upload
Trạng thái review
Điểm đánh giá kiến trúc
Các dịch vụ phát hiện được
Khuyến nghị
Rủi ro
Link báo cáo
```

Bước này hoàn tất toàn bộ quy trình upload và AI review.

```text
Upload Backend → S3 Input Bucket → EventBridge → Step Functions
→ AI Analyzer → Cost Tool → PDF Generator
→ S3 Report Bucket → DynamoDB → Frontend Review History
```

![Frontend Review History](/images/5-Workshop/5.5-AI-workflow/frontend-review-history.png)

</details>

---

#### Kết quả AI Workflow

Sau khi hoàn thành phần này, hệ thống có thể tự động xử lý một sơ đồ kiến trúc AWS đã upload và tạo báo cáo đánh giá hoàn chỉnh.

Kết quả cuối cùng bao gồm:

```text
Phân tích kiến trúc bằng AI
Danh sách dịch vụ AWS phát hiện được
Đánh giá theo AWS Well-Architected Framework
Chi phí ước tính hằng tháng
Đề xuất tối ưu chi phí
Báo cáo HTML
Báo cáo PDF
Lịch sử review đã được cập nhật
```

AI Workflow giúp hệ thống tự động hóa toàn bộ quy trình sau khi upload. Người dùng chỉ cần upload sơ đồ kiến trúc, backend sẽ tự động thực hiện phân tích, ước tính chi phí, tạo báo cáo và cập nhật lịch sử review.
