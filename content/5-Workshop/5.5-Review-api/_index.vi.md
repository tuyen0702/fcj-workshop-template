---
title : "Tích hợp Review APIs và Frontend Pages"
date : 2026-07-03 
weight : 5
chapter : false
pre : " <b> 5.5. </b> "
---

#### Tổng quan Review API

Trong phần này, các review data APIs được tạo và tích hợp với các trang React frontend.

Sau khi người dùng upload một sơ đồ kiến trúc, hệ thống sẽ lưu review metadata vào DynamoDB. Frontend cần truy xuất dữ liệu này để hiển thị review history, review details và review progress.

Luồng xử lý của Review API là:

```text
React Frontend → API Gateway → Lambda Upload Service → DynamoDB
```

API Gateway endpoint được sử dụng trong dự án này là:

```text
https://031hqksomd.execute-api.ap-southeast-1.amazonaws.com
```

#### Các Review API routes

Các API routes sau được sử dụng trong dự án này:

```text
GET /reviews
GET /reviews/{reviewId}
GET /reviews/{reviewId}/status
```

Mỗi route có một mục đích cụ thể:

```text
GET /reviews
Truy xuất danh sách các reviews đã được upload từ DynamoDB.

GET /reviews/{reviewId}
Truy xuất thông tin chi tiết của một review cụ thể.

GET /reviews/{reviewId}/status
Truy xuất trạng thái hiện tại của một review cụ thể.
```

#### Bước 1: Tạo route GET /reviews

Tạo route sau trong API Gateway:

```text
GET /reviews
```

Route này được tích hợp với Lambda Upload Service.

Lambda function đọc các review records từ DynamoDB và trả danh sách reviews về frontend.

API này được sử dụng bởi trang Review History.

#### Bước 2: Tạo route GET /reviews/{reviewId}

Tạo route sau trong API Gateway:

```text
GET /reviews/{reviewId}
```

Route này truy xuất thông tin chi tiết của một review dựa trên `reviewId`.

Ví dụ review ID:

```text
REV-C6A0D048
```

API này được sử dụng bởi trang Review Detail.

#### Bước 3: Tạo route GET /reviews/{reviewId}/status

Tạo route sau trong API Gateway:

```text
GET /reviews/{reviewId}/status
```

Route này truy xuất trạng thái xử lý hiện tại của một review.

Ví dụ các trạng thái gồm:

```text
uploaded
processing
completed
failed
```

Ở giai đoạn hiện tại của dự án, trạng thái ban đầu sau khi upload là:

```text
uploaded
```

API này được sử dụng bởi trang Review Progress.

![Review API](/images/5-Workshop/5.5-Review-api/ai-aws-reviewer-api.png)

#### Bước 4: Cấu hình CORS cho Review APIs

CORS cần được cấu hình để frontend có thể gọi các review APIs.

Allowed origins:

```text
http://localhost:5173
https://d9353ayez9zar.cloudfront.net
```

Allowed methods:

```text
GET
POST
OPTIONS
```

Allowed headers:

```text
content-type
authorization
```

Phương thức `OPTIONS` là cần thiết cho browser preflight requests.

![Review API CORS](/images/5-Workshop/5.5-Review-api/ai-aws-reviewer-api-cors.png)

#### Bước 5: Kiểm thử API GET /reviews

Sử dụng PowerShell để kiểm thử review list API:

```text
curl.exe -i "https://031hqksomd.execute-api.ap-southeast-1.amazonaws.com/reviews" -H "Origin: https://d9353ayez9zar.cloudfront.net"
```

Nếu API hoạt động chính xác, nó sẽ trả về danh sách các review records từ DynamoDB.

![Review API test](/images/5-Workshop/5.5-Review-api/test-reviews.png)

#### Bước 6: Kiểm thử API GET /reviews/{reviewId}

Sử dụng PowerShell để kiểm thử review detail API:

```text
curl.exe -i "https://031hqksomd.execute-api.ap-southeast-1.amazonaws.com/reviews/REV-C6A0D048" -H "Origin: https://d9353ayez9zar.cloudfront.net"
```

Thay `REV-C6A0D048` bằng một review ID thực tế trong DynamoDB.

Nếu API hoạt động chính xác, nó sẽ trả về thông tin chi tiết của review được chọn.

Response ví dụ:

```text
{
  "reviewId": "REV-C6A0D048",
  "status": "uploaded"
}
```

![Review API test](/images/5-Workshop/5.5-Review-api/test-review-detail.png)

#### Bước 7: Kiểm thử API GET /reviews/{reviewId}/status

Sử dụng PowerShell để kiểm thử review status API:

```text
curl.exe -i "https://031hqksomd.execute-api.ap-southeast-1.amazonaws.com/reviews/REV-C6A0D048/status" -H "Origin: https://d9353ayez9zar.cloudfront.net"
```

Thay `REV-C6A0D048` bằng một review ID thực tế trong DynamoDB.

Nếu API hoạt động chính xác, nó sẽ trả về trạng thái hiện tại của review.

Response ví dụ:

```text
{
  "reviewId": "REV-C6A0D048",
  "status": "uploaded"
}
```

![Review API test](/images/5-Workshop/5.5-Review-api/test-review-detail-status.png)

#### Bước 8: Kết nối trang Review History

Trang Review History sử dụng API sau:

```text
GET /reviews
```

Trang này hiển thị các review records đã được upload từ DynamoDB.

Trang có thể hiển thị các thông tin như:

```text
Review ID
File name
Upload date
Status
Architecture type
```

![Review History page](/images/5-Workshop/5.5-Review-api/Review-history-page.png)

#### Bước 9: Kết nối trang Review Detail

Trang Review Detail sử dụng API sau:

```text
GET /reviews/{reviewId}
```

Trang này hiển thị thông tin chi tiết của một review được chọn.

Trang có thể hiển thị các thông tin như:

```text
Review ID
File name
File type
File size
Upload date
Review status
```

#### Bước 10: Kết nối trang Review Progress

Trang Review Progress sử dụng API sau:

```text
GET /reviews/{reviewId}/status
```

Trang này hiển thị trạng thái hiện tại của review workflow.

Ở giai đoạn triển khai hiện tại, các diagrams đã upload được đánh dấu là:

```text
uploaded
```

Ở giai đoạn tiếp theo, trạng thái này sẽ được cập nhật bởi AI review workflow.

![Review Detail and Progress page](/images/5-Workshop/5.5-Review-api/Review-detail-and-process-page.png)