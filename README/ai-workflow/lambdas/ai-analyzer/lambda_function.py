import boto3
import json
import os
import re
import urllib.parse
from datetime import datetime

s3 = boto3.client("s3")

BEDROCK_REGION = os.environ.get("BEDROCK_REGION", "ap-southeast-1")
MODEL_ID = os.environ.get("MODEL_ID", "global.amazon.nova-2-lite-v1:0")

bedrock = boto3.client("bedrock-runtime", region_name=BEDROCK_REGION)

ALLOWED_IMAGE_FORMATS = {
    ".png": "png",
    ".jpg": "jpeg",
    ".jpeg": "jpeg",
    ".webp": "webp"
}


def lambda_handler(event, context):
    try:
        bucket, key, region = get_input(event)
        review_id = extract_review_id_from_key(key)

        image_format = get_image_format(key)

        if image_format is None:
            return {
                "status": "INVALID_FILE_TYPE",
                "message": "Analyzer chỉ hỗ trợ file ảnh PNG, JPG, JPEG hoặc WEBP.",
                "review_id": review_id,
                "source": {
                    "bucket": bucket,
                    "key": key,
                    "region": region
                }
            }

        image_bytes = read_s3_bytes(bucket, key)

        ai_result = analyze_image_with_bedrock(image_bytes, image_format)

        normalized_result = normalize_ai_result(
            ai_result=ai_result,
            review_id=review_id,
            bucket=bucket,
            key=key,
            region=region,
            image_format=image_format
        )

        return normalized_result

    except Exception as e:
        return {
            "status": "FAILED",
            "message": "AI Architecture Analyzer thất bại.",
            "error": str(e),
            "failed_at": datetime.utcnow().isoformat()
        }


def get_input(event):
    if "bucket" in event and "key" in event:
        bucket = event["bucket"]
        key = urllib.parse.unquote_plus(event["key"])
        region = event.get("region", "ap-southeast-1")
        return bucket, key, region

    if "detail" in event:
        bucket = event["detail"]["bucket"]["name"]
        key = urllib.parse.unquote_plus(event["detail"]["object"]["key"])
        region = event.get("region", "ap-southeast-1")
        return bucket, key, region

    raise ValueError("Input event không có bucket/key hợp lệ.")


def read_s3_bytes(bucket, key):
    obj = s3.get_object(Bucket=bucket, Key=key)
    return obj["Body"].read()


def get_image_format(key):
    lower_key = key.lower()

    for ext, fmt in ALLOWED_IMAGE_FORMATS.items():
        if lower_key.endswith(ext):
            return fmt

    return None


def analyze_image_with_bedrock(image_bytes, image_format):
    prompt = """
Bạn là AI AWS Architecture Reviewer.

Nhiệm vụ:
Phân tích ảnh sơ đồ kiến trúc AWS và đánh giá kiến trúc dựa trên AWS Well-Architected Framework.

Chỉ trả về JSON hợp lệ. Không dùng markdown. Không giải thích ngoài JSON.

Nếu không phát hiện được dịch vụ AWS nào trong ảnh, trả về:
{
  "status": "NO_SERVICES_DETECTED",
  "message": "Không quét được dịch vụ AWS nào trong sơ đồ.",
  "architecture_json": {
    "services": [],
    "connections": [],
    "unknown_components": [],
    "service_count": 0
  },
  "well_architected_review": null,
  "limitations": ["Không đủ dữ liệu để đánh giá kiến trúc."]
}

Nếu phát hiện được dịch vụ AWS, trả về đúng format sau:
{
  "status": "ANALYZED",
  "message": "Đã phân tích kiến trúc bằng AI.",
  "architecture_json": {
    "services": [
      {
        "name": "Amazon S3",
        "category": "Storage",
        "confidence": 0.9,
        "evidence": "Text/icon visible in diagram"
      }
    ],
    "connections": [
      {
        "from": "Amazon CloudFront",
        "to": "Amazon S3",
        "confidence": 0.8,
        "evidence": "Arrow from CloudFront to S3"
      }
    ],
    "unknown_components": [],
    "service_count": 1
  },
  "well_architected_review": {
    "overall_score": 80,
    "pillar_scores": {
      "Operational Excellence": 80,
      "Security": 80,
      "Reliability": 80,
      "Performance Efficiency": 80,
      "Cost Optimization": 80,
      "Sustainability": 80
    },
    "findings": [
      {
        "pillar": "Security",
        "severity": "Medium",
        "issue": "Chưa thấy IAM least privilege trong sơ đồ.",
        "evidence": "IAM role/policy không xuất hiện trong ảnh.",
        "recommendation": "Bổ sung IAM Role riêng cho từng Lambda/service và áp dụng least privilege."
      }
    ],
    "strengths": [
      "Kiến trúc sử dụng CloudFront để phân phối nội dung."
    ],
    "assumptions": [
      "Đánh giá dựa trên các thành phần nhìn thấy được trong ảnh."
    ]
  },
  "limitations": [
    "AI chỉ đánh giá dựa trên sơ đồ ảnh, không kiểm tra cấu hình thật trong AWS account."
  ]
}

Quy tắc bắt buộc:
- Chỉ liệt kê dịch vụ thật sự nhìn thấy hoặc đọc được trong ảnh.
- Không bịa service không xuất hiện trong ảnh.
- Nếu không chắc, đưa vào unknown_components.
- Đánh giá theo 6 pillar: Operational Excellence, Security, Reliability, Performance Efficiency, Cost Optimization, Sustainability.
- Nếu thiếu thông tin, ghi rõ trong assumptions hoặc limitations.
- Không tự khẳng định cấu hình thật như encryption, backup, IAM policy nếu ảnh không thể hiện.
- Tên service nên dùng tên AWS chuẩn, ví dụ: Amazon S3, AWS Lambda, Amazon API Gateway, Amazon CloudFront, Amazon RDS, Amazon EC2, Amazon DynamoDB, Amazon SNS, Amazon SQS, AWS Step Functions, Amazon EventBridge, Amazon Bedrock, Amazon CloudWatch.
"""

    response = bedrock.converse(
        modelId=MODEL_ID,
        messages=[
            {
                "role": "user",
                "content": [
                    {"text": prompt},
                    {
                        "image": {
                            "format": image_format,
                            "source": {
                                "bytes": image_bytes
                            }
                        }
                    }
                ]
            }
        ],
        inferenceConfig={
            "maxTokens": 4000,
            "temperature": 0.1
        }
    )

    output_text = response["output"]["message"]["content"][0]["text"]
    return extract_json_from_text(output_text)


def extract_json_from_text(text):
    text = text.strip()

    try:
        return json.loads(text)
    except Exception:
        pass

    match = re.search(r"\{[\s\S]*\}", text)

    if match:
        return json.loads(match.group(0))

    raise ValueError("Bedrock không trả về JSON hợp lệ.")


def normalize_ai_result(ai_result, review_id, bucket, key, region, image_format):
    status = ai_result.get("status", "ANALYZED")

    architecture_json = ai_result.get("architecture_json", {})
    services = architecture_json.get("services", [])
    connections = architecture_json.get("connections", [])
    unknown_components = architecture_json.get("unknown_components", [])

    normalized_services = normalize_services(services)

    architecture_json = {
        "services": normalized_services,
        "connections": normalize_connections(connections),
        "unknown_components": unknown_components if isinstance(unknown_components, list) else [],
        "service_count": len(normalized_services),
        "extraction_method": "amazon_bedrock_nova_vision",
        "extraction_confidence": calculate_extraction_confidence(normalized_services),
        "notes": architecture_json.get("notes", [])
    }

    if len(normalized_services) == 0:
        return {
            "status": "NO_SERVICES_DETECTED",
            "message": "Không quét được dịch vụ AWS nào trong sơ đồ. Hệ thống sẽ không thực hiện đánh giá kiến trúc.",
            "review_id": review_id,
            "source": {
                "bucket": bucket,
                "key": key,
                "region": region,
                "file_type": image_format
            },
            "analyzed_at": datetime.utcnow().isoformat(),
            "architecture_json": architecture_json,
            "well_architected_review": None,
            "limitations": [
                "Không phát hiện được dịch vụ AWS nào trong ảnh.",
                "Không đủ dữ liệu để đánh giá Well-Architected."
            ]
        }

    review = ai_result.get("well_architected_review", {})

    return {
        "status": "ANALYZED",
        "message": ai_result.get("message", "Đã phân tích kiến trúc bằng AI."),
        "review_id": review_id,
        "source": {
            "bucket": bucket,
            "key": key,
            "region": region,
            "file_type": image_format
        },
        "analyzed_at": datetime.utcnow().isoformat(),
        "architecture_json": architecture_json,
        "well_architected_review": normalize_review(review),
        "limitations": ai_result.get("limitations", [
            "Kết quả được tạo bởi AI dựa trên ảnh sơ đồ, không thay thế kiểm tra cấu hình thật trong AWS account."
        ])
    }


def normalize_services(services):
    normalized = []

    if not isinstance(services, list):
        return normalized

    for service in services:
        if isinstance(service, str):
            item = {
                "name": service,
                "category": "Unknown",
                "confidence": 0.7,
                "evidence": ""
            }
        elif isinstance(service, dict):
            item = {
                "name": str(service.get("name", "")).strip(),
                "category": service.get("category", "Unknown"),
                "confidence": float(service.get("confidence", 0.7)),
                "evidence": service.get("evidence", "")
            }
        else:
            continue

        if item["name"] and not service_exists(normalized, item["name"]):
            normalized.append(item)

    return normalized


def service_exists(services, name):
    for item in services:
        if item["name"].lower() == name.lower():
            return True
    return False


def normalize_connections(connections):
    normalized = []

    if not isinstance(connections, list):
        return normalized

    for conn in connections:
        if not isinstance(conn, dict):
            continue

        from_service = str(conn.get("from", "")).strip()
        to_service = str(conn.get("to", "")).strip()

        if from_service and to_service:
            normalized.append({
                "from": from_service,
                "to": to_service,
                "confidence": float(conn.get("confidence", 0.7)),
                "evidence": conn.get("evidence", "")
            })

    return normalized


def normalize_review(review):
    if not isinstance(review, dict):
        review = {}

    pillar_scores = review.get("pillar_scores", {})

    default_scores = {
        "Operational Excellence": 70,
        "Security": 70,
        "Reliability": 70,
        "Performance Efficiency": 70,
        "Cost Optimization": 70,
        "Sustainability": 70
    }

    for pillar in default_scores:
        if pillar not in pillar_scores:
            pillar_scores[pillar] = default_scores[pillar]

    overall_score = review.get("overall_score")

    if overall_score is None:
        overall_score = round(sum(pillar_scores.values()) / len(pillar_scores))

    return {
        "overall_score": int(overall_score),
        "pillar_scores": pillar_scores,
        "findings": review.get("findings", []),
        "strengths": review.get("strengths", []),
        "assumptions": review.get("assumptions", [
            "Đánh giá dựa trên các thành phần nhìn thấy được trong sơ đồ."
        ])
    }


def calculate_extraction_confidence(services):
    if not services:
        return 0.0

    total = 0

    for service in services:
        total += float(service.get("confidence", 0.7))

    return round(total / len(services), 2)


def extract_review_id_from_key(key):
    parts = key.split("/")

    if len(parts) >= 2 and parts[0] == "uploads":
        return parts[1]

    return "unknown-review"

