---
title : "Integrate Review APIs and Frontend Pages"
date : 2026-07-03 
weight : 5
chapter : false
pre : " <b> 5.5. </b> "
---

#### Review API overview

In this section, review data APIs are created and integrated with the React frontend pages.

After a user uploads an architecture diagram, the system stores review metadata in DynamoDB. The frontend needs to retrieve this data to display review history, review details, and review progress.

The review API flow is:

```text
React Frontend → API Gateway → Lambda Upload Service → DynamoDB
```

The API Gateway endpoint used in this project is:
```text
https://031hqksomd.execute-api.ap-southeast-1.amazonaws.com
```

#### Review API routes

The following API routes are used in this project:
```text
GET /reviews
GET /reviews/{reviewId}
GET /reviews/{reviewId}/status
```
Each route has a specific purpose:
```text
GET /reviews
Retrieves the list of uploaded reviews from DynamoDB.
GET /reviews/{reviewId}
Retrieves detailed information of a specific review.
GET /reviews/{reviewId}/status
Retrieves the current status of a specific review.
```

#### Step 1: Create GET /reviews route

Create the following route in API Gateway:
```text
GET /reviews
```
This route is integrated with the Lambda Upload Service.

The Lambda function reads review records from DynamoDB and returns the review list to the frontend.

This API is used by the Review History page.

#### Step 2: Create GET /reviews/{reviewId} route

Create the following route in API Gateway:
```text
GET /reviews/{reviewId}
```

This route retrieves detailed information for one review based on the reviewId.

Example review ID:
```text
REV-C6A0D048
```
This API is used by the Review Detail page.

#### Step 3: Create GET /reviews/{reviewId}/status route

Create the following route in API Gateway:
```text
GET /reviews/{reviewId}/status
```

This route retrieves the current processing status of a review.

Example statuses include:
```text
uploaded
processing
completed
failed
```
At the current stage of the project, the initial status after upload is:
```text
uploaded
```
This API is used by the Review Progress page.

![Review API](/images/5-Workshop/5.5-Review-api/ai-aws-reviewer-api.png)

#### Step 4: Configure CORS for review APIs

CORS must be configured for the frontend to call the review APIs.

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
The OPTIONS method is required for browser preflight requests.

![Review API CORS](/images/5-Workshop/5.5-Review-api/ai-aws-reviewer-api-cors.png)

#### Step 5: Test GET /reviews API

Use PowerShell to test the review list API:
```text
curl.exe -i "https://031hqksomd.execute-api.ap-southeast-1.amazonaws.com/reviews" -H "Origin: https://d9353ayez9zar.cloudfront.net"
```

If the API works correctly, it returns a list of review records from DynamoDB.

![Review API test](/images/5-Workshop/5.5-Review-api/test-reviews.png)

#### Step 6: Test GET /reviews/{reviewId} API

Use PowerShell to test the review detail API:
```text
curl.exe -i "https://031hqksomd.execute-api.ap-southeast-1.amazonaws.com/reviews/REV-C6A0D048" -H "Origin: https://d9353ayez9zar.cloudfront.net"
```
Replace REV-C6A0D048 with an actual review ID from DynamoDB.

If the API works correctly, it returns detailed information for the selected review.

Example response:

{
  "reviewId": "REV-C6A0D048",
  "status": "uploaded"
}

![Review API test](/images/5-Workshop/5.5-Review-api/test-review-detail.png)

#### Step 7: Test GET /reviews/{reviewId}/status API

Use PowerShell to test the review status API:
```text
curl.exe -i "https://031hqksomd.execute-api.ap-southeast-1.amazonaws.com/reviews/REV-C6A0D048/status" -H "Origin: https://d9353ayez9zar.cloudfront.net"
```
Replace REV-C6A0D048 with an actual review ID from DynamoDB.

If the API works correctly, it returns the current review status.

Example response:
```text
{
  "reviewId": "REV-C6A0D048",
  "status": "uploaded"
}
```

![Review API test](/images/5-Workshop/5.5-Review-api/test-review-detail-status.png)

#### Step 8: Connect Review History page

The Review History page uses the following API:

```text
GET /reviews
```

This page displays uploaded review records from DynamoDB.

The page may display information such as:
```text
Review ID
File name
Upload date
Status
Architecture type
```

![Review History page](/images/5-Workshop/5.5-Review-api/Review-history-page.png)

#### Step 9: Connect Review Detail page

The Review Detail page uses the following API:

```text
GET /reviews/{reviewId}
```

This page displays detailed information about a selected review.

The page may display information such as:
```text
Review ID
File name
File type
File size
Upload date
Review status
```

#### Step 10: Connect Review Progress page

The Review Progress page uses the following API:
```text
GET /reviews/{reviewId}/status
```
This page displays the current status of the review workflow.

At the current implementation stage, uploaded diagrams are marked as:
```text
uploaded
```
In the next phase, this status will be updated by the AI review workflow.

![Review Detail and process page](/images/5-Workshop/5.5-Review-api/Review-detail-and-process-page.png)