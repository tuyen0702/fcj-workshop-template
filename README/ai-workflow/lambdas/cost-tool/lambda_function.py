import boto3
import json
import os
import re
from datetime import datetime
from botocore.config import Config

# Pricing API thường dùng endpoint us-east-1 cho Query API
pricing = boto3.client(
    "pricing",
    region_name="us-east-1",
    config=Config(
        connect_timeout=10,
        read_timeout=60,
        retries={"max_attempts": 2}
    )
)

BEDROCK_REGION = os.environ.get("BEDROCK_REGION", "ap-southeast-1").strip()
MODEL_ID = os.environ.get("MODEL_ID", "global.amazon.nova-2-lite-v1:0").strip()
DEFAULT_REGION = os.environ.get("DEFAULT_REGION", "ap-southeast-1").strip()

bedrock = boto3.client(
    "bedrock-runtime",
    region_name=BEDROCK_REGION,
    config=Config(
        connect_timeout=10,
        read_timeout=90,
        retries={"max_attempts": 2}
    )
)

REGION_TO_LOCATION = {
    "ap-southeast-1": "Asia Pacific (Singapore)",
    "ap-southeast-2": "Asia Pacific (Sydney)",
    "ap-northeast-1": "Asia Pacific (Tokyo)",
    "us-east-1": "US East (N. Virginia)",
    "us-east-2": "US East (Ohio)",
    "us-west-2": "US West (Oregon)",
    "eu-west-1": "EU (Ireland)",
    "eu-central-1": "EU (Frankfurt)"
}

# Các assumption này dùng vì sơ đồ ảnh không có đủ thông số usage thật
SERVICE_PRICING_CONFIG = {
    "Amazon EC2": {
        "service_code": "AmazonEC2",
        "assumption": "1 EC2 t3.micro Linux On-Demand chạy 730 giờ/tháng",
        "monthly_quantity": 730,
        "unit_contains": "Hrs",
        "filters": [
            {"Field": "instanceType", "Value": "t3.micro"},
            {"Field": "operatingSystem", "Value": "Linux"},
            {"Field": "tenancy", "Value": "Shared"},
            {"Field": "preInstalledSw", "Value": "NA"},
            {"Field": "capacitystatus", "Value": "Used"},
            {"Field": "operation", "Value": "RunInstances"}
        ]
    },
    "Amazon RDS": {
        "service_code": "AmazonRDS",
        "assumption": "1 RDS db.t3.micro MySQL Single-AZ chạy 730 giờ/tháng",
        "monthly_quantity": 730,
        "unit_contains": "Hrs",
        "filters": [
            {"Field": "instanceType", "Value": "db.t3.micro"},
            {"Field": "databaseEngine", "Value": "MySQL"},
            {"Field": "deploymentOption", "Value": "Single-AZ"}
        ]
    },
    "Amazon S3": {
        "service_code": "AmazonS3",
        "assumption": "10 GB Amazon S3 Standard storage/tháng",
        "monthly_quantity": 10,
        "unit_contains": "GB-Mo",
        "description_keywords": ["Standard", "Storage"],
        "filters": [
            {"Field": "storageClass", "Value": "General Purpose"}
        ]
    },
    "AWS Lambda": {
        "service_code": "AWSLambda",
        "assumption": "1 triệu Lambda requests/tháng, chỉ ước tính phần request",
        "monthly_quantity": 1,
        "description_keywords": ["request"],
        "filters": []
    },
    "Amazon API Gateway": {
        "service_code": "AmazonApiGateway",
        "assumption": "1 triệu API Gateway requests/tháng",
        "monthly_quantity": 1,
        "description_keywords": ["API", "request"],
        "filters": []
    },
    "Amazon DynamoDB": {
        "service_code": "AmazonDynamoDB",
        "assumption": "1 GB DynamoDB storage/tháng, usage đọc/ghi chưa đủ dữ liệu để ước tính chính xác",
        "monthly_quantity": 1,
        "unit_contains": "GB-Mo",
        "description_keywords": ["storage"],
        "filters": []
    },
    "Amazon CloudWatch": {
        "service_code": "AmazonCloudWatch",
        "assumption": "Lấy mẫu giá CloudWatch, usage log/metric thực tế chưa xác định",
        "monthly_quantity": 1,
        "description_keywords": ["metric", "log"],
        "filters": []
    },
    "Amazon SNS": {
        "service_code": "AmazonSNS",
        "assumption": "1 triệu SNS requests/tháng",
        "monthly_quantity": 1,
        "description_keywords": ["request"],
        "filters": []
    },
    "Amazon SQS": {
        "service_code": "AmazonSQS",
        "assumption": "1 triệu SQS requests/tháng",
        "monthly_quantity": 1,
        "description_keywords": ["request"],
        "filters": []
    },
    "AWS Step Functions": {
        "service_code": "AWSStepFunctions",
        "assumption": "1,000 state transitions/tháng",
        "monthly_quantity": 1000,
        "description_keywords": ["state transition"],
        "filters": []
    },
    "Amazon CloudFront": {
        "service_code": "AmazonCloudFront",
        "assumption": "10 GB CloudFront data transfer out/tháng",
        "monthly_quantity": 10,
        "unit_contains": "GB",
        "description_keywords": ["Data Transfer"],
        "filters": []
    }
}

# Những service này khó/không nên tự tính nếu sơ đồ chỉ là ảnh
SERVICE_NOT_ESTIMATED = {
    "AWS IAM": "IAM không có chi phí trực tiếp cho role/policy cơ bản.",
    "Amazon VPC": "VPC cơ bản không có chi phí trực tiếp, nhưng NAT Gateway, VPN, Endpoint có thể phát sinh chi phí.",
    "Amazon EventBridge": "Cần số lượng event/tháng để ước tính chính xác.",
    "Amazon Bedrock": "Cần model, số input/output token, số request hoặc image/video usage để tính chính xác.",
    "AWS WAF": "Cần số Web ACL, rule và request/tháng để tính chính xác.",
    "NAT Gateway": "Cần số giờ chạy và data processed để tính chính xác."
}


def lambda_handler(event, context):
    try:
        review_id = event.get("review_id", "unknown-review")
        region = event.get("region", DEFAULT_REGION)

        services = normalize_services(event.get("services", []))

        if not services:
            return {
                "status": "NO_SERVICES_FOR_COST",
                "review_id": review_id,
                "message": "Không có dịch vụ AWS để tính chi phí.",
                "currency": "USD",
                "estimated_monthly_cost": 0,
                "breakdown": [],
                "cost_ai_review": {
                    "summary": "Không có dữ liệu dịch vụ để đánh giá chi phí.",
                    "optimization_recommendations": []
                }
            }

        location = REGION_TO_LOCATION.get(region, REGION_TO_LOCATION[DEFAULT_REGION])

        print("Cost Tool services:", services)
        print("Pricing location:", location)

        breakdown = []
        total = 0.0

        for service_name in services:
            item = estimate_service_cost(service_name, location)
            breakdown.append(item)

            value = item.get("estimated_monthly_cost")
            if isinstance(value, (int, float)):
                total += value

        cost_result = {
            "status": "COST_ESTIMATED",
            "review_id": review_id,
            "region": region,
            "location": location,
            "currency": "USD",
            "estimated_monthly_cost": round(total, 4),
            "breakdown": breakdown,
            "pricing_method": "AWS Price List API + default usage assumptions",
            "calculated_at": datetime.utcnow().isoformat(),
            "important_note": (
                "Chi phí được ước tính dựa trên AWS Price List API và assumption mặc định. "
                "Sơ đồ ảnh không có đủ thông tin usage như số request, dung lượng, instance type thật, "
                "nên kết quả dùng cho demo và tham khảo."
            )
        }

        cost_ai_review = generate_cost_review_with_bedrock(cost_result)

        cost_result["cost_ai_review"] = cost_ai_review

        return cost_result

    except Exception as e:
        return {
            "status": "FAILED",
            "message": "Cost Tool thất bại.",
            "error": str(e),
            "failed_at": datetime.utcnow().isoformat()
        }


def normalize_services(services):
    result = []

    if not isinstance(services, list):
        return result

    for item in services:
        if isinstance(item, str):
            name = item.strip()
        elif isinstance(item, dict):
            name = str(item.get("name", "")).strip()
        else:
            continue

        if name and name not in result:
            result.append(name)

    return result


def estimate_service_cost(service_name, location):
    if service_name in SERVICE_NOT_ESTIMATED:
        return {
            "service": service_name,
            "status": "NOT_ESTIMATED",
            "price_source": "NOT_ENOUGH_USAGE_DATA",
            "unit_price": None,
            "unit": None,
            "monthly_quantity": 0,
            "estimated_monthly_cost": 0,
            "assumption": SERVICE_NOT_ESTIMATED[service_name],
            "optimization_hint": get_basic_optimization_hint(service_name)
        }

    config = SERVICE_PRICING_CONFIG.get(service_name)

    if not config:
        return {
            "service": service_name,
            "status": "NOT_SUPPORTED",
            "price_source": "NO_PRICING_MAPPING",
            "unit_price": None,
            "unit": None,
            "monthly_quantity": 0,
            "estimated_monthly_cost": None,
            "assumption": "Cost Tool chưa có mapping Price List API cho service này.",
            "optimization_hint": "Cần bổ sung pricing mapping hoặc yêu cầu người dùng nhập usage cụ thể."
        }

    price_info = get_price_from_price_list_api(config, location)

    if not price_info:
        return {
            "service": service_name,
            "status": "PRICE_NOT_FOUND",
            "price_source": "AWS_PRICE_LIST_API",
            "unit_price": None,
            "unit": None,
            "monthly_quantity": config.get("monthly_quantity", 0),
            "estimated_monthly_cost": None,
            "assumption": config.get("assumption"),
            "optimization_hint": get_basic_optimization_hint(service_name)
        }

    unit_price = price_info["unit_price"]
    monthly_quantity = config.get("monthly_quantity", 1)
    estimated_monthly_cost = unit_price * monthly_quantity

    return {
        "service": service_name,
        "status": "ESTIMATED",
        "price_source": "AWS_PRICE_LIST_API",
        "unit_price": unit_price,
        "unit": price_info["unit"],
        "price_description": price_info["description"],
        "monthly_quantity": monthly_quantity,
        "estimated_monthly_cost": round(estimated_monthly_cost, 4),
        "assumption": config.get("assumption"),
        "optimization_hint": get_basic_optimization_hint(service_name)
    }


def get_price_from_price_list_api(config, location):
    filters = [
        {
            "Type": "TERM_MATCH",
            "Field": "location",
            "Value": location
        }
    ]

    for item in config.get("filters", []):
        filters.append({
            "Type": "TERM_MATCH",
            "Field": item["Field"],
            "Value": item["Value"]
        })

    paginator = pricing.get_paginator("get_products")

    pages = paginator.paginate(
        ServiceCode=config["service_code"],
        Filters=filters,
        PaginationConfig={
            "MaxItems": 100
        }
    )

    for page in pages:
        for price_item in page.get("PriceList", []):
            product = json.loads(price_item)

            price_dimension = extract_price_dimension(
                product=product,
                unit_contains=config.get("unit_contains"),
                description_keywords=config.get("description_keywords", [])
            )

            if price_dimension:
                return price_dimension

    return None


def extract_price_dimension(product, unit_contains=None, description_keywords=None):
    description_keywords = description_keywords or []

    terms = product.get("terms", {}).get("OnDemand", {})

    for term in terms.values():
        price_dimensions = term.get("priceDimensions", {})

        for dimension in price_dimensions.values():
            unit = dimension.get("unit", "")
            description = dimension.get("description", "")
            price_per_unit = dimension.get("pricePerUnit", {})
            usd = price_per_unit.get("USD")

            if usd is None:
                continue

            try:
                unit_price = float(usd)
            except Exception:
                continue

            if unit_price < 0:
                continue

            if unit_contains:
                if unit_contains.lower() not in unit.lower():
                    continue

            if description_keywords:
                desc_lower = description.lower()
                matched = any(keyword.lower() in desc_lower for keyword in description_keywords)

                if not matched:
                    continue

            return {
                "unit_price": unit_price,
                "unit": unit,
                "description": description
            }

    return None


def get_basic_optimization_hint(service_name):
    hints = {
        "Amazon EC2": "Dùng right-sizing, tự động stop môi trường dev/test, cân nhắc Savings Plans nếu chạy dài hạn.",
        "Amazon RDS": "Chọn instance phù hợp, kiểm soát backup retention, dùng reserved instance nếu workload ổn định.",
        "Amazon S3": "Dùng S3 Lifecycle, xóa file tạm, chuyển dữ liệu cũ sang storage class rẻ hơn.",
        "Amazon CloudFront": "Bật caching hợp lý để giảm tải origin và tối ưu data transfer.",
        "AWS Lambda": "Tối ưu memory/runtime, giảm số lần gọi không cần thiết, theo dõi duration.",
        "Amazon API Gateway": "Giảm request dư thừa, cache response nếu phù hợp, chọn HTTP API nếu không cần REST API feature nâng cao.",
        "Amazon DynamoDB": "Chọn on-demand/provisioned phù hợp, dùng TTL, thiết kế partition key tốt.",
        "Amazon CloudWatch": "Kiểm soát log retention để tránh chi phí log tăng.",
        "Amazon SNS": "Theo dõi số lượng notification và tránh gửi lặp.",
        "Amazon SQS": "Giảm polling không cần thiết, dùng long polling.",
        "AWS Step Functions": "Tối ưu số state transition, gộp bước nhỏ nếu phù hợp.",
        "Amazon Bedrock": "Giới hạn max token, tối ưu prompt, cache kết quả nếu input giống nhau."
    }

    return hints.get(service_name, "Cần thêm usage cụ thể để đề xuất tối ưu chi phí chính xác hơn.")


def generate_cost_review_with_bedrock(cost_result):
    prompt = f"""
Bạn là AWS Cost Optimization Advisor.

Nhiệm vụ:
Dựa trên kết quả tính chi phí từ AWS Price List API bên dưới, hãy đánh giá chi phí và đề xuất tối ưu.

Dữ liệu cost_result:
{json.dumps(cost_result, ensure_ascii=False, indent=2)}

Yêu cầu:
- Chỉ dựa trên cost_result, không bịa thêm dịch vụ hoặc giá mới.
- Ghi rõ chi phí là ước tính theo assumption mặc định.
- Phân tích service nào có khả năng tạo chi phí cao.
- Nêu các rủi ro chi phí do thiếu thông tin usage.
- Đề xuất tối ưu chi phí thực tế, dễ hiểu cho sinh viên Cloud Computing.
- Trả về JSON hợp lệ, không markdown.

Format JSON:
{{
  "summary": "Tóm tắt ngắn về chi phí.",
  "cost_level": "Low | Medium | High | Unknown",
  "main_cost_drivers": [
    {{
      "service": "Amazon EC2",
      "reason": "Lý do service này có thể tạo chi phí đáng chú ý."
    }}
  ],
  "optimization_recommendations": [
    {{
      "service": "Amazon S3",
      "recommendation": "Dùng S3 Lifecycle để giảm chi phí lưu trữ.",
      "priority": "Low | Medium | High"
    }}
  ],
  "missing_usage_data": [
    "Thiếu số request/tháng của API Gateway."
  ],
  "disclaimer": "Chi phí chỉ là ước tính dựa trên AWS Price List API và assumption mặc định."
}}
"""

    try:
        response = bedrock.converse(
            modelId=MODEL_ID,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "text": prompt
                        }
                    ]
                }
            ],
            inferenceConfig={
                "maxTokens": 1800,
                "temperature": 0.2
            }
        )

        output_text = response["output"]["message"]["content"][0]["text"]
        return extract_json_from_text(output_text)

    except Exception as e:
        return {
            "summary": "Không tạo được cost review bằng Bedrock.",
            "cost_level": "Unknown",
            "main_cost_drivers": [],
            "optimization_recommendations": [],
            "missing_usage_data": [],
            "disclaimer": "Cost Tool đã tính chi phí, nhưng bước Bedrock cost review bị lỗi.",
            "bedrock_error": str(e)
        }


def extract_json_from_text(text):
    text = text.strip()

    try:
        return json.loads(text)
    except Exception:
        pass

    match = re.search(r"\{[\s\S]*\}", text)

    if match:
        return json.loads(match.group(0))

    return {
        "summary": text,
        "cost_level": "Unknown",
        "main_cost_drivers": [],
        "optimization_recommendations": [],
        "missing_usage_data": [],
        "disclaimer": "Bedrock không trả về JSON hợp lệ, hệ thống lưu raw text vào summary."
    }