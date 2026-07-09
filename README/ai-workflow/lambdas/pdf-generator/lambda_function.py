import boto3
import html
import json
import os
import re
from datetime import datetime
from botocore.config import Config
from decimal import Decimal

dynamodb = boto3.resource("dynamodb")

TABLE_NAME = os.environ.get("TABLE_NAME", "").strip()
review_table = dynamodb.Table(TABLE_NAME) if TABLE_NAME else None

s3 = boto3.client("s3")

REPORT_BUCKET = os.environ["REPORT_BUCKET"].strip()
BEDROCK_REGION = os.environ.get("BEDROCK_REGION", "ap-southeast-1").strip()
MODEL_ID = os.environ.get("MODEL_ID", "global.amazon.nova-2-lite-v1:0").strip()

bedrock = boto3.client(
    "bedrock-runtime",
    region_name=BEDROCK_REGION,
    config=Config(
        connect_timeout=10,
        read_timeout=120,
        retries={"max_attempts": 2}
    )
)

# Nếu bạn thêm Lambda Layer reportlab thì Lambda sẽ tạo thêm PDF.
# Nếu chưa có layer, Lambda vẫn tạo HTML report đầy đủ.
REPORTLAB_IMPORT_ERROR = None

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    REPORTLAB_AVAILABLE = True
except Exception as e:
    REPORTLAB_AVAILABLE = False
    REPORTLAB_IMPORT_ERROR = str(e)

def lambda_handler(event, context):
    review_id = "unknown-review"

    try:
        print("Received event:", json.dumps(event, ensure_ascii=False)[:3000])
        print("Using model:", MODEL_ID)
        print("Using Bedrock region:", BEDROCK_REGION)

        analysis = event.get("analysis", {})
        cost = event.get("cost", {})

        review_id = analysis.get("review_id", "unknown-review")
        analysis_status = analysis.get("status", "UNKNOWN")

        final_review = generate_final_review_with_bedrock(analysis, cost)

        report_json = {
            "review_id": review_id,
            "analysis_status": analysis_status,
            "generated_at": datetime.utcnow().isoformat(),
            "analysis": analysis,
            "cost": cost,
            "final_review": final_review
        }

        html_content = build_html_report(report_json)

        base_key = f"reports/{review_id}"

        json_key = f"{base_key}/report-data.json"
        html_key = f"{base_key}/report.html"

        put_json_report(json_key, report_json)
        put_html_report(html_key, html_content)

        result = {
            "status": "REPORT_GENERATED",
            "message": "Đã tạo báo cáo đánh giá kiến trúc AWS.",
            "review_id": review_id,
            "analysis_status": analysis_status,
            "report_bucket": REPORT_BUCKET,
            "json_report_s3_key": json_key,
            "json_report_s3_uri": f"s3://{REPORT_BUCKET}/{json_key}",
            "html_report_s3_key": html_key,
            "html_report_s3_uri": f"s3://{REPORT_BUCKET}/{html_key}",
            "generated_at": datetime.utcnow().isoformat(),
            "reportlab_available": REPORTLAB_AVAILABLE,
            "reportlab_import_error": REPORTLAB_IMPORT_ERROR
        }

        if REPORTLAB_AVAILABLE:
            try:
                pdf_bytes = build_pdf_report(report_json)
                pdf_key = f"{base_key}/report.pdf"

                put_pdf_report(pdf_key, pdf_bytes)

                result["pdf_status"] = "PDF_GENERATED"
                result["pdf_report_s3_key"] = pdf_key
                result["pdf_report_s3_uri"] = f"s3://{REPORT_BUCKET}/{pdf_key}"

            except Exception as pdf_error:
                result["pdf_status"] = "PDF_FAILED"
                result["pdf_error"] = str(pdf_error)
        else:
            result["pdf_status"] = "PDF_SKIPPED"
            result["pdf_error"] = REPORTLAB_IMPORT_ERROR
            result["pdf_note"] = "ReportLab chưa import được nên Lambda chỉ tạo HTML report."

        update_review_history_completed(report_json, result)

        return result

    except Exception as e:
        try:
            if isinstance(event, dict):
                analysis = event.get("analysis", {})
                review_id = analysis.get("review_id", review_id)

            update_review_history_failed(review_id, str(e))

        except Exception as update_error:
            print(f"Failed to update DynamoDB failed status: {str(update_error)}")

        return {
            "status": "FAILED",
            "message": "PDF Generator + Bedrock Review thất bại.",
            "review_id": review_id,
            "error": str(e),
            "failed_at": datetime.utcnow().isoformat()
        }

def register_vietnamese_fonts():
    regular_font_path = "/opt/fonts/DejaVuSans.ttf"
    bold_font_path = "/opt/fonts/DejaVuSans-Bold.ttf"

    pdfmetrics.registerFont(TTFont("DejaVuSans", regular_font_path))
    pdfmetrics.registerFont(TTFont("DejaVuSans-Bold", bold_font_path))

    return {
        "regular": "DejaVuSans",
        "bold": "DejaVuSans-Bold"
    }

def generate_final_review_with_bedrock(analysis, cost):
    if analysis.get("status") == "NO_SERVICES_DETECTED":
        return {
            "executive_summary": "Không quét được dịch vụ AWS nào trong sơ đồ, vì vậy hệ thống không đủ dữ liệu để đánh giá kiến trúc.",
            "architecture_summary": "Không có dịch vụ AWS được phát hiện.",
            "well_architected_assessment": {
                "overall_comment": "Không đủ dữ liệu để đánh giá theo AWS Well-Architected Framework.",
                "pillar_reviews": []
            },
            "cost_assessment": {
                "summary": "Không có dịch vụ AWS để tính chi phí.",
                "estimated_monthly_cost": 0,
                "cost_level": "Unknown",
                "optimization_summary": "Không có dữ liệu để đề xuất tối ưu chi phí."
            },
            "recommendations": [
                "Cần upload ảnh sơ đồ rõ hơn, có label tên dịch vụ AWS như Amazon S3, AWS Lambda, Amazon API Gateway."
            ],
            "limitations": [
                "Không phát hiện được dịch vụ AWS nào từ ảnh đầu vào."
            ],
            "conclusion": "Báo cáo dừng ở mức thông báo lỗi nhận diện, không thực hiện đánh giá kiến trúc."
        }

    prompt = build_final_review_prompt(analysis, cost)

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
                "maxTokens": 3500,
                "temperature": 0.25
            }
        )

        output_text = response["output"]["message"]["content"][0]["text"]
        return extract_json_from_text(output_text)

    except Exception as e:
        return {
            "executive_summary": "Không tạo được phần nhận xét cuối bằng Bedrock.",
            "architecture_summary": "Hệ thống vẫn lưu kết quả phân tích kỹ thuật và chi phí.",
            "well_architected_assessment": {
                "overall_comment": "Bedrock final review bị lỗi.",
                "pillar_reviews": []
            },
            "cost_assessment": {
                "summary": "Không tạo được phần diễn giải chi phí bằng Bedrock final review.",
                "estimated_monthly_cost": cost.get("estimated_monthly_cost", 0),
                "cost_level": cost.get("cost_ai_review", {}).get("cost_level", "Unknown"),
                "optimization_summary": "Xem cost_ai_review từ Cost Tool."
            },
            "recommendations": [],
            "limitations": [
                "Bedrock final review bị lỗi.",
                str(e)
            ],
            "conclusion": "Báo cáo được tạo từ dữ liệu thô do Bedrock final review không chạy thành công."
        }


def build_final_review_prompt(analysis, cost):
    return f"""
Bạn là AI AWS Architecture Review Report Writer.

Nhiệm vụ:
Tạo báo cáo cuối cùng bằng tiếng Việt dựa trên:
1. Kết quả AI Architecture Analyzer
2. Kết quả Cost Tool
3. Cost AI Review từ Cost Tool

Dữ liệu AI Architecture Analyzer:
{json.dumps(analysis, ensure_ascii=False, indent=2)}

Dữ liệu Cost Tool:
{json.dumps(cost, ensure_ascii=False, indent=2)}

Yêu cầu bắt buộc:
- Chỉ dựa trên dữ liệu được cung cấp.
- Không bịa thêm dịch vụ AWS ngoài architecture_json.services.
- Không bịa thêm giá ngoài cost.breakdown và cost.estimated_monthly_cost.
- Nếu thiếu thông tin usage, phải ghi rõ là chi phí chỉ là ước tính theo assumption mặc định.
- Phần đánh giá kiến trúc dựa theo AWS Well-Architected Framework.
- Phần chi phí phải dùng cost_ai_review nếu có.
- Văn phong chuyên nghiệp, rõ ràng, phù hợp đưa vào báo cáo đồ án.
- Trả về JSON hợp lệ, không markdown, không giải thích ngoài JSON.

Format JSON bắt buộc:
{{
  "executive_summary": "Tóm tắt ngắn gọn toàn bộ kết quả đánh giá.",
  "architecture_summary": "Mô tả ngắn kiến trúc dựa trên dịch vụ và kết nối phát hiện được.",
  "detected_services_summary": [
    {{
      "service": "Amazon S3",
      "role_in_architecture": "Vai trò của dịch vụ trong kiến trúc dựa trên sơ đồ."
    }}
  ],
  "well_architected_assessment": {{
    "overall_score": 80,
    "overall_comment": "Nhận xét tổng quan theo Well-Architected.",
    "pillar_reviews": [
      {{
        "pillar": "Security",
        "score": 75,
        "comment": "Nhận xét ngắn.",
        "risks": ["Rủi ro nếu có."],
        "improvements": ["Đề xuất cải thiện."]
      }}
    ]
  }},
  "cost_assessment": {{
    "estimated_monthly_cost": 12.34,
    "currency": "USD",
    "cost_level": "Low | Medium | High | Unknown",
    "summary": "Nhận xét tổng quan chi phí.",
    "main_cost_drivers": [
      {{
        "service": "Amazon EC2",
        "reason": "Vì sao dịch vụ này có thể là cost driver."
      }}
    ],
    "optimization_recommendations": [
      {{
        "service": "Amazon S3",
        "recommendation": "Đề xuất tối ưu.",
        "priority": "Low | Medium | High"
      }}
    ]
  }},
  "key_risks": [
    "Các rủi ro chính về bảo mật, độ tin cậy, vận hành hoặc chi phí."
  ],
  "priority_recommendations": [
    {{
      "priority": "High",
      "recommendation": "Việc nên làm trước.",
      "reason": "Lý do."
    }}
  ],
  "limitations": [
    "Các giới hạn của báo cáo."
  ],
  "conclusion": "Kết luận cuối cùng."
}}
"""


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
        "executive_summary": text,
        "architecture_summary": "Bedrock không trả về JSON hợp lệ, hệ thống lưu raw text vào executive_summary.",
        "well_architected_assessment": {
            "overall_comment": "Không parse được JSON từ Bedrock.",
            "pillar_reviews": []
        },
        "cost_assessment": {
            "summary": "Không parse được JSON từ Bedrock.",
            "estimated_monthly_cost": 0,
            "currency": "USD",
            "cost_level": "Unknown",
            "main_cost_drivers": [],
            "optimization_recommendations": []
        },
        "recommendations": [],
        "limitations": [
            "Bedrock không trả về JSON hợp lệ."
        ],
        "conclusion": "Cần kiểm tra lại prompt hoặc response của Bedrock."
    }


def build_html_report(report_json):
    review_id = report_json.get("review_id", "unknown-review")
    generated_at = report_json.get("generated_at", "")
    analysis = report_json.get("analysis", {})
    cost = report_json.get("cost", {})
    final_review = report_json.get("final_review", {})

    architecture_json = analysis.get("architecture_json", {})
    services = architecture_json.get("services", [])
    connections = architecture_json.get("connections", [])
    well_review = analysis.get("well_architected_review") or {}

    executive_summary = final_review.get("executive_summary", "")
    architecture_summary = final_review.get("architecture_summary", "")
    conclusion = final_review.get("conclusion", "")

    html_parts = []

    html_parts.append(get_html_header(review_id))

    html_parts.append(f"""
    <div class="header">
        <h1>AWS Architecture Review Report</h1>
        <p class="muted">Review ID: <code>{escape(review_id)}</code></p>
        <p class="muted">Generated at: {escape(generated_at)}</p>
        <p class="badge">{escape(analysis.get("status", "UNKNOWN"))}</p>
    </div>
    """)

    html_parts.append(build_section(
        "1. Executive Summary",
        f"<p>{escape(executive_summary)}</p>"
    ))

    html_parts.append(build_section(
        "2. Architecture Summary",
        f"<p>{escape(architecture_summary)}</p>"
    ))

    html_parts.append(build_detected_services_section(services))
    html_parts.append(build_connections_section(connections))
    html_parts.append(build_well_architected_section(well_review, final_review))
    html_parts.append(build_cost_section(cost, final_review))
    html_parts.append(build_risks_section(final_review))
    html_parts.append(build_recommendations_section(final_review))

    limitations = final_review.get("limitations", analysis.get("limitations", []))
    html_parts.append(build_list_section("9. Limitations", limitations))

    html_parts.append(build_section(
        "10. Conclusion",
        f"<p>{escape(conclusion)}</p>"
    ))

    html_parts.append("""
    <div class="footer">
        <p>
            This report is generated by an AI-based AWS Architecture Reviewer.
            The assessment is based on the uploaded architecture image and does not replace manual AWS configuration auditing.
        </p>
    </div>
    </body>
    </html>
    """)

    return "\n".join(html_parts)


def get_html_header(review_id):
    return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>AWS Architecture Review Report - {escape(review_id)}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 40px;
            color: #111827;
            background: #f9fafb;
            line-height: 1.6;
        }}
        .header {{
            background: #232f3e;
            color: white;
            padding: 28px;
            border-radius: 14px;
            margin-bottom: 24px;
        }}
        .header h1 {{
            margin: 0 0 8px 0;
        }}
        .card {{
            background: white;
            border: 1px solid #e5e7eb;
            border-radius: 14px;
            padding: 22px;
            margin-bottom: 22px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        }}
        h2 {{
            color: #232f3e;
            margin-top: 0;
            border-bottom: 2px solid #ff9900;
            padding-bottom: 8px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 12px;
        }}
        th, td {{
            border: 1px solid #e5e7eb;
            padding: 10px;
            text-align: left;
            vertical-align: top;
        }}
        th {{
            background: #f3f4f6;
            color: #111827;
        }}
        .muted {{
            color: #d1d5db;
        }}
        .badge {{
            display: inline-block;
            background: #ff9900;
            color: #111827;
            padding: 6px 12px;
            border-radius: 999px;
            font-weight: bold;
            margin-top: 8px;
        }}
        .score {{
            font-size: 30px;
            font-weight: bold;
            color: #232f3e;
        }}
        .small {{
            color: #6b7280;
            font-size: 14px;
        }}
        code {{
            background: rgba(255,255,255,0.15);
            padding: 2px 6px;
            border-radius: 4px;
        }}
        .footer {{
            color: #6b7280;
            font-size: 13px;
            margin-top: 30px;
            text-align: center;
        }}
    </style>
</head>
<body>
"""


def build_section(title, body_html):
    return f"""
    <div class="card">
        <h2>{escape(title)}</h2>
        {body_html}
    </div>
    """


def build_detected_services_section(services):
    if not services:
        body = "<p>Không phát hiện được dịch vụ AWS nào.</p>"
        return build_section("3. Detected AWS Services", body)

    rows = ""

    for service in services:
        if isinstance(service, dict):
            name = service.get("name", "Unknown")
            category = service.get("category", "Unknown")
            confidence = service.get("confidence", "")
            evidence = service.get("evidence", "")
        else:
            name = str(service)
            category = "Unknown"
            confidence = ""
            evidence = ""

        rows += f"""
        <tr>
            <td>{escape(name)}</td>
            <td>{escape(category)}</td>
            <td>{escape(confidence)}</td>
            <td>{escape(evidence)}</td>
        </tr>
        """

    body = f"""
    <table>
        <tr>
            <th>Service</th>
            <th>Category</th>
            <th>Confidence</th>
            <th>Evidence</th>
        </tr>
        {rows}
    </table>
    """

    return build_section("3. Detected AWS Services", body)


def build_connections_section(connections):
    if not connections:
        return build_section(
            "4. Detected Connections",
            "<p>Không xác định được kết nối rõ ràng giữa các dịch vụ hoặc sơ đồ không thể hiện connector đủ rõ.</p>"
        )

    rows = ""

    for conn in connections:
        rows += f"""
        <tr>
            <td>{escape(conn.get("from", ""))}</td>
            <td>{escape(conn.get("to", ""))}</td>
            <td>{escape(conn.get("confidence", ""))}</td>
            <td>{escape(conn.get("evidence", ""))}</td>
        </tr>
        """

    body = f"""
    <table>
        <tr>
            <th>From</th>
            <th>To</th>
            <th>Confidence</th>
            <th>Evidence</th>
        </tr>
        {rows}
    </table>
    """

    return build_section("4. Detected Connections", body)


def build_well_architected_section(well_review, final_review):
    final_wa = final_review.get("well_architected_assessment", {})

    overall_score = (
        final_wa.get("overall_score")
        or well_review.get("overall_score")
        or "N/A"
    )

    pillar_scores = well_review.get("pillar_scores", {})
    pillar_reviews = final_wa.get("pillar_reviews", [])

    score_rows = ""

    if isinstance(pillar_scores, dict):
        for pillar, score in pillar_scores.items():
            score_rows += f"""
            <tr>
                <td>{escape(pillar)}</td>
                <td>{escape(score)}</td>
            </tr>
            """

    pillar_review_rows = ""

    for item in pillar_reviews:
        risks = item.get("risks", [])
        improvements = item.get("improvements", [])

        pillar_review_rows += f"""
        <tr>
            <td>{escape(item.get("pillar", ""))}</td>
            <td>{escape(item.get("score", ""))}</td>
            <td>{escape(item.get("comment", ""))}</td>
            <td>{list_to_html(risks)}</td>
            <td>{list_to_html(improvements)}</td>
        </tr>
        """

    findings = well_review.get("findings", [])
    finding_rows = ""

    for finding in findings:
        finding_rows += f"""
        <tr>
            <td>{escape(finding.get("pillar", ""))}</td>
            <td>{escape(finding.get("severity", ""))}</td>
            <td>{escape(finding.get("issue", ""))}</td>
            <td>{escape(finding.get("recommendation", ""))}</td>
        </tr>
        """

    body = f"""
    <p class="score">Overall Score: {escape(overall_score)}</p>
    <p>{escape(final_wa.get("overall_comment", ""))}</p>

    <h3>Pillar Scores</h3>
    <table>
        <tr>
            <th>Pillar</th>
            <th>Score</th>
        </tr>
        {score_rows if score_rows else "<tr><td colspan='2'>Không có dữ liệu điểm pillar.</td></tr>"}
    </table>

    <h3>Pillar Review</h3>
    <table>
        <tr>
            <th>Pillar</th>
            <th>Score</th>
            <th>Comment</th>
            <th>Risks</th>
            <th>Improvements</th>
        </tr>
        {pillar_review_rows if pillar_review_rows else "<tr><td colspan='5'>Không có nhận xét chi tiết theo pillar.</td></tr>"}
    </table>

    <h3>Findings from AI Analyzer</h3>
    <table>
        <tr>
            <th>Pillar</th>
            <th>Severity</th>
            <th>Issue</th>
            <th>Recommendation</th>
        </tr>
        {finding_rows if finding_rows else "<tr><td colspan='4'>Không có finding cụ thể.</td></tr>"}
    </table>
    """

    return build_section("5. Well-Architected Assessment", body)


def build_cost_section(cost, final_review):
    final_cost = final_review.get("cost_assessment", {})
    cost_ai_review = cost.get("cost_ai_review", {})

    total = cost.get("estimated_monthly_cost", 0)
    currency = cost.get("currency", "USD")

    breakdown = cost.get("breakdown", [])
    rows = ""

    for item in breakdown:
        rows += f"""
        <tr>
            <td>{escape(item.get("service", ""))}</td>
            <td>{escape(item.get("status", ""))}</td>
            <td>{escape(item.get("unit_price", ""))}</td>
            <td>{escape(item.get("unit", ""))}</td>
            <td>{escape(item.get("monthly_quantity", ""))}</td>
            <td>{escape(item.get("estimated_monthly_cost", ""))}</td>
            <td>{escape(item.get("assumption", ""))}</td>
        </tr>
        """

    main_cost_drivers = final_cost.get(
        "main_cost_drivers",
        cost_ai_review.get("main_cost_drivers", [])
    )

    optimization_recommendations = final_cost.get(
        "optimization_recommendations",
        cost_ai_review.get("optimization_recommendations", [])
    )

    body = f"""
    <p class="score">{escape(total)} {escape(currency)} / month</p>
    <p>{escape(final_cost.get("summary", cost_ai_review.get("summary", "")))}</p>
    <p><strong>Cost Level:</strong> {escape(final_cost.get("cost_level", cost_ai_review.get("cost_level", "Unknown")))}</p>
    <p class="small">{escape(cost.get("important_note", ""))}</p>

    <h3>Cost Breakdown</h3>
    <table>
        <tr>
            <th>Service</th>
            <th>Status</th>
            <th>Unit Price</th>
            <th>Unit</th>
            <th>Monthly Quantity</th>
            <th>Monthly Cost</th>
            <th>Assumption</th>
        </tr>
        {rows if rows else "<tr><td colspan='7'>Không có dữ liệu chi phí.</td></tr>"}
    </table>

    <h3>Main Cost Drivers</h3>
    {cost_drivers_to_html(main_cost_drivers)}

    <h3>Cost Optimization Recommendations</h3>
    {cost_recommendations_to_html(optimization_recommendations)}
    """

    return build_section("6. Cost Assessment", body)


def build_risks_section(final_review):
    risks = final_review.get("key_risks", [])
    return build_list_section("7. Key Risks", risks)


def build_recommendations_section(final_review):
    recommendations = final_review.get("priority_recommendations", final_review.get("recommendations", []))

    if not recommendations:
        return build_section("8. Priority Recommendations", "<p>Không có khuyến nghị ưu tiên.</p>")

    rows = ""

    for item in recommendations:
        if isinstance(item, dict):
            rows += f"""
            <tr>
                <td>{escape(item.get("priority", ""))}</td>
                <td>{escape(item.get("recommendation", ""))}</td>
                <td>{escape(item.get("reason", ""))}</td>
            </tr>
            """
        else:
            rows += f"""
            <tr>
                <td>N/A</td>
                <td>{escape(item)}</td>
                <td></td>
            </tr>
            """

    body = f"""
    <table>
        <tr>
            <th>Priority</th>
            <th>Recommendation</th>
            <th>Reason</th>
        </tr>
        {rows}
    </table>
    """

    return build_section("8. Priority Recommendations", body)


def build_list_section(title, items):
    return build_section(title, list_to_html(items))


def list_to_html(items):
    if not items:
        return "<p>Không có dữ liệu.</p>"

    if not isinstance(items, list):
        return f"<p>{escape(items)}</p>"

    lis = ""

    for item in items:
        if isinstance(item, dict):
            lis += f"<li>{escape(json.dumps(item, ensure_ascii=False))}</li>"
        else:
            lis += f"<li>{escape(item)}</li>"

    return f"<ul>{lis}</ul>"


def cost_drivers_to_html(items):
    if not items:
        return "<p>Không xác định cost driver chính.</p>"

    rows = ""

    for item in items:
        rows += f"""
        <tr>
            <td>{escape(item.get("service", ""))}</td>
            <td>{escape(item.get("reason", ""))}</td>
        </tr>
        """

    return f"""
    <table>
        <tr>
            <th>Service</th>
            <th>Reason</th>
        </tr>
        {rows}
    </table>
    """


def cost_recommendations_to_html(items):
    if not items:
        return "<p>Không có đề xuất tối ưu chi phí.</p>"

    rows = ""

    for item in items:
        rows += f"""
        <tr>
            <td>{escape(item.get("service", ""))}</td>
            <td>{escape(item.get("priority", ""))}</td>
            <td>{escape(item.get("recommendation", ""))}</td>
        </tr>
        """

    return f"""
    <table>
        <tr>
            <th>Service</th>
            <th>Priority</th>
            <th>Recommendation</th>
        </tr>
        {rows}
    </table>
    """


def build_pdf_report(report_json):
    import io

    fonts = register_vietnamese_fonts()

    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name="VNTitle",
        parent=styles["Title"],
        fontName=fonts["bold"],
        fontSize=18,
        leading=22
    ))

    styles.add(ParagraphStyle(
        name="VNHeading2",
        parent=styles["Heading2"],
        fontName=fonts["bold"],
        fontSize=13,
        leading=16,
        spaceAfter=8
    ))

    styles.add(ParagraphStyle(
        name="VNBody",
        parent=styles["BodyText"],
        fontName=fonts["regular"],
        fontSize=10,
        leading=14
    ))

    story = []

    review_id = report_json.get("review_id", "unknown-review")
    final_review = report_json.get("final_review", {})
    cost = report_json.get("cost", {})
    analysis = report_json.get("analysis", {})

    architecture_json = analysis.get("architecture_json", {})
    services = architecture_json.get("services", [])

    story.append(Paragraph("Báo cáo đánh giá kiến trúc AWS", styles["VNTitle"]))
    story.append(Spacer(1, 12))

    story.append(Paragraph(f"Review ID: {safe_pdf_text(review_id)}", styles["VNBody"]))
    story.append(Spacer(1, 12))

    story.append(Paragraph("1. Tóm tắt tổng quan", styles["VNHeading2"]))
    story.append(Paragraph(safe_pdf_text(final_review.get("executive_summary", "")), styles["VNBody"]))
    story.append(Spacer(1, 12))

    story.append(Paragraph("2. Các dịch vụ AWS phát hiện được", styles["VNHeading2"]))

    if services:
        for service in services:
            if isinstance(service, dict):
                name = service.get("name", "Unknown")
                category = service.get("category", "Unknown")
                confidence = service.get("confidence", "")
                line = f"- {name} | Nhóm dịch vụ: {category} | Độ tin cậy: {confidence}"
            else:
                line = f"- {service}"

            story.append(Paragraph(safe_pdf_text(line), styles["VNBody"]))
            story.append(Spacer(1, 4))
    else:
        story.append(Paragraph("Không phát hiện được dịch vụ AWS nào.", styles["VNBody"]))

    story.append(Spacer(1, 12))

    story.append(Paragraph("3. Tóm tắt kiến trúc", styles["VNHeading2"]))
    story.append(Paragraph(safe_pdf_text(final_review.get("architecture_summary", "")), styles["VNBody"]))
    story.append(Spacer(1, 12))

    story.append(Paragraph("4. Đánh giá Well-Architected", styles["VNHeading2"]))

    wa = final_review.get("well_architected_assessment", {})
    overall_score = wa.get("overall_score", "N/A")
    overall_comment = wa.get("overall_comment", "")

    story.append(Paragraph(safe_pdf_text(f"Điểm tổng quan: {overall_score}"), styles["VNBody"]))
    story.append(Paragraph(safe_pdf_text(overall_comment), styles["VNBody"]))
    story.append(Spacer(1, 12))

    story.append(Paragraph("5. Tóm tắt chi phí", styles["VNHeading2"]))

    cost_text = (
        f"Chi phí ước tính hằng tháng: "
        f"{cost.get('estimated_monthly_cost', 0)} {cost.get('currency', 'USD')}"
    )

    story.append(Paragraph(safe_pdf_text(cost_text), styles["VNBody"]))

    cost_ai = cost.get("cost_ai_review", {})
    story.append(Paragraph(safe_pdf_text(cost_ai.get("summary", "")), styles["VNBody"]))
    story.append(Spacer(1, 12))

    story.append(Paragraph("6. Khuyến nghị ưu tiên", styles["VNHeading2"]))

    recommendations = final_review.get("priority_recommendations", [])

    if recommendations:
        for item in recommendations:
            if isinstance(item, dict):
                line = (
                    f"{item.get('priority', 'N/A')}: "
                    f"{item.get('recommendation', '')} "
                    f"Lý do: {item.get('reason', '')}"
                )
            else:
                line = str(item)

            story.append(Paragraph(safe_pdf_text(line), styles["VNBody"]))
            story.append(Spacer(1, 6))
    else:
        story.append(Paragraph("Không có khuyến nghị ưu tiên.", styles["VNBody"]))

    story.append(Spacer(1, 12))

    story.append(Paragraph("7. Kết luận", styles["VNHeading2"]))
    story.append(Paragraph(safe_pdf_text(final_review.get("conclusion", "")), styles["VNBody"]))

    doc.build(story)

    pdf = buffer.getvalue()
    buffer.close()

    return pdf


def add_pdf_heading(story, styles, text):
    story.append(Paragraph(safe_pdf_text(text), styles["Heading2"]))
    story.append(Spacer(1, 6))


def safe_pdf_text(value):
    if value is None:
        return ""

    text = str(value)

    # ReportLab Paragraph dùng một số ký tự giống XML/HTML markup,
    # nên cần escape để tránh lỗi.
    return html.escape(text)


def put_json_report(key, report_json):
    s3.put_object(
        Bucket=REPORT_BUCKET,
        Key=key,
        Body=json.dumps(report_json, ensure_ascii=False, indent=2).encode("utf-8"),
        ContentType="application/json; charset=utf-8",
        ServerSideEncryption="AES256"
    )


def put_html_report(key, html_content):
    s3.put_object(
        Bucket=REPORT_BUCKET,
        Key=key,
        Body=html_content.encode("utf-8"),
        ContentType="text/html; charset=utf-8",
        ServerSideEncryption="AES256"
    )


def put_pdf_report(key, pdf_bytes):
    s3.put_object(
        Bucket=REPORT_BUCKET,
        Key=key,
        Body=pdf_bytes,
        ContentType="application/pdf",
        ServerSideEncryption="AES256"
    )

def to_dynamodb_value(value):
    """
    DynamoDB không nhận float trực tiếp.
    Hàm này chuyển float thành Decimal và xử lý list/dict lồng nhau.
    """
    if isinstance(value, float):
        return Decimal(str(value))

    if isinstance(value, int):
        return value

    if isinstance(value, str):
        return value

    if isinstance(value, bool):
        return value

    if value is None:
        return None

    if isinstance(value, list):
        return [to_dynamodb_value(item) for item in value]

    if isinstance(value, dict):
        return {
            key: to_dynamodb_value(val)
            for key, val in value.items()
        }

    return str(value)


def extract_detected_services(analysis):
    services = analysis.get("architecture_json", {}).get("services", [])
    result = []

    for service in services:
        if isinstance(service, dict):
            result.append({
                "name": service.get("name", "Unknown"),
                "category": service.get("category", "Unknown"),
                "confidence": service.get("confidence", 0),
                "evidence": service.get("evidence", "")
            })
        else:
            result.append({
                "name": str(service),
                "category": "Unknown",
                "confidence": 0,
                "evidence": ""
            })

    return result


def extract_score(analysis, final_review):
    final_wa = final_review.get("well_architected_assessment", {})
    analysis_wa = analysis.get("well_architected_review", {})

    score = (
        final_wa.get("overall_score")
        or analysis_wa.get("overall_score")
        or 0
    )

    try:
        return int(score)
    except Exception:
        return 0


def extract_recommendations(final_review):
    recommendations = final_review.get("priority_recommendations", [])

    if recommendations:
        return recommendations

    fallback = final_review.get("recommendations", [])

    if fallback:
        return fallback

    return []


def extract_risks(final_review):
    risks = final_review.get("key_risks", [])

    if risks:
        return risks

    return []


def extract_best_practices(analysis, final_review):
    best_practices = []

    strengths = (
        analysis.get("well_architected_review", {})
        .get("strengths", [])
    )

    if isinstance(strengths, list):
        best_practices.extend(strengths)

    detected_summary = final_review.get("detected_services_summary", [])

    if isinstance(detected_summary, list):
        for item in detected_summary:
            if isinstance(item, dict):
                service = item.get("service", "")
                role = item.get("role_in_architecture", "")

                if service and role:
                    best_practices.append(
                        f"{service}: {role}"
                    )

    return best_practices


def extract_architecture_type(analysis):
    services = analysis.get("architecture_json", {}).get("services", [])

    service_names = []

    for service in services:
        if isinstance(service, dict):
            service_names.append(service.get("name", ""))
        else:
            service_names.append(str(service))

    names = " ".join(service_names).lower()

    if "lambda" in names or "api gateway" in names:
        return "Serverless Architecture"

    if "ec2" in names and "rds" in names:
        return "Web Application / Database Architecture"

    if "cloudfront" in names and "s3" in names:
        return "Static Web / CDN Architecture"

    if "ecs" in names or "eks" in names:
        return "Containerized Microservices"

    return "AI-detected AWS Architecture"


def update_review_history_completed(report_json, report_result):
    """
    Cập nhật DynamoDB sau khi report đã được tạo thành công.
    """
    if not review_table:
        print("TABLE_NAME is missing. Skip DynamoDB update.")
        return

    review_id = report_json.get("review_id")

    if not review_id:
        print("review_id is missing. Skip DynamoDB update.")
        return

    analysis = report_json.get("analysis", {})
    cost = report_json.get("cost", {})
    final_review = report_json.get("final_review", {})

    now = datetime.utcnow().isoformat()

    detected_services = extract_detected_services(analysis)
    score = extract_score(analysis, final_review)

    well_architected_result = {
        "analysisReview": analysis.get("well_architected_review", {}),
        "finalReview": final_review.get("well_architected_assessment", {}),
        "overallScore": score
    }

    cost_result = {
        "estimatedMonthlyCost": cost.get("estimated_monthly_cost", 0),
        "currency": cost.get("currency", "USD"),
        "breakdown": cost.get("breakdown", []),
        "costAiReview": cost.get("cost_ai_review", {}),
        "pricingMethod": cost.get("pricing_method", ""),
        "importantNote": cost.get("important_note", "")
    }

    report_files = {
        "jsonReportS3Key": report_result.get("json_report_s3_key"),
        "jsonReportS3Uri": report_result.get("json_report_s3_uri"),
        "htmlReportS3Key": report_result.get("html_report_s3_key"),
        "htmlReportS3Uri": report_result.get("html_report_s3_uri"),
        "pdfReportS3Key": report_result.get("pdf_report_s3_key"),
        "pdfReportS3Uri": report_result.get("pdf_report_s3_uri"),
        "pdfStatus": report_result.get("pdf_status", "UNKNOWN")
    }

    update_values = {
        ":status": "completed",
        ":updatedAt": now,
        ":completedDate": now,
        ":score": score,
        ":architectureType": extract_architecture_type(analysis),
        ":detectedServices": detected_services,
        ":wellArchitectedResult": well_architected_result,
        ":recommendations": extract_recommendations(final_review),
        ":risks": extract_risks(final_review),
        ":bestPractices": extract_best_practices(analysis, final_review),
        ":costResult": cost_result,
        ":reportFiles": report_files,
        ":reportBucket": report_result.get("report_bucket"),
        ":htmlReportS3Key": report_result.get("html_report_s3_key"),
        ":pdfReportS3Key": report_result.get("pdf_report_s3_key", ""),
        ":finalReview": final_review,
        ":analysisStatus": analysis.get("status", "UNKNOWN")
    }

    update_values = to_dynamodb_value(update_values)

    # Thêm SNS Notification logic
    sns = boto3.client("sns", region_name=os.environ.get("AWS_REGION", "ap-southeast-1"))
    sns_topic_arn = os.environ.get("SNS_TOPIC_ARN", "").strip()
    app_url = os.environ.get("APP_URL", "https://d9353ayez9zar.cloudfront.net").strip()

    try:
        # Fetch current item to get notificationEmail and enableNotification
        response = review_table.get_item(Key={"reviewId": review_id})
        item = response.get("Item", {})
        
        enable_notification = item.get("enableNotification", False)
        notification_email = item.get("notificationEmail", "")
        
        print("Notification enabled:", enable_notification)
        print("Notification email:", notification_email)
        print("SNS topic arn:", sns_topic_arn)
        
        if enable_notification:
            notification_status = "pending"
            try:
                print("Publishing SNS notification for review:", review_id)
                message = f"""AI AWS Architecture Review Completed

Review ID: {review_id}
File name: {item.get('fileName', 'Unknown')}
Architecture type: {extract_architecture_type(analysis)}
Overall score: {score}/100
Status: Completed
Completed date: {now}

Your AWS architecture review report has been generated successfully.

View report:
{app_url}/report/{review_id}

This notification was sent automatically by AI AWS Architecture Reviewer."""

                sns_response = sns.publish(
                    TopicArn=sns_topic_arn,
                    Message=message,
                    Subject=f"AI AWS Architecture Review Completed - {review_id}"
                )
                print("SNS publish response:", sns_response)
                print("Notification status updated to sent")
                notification_status = "sent"
            except Exception as sns_error:
                print("SNS publish failed:", str(sns_error))
                notification_status = "failed"
                
            # Add to UpdateExpression
            update_values[":notificationStatus"] = notification_status
            update_values[":notificationSentAt"] = now
        else:
            update_values[":notificationStatus"] = "disabled"
            
    except Exception as e:
        print(f"Error checking/sending notification: {e}")

    update_expression = """
            SET
                #status = :status,
                updatedAt = :updatedAt,
                completedDate = :completedDate,
                score = :score,
                architectureType = :architectureType,
                detectedServices = :detectedServices,
                wellArchitectedResult = :wellArchitectedResult,
                recommendations = :recommendations,
                risks = :risks,
                bestPractices = :bestPractices,
                costResult = :costResult,
                reportFiles = :reportFiles,
                reportBucket = :reportBucket,
                htmlReportS3Key = :htmlReportS3Key,
                pdfReportS3Key = :pdfReportS3Key,
                finalReview = :finalReview,
                analysisStatus = :analysisStatus
        """
    if ":notificationStatus" in update_values:
        update_expression += ", notificationStatus = :notificationStatus"
    if ":notificationSentAt" in update_values:
        update_expression += ", notificationSentAt = :notificationSentAt"

    review_table.update_item(
        Key={
            "reviewId": review_id
        },
        UpdateExpression=update_expression,
        ExpressionAttributeNames={
            "#status": "status"
        },
        ExpressionAttributeValues=update_values
    )

    print(f"DynamoDB review history updated: {review_id}")


def update_review_history_failed(review_id, error_message):
    """
    Cập nhật DynamoDB nếu PDF Generator lỗi.
    """
    if not review_table:
        print("TABLE_NAME is missing. Skip DynamoDB failed update.")
        return

    if not review_id:
        print("review_id is missing. Skip failed update.")
        return

    now = datetime.utcnow().isoformat()

    review_table.update_item(
        Key={
            "reviewId": review_id
        },
        UpdateExpression="""
            SET
                #status = :status,
                updatedAt = :updatedAt,
                errorMessage = :errorMessage
        """,
        ExpressionAttributeNames={
            "#status": "status"
        },
        ExpressionAttributeValues={
            ":status": "failed",
            ":updatedAt": now,
            ":errorMessage": str(error_message)
        }
    )

    print(f"DynamoDB review marked as failed: {review_id}")

def escape(value):
    if value is None:
        return ""

    return html.escape(str(value))