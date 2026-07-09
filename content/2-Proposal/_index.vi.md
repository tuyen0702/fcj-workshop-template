---
title: "Bản đề xuất"
date: 2026-07-03
weight: 2
chapter: false
pre: " <b> 2. </b> "
---

Trong phần này, nội dung đề tài workshop được tóm tắt, bao gồm tuyên bố vấn đề, kiến trúc giải pháp, các dịch vụ AWS sử dụng, kế hoạch triển khai kỹ thuật, lộ trình, rủi ro và kết quả kỳ vọng.

# AI AWS Architecture Reviewer
## Nền tảng Serverless sử dụng AI để đánh giá sơ đồ kiến trúc AWS

### 1. Tóm tắt điều hành

AI AWS Architecture Reviewer là một nền tảng web serverless được thiết kế để hỗ trợ người dùng đánh giá sơ đồ kiến trúc AWS một cách tự động bằng AI và AWS Well-Architected Framework. Nền tảng cho phép người dùng upload sơ đồ kiến trúc thông qua ứng dụng web React, lưu trữ file upload an toàn trong Amazon S3, ghi metadata của mỗi lần review vào Amazon DynamoDB và kích hoạt một workflow review tự động.

Giải pháp sử dụng Amazon CloudFront và Amazon S3 để phân phối frontend React, Amazon API Gateway và AWS Lambda để xử lý upload, Amazon S3 Input Bucket để lưu trữ sơ đồ kiến trúc được upload, Amazon EventBridge và AWS Step Functions để khởi động và quản lý workflow review.

Trong workflow xử lý, AWS Lambda Diagram Extractor đọc uploaded diagram từ Amazon S3 Input Bucket và chuẩn bị dữ liệu đầu vào để gửi sang Amazon Bedrock. Amazon Bedrock nhận diện các AWS services, connections, text notes và các thành phần kiến trúc từ sơ đồ, sau đó trả về architecture JSON có cấu trúc. Architecture JSON này được sử dụng làm dữ liệu trung tâm cho các bước phân tích tiếp theo.

Sau khi có architecture JSON, hệ thống gửi dữ liệu này sang AWS Lambda Cost Tool để ước tính chi phí hàng tháng dựa trên các AWS services được phát hiện trong sơ đồ. Lambda Cost Tool tạo cost estimation result, bao gồm danh sách dịch vụ, đơn vị tính chi phí, giả định sử dụng và chi phí ước tính theo tháng.

Cuối cùng, architecture JSON và cost estimation result được gửi lại sang Amazon Bedrock để thực hiện đánh giá tổng thể kiến trúc dựa trên AWS Well-Architected Framework. Amazon Bedrock phân tích các khía cạnh như Security, Reliability, Performance Efficiency, Cost Optimization, Operational Excellence và Sustainability, đồng thời giải thích chi phí và đề xuất hướng tối ưu.

Sau khi quá trình phân tích hoàn tất, AWS Lambda PDF Generator tạo báo cáo PDF bao gồm architecture review, cost estimation, cost explanation và optimization recommendations. Báo cáo được lưu vào Amazon S3 Report Bucket, lịch sử review được cập nhật trong Amazon DynamoDB và thông báo hoàn tất review được gửi đến người dùng thông qua Amazon SNS. Amazon CloudWatch được sử dụng để ghi log và giám sát hệ thống, trong khi AWS IAM được dùng để áp dụng quyền truy cập theo nguyên tắc least privilege trên toàn hệ thống.

Mục tiêu của đề tài là cung cấp một giải pháp AWS serverless thực tế, có khả năng mở rộng và tối ưu chi phí, giúp sinh viên, người học và nhóm dự án cloud review kiến trúc AWS nhất quán hơn, giảm công sức review thủ công và cải thiện hiểu biết về các best practices trong thiết kế kiến trúc cloud.

---

### 2. Tuyên bố vấn đề

### Vấn đề hiện tại

Việc review một kiến trúc AWS thủ công đòi hỏi kiến thức về nhiều dịch vụ AWS, các mẫu thiết kế cloud, best practices về bảo mật, chiến lược đảm bảo độ tin cậy, tối ưu hiệu năng, tối ưu chi phí và vận hành hệ thống. Đối với sinh viên, người mới học cloud hoặc các nhóm dự án, việc xác định một kiến trúc AWS có tuân thủ AWS Well-Architected Framework hay không thường gặp nhiều khó khăn.

Các thách thức phổ biến gồm:

- Sơ đồ kiến trúc AWS thường được review thủ công và thiếu tính nhất quán.
- Sinh viên có thể không biết kiến trúc của mình đang thiếu dịch vụ quan trọng nào hoặc có rủi ro thiết kế nào.
- Review thủ công yêu cầu kinh nghiệm về cloud architecture và mất nhiều thời gian.
- Chưa có một hệ thống tập trung để upload, review, lưu trữ và theo dõi lịch sử review kiến trúc.
- Việc tạo một báo cáo review có cấu trúc rõ ràng bằng tay thường mất thời gian.
- Các nhóm cần một giải pháp tự động có thể phân tích sơ đồ kiến trúc và đưa ra đề xuất cải thiện.

### Giải pháp

AI AWS Architecture Reviewer cung cấp một workflow serverless tự động để review sơ đồ kiến trúc AWS. Người dùng truy cập ứng dụng web thông qua Amazon CloudFront. Frontend React được phân phối từ S3 Static Website bucket. Người dùng upload sơ đồ kiến trúc thông qua frontend, sau đó request được gửi đến Amazon API Gateway.

API Gateway chuyển upload request đến AWS Lambda Upload Service. Lambda function validate file được upload, lưu diagram vào Amazon S3 Input Bucket và ghi metadata ban đầu vào Amazon DynamoDB. Sau khi object được tạo trong input bucket, Amazon S3 publish object-created event. Event này được route thông qua Amazon EventBridge để khởi động AWS Step Functions review workflow.

AWS Step Functions điều phối toàn bộ quá trình review. Đầu tiên, Step Functions gọi AWS Lambda Diagram Extractor để đọc uploaded diagram từ S3 Input Bucket. Lambda Diagram Extractor chuẩn bị dữ liệu đầu vào và gửi diagram sang Amazon Bedrock. Amazon Bedrock phân tích sơ đồ để nhận diện AWS services, connections, text notes và các thành phần kiến trúc quan trọng, sau đó trả về architecture JSON có cấu trúc.

Sau khi nhận được architecture JSON, Lambda Diagram Extractor gửi dữ liệu này sang AWS Lambda Cost Tool. Lambda Cost Tool sử dụng danh sách AWS services trong architecture JSON để ước tính chi phí hàng tháng. Kết quả của bước này là cost estimation result, bao gồm các dịch vụ được phát hiện, giả định sử dụng, chi phí ước tính và các thành phần có khả năng ảnh hưởng lớn đến ngân sách.

Tiếp theo, architecture JSON và cost estimation result được gửi lại sang Amazon Bedrock để thực hiện đánh giá tổng thể kiến trúc. Ở bước này, Amazon Bedrock phân tích kiến trúc dựa trên AWS Well-Architected Framework, giải thích các rủi ro thiết kế, đánh giá chi phí, đề xuất cost optimization và đưa ra khuyến nghị cải thiện.

Sau khi Bedrock hoàn tất phần đánh giá tổng thể, AWS Lambda PDF Generator tạo báo cáo PDF từ kết quả AI review. Báo cáo được lưu trong Amazon S3 Report Bucket, review history được cập nhật trong Amazon DynamoDB và Amazon SNS gửi thông báo review đến người dùng.

Flow tổng thể của hệ thống:

User → Amazon CloudFront → S3 Static Website React App → API Gateway → Lambda Upload Service → S3 Input Bucket → EventBridge → Step Functions → Lambda Diagram Extractor → Amazon Bedrock sinh architecture JSON → Lambda Cost Tool ước tính monthly cost → Amazon Bedrock đánh giá tổng thể kiến trúc và tối ưu chi phí → Lambda PDF Generator → S3 Report Bucket + DynamoDB + SNS Email Notification.

### Lợi ích và hoàn vốn đầu tư

Giải pháp cung cấp một công cụ thực tế để học tập và review thiết kế kiến trúc AWS. Hệ thống giúp giảm công sức review thủ công, cải thiện tính nhất quán trong đánh giá kiến trúc và hỗ trợ người dùng hiểu rõ hơn về AWS Well-Architected principles.

Các lợi ích chính gồm:

- Tự động review kiến trúc AWS dựa trên Well-Architected best practices.
- Cung cấp phản hồi nhanh hơn cho sinh viên và nhóm dự án.
- Lưu trữ tập trung các sơ đồ đã upload và metadata review.
- Theo dõi lịch sử review thông qua DynamoDB.
- Tạo báo cáo PDF phục vụ tài liệu và thuyết trình.
- Gửi email notification khi quá trình review hoàn tất.
- Kiến trúc serverless giúp giảm công sức vận hành.
- Thiết kế tối ưu chi phí vì hầu hết dịch vụ hoạt động theo mô hình pay-per-use.
- Dễ mở rộng thông qua EventBridge, Step Functions, Lambda, S3 và DynamoDB.

Đề tài cũng tạo giá trị dài hạn như một nền tảng giáo dục có thể tái sử dụng cho việc học cloud architecture, review dự án AWS và phát triển các công cụ đánh giá cloud bằng AI trong tương lai.

---

### 3. Kiến trúc giải pháp

Nền tảng sử dụng kiến trúc AWS serverless event-driven. Frontend layer được host bằng Amazon S3 và phân phối thông qua Amazon CloudFront. API layer được xây dựng bằng Amazon API Gateway và AWS Lambda. File upload được lưu trong Amazon S3 Input Bucket, trong khi metadata review được lưu trong Amazon DynamoDB. Workflow review được kích hoạt bởi Amazon EventBridge và được điều phối bằng AWS Step Functions.

Trong Processing Layer, AWS Lambda Diagram Extractor đọc uploaded diagram từ S3 Input Bucket và gửi diagram sang Amazon Bedrock để phân tích sơ đồ. Amazon Bedrock trả về architecture JSON, bao gồm các AWS services, connections, text notes và các thành phần kiến trúc được nhận diện. Sau đó, architecture JSON được gửi sang AWS Lambda Cost Tool để ước tính monthly cost. Kết quả cost estimation cùng với architecture JSON được gửi lại sang Amazon Bedrock để đánh giá tổng thể kiến trúc theo AWS Well-Architected Framework và tạo nội dung phân tích cuối cùng. AWS Lambda PDF Generator sử dụng kết quả này để tạo báo cáo PDF.

Kiến trúc bao gồm các bước chính sau:

1. User truy cập web application thông qua Amazon CloudFront.
2. CloudFront phân phối React frontend từ S3 Static Website bucket.
3. User submit architecture diagram thông qua frontend.
4. API Gateway nhận upload request và gửi đến AWS Lambda Upload Service.
5. Lambda Upload Service validate upload request và lưu uploaded diagram vào Amazon S3 Input Bucket.
6. Amazon S3 publish object-created event sau khi diagram được upload.
7. Amazon EventBridge nhận object-created event và khởi động AWS Step Functions review workflow.
8. AWS Step Functions điều phối review workflow và gọi AWS Lambda Diagram Extractor.
9. AWS Lambda Diagram Extractor gửi uploaded diagram sang Amazon Bedrock để Bedrock nhận diện AWS services, connections, text notes và sinh architecture JSON.
10. AWS Lambda Diagram Extractor gửi architecture JSON sang AWS Lambda Cost Tool để ước tính monthly cost.
11. AWS Lambda Cost Tool gửi cost estimation result cùng với architecture JSON sang Amazon Bedrock để đánh giá toàn bộ kiến trúc, giải thích chi phí và đề xuất tối ưu.
12. AWS Lambda PDF Generator tạo PDF report từ kết quả final AI review.
13. AWS Lambda PDF Generator cập nhật review history và review status vào Amazon DynamoDB.
14. AWS Lambda PDF Generator lưu generated PDF report vào Amazon S3 Report Bucket.
15. Amazon SNS gửi review notification đến người dùng sau khi quá trình review hoàn tất.
16. Amazon CloudWatch ghi logs, metrics và hỗ trợ troubleshooting cho Lambda, Step Functions, API Gateway và workflow execution.
17. AWS IAM áp dụng least privilege access giữa các services.

![AI AWS Architecture Reviewer Architecture](/images/2-Proposal/ai-aws-architecture-reviewer-proposal.png)

### Các dịch vụ AWS sử dụng

- **Amazon CloudFront**: Phân phối ứng dụng web React và cải thiện hiệu năng frontend.
- **Amazon S3 Static Website Bucket**: Lưu React production build, bao gồm `index.html` và static assets.
- **Amazon API Gateway**: Cung cấp API endpoints cho upload, review history, review detail và review status.
- **AWS Lambda Upload Service**: Validate upload request, lưu uploaded diagrams, ghi metadata và xử lý các review data APIs.
- **Amazon S3 Input Bucket**: Lưu trữ sơ đồ kiến trúc gốc do người dùng upload.
- **Amazon DynamoDB**: Lưu review metadata, thông tin upload, review status và review history.
- **Amazon EventBridge**: Bắt S3 object-created events và kích hoạt review workflow.
- **AWS Step Functions**: Điều phối review workflow với retry và error handling.
- **AWS Lambda Diagram Extractor**: Đọc uploaded architecture diagram từ Amazon S3 Input Bucket, chuẩn bị dữ liệu đầu vào và gửi diagram sang Amazon Bedrock để nhận diện các AWS services, connections, text notes và sinh architecture JSON.
- **Amazon Bedrock**: Được sử dụng trong hai giai đoạn chính. Giai đoạn đầu, Bedrock phân tích diagram để sinh architecture JSON có cấu trúc. Giai đoạn sau, Bedrock nhận architecture JSON và cost estimation result để đánh giá tổng thể kiến trúc theo AWS Well-Architected Framework, giải thích chi phí và đề xuất hướng tối ưu.
- **AWS Lambda Cost Tool**: Nhận architecture JSON từ Lambda Diagram Extractor, phân tích các AWS services được phát hiện trong sơ đồ và ước tính monthly cost. Kết quả cost estimation được gửi lại sang Amazon Bedrock để phục vụ bước đánh giá tổng thể và cost optimization.
- **AWS Lambda PDF Generator**: Tạo PDF reports từ kết quả final AI review, bao gồm architecture review, cost estimation, cost explanation và optimization recommendations.
- **Amazon S3 Report Bucket**: Lưu generated PDF reports với server-side encryption.
- **Amazon SNS**: Gửi email notifications khi quá trình review hoàn tất.
- **Amazon CloudWatch**: Cung cấp logging, monitoring và troubleshooting cho Lambda và workflow execution.
- **AWS IAM**: Kiểm soát quyền truy cập của các services bằng least privilege access.

### Thiết kế thành phần

- **Frontend Layer**: Ứng dụng React được host trong Amazon S3 và phân phối thông qua Amazon CloudFront. Frontend gồm các trang Dashboard, Upload Diagram, Review Progress, Review History, Report Detail và Settings.
- **API Layer**: Amazon API Gateway cung cấp các endpoints như `POST /upload`, `GET /reviews`, `GET /reviews/{reviewId}` và `GET /reviews/{reviewId}/status`.
- **Upload Processing Layer**: AWS Lambda Upload Service validate uploaded files, tạo unique review ID, lưu file vào S3 và ghi metadata vào DynamoDB.
- **Storage Layer**: Amazon S3 Input Bucket lưu uploaded diagrams, Amazon S3 Report Bucket lưu generated PDF reports, DynamoDB lưu metadata và review history.
- **Workflow Layer**: EventBridge nhận object-created events từ S3 và khởi động Step Functions để điều phối quá trình review.
- **AI Processing Layer**: AWS Lambda Diagram Extractor đọc uploaded diagram từ S3 Input Bucket và gửi diagram sang Amazon Bedrock để trích xuất thông tin kiến trúc. Amazon Bedrock nhận diện AWS services, connections, text notes và trả về architecture JSON. Architecture JSON sau đó được dùng làm dữ liệu đầu vào cho bước ước tính chi phí và bước đánh giá tổng thể kiến trúc.
- **Cost Analysis Component**: AWS Lambda Cost Tool nhận architecture JSON, xác định các AWS services xuất hiện trong sơ đồ và ước tính monthly cost dựa trên các giả định sử dụng ở mức demo. Kết quả cost estimation giúp báo cáo không chỉ đánh giá thiết kế kiến trúc mà còn cung cấp góc nhìn về chi phí vận hành dự kiến.
- **Final AI Review Component**: Amazon Bedrock nhận architecture JSON và cost estimation result để đánh giá toàn bộ kiến trúc theo AWS Well-Architected Framework. Kết quả phân tích bao gồm điểm mạnh, rủi ro, vấn đề cần cải thiện, giải thích chi phí và đề xuất tối ưu.
- **Reporting Layer**: AWS Lambda PDF Generator nhận kết quả final AI review từ Amazon Bedrock, tạo PDF report và lưu báo cáo vào Amazon S3 Report Bucket.
- **Notification Layer**: Amazon SNS gửi email notifications sau khi review hoàn tất.
- **Monitoring and Security Layer**: CloudWatch giám sát logs và workflow execution, trong khi IAM áp dụng least privilege access.

---

### 4. Triển khai kỹ thuật

**Các giai đoạn triển khai**

Dự án được triển khai theo nhiều giai đoạn, bắt đầu từ phát triển frontend và chức năng upload cơ bản, sau đó mở rộng sang event-driven AI workflow và PDF reporting.

- **Phát triển frontend và hosting**: Xây dựng frontend React bằng Vite, tạo các trang chính, build production files, upload lên Amazon S3 và phân phối frontend thông qua Amazon CloudFront.
- **Triển khai upload backend**: Tạo S3 Input Bucket, DynamoDB review table, Lambda execution role và Lambda Upload Service để xử lý file upload và lưu metadata.
- **API Gateway và Review Data API**: Tạo các API Gateway routes cho upload diagram và lấy dữ liệu review. Cấu hình CORS để cho phép request từ CloudFront frontend đã deploy.
- **Event-Driven Review Workflow**: Cấu hình S3 object-created events, route event qua EventBridge và khởi động Step Functions workflow để xử lý uploaded architecture diagram.
- **AI Analysis và Reporting**: Sử dụng Lambda Diagram Extractor để đọc uploaded diagram và gửi diagram sang Amazon Bedrock nhằm sinh architecture JSON. Sau đó, architecture JSON được gửi sang Lambda Cost Tool để ước tính monthly cost. Kết quả architecture JSON và cost estimation result được gửi lại sang Amazon Bedrock để đánh giá tổng thể kiến trúc theo AWS Well-Architected Framework. Cuối cùng, Lambda PDF Generator tạo PDF report và lưu vào S3 Report Bucket.
- **Notification, Monitoring và Security**: Gửi review notifications thông qua SNS, giám sát logs và workflow execution bằng CloudWatch, đồng thời áp dụng IAM least privilege permissions.

### Yêu cầu kỹ thuật

- React frontend sử dụng Vite.
- Amazon S3 frontend bucket cho static hosting.
- Amazon CloudFront distribution với Origin Access Control.
- API Gateway cho backend APIs.
- AWS Lambda cho upload handling và review API logic.
- Amazon S3 Input Bucket cho uploaded diagrams.
- Amazon DynamoDB cho metadata và review history.
- Amazon EventBridge cho event-driven workflow triggering.
- AWS Step Functions cho review orchestration.
- AWS Lambda Diagram Extractor cho diagram parsing.
- Amazon Bedrock cho diagram-to-JSON extraction và final AI architecture review.
- AWS Lambda Cost Tool cho monthly cost estimation dựa trên architecture JSON.
- AWS Lambda PDF Generator cho report generation.
- Amazon S3 Report Bucket cho PDF storage.
- Amazon SNS cho email notification.
- CloudWatch cho monitoring và troubleshooting.
- IAM cho least privilege access control.

---

### 5. Lộ trình & Mốc triển khai

**Project Timeline**

Dự án được lập kế hoạch và triển khai trong 4 tuần thực tập, từ Tuần 9 đến Tuần 12. Lộ trình tập trung vào thiết kế kiến trúc, phát triển frontend, cấu hình backend trên AWS, triển khai hệ thống, tích hợp workflow AI, kiểm thử và hoàn thiện tài liệu.

- **Tuần 9: Lập kế hoạch dự án và thiết kế kiến trúc**
  - Xác định đề tài dự án: AI AWS Architecture Reviewer.
  - Phân tích yêu cầu hệ thống và luồng xử lý chính của người dùng.
  - Nghiên cứu AWS Well-Architected Framework.
  - Lựa chọn các dịch vụ AWS cần sử dụng cho giải pháp.
  - Thiết kế sơ đồ kiến trúc AWS serverless tổng thể.
  - Lập kế hoạch cho các chức năng chính của ứng dụng, bao gồm Dashboard, Upload Diagram, Review Progress, Review History, Report Detail và Settings.

- **Tuần 10: Phát triển Frontend**
  - Tạo dự án React bằng Vite.
  - Xây dựng bố cục frontend chính với Header, Sidebar và Main Content.
  - Phát triển trang Dashboard.
  - Phát triển trang Upload Diagram.
  - Phát triển trang Review Progress.
  - Phát triển trang Review History.
  - Phát triển trang Report Detail và Settings.
  - Chuẩn bị cấu trúc frontend để tích hợp API với backend AWS.

- **Tuần 11: Xây dựng Backend AWS và triển khai Frontend**
  - Tạo S3 Frontend Bucket để lưu trữ bản build production của React.
  - Build và upload các file production của React lên Amazon S3.
  - Tạo Amazon CloudFront Distribution.
  - Cấu hình Origin Access Control, S3 bucket policy, default root object, SPA fallback và CloudFront invalidation.
  - Tạo S3 Input Bucket để lưu các sơ đồ kiến trúc do người dùng upload.
  - Tạo DynamoDB Review Table để lưu metadata của các lần review.
  - Tạo Lambda Execution Role với các quyền cần thiết cho S3, DynamoDB và CloudWatch.
  - Tạo Lambda Upload Service.
  - Tạo các route trong API Gateway, bao gồm `POST /upload`, `GET /reviews`, `GET /reviews/{reviewId}` và `GET /reviews/{reviewId}/status`.
  - Cấu hình CORS cho localhost và CloudFront frontend domain.
  - Kiểm thử chức năng upload file từ frontend lên S3 và ghi metadata vào DynamoDB.

- **Tuần 12: Tích hợp AI Workflow, Reporting, Kiểm thử và Hoàn thiện**
  - Tạo AWS Step Functions Review Workflow.
  - Tạo Lambda Diagram Extractor để đọc uploaded diagram từ S3 Input Bucket.
  - Tích hợp Amazon Bedrock ở bước đầu để phân tích diagram và sinh architecture JSON.
  - Tạo Lambda Cost Tool để ước tính monthly cost dựa trên architecture JSON.
  - Tích hợp Amazon Bedrock ở bước final review để đánh giá toàn bộ kiến trúc theo AWS Well-Architected Framework, giải thích chi phí và đề xuất tối ưu.
  - Tạo Lambda PDF Generator để tạo báo cáo review từ kết quả final AI review.
  - Lưu các báo cáo PDF được tạo vào S3 Report Bucket.
  - Gửi thông báo hoàn tất review thông qua Amazon SNS.
  - Giám sát logs và trạng thái thực thi bằng Amazon CloudWatch.
  - Kiểm tra lại IAM permissions theo nguyên tắc least privilege access.
  - Thực hiện kiểm thử end-to-end cho upload, diagram extraction, cost estimation, AI review, report generation và notification.

---

### 6. Ước tính ngân sách

Dự án sử dụng các dịch vụ AWS serverless nên chi phí chủ yếu phụ thuộc vào mức sử dụng. Trong giai đoạn MVP và demo vừa, lượng truy cập dự kiến không quá lớn nhưng hệ thống vẫn có đầy đủ các thành phần chính như frontend hosting, API backend, file storage, metadata database, event-driven workflow, AI analysis, PDF report generation, email notification và monitoring.

### Giả định tính toán

Ước tính ngân sách được tính dựa trên quy mô demo vừa như sau:

- Số lượng người dùng: khoảng 5–10 users.
- Số lượng diagram upload: khoảng 200–300 diagrams/tháng.
- Dung lượng trung bình mỗi diagram: khoảng 3–5 MB.
- Số lượng PDF report tạo ra: khoảng 200–300 reports/tháng.
- Số lần chạy review workflow: khoảng 200–300 executions/tháng.
- Số API requests: khoảng 5.000–15.000 requests/tháng.
- Mỗi workflow gồm các bước: upload diagram, lưu metadata, kích hoạt workflow, gửi diagram sang Bedrock để sinh architecture JSON, ước tính monthly cost bằng Lambda Cost Tool, gửi architecture JSON và cost estimation result sang Bedrock để đánh giá tổng thể, tạo PDF report, lưu report và gửi notification.
- Amazon Bedrock được sử dụng để phân tích kiến trúc ở mức demo, không phải production traffic lớn.

### Chi phí hạ tầng ước tính

- **Amazon S3**: khoảng **0.10–0.50 USD/tháng**  
  Dùng để lưu React frontend build files, uploaded diagrams và generated PDF reports. Với dung lượng vài GB trong giai đoạn demo, chi phí S3 rất thấp.

- **Amazon CloudFront**: khoảng **0.00–1.00 USD/tháng**  
  Dùng để phân phối frontend web application. Với lượng truy cập demo vừa, chi phí CloudFront thường thấp vì dữ liệu truyền tải chưa nhiều.

- **Amazon API Gateway**: khoảng **0.05–0.20 USD/tháng**  
  Dùng để xử lý các API requests như `POST /upload`, `GET /reviews`, `GET /reviews/{reviewId}` và `GET /reviews/{reviewId}/status`.

- **AWS Lambda**: khoảng **0.00–0.70 USD/tháng**  
  Dùng để xử lý upload, validate file, ghi metadata, đọc uploaded diagram, điều phối dữ liệu architecture JSON, ước tính monthly cost thông qua Lambda Cost Tool và tạo PDF reports. Với số lượng request ở mức demo, chi phí Lambda vẫn rất thấp.

- **AWS Lambda Cost Tool**: khoảng **0.00–0.20 USD/tháng**  
  Dùng để nhận architecture JSON, xác định các AWS services trong sơ đồ và ước tính monthly cost. Với quy mô demo 200–300 diagrams/tháng, chi phí chạy Lambda Cost Tool rất thấp. Chi phí thực tế phụ thuộc vào thời gian chạy Lambda, số lượng services cần tính toán và độ phức tạp của logic cost estimation.

- **Amazon DynamoDB**: khoảng **0.05–0.30 USD/tháng**  
  Dùng để lưu review metadata, review history và review status. Dữ liệu mỗi review nhỏ nên chi phí DynamoDB thấp trong giai đoạn demo.

- **Amazon EventBridge**: khoảng **0.01–0.05 USD/tháng**  
  Dùng để route S3 object-created events và kích hoạt workflow sau khi user upload diagram.

- **AWS Step Functions**: khoảng **0.00–0.30 USD/tháng**  
  Dùng để điều phối review workflow. Với khoảng 200–300 workflow executions/tháng, chi phí Step Functions vẫn rất thấp nếu số state transitions không quá lớn.

- **Amazon SNS**: khoảng **0.00–0.10 USD/tháng**  
  Dùng để gửi email notifications khi quá trình review hoàn tất.

- **Amazon CloudWatch**: khoảng **0.50–2.00 USD/tháng**  
  Dùng để lưu logs và hỗ trợ monitoring cho Lambda, API Gateway và Step Functions. Chi phí CloudWatch phụ thuộc vào lượng logs được ghi ra trong quá trình test và debug.

- **Amazon Bedrock**: khoảng **5.00–35.00 USD/tháng**  
  Dùng trong hai giai đoạn: phân tích diagram để sinh architecture JSON và đánh giá tổng thể kiến trúc dựa trên architecture JSON cùng cost estimation result. Đây là thành phần có chi phí biến động lớn nhất vì phụ thuộc vào model được chọn, số lượng input/output tokens, kích thước diagram, độ dài architecture JSON, độ chi tiết của cost estimation result và số lần gọi AI. Nếu sử dụng model nhỏ, giới hạn độ dài prompt và rút gọn dữ liệu đầu vào, chi phí sẽ thấp hơn.

### Tổng chi phí ước tính

Với quy mô demo vừa, tổng chi phí hạ tầng ước tính khoảng:

**10–40 USD/tháng**

Tương đương khoảng:

**120–480 USD/năm**

Trong đó, các dịch vụ serverless cơ bản như S3, CloudFront, API Gateway, Lambda, DynamoDB, EventBridge, Step Functions, SNS và Lambda Cost Tool chiếm chi phí khá thấp. Thành phần ảnh hưởng lớn nhất đến ngân sách là Amazon Bedrock, vì hệ thống sử dụng Bedrock cho cả bước sinh architecture JSON từ diagram và bước final AI architecture review.

### Ghi chú

Để kiểm soát chi phí, hệ thống nên giới hạn dung lượng file upload, giới hạn số lần gọi AI, chọn model Bedrock phù hợp, rút gọn dữ liệu diagram trước khi gửi sang Bedrock, chuẩn hóa architecture JSON ở mức cần thiết, chỉ gửi cost estimation result quan trọng thay vì toàn bộ dữ liệu thô, giảm lượng log không cần thiết và sử dụng AWS Budgets để theo dõi chi phí hàng tháng.

---

### 7. Đánh giá rủi ro

#### Ma trận rủi ro

- File diagram không hợp lệ hoặc không được hỗ trợ: Ảnh hưởng trung bình, xác suất trung bình.
- Kết quả AI review không chính xác hoặc chưa đầy đủ: Ảnh hưởng cao, xác suất trung bình.
- Workflow thất bại trong quá trình extraction hoặc report generation: Ảnh hưởng trung bình, xác suất trung bình.
- Lỗi CORS giữa CloudFront và API Gateway: Ảnh hưởng trung bình, xác suất trung bình.
- CloudFront cache vẫn phục vụ frontend build cũ: Ảnh hưởng thấp đến trung bình, xác suất trung bình.
- IAM permissions quá rộng hoặc quá hạn chế: Ảnh hưởng cao, xác suất trung bình.
- Chi phí Amazon Bedrock tăng do token usage cao: Ảnh hưởng trung bình, xác suất thấp.
- Bedrock nhận diện sai AWS services hoặc connections từ diagram: Ảnh hưởng cao, xác suất trung bình.
- Architecture JSON sinh ra chưa đầy đủ hoặc không đúng cấu trúc: Ảnh hưởng cao, xác suất trung bình.
- Cost estimation không chính xác do thiếu usage assumptions: Ảnh hưởng trung bình, xác suất trung bình.
- Chi phí Amazon Bedrock tăng do gọi AI ở cả bước sinh JSON và bước final review: Ảnh hưởng trung bình, xác suất trung bình.

#### Chiến lược giảm thiểu

- Validate file type và file size trước khi lưu upload.
- Sử dụng structured prompts cho Amazon Bedrock.
- Sử dụng Step Functions retry và error handling.
- Lưu workflow status trong DynamoDB.
- Cấu hình CORS chính xác cho localhost và CloudFront domain.
- Tạo CloudFront invalidation sau mỗi lần deploy frontend.
- Áp dụng least privilege IAM policies.
- Theo dõi Lambda, API Gateway, Step Functions và Bedrock usage thông qua CloudWatch.
- Sử dụng AWS Budgets để theo dõi chi phí hàng tháng dự kiến.
- Chuẩn hóa prompt cho bước diagram-to-JSON extraction.
- Validate architecture JSON trước khi gửi sang Lambda Cost Tool.
- Sử dụng default usage assumptions rõ ràng cho cost estimation.
- Giới hạn kích thước diagram và độ dài dữ liệu gửi sang Bedrock.
- Tách riêng prompt sinh architecture JSON và prompt final architecture review để dễ kiểm soát output.

#### Kế hoạch dự phòng

- Nếu AI analysis thất bại, đánh dấu review status là failed trong DynamoDB.
- Nếu PDF generation thất bại, giữ lại AI review result và retry quá trình tạo PDF.
- Nếu SNS email thất bại, cho phép user xem report trực tiếp từ web application.
- Nếu CloudFront vẫn phục vụ file cũ, tạo invalidation và redeploy frontend.
- Nếu Bedrock usage trở nên tốn kém, giới hạn input size hoặc giảm số lượng review requests.

---

### 8. Kết quả kỳ vọng

#### Cải tiến kỹ thuật

Dự án kỳ vọng tạo ra một nền tảng AWS serverless hoạt động được, cho phép người dùng upload architecture diagrams và nhận kết quả review kiến trúc có hỗ trợ bởi AI.

Các kết quả kỹ thuật kỳ vọng gồm:

- Ứng dụng web React hoạt động trên S3 và được phân phối thông qua CloudFront.
- Phân phối frontend an toàn bằng CloudFront OAC và private S3 bucket access.
- API Gateway routes cho upload và lấy review data.
- Lambda Upload Service cho file validation, S3 storage và DynamoDB metadata.
- S3 Input Bucket cho uploaded architecture diagrams.
- DynamoDB Review Database cho review history và status tracking.
- EventBridge và Step Functions workflow cho automated review processing.
- Lambda Diagram Extractor đọc uploaded diagram và gửi diagram sang Amazon Bedrock.
- Amazon Bedrock sinh architecture JSON từ uploaded diagram.
- Lambda Cost Tool ước tính monthly cost dựa trên architecture JSON.
- Amazon Bedrock thực hiện final AI architecture review dựa trên architecture JSON và cost estimation result.
- PDF report generation bao gồm architecture review, cost estimation, cost explanation và optimization recommendations.
- PDF report được lưu trữ trong S3 Report Bucket.
- SNS email notification khi review hoàn tất.
- CloudWatch monitoring và IAM least privilege security.

#### Giá trị dài hạn

Nền tảng có thể được tái sử dụng như một công cụ học tập cho AWS architecture design và thực hành Well-Architected review. Hệ thống cũng có thể được mở rộng thành một nền tảng đánh giá kiến trúc cloud nâng cao hơn với các tính năng như user authentication, multi-user review history, architecture scoring, advanced report templates và hỗ trợ nhiều định dạng diagram hơn.

Dự án cung cấp kinh nghiệm thực tế với các dịch vụ AWS quan trọng, bao gồm CloudFront, S3, API Gateway, Lambda, DynamoDB, EventBridge, Step Functions, Amazon Bedrock, SNS, CloudWatch và IAM.