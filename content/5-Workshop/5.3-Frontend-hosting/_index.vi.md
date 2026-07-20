---
title : "Triển khai React Frontend với S3 và CloudFront"
date : 2026-07-03
weight : 3
chapter : false
pre : " <b> 5.3. </b> "
---

#### Tổng quan về việc lưu trữ frontend

Trong phần này, frontend React của dự án **AI AWS Architecture Reviewer** được triển khai lên AWS bằng **Amazon S3** và **Amazon CloudFront**.

Ứng dụng React được build cục bộ bằng Vite. Sau khi bản build production được tạo, các tệp bên trong thư mục `dist` sẽ được tải lên một Amazon S3 bucket. Sau đó, Amazon CloudFront được sử dụng để phân phối website đến người dùng một cách an toàn với hiệu suất và khả năng lưu bộ nhớ đệm tốt hơn.

Luồng triển khai frontend như sau:

```text
Mã nguồn React → npm run build → thư mục dist → Amazon S3 Frontend Bucket → Amazon CloudFront → Người dùng
```

Frontend bucket được sử dụng trong dự án này là:

```text
ai-aws-reviewer-frontend-tiersteam
```

Tên miền CloudFront được sử dụng để truy cập website đã triển khai là:

```text
https://d9353ayez9zar.cloudfront.net
```

#### Bước 1: Build ứng dụng React

Mở PowerShell và di chuyển đến thư mục dự án:

```text
cd D:\Learning\AWS\ai-aws-architecture-reviewer
```

Chạy lệnh build:

```text
npm run build
```

Sau khi quá trình build hoàn tất, Vite sẽ tạo các tệp production trong thư mục `dist`.

#### Bước 2: Tạo S3 frontend bucket

Tạo một Amazon S3 bucket để lưu trữ các tệp build production của ứng dụng React.

Tên bucket được sử dụng trong dự án này là:

```text
ai-aws-reviewer-frontend-tiersteam
```

Bucket này lưu trữ các tệp như:

```text
index.html
Các tài nguyên JavaScript
Các tài nguyên CSS
Các tài nguyên hình ảnh
Các tệp frontend tĩnh khác
```

![S3 React App](/images/5-Workshop/5.3-Frontend-hosting/ai-aws-reviewer-frontend-tiersteam.png)

#### Bước 3: Tải các tệp build frontend lên S3

Sau khi ứng dụng React được build, tải nội dung của thư mục `dist` lên S3 frontend bucket.

Chạy lệnh sau:

```text
aws s3 sync dist s3://ai-aws-reviewer-frontend-tiersteam --delete
```

Tùy chọn `--delete` sẽ xóa các tệp cũ trong S3 bucket nếu chúng không còn tồn tại trong bản build mới nhất. Điều này giúp ngăn CloudFront hoặc trình duyệt tải các tài nguyên frontend đã lỗi thời.

#### Bước 4: Tạo CloudFront distribution

Amazon CloudFront được sử dụng để phân phối React frontend đến người dùng.

CloudFront distribution kết nối với S3 frontend bucket với vai trò là origin. Người dùng truy cập frontend thông qua tên miền CloudFront thay vì truy cập trực tiếp vào S3 bucket.

Tên miền CloudFront distribution:

```text
https://d9353ayez9zar.cloudfront.net
```

CloudFront distribution ID:

```text
E2JHD76RIC6AML
```

![CloudFront](/images/5-Workshop/5.3-Frontend-hosting/ai-aws-reviewer-cloudfront.png)

#### Bước 5: Cấu hình Origin Access Control

S3 frontend bucket được giữ ở chế độ private. Để cho phép CloudFront đọc các tệp từ S3 bucket private, Origin Access Control được cấu hình.

Cấu hình này giúp cải thiện tính bảo mật vì người dùng không thể truy cập trực tiếp vào S3 bucket. Họ phải truy cập website thông qua CloudFront.

![CloudFront](/images/5-Workshop/5.3-Frontend-hosting/ai-aws-reviewer-cloudfront-2.png)

#### Bước 6: Cấu hình S3 bucket policy

Sau khi cấu hình Origin Access Control, cập nhật S3 bucket policy để cho phép CloudFront distribution đọc các object từ bucket.

Bucket policy cho phép CloudFront thực hiện hành động `s3:GetObject` trên các tệp frontend.

![S3 React App Policy](/images/5-Workshop/5.3-Frontend-hosting/ai-aws-reviewer-frontend-tiersteam-policy.png)

#### Bước 7: Cấu hình default root object

Trong CloudFront, cấu hình default root object là:

```text
index.html
```

Điều này cho phép người dùng truy cập website bằng cách mở tên miền gốc của CloudFront mà không cần nhập `index.html`.

Ví dụ:

```text
https://d9353ayez9zar.cloudfront.net
```

#### Bước 8: Cấu hình React Router fallback

Vì frontend là một ứng dụng React Single Page Application, việc truy cập trực tiếp vào các route như `/reviews` hoặc `/settings` có thể trả về lỗi nếu CloudFront không tìm thấy một tệp vật lý tương ứng với đường dẫn đó.

Để khắc phục vấn đề này, các custom error response được cấu hình trong CloudFront:

```text
403 → /index.html → 200
404 → /index.html → 200
```

Điều này cho phép React Router xử lý chính xác các route của frontend.

![CloudFront](/images/5-Workshop/5.3-Frontend-hosting/ai-aws-reviewer-cloudfront-3.png)

#### Bước 9: Tạo CloudFront invalidation

Sau khi tải một bản build frontend mới lên S3, CloudFront vẫn có thể phân phối các tệp đã được lưu trong bộ nhớ đệm. Để CloudFront tải phiên bản frontend mới nhất, hãy tạo một invalidation.

Chạy lệnh sau:

```text
aws cloudfront create-invalidation --distribution-id E2JHD76RIC6AML --paths "/*"
```

Chờ cho đến khi trạng thái invalidation chuyển thành **Completed**.

![CloudFront](/images/5-Workshop/5.3-Frontend-hosting/ai-aws-reviewer-cloudfront-4.png)

#### Bước 10: Kiểm tra website đã triển khai

Mở tên miền CloudFront trong trình duyệt:

```text
https://d9353ayez9zar.cloudfront.net
```

React frontend sẽ được tải thành công.

![React App](/images/5-Workshop/5.3-Frontend-hosting/Website-project.png)
