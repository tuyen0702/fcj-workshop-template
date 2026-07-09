---
title : "Xây dựng Upload Backend với API Gateway, Lambda, S3 và DynamoDB"
date : 2026-07-03 
weight : 4
chapter : false
pre : " <b> 5.4. </b> "
---

#### Tổng quan Upload Backend

Trong phần này, backend upload service của dự án **AI AWS Architecture Reviewer** được triển khai bằng **Amazon API Gateway**, **AWS Lambda**, **Amazon S3** và **Amazon DynamoDB**.

Upload backend cho phép người dùng upload sơ đồ kiến trúc AWS từ React frontend. File được upload sẽ được lưu trong S3 Input Bucket, trong khi review metadata được lưu trong DynamoDB.

Luồng xử lý của upload backend là:

```text
React Frontend → API Gateway → Lambda Upload Service → S3 Input Bucket
                                      ↓
                                  DynamoDB
```

Các backend resources chính được sử dụng trong phần này gồm:

```text
Amazon API Gateway
AWS Lambda Upload Service
Amazon S3 Input Bucket
Amazon DynamoDB
Amazon CloudWatch
AWS IAM
```

#### Bước 1: Tạo S3 Input Bucket

Tạo một Amazon S3 bucket để lưu trữ các sơ đồ kiến trúc được upload.

S3 Input Bucket được sử dụng trong dự án này là:

```text
ai-aws-reviewer-input-bucket-tiersteam
```

Các file được upload sẽ được lưu theo cấu trúc key sau:

```text
uploads/{reviewId}/{fileName}
```

Ví dụ:

```text
uploads/REV-C6A0D048/architecture-2.jpg
```

![S3 Input](/images/5-Workshop/5.4-Upload-backend/ai-aws-reviewer-input-bucket-tiersteam.png)

#### Bước 2: Tạo DynamoDB Review Table

Tạo một DynamoDB table để lưu review metadata và review history.

DynamoDB table được sử dụng trong dự án này là:

```text
AIArchitectureReviews
```

Partition key là:

```text
reviewId
```

Table này lưu các thông tin như:

```text
Review ID
File name
File type
File size
S3 input bucket
S3 object key
Upload date
Updated date
Review status
Architecture type
```

![DynamoDB](/images/5-Workshop/5.4-Upload-backend/AIArchitectureReviews.png)

#### Bước 3: Tạo Lambda Execution Role

Tạo một IAM role cho Lambda Upload Service.

Role này cho phép Lambda truy cập các AWS services cần thiết, bao gồm:

```text
Amazon S3
Amazon DynamoDB
Amazon CloudWatch Logs
```

Lambda function cần quyền để upload file lên S3, ghi review metadata vào DynamoDB và ghi logs vào CloudWatch.

![Lambda Execution Role](/images/5-Workshop/5.4-Upload-backend/ai-aws-reviewer-upload-lambda-role.png)

![Lambda Execution Inline Policy](/images/5-Workshop/5.4-Upload-backend/ai-aws-reviewer-upload-lambda-role-inline-policy.png)

#### Bước 4: Tạo Lambda Upload Service

Tạo một AWS Lambda function để xử lý các upload requests.

Tên Lambda function là:

```text
ai-aws-reviewer-upload-service
```

Function này chịu trách nhiệm cho các nhiệm vụ sau:

```text
Nhận upload requests từ API Gateway.
Validate file type và file size.
Tạo một review ID duy nhất.
Upload diagram file lên Amazon S3.
Lưu review metadata vào DynamoDB.
Trả upload response về frontend.
```

![Lambda](/images/5-Workshop/5.4-Upload-backend/ai-aws-reviewer-upload-service.png)

#### Bước 5: Cấu hình Lambda Environment Variables

Cấu hình các environment variables cần thiết cho Lambda Upload Service.

Ví dụ environment variables:

```text
INPUT_BUCKET = ai-aws-reviewer-input-bucket-tiersteam
TABLE_NAME = AIArchitectureReviews
MAX_FILE_SIZE_MB = 5
ALLOWED_ORIGINS = http://localhost:5173,https://d9353ayez9zar.cloudfront.net
```

Các environment variables này cho phép Lambda function xác định input bucket, DynamoDB table, giới hạn dung lượng upload và các frontend origins được phép gọi API.

![Lambda](/images/5-Workshop/5.4-Upload-backend/ai-aws-reviewer-upload-service-env.png)

#### Bước 6: Triển khai logic xử lý upload

Lambda function validate file được upload và tạo một review ID duy nhất.

Định dạng của review ID là:

```text
REV-XXXXXXXX
```

Ví dụ:

```text
REV-C6A0D048
```

Sau khi review ID được tạo, file upload sẽ được lưu vào Amazon S3 theo cấu trúc key sau:

```text
uploads/{reviewId}/{fileName}
```

Sau đó, Lambda function ghi metadata vào DynamoDB với trạng thái ban đầu là:

```text
uploaded
```

Trạng thái này có nghĩa là diagram đã được upload thành công và sẵn sàng cho review workflow tiếp theo.

#### Bước 7: Tạo API Gateway Upload Route

Tạo một API Gateway endpoint và kết nối endpoint này với Lambda Upload Service.

API Gateway endpoint được sử dụng trong dự án này là:

```text
https://031hqksomd.execute-api.ap-southeast-1.amazonaws.com
```

Tạo route sau:

```text
POST /upload
```

Route này nhận upload requests từ React frontend và chuyển tiếp request đến Lambda Upload Service.

![API Gateway](/images/5-Workshop/5.4-Upload-backend/ai-aws-reviewer-api.png)

#### Bước 8: Cấu hình CORS

CORS cần được cấu hình để React frontend có thể gọi backend API.

Allowed origins:

```text
http://localhost:5173
https://d9353ayez9zar.cloudfront.net
```

Allowed methods:

```text
POST
OPTIONS
```

Allowed headers:

```text
content-type
authorization
```

Phương thức `OPTIONS` là cần thiết vì trình duyệt sẽ gửi preflight requests trước một số cross-origin API calls.

![API Gateway](/images/5-Workshop/5.4-Upload-backend/ai-aws-reviewer-api-cors.png)

#### Bước 9: Kiểm thử upload file bằng PowerShell

Chuẩn bị một file sơ đồ kiến trúc để kiểm thử.

Đường dẫn file ví dụ:

```text
D:\Learning\AWS\test-files\architecture-1.png
```

Chạy lệnh sau để kiểm thử upload:

```text
curl.exe -X POST "https://031hqksomd.execute-api.ap-southeast-1.amazonaws.com/upload" -F "file=@D:\Learning\AWS\test-files\architecture-1.png"
```

Nếu upload thành công, API sẽ trả về response tương tự như sau:

```text
{
  "reviewId": "REV-5E57628D",
  "status": "uploaded",
  "fileName": "architecture-1.png",
  "fileType": "image/png",
  "fileSize": 17755,
  "message": "Upload successful"
}
```

![API Gateway](/images/5-Workshop/5.4-Upload-backend/ai-aws-reviewer-upload-service-test-files.png)

#### Bước 10: Kiểm tra file đã upload trong S3

Sau khi kiểm thử upload API, mở S3 Input Bucket và kiểm tra rằng diagram file đã được upload thành công.

File nên được lưu theo cấu trúc sau:

```text
uploads/{reviewId}/{fileName}
```

Ví dụ:

```text
uploads/REV-C29F2778/architecture-1.png
```

![S3](/images/5-Workshop/5.4-Upload-backend/ai-aws-reviewer-input-bucket-tiersteam.png)

#### Bước 11: Kiểm tra metadata trong DynamoDB

Mở DynamoDB table và kiểm tra rằng một review item mới đã được tạo.

Item này nên bao gồm các thông tin như:

```text
reviewId
fileName
fileType
fileSize
s3InputBucket
s3InputKey
status
uploadDate
updatedAt
```

![DynamoDB](/images/5-Workshop/5.4-Upload-backend/AIArchitectureReviews-verify.png)