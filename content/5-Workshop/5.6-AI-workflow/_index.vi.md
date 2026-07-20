---
title : "Xây dựng AI Workflow với EventBridge, Step Functions, Bedrock và PDF Generator"
date : 2026-07-08
weight : 6
chapter : false
pre : " <b> 5.6. </b> "
---

#### Tổng quan AI Workflow

Trong phần này, **AI Workflow** của dự án **AI AWS Architecture Reviewer** được xây dựng bằng **Amazon EventBridge**, **AWS Step Functions**, **AWS Lambda**, **Amazon Bedrock**, **AWS Price List API**, **Amazon S3**, **Amazon DynamoDB**, **Amazon CloudWatch** và **AWS IAM**.

Sau khi người dùng upload sơ đồ kiến trúc AWS thông qua upload backend, file sẽ được lưu vào **S3 Input Bucket**. Sự kiện tạo object mới trong S3 được gửi sang **Amazon EventBridge**. EventBridge sau đó tự động kích hoạt **AWS Step Functions** để bắt đầu quy trình phân tích kiến trúc.

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
Lambda Layer
```

Trong phần này, các cấu hình ngắn như **environment variables**, **EventBridge pattern**, **Step Functions definition**, **IAM permissions** và **lệnh kiểm thử** được ghi trực tiếp trong bài. Source code dài của các Lambda function được lưu riêng trong thư mục README để trang workshop gọn hơn.

<details>
<summary><strong>Cấu trúc thư mục README dùng để lưu source code Lambda</strong></summary>

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
<summary><strong>Bước 1: Bật EventBridge notification cho S3 Input Bucket</strong></summary>

AI Workflow bắt đầu khi một sơ đồ kiến trúc mới được upload vào S3 Input Bucket. Upload backend đã lưu file vào bucket input theo cấu trúc key có chứa `reviewId`, vì vậy các bước phía sau có thể dùng `reviewId` để theo dõi toàn bộ quá trình phân tích.

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

Thực hiện cấu hình trên AWS Console:

```text
1. Chọn region ap-southeast-1.
2. Vào Amazon S3.
3. Mở bucket ai-aws-reviewer-input-bucket-tiersteam.
4. Chọn tab Properties.
5. Tìm mục Amazon EventBridge.
6. Chọn Edit.
7. Bật Send notifications to Amazon EventBridge for all events in this bucket.
8. Chọn Save changes.
```

Sau khi bật tùy chọn này, các sự kiện tạo object mới trong bucket sẽ có thể được định tuyến sang EventBridge.

![S3 EventBridge](/images/5-Workshop/5.6-AI-workflow/s3-input-bucket-eventbridge.png)

</details>

---

<details>
<summary><strong>Bước 2: Tạo EventBridge rule cho sự kiện S3 Object Created</strong></summary>

EventBridge rule được dùng để bắt sự kiện file mới được upload vào S3 Input Bucket. Khi có object mới, rule sẽ kích hoạt Step Functions để bắt đầu AI Workflow.

Thực hiện cấu hình trên AWS Console:

```text
1. Vào Amazon EventBridge.
2. Chọn Rules.
3. Chọn Create rule.
4. Nhập tên rule.
5. Event bus chọn default.
6. Rule type chọn Rule with an event pattern.
7. Chọn Next.
```

Tên rule sử dụng trong project:

```text
ai-aws-reviewer-s3-object-created-rule
```

Ở phần Event source, chọn:

```text
AWS events or EventBridge partner events
```

Ở phần Creation method, chọn:

```text
Custom pattern JSON editor
```

Dán event pattern sau:

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

Ý nghĩa của pattern:

```text
source = aws.s3:
Chỉ nhận sự kiện đến từ Amazon S3.

detail-type = Object Created:
Chỉ nhận sự kiện khi có object mới được tạo.

bucket.name:
Chỉ nhận sự kiện từ bucket input của project.
```

Sau khi cấu hình xong, chọn:

```text
Next
```

![EventBridge Rule](/images/5-Workshop/5.6-AI-workflow/eventbridge-rule.png)

</details>

---

<details>
<summary><strong>Bước 3: Cấu hình EventBridge target là Step Functions</strong></summary>

Target của EventBridge rule là Step Functions state machine. Khi file mới được upload lên S3, EventBridge sẽ gọi `StartExecution` để chạy state machine.

Step Functions workflow được sử dụng trong dự án là:

```text
Architecture-review-workflow
```

Thực hiện cấu hình target:

```text
1. Ở bước Select target của EventBridge rule, chọn Target type là AWS service.
2. Ở Select a target, chọn Step Functions state machine.
3. Chọn state machine Architecture-review-workflow.
4. Phần Execution role chọn tạo role mới hoặc chọn role đã có quyền states:StartExecution.
5. Mở phần Additional settings.
6. Chọn Configure target input.
7. Chọn Input transformer.
```

Input transformer dùng để lấy bucket name và object key từ event S3, sau đó truyền sang Step Functions dưới dạng JSON gọn hơn.

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

Ví dụ input mà Step Functions nhận được:

```json
{
  "bucket": "ai-aws-reviewer-input-bucket-tiersteam",
  "key": "uploads/REV-0491BC4A/architecture-diagram.jpg",
  "region": "ap-southeast-1"
}
```

Input này giúp AI Analyzer Lambda xác định đúng bucket và object key để đọc sơ đồ kiến trúc đã upload từ S3.

![EventBridge Target](/images/5-Workshop/5.6-AI-workflow/eventbridge-target-step-functions.png)

</details>

---

<details>
<summary><strong>Bước 4: Tạo Step Functions AI Workflow</strong></summary>

Step Functions được dùng để điều phối toàn bộ quy trình phân tích kiến trúc. Thay vì gọi từng Lambda thủ công, Step Functions giúp workflow chạy theo đúng thứ tự và dễ quan sát trạng thái từng bước.

Tên workflow là:

```text
Architecture-review-workflow
```

Thực hiện tạo state machine:

```text
1. Vào AWS Step Functions.
2. Chọn State machines.
3. Chọn Create state machine.
4. Chọn Write your workflow in code.
5. Type chọn Standard.
6. Definition language chọn JSON.
7. Đặt tên state machine là Architecture-review-workflow.
8. Chọn hoặc tạo IAM role cho Step Functions.
9. Bật logging nếu cần theo dõi execution trong CloudWatch.
10. Chọn Create state machine.
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

Trong workflow có thêm Choice state `HasDetectedServices`. Nếu AI Analyzer không phát hiện dịch vụ AWS nào, workflow sẽ bỏ qua bước tính chi phí và chuyển thẳng sang tạo report với cost bằng 0.

![Step Functions](/images/5-Workshop/5.6-AI-workflow/architecture-review-workflow.png)

</details>

---

<details>
<summary><strong>Bước 5: Cấu hình Step Functions definition</strong></summary>

Sau khi tạo state machine, dán Amazon States Language definition vào phần code editor của Step Functions.

Thực hiện trong AWS Console:

```text
1. Mở state machine Architecture-review-workflow.
2. Chọn Edit.
3. Chọn Definition.
4. Xóa definition mẫu nếu có.
5. Dán JSON definition bên dưới.
6. Kiểm tra lại ARN của ba Lambda function.
7. Chọn Save.
```

Workflow definition sử dụng trong project:

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

Sau khi lưu, kiểm tra lại graph view. Graph đúng cần có các state sau:

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
<summary><strong>Bước 6: Tạo AI Analyzer Lambda</strong></summary>

AI Analyzer Lambda là bước đầu tiên trong Step Functions. Lambda này nhận thông tin bucket và object key từ EventBridge, đọc ảnh kiến trúc trong S3 rồi gửi ảnh sang Amazon Bedrock để phân tích.

Tên Lambda function là:

```text
aws-reviewer-ai-analyzer
```

Thực hiện tạo Lambda:

```text
1. Vào AWS Lambda.
2. Chọn Create function.
3. Chọn Author from scratch.
4. Function name nhập aws-reviewer-ai-analyzer.
5. Runtime chọn Python 3.14 hoặc runtime đang dùng trong project.
6. Architecture chọn x86_64.
7. Execution role chọn role có quyền S3 GetObject, Bedrock InvokeModel và CloudWatch Logs.
8. Chọn Create function.
```

Sau khi tạo function, cấu hình general settings:

```text
Memory: 1024 MB
Timeout: 120 seconds
```

Cấu hình environment variables:

```text
MODEL_ID = global.amazon.nova-2-lite-v1:0
BEDROCK_REGION = ap-southeast-1
```

Source code dài của Lambda được lưu trong thư mục:

```text
README/ai-workflow/lambdas/ai-analyzer/lambda_function.py
```

Sau khi copy code vào Lambda, chọn:

```text
Deploy
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

Output chính của Lambda này bao gồm:

```text
Review ID
Source bucket
Source object key
Danh sách dịch vụ AWS phát hiện được
Các kết nối giữa dịch vụ
Kết quả đánh giá Well-Architected
Các giới hạn của quá trình phân tích
```

Có thể test Lambda bằng event mẫu:

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
<summary><strong>Bước 7: Tạo Cost Tool Lambda</strong></summary>

Cost Tool Lambda là bước thứ hai trong workflow. Lambda này nhận danh sách dịch vụ AWS đã được AI Analyzer phát hiện, sau đó tính chi phí ước tính hằng tháng.

Tên Lambda function là:

```text
aws-reviewer-cost-tool
```

Thực hiện tạo Lambda:

```text
1. Vào AWS Lambda.
2. Chọn Create function.
3. Chọn Author from scratch.
4. Function name nhập aws-reviewer-cost-tool.
5. Runtime chọn Python 3.14 hoặc runtime đang dùng trong project.
6. Architecture chọn x86_64.
7. Execution role chọn role có quyền Pricing API, Bedrock InvokeModel và CloudWatch Logs.
8. Chọn Create function.
```

Cấu hình general settings:

```text
Memory: 1024 MB
Timeout: 120 seconds
```

Cấu hình environment variables:

```text
MODEL_ID = global.amazon.nova-2-lite-v1:0
BEDROCK_REGION = ap-southeast-1
DEFAULT_REGION = ap-southeast-1
```

Source code dài của Lambda được lưu trong thư mục:

```text
README/ai-workflow/lambdas/cost-tool/lambda_function.py
```

Sau khi copy code vào Lambda, chọn:

```text
Deploy
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

Cost Tool không cho AI tự tạo ra giá. Giá trị chi phí được tính từ dữ liệu AWS Price List API, còn Amazon Bedrock chỉ được dùng để giải thích kết quả chi phí và đưa ra đề xuất tối ưu.

Có thể test Lambda bằng event mẫu:

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

Output chính của Lambda này bao gồm:

```text
Chi phí ước tính hằng tháng
Đơn vị tiền tệ
Bảng phân tích chi phí theo dịch vụ
Nguồn dữ liệu giá
Assumption sử dụng mặc định
Đề xuất tối ưu chi phí
```

![Cost Tool Lambda](/images/5-Workshop/5.6-AI-workflow/aws-reviewer-cost-tool.png)

</details>

---

<details>
<summary><strong>Bước 8: Tạo S3 Report Bucket</strong></summary>

S3 Report Bucket được dùng để lưu các file báo cáo sau khi AI Workflow hoàn tất. PDF Generator Lambda sẽ upload `report-data.json`, `report.html` và `report.pdf` vào bucket này.

S3 Report Bucket được sử dụng trong dự án là:

```text
ai-aws-reviewer-report-bucket-tiersteam
```

Thực hiện tạo bucket:

```text
1. Vào Amazon S3.
2. Chọn Create bucket.
3. Region chọn ap-southeast-1.
4. Bucket name nhập ai-aws-reviewer-report-bucket-tiersteam.
5. Object Ownership để mặc định ACLs disabled.
6. Block Public Access giữ nguyên bật toàn bộ nếu chỉ truy cập report qua backend hoặc presigned URL.
7. Bật Bucket Versioning nếu muốn lưu nhiều phiên bản report.
8. Encryption chọn Server-side encryption with Amazon S3 managed keys (SSE-S3).
9. Chọn Create bucket.
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

Ý nghĩa từng file:

```text
report-data.json:
Lưu dữ liệu review dạng JSON có cấu trúc.

report.html:
Lưu báo cáo HTML, dễ mở bằng trình duyệt.

report.pdf:
Lưu báo cáo PDF cuối cùng để tải xuống hoặc nộp báo cáo.
```

![S3 Report Bucket](/images/5-Workshop/5.6-AI-workflow/s3-report-bucket.png)

</details>

---

<details>
<summary><strong>Bước 9: Tạo PDF Generator Lambda</strong></summary>

PDF Generator Lambda là bước cuối cùng trong AI Workflow. Lambda này nhận kết quả phân tích kiến trúc và kết quả chi phí từ Step Functions, sau đó tạo báo cáo cuối cùng và cập nhật lịch sử review trong DynamoDB.

Tên Lambda function là:

```text
aws-reviewer-pdf-generator
```

Thực hiện tạo Lambda:

```text
1. Vào AWS Lambda.
2. Chọn Create function.
3. Chọn Author from scratch.
4. Function name nhập aws-reviewer-pdf-generator.
5. Runtime chọn Python 3.14.
6. Architecture chọn x86_64.
7. Execution role chọn role có quyền S3 PutObject, DynamoDB UpdateItem, Bedrock InvokeModel và CloudWatch Logs.
8. Chọn Create function.
```

Cấu hình general settings:

```text
Memory: 1024 MB
Timeout: 180 seconds
```

Cấu hình environment variables:

```text
REPORT_BUCKET = ai-aws-reviewer-report-bucket-tiersteam
TABLE_NAME = AIArchitectureReviews
MODEL_ID = global.amazon.nova-2-lite-v1:0
BEDROCK_REGION = ap-southeast-1
```

Source code dài của Lambda được lưu trong thư mục:

```text
README/ai-workflow/lambdas/pdf-generator/lambda_function.py
```

Sau khi copy code vào Lambda, chọn:

```text
Deploy
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

Có thể test Lambda bằng event mẫu:

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

PDF Generator Lambda là state cuối cùng của AI Workflow.

![PDF Generator Lambda](/images/5-Workshop/5.6-AI-workflow/aws-reviewer-pdf-generator.png)

</details>

---

<details>
<summary><strong>Bước 10: Cấu hình ReportLab Layer để tạo PDF</strong></summary>

Để tạo file PDF bên trong Lambda, hệ thống sử dụng **Lambda Layer** để cung cấp thư viện **ReportLab**, **Pillow** và font hỗ trợ tiếng Việt. Layer này được gắn vào Lambda `aws-reviewer-pdf-generator` để function có thể import ReportLab và xuất file `report.pdf`.

Trong dự án này, PDF Generator Lambda sử dụng:

```text
Region: ap-southeast-1
Runtime: Python 3.14
Architecture: x86_64
Layer name: reportlab-layer-py314-vn
```

##### 10.1. Mở CloudShell đúng region

Trên AWS Console, chọn region:

```text
ap-southeast-1
```

Sau đó mở:

```text
CloudShell
```

CloudShell được dùng để cài thư viện ReportLab, Pillow và đóng gói chúng thành file `.zip` theo đúng cấu trúc Lambda Layer.

##### 10.2. Tạo thư mục layer và cài ReportLab

Chạy các lệnh sau trong CloudShell:

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

Ý nghĩa chính của lệnh trên:

```text
--platform manylinux2014_x86_64 : build package phù hợp với môi trường Linux x86_64 của Lambda
--python-version 3.14          : build đúng với runtime Python 3.14
--abi cp314                    : dùng ABI tương ứng Python 3.14
--target                       : cài thư viện vào thư mục python/ của Lambda Layer
```

Sau khi cài xong, di chuyển vào thư mục layer:

```bash
cd reportlab-layer-py314
```

##### 10.3. Tạo thư mục fonts và thêm font tiếng Việt

ReportLab mặc định không hiển thị tốt tiếng Việt nếu chỉ dùng font mặc định. Vì vậy, layer cần thêm font Unicode như **DejaVuSans**.

Tạo thư mục `fonts`:

```bash
mkdir -p fonts
```

Copy font DejaVuSans vào thư mục `fonts`:

```bash
cp /usr/share/fonts/dejavu-sans-fonts/DejaVuSans.ttf fonts/
cp /usr/share/fonts/dejavu-sans-fonts/DejaVuSans-Bold.ttf fonts/
```

Sau khi copy xong, kiểm tra lại thư mục font:

```bash
ls -l fonts
```

Kết quả mong muốn:

```text
DejaVuSans.ttf
DejaVuSans-Bold.ttf
```

Nếu CloudShell không tìm thấy đường dẫn font ở trên, có thể tìm lại bằng lệnh:

```bash
find /usr/share/fonts -iname "DejaVuSans*.ttf"
```

Sau đó dùng đúng đường dẫn mà lệnh `find` trả về để copy font vào thư mục `fonts`.

##### 10.4. Đóng gói Lambda Layer

Sau khi thư mục `python` và `fonts` đã sẵn sàng, tạo file zip:

```bash
zip -r reportlab-layer-py314-vn.zip python fonts
```

Cấu trúc file zip sau khi đóng gói sẽ có dạng:

```text
python/
  reportlab/
  PIL/
  ...
fonts/
  DejaVuSans.ttf
  DejaVuSans-Bold.ttf
```

Khi Lambda gắn layer này, các file font sẽ nằm tại:

```text
/opt/fonts/DejaVuSans.ttf
/opt/fonts/DejaVuSans-Bold.ttf
```

PDF Generator Lambda sẽ dùng các đường dẫn này để đăng ký font tiếng Việt trong ReportLab.

##### 10.5. Download file layer từ CloudShell

Trong CloudShell, chọn:

```text
Actions → Download file
```

Nhập file path:

```text
reportlab-layer-py314/reportlab-layer-py314-vn.zip
```

Sau đó chọn:

```text
Download
```

File cần tải về là:

```text
reportlab-layer-py314-vn.zip
```

##### 10.6. Tạo Lambda Layer mới

Vào AWS Console:

```text
Lambda → Layers → Create layer
```

Điền thông tin layer:

```text
Name: reportlab-layer-py314-vn
Upload: reportlab-layer-py314-vn.zip
Compatible runtime: Python 3.14
Compatible architecture: x86_64
```

Sau đó chọn:

```text
Create
```

![ReportLab Layer](/images/5-Workshop/5.6-AI-workflow/reportlab-layer.png)

##### 10.7. Gắn layer vào PDF Generator Lambda

Vào Lambda PDF Generator:

```text
Lambda → aws-reviewer-pdf-generator → Code → Layers
```

Chọn:

```text
Add a layer
```

Sau đó chọn:

```text
Custom layers → reportlab-layer-py314-vn → Version mới nhất → Add
```

Sau khi gắn layer, lưu lại cấu hình Lambda.

##### 10.8. Cấu hình code sử dụng font tiếng Việt

Trong Lambda `aws-reviewer-pdf-generator`, ReportLab cần đăng ký font trước khi build PDF.

Đường dẫn font trong Lambda là:

```text
/opt/fonts/DejaVuSans.ttf
/opt/fonts/DejaVuSans-Bold.ttf
```

Ví dụ đoạn code đăng ký font:

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

Các style trong ReportLab cần sử dụng font này thay vì font mặc định:

```python
styles.add(ParagraphStyle(
    name="VNBody",
    parent=styles["BodyText"],
    fontName="DejaVuSans",
    fontSize=10,
    leading=14
))
```

##### 10.9. Kiểm tra PDF sau khi gắn layer

Sau khi gắn layer và deploy code, test lại Lambda `aws-reviewer-pdf-generator`.

Kết quả mong muốn trong output:

```json
{
  "reportlab_available": true,
  "pdf_status": "PDF_GENERATED",
  "pdf_report_s3_uri": "s3://ai-aws-reviewer-report-bucket-tiersteam/reports/REV-TEST-PDF/report.pdf"
}
```

Sau đó mở S3 Report Bucket và kiểm tra file PDF:

```text
reports/{reviewId}/report.pdf
```

Nếu PDF hiển thị được các ký tự như `đ`, `ư`, `ế`, `ệ`, `ộ`, nghĩa là font tiếng Việt đã được cấu hình thành công.

</details>

---

<details>
<summary><strong>Bước 11: Cập nhật lịch sử review trong DynamoDB</strong></summary>

Sau khi báo cáo được tạo thành công, PDF Generator Lambda cập nhật review item trong DynamoDB. Việc cập nhật này giúp frontend hiển thị được kết quả review thay vì chỉ thấy trạng thái `uploaded`.

DynamoDB table được sử dụng trong dự án là:

```text
AIArchitectureReviews
```

Partition key là:

```text
reviewId
```

Quy trình cập nhật trong DynamoDB:

```text
1. Upload Lambda tạo item mới với status = uploaded.
2. EventBridge kích hoạt Step Functions.
3. Step Functions chạy AI Analyzer, Cost Tool và PDF Generator.
4. PDF Generator tạo report thành công.
5. PDF Generator gọi DynamoDB UpdateItem.
6. Item được cập nhật status = completed.
```

Khi upload backend tạo review item mới, trạng thái ban đầu là:

```text
uploaded
```

Sau khi AI Workflow hoàn tất, PDF Generator Lambda cập nhật trạng thái thành:

```text
completed
```

Các field được cập nhật sau khi hoàn thành:

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

Ví dụ DynamoDB item sau khi hoàn thành:

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

Thực hiện kiểm tra trong DynamoDB:

```text
1. Vào Amazon DynamoDB.
2. Chọn Tables.
3. Mở bảng AIArchitectureReviews.
4. Chọn Explore table items.
5. Tìm reviewId tương ứng, ví dụ REV-0491BC4A.
6. Kiểm tra status đã chuyển thành completed.
7. Kiểm tra các field reportFiles, score, costResult và recommendations.
```

Việc cập nhật này giúp React frontend hiển thị được lịch sử review và kết quả phân tích đã hoàn thành.

![DynamoDB Updated Review](/images/5-Workshop/5.6-AI-workflow/dynamodb-review-completed.png)

</details>

---

<details>
<summary><strong>Bước 12: Cấu hình IAM permissions</strong></summary>

Mỗi Lambda function, Step Functions workflow và EventBridge target cần có IAM role với các quyền phù hợp. IAM là phần quan trọng vì nếu thiếu quyền, workflow có thể chạy tới một bước rồi bị lỗi `AccessDenied`.

Cách thêm inline policy cho từng role:

```text
1. Vào IAM.
2. Chọn Roles.
3. Mở role cần cấu hình.
4. Chọn Add permissions.
5. Chọn Create inline policy.
6. Chọn tab JSON.
7. Dán policy tương ứng.
8. Chọn Next.
9. Đặt tên policy.
10. Chọn Create policy.
```

##### 12.1. IAM policy cho AI Analyzer Lambda

AI Analyzer Lambda cần quyền đọc file từ S3 Input Bucket, gọi Amazon Bedrock và ghi log vào CloudWatch.

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

##### 12.2. IAM policy cho Cost Tool Lambda

Cost Tool Lambda cần quyền gọi AWS Price List API, gọi Amazon Bedrock và ghi log vào CloudWatch.

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

##### 12.3. IAM policy cho PDF Generator Lambda

PDF Generator Lambda cần quyền ghi report vào S3 Report Bucket, cập nhật DynamoDB, gọi Amazon Bedrock và ghi log vào CloudWatch.

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

##### 12.4. IAM policy cho Step Functions role

Step Functions role cần quyền invoke ba Lambda function trong AI Workflow.

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

##### 12.5. IAM policy cho EventBridge target role

EventBridge cần quyền start execution của Step Functions state machine.

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
<summary><strong>Bước 13: Kiểm thử AI Workflow</strong></summary>

Để kiểm thử toàn bộ AI Workflow, upload một sơ đồ kiến trúc từ frontend hoặc sử dụng upload API. Khi upload thành công, S3 sẽ phát sinh sự kiện Object Created, EventBridge sẽ bắt sự kiện đó và tự động khởi chạy Step Functions.

Chuẩn bị file ảnh kiến trúc trên máy:

```text
D:\Learning\AWS\test-files\architecture-1.png
```

Lệnh kiểm thử upload bằng PowerShell:

```powershell
curl.exe -X POST "https://031hqksomd.execute-api.ap-southeast-1.amazonaws.com/upload" -F "file=@D:\Learning\AWS\test-files\architecture-1.png"
```

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

Sau khi có review ID, kiểm tra theo thứ tự:

```text
1. Vào S3 Input Bucket.
2. Kiểm tra file nằm trong uploads/{reviewId}/.
3. Vào EventBridge rule để kiểm tra metric Matched events.
4. Vào Step Functions.
5. Mở state machine Architecture-review-workflow.
6. Chọn execution mới nhất.
7. Kiểm tra Graph view.
```

Các state cần chạy thành công:

```text
AnalyzeArchitectureWithAI
EstimateCost
GenerateReport
```

Nếu một state bị lỗi, mở tab `Input` và `Output` của state đó để xem dữ liệu truyền vào và lỗi trả ra.

![Step Functions Success](/images/5-Workshop/5.6-AI-workflow/step-functions-execution-success.png)

</details>

---

<details>
<summary><strong>Bước 14: Kiểm tra báo cáo được tạo trong S3</strong></summary>

Sau khi Step Functions execution hoàn tất, PDF Generator Lambda sẽ lưu các file báo cáo vào S3 Report Bucket.

Mở S3 Report Bucket:

```text
ai-aws-reviewer-report-bucket-tiersteam
```

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

Thực hiện kiểm tra:

```text
1. Vào Amazon S3.
2. Mở bucket ai-aws-reviewer-report-bucket-tiersteam.
3. Mở thư mục reports.
4. Mở thư mục theo reviewId, ví dụ REV-0491BC4A.
5. Kiểm tra có đủ report-data.json, report.html và report.pdf.
6. Mở hoặc download report.pdf để kiểm tra nội dung báo cáo.
```

Ý nghĩa từng file:

```text
report-data.json:
Lưu dữ liệu review có cấu trúc, phù hợp để frontend hoặc backend đọc lại.

report.html:
Lưu báo cáo dạng HTML, hiển thị tốt trên trình duyệt.

report.pdf:
Lưu báo cáo PDF cuối cùng, có thể tải xuống hoặc đưa vào phần kết quả demo.
```

![Generated Reports](/images/5-Workshop/5.6-AI-workflow/s3-generated-reports.png)

</details>

---

<details>
<summary><strong>Bước 15: Kiểm tra review đã hoàn thành trong DynamoDB</strong></summary>

DynamoDB lưu lịch sử review và trạng thái xử lý. Sau khi workflow hoàn tất, PDF Generator Lambda phải cập nhật item tương ứng với `reviewId`.

Mở DynamoDB table:

```text
AIArchitectureReviews
```

Thực hiện kiểm tra:

```text
1. Vào Amazon DynamoDB.
2. Chọn Tables.
3. Mở bảng AIArchitectureReviews.
4. Chọn Explore table items.
5. Tìm reviewId vừa upload, ví dụ REV-0491BC4A.
6. Kiểm tra field status.
7. Kiểm tra field completedDate và updatedAt.
8. Kiểm tra reportFiles, costResult, detectedServices và recommendations.
```

Trạng thái review sẽ được đổi từ:

```text
uploaded
```

thành:

```text
completed
```

Các field quan trọng cần có:

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

Nếu item vẫn ở trạng thái `uploaded`, cần kiểm tra CloudWatch Logs của PDF Generator Lambda. Lỗi thường gặp là thiếu biến môi trường `TABLE_NAME` hoặc thiếu quyền `dynamodb:UpdateItem`.

![DynamoDB Completed Review](/images/5-Workshop/5.6-AI-workflow/dynamodb-completed-review.png)

</details>

---

<details>
<summary><strong>Bước 16: Kiểm tra lịch sử review trên frontend</strong></summary>

React frontend đọc lịch sử review từ upload backend API. Sau khi PDF Generator cập nhật DynamoDB, frontend có thể hiển thị trạng thái và kết quả phân tích đã hoàn thành.

Các API route dùng cho lịch sử review là:

```text
GET /reviews
GET /reviews/{reviewId}
GET /reviews/{reviewId}/status
```

Thực hiện kiểm tra trên frontend:

```text
1. Mở React frontend.
2. Upload một sơ đồ kiến trúc mới.
3. Ghi lại reviewId trả về từ API.
4. Chờ AI Workflow chạy xong trong Step Functions.
5. Refresh trang lịch sử review.
6. Kiểm tra review đã chuyển sang completed.
7. Mở chi tiết review để xem score, detected services, recommendations và report links.
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

![Frontend Review History](/images/5-Workshop/5.6-AI-workflow/frontend-review-history.png)

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
