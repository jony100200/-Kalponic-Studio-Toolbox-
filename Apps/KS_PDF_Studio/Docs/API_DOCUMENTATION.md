# KS PDF Studio API Documentation

## Overview

KS PDF Studio provides a comprehensive REST API for enterprise integrations, automation workflows, and third-party applications. The API enables programmatic access to all KS PDF Studio features including PDF generation, AI enhancement, document processing, and monetization tools.

## Base URL
```
https://api.kspdfstudio.com/v1
```

## Authentication

### API Key Authentication
Include your API key in the request header:
```
X-API-Key: your_api_key_here
```

### Bearer Token Authentication
Include a Bearer token in the Authorization header:
```
Authorization: Bearer your_jwt_token
```

## Rate Limits
- 1000 requests per hour for free tier
- 10000 requests per hour for enterprise tier
- Rate limit headers are included in all responses

## Error Handling

All errors return a JSON response with the following structure:
```json
{
  "error": "Error message",
  "code": "ERROR_CODE",
  "details": {}
}
```

Common HTTP status codes:
- `200` - Success
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `429` - Too Many Requests
- `500` - Internal Server Error

---

## Endpoints

### Health & Info

#### GET /api/v1/health
Check API health status.

**Response:**
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "timestamp": "2024-01-01T12:00:00Z",
  "services": {
    "pdf_engine": "available",
    "ai_manager": "available",
    "license_manager": "available",
    "analytics": "available"
  }
}
```

#### GET /api/v1/info
Get API information.

**Response:**
```json
{
  "name": "KS PDF Studio API",
  "version": "v1",
  "description": "REST API for KS PDF Studio enterprise integrations",
  "documentation": "/api/v1/docs",
  "endpoints": [
    "/api/v1/documents",
    "/api/v1/pdf",
    "/api/v1/ai",
    "/api/v1/licenses",
    "/api/v1/analytics"
  ]
}
```

### Authentication

#### POST /api/v1/auth/login
User login.

**Request:**
```json
{
  "username": "user@example.com",
  "password": "password123"
}
```

**Response:**
```json
{
  "token": "jwt_token_here",
  "user_id": "user123"
}
```

#### POST /api/v1/auth/register
User registration.

**Request:**
```json
{
  "username": "user@example.com",
  "password": "password123",
  "email": "user@example.com"
}
```

**Response:**
```json
{
  "user_id": "user123",
  "api_key": "api_key_here",
  "message": "Registration successful"
}
```

#### GET /api/v1/auth/validate
Validate authentication token.

**Response:**
```json
{
  "valid": true,
  "user": {
    "user_id": "user123",
    "license_id": "enterprise"
  }
}
```

### Document Management

#### GET /api/v1/documents
List user documents.

**Query Parameters:**
- `limit` (integer): Maximum number of documents to return (default: 50)
- `offset` (integer): Number of documents to skip (default: 0)
- `sort_by` (string): Sort field (default: "created")
- `sort_order` (string): Sort order: "asc" or "desc" (default: "desc")

**Response:**
```json
{
  "documents": [
    {
      "id": "doc123",
      "title": "Tutorial Document",
      "created": "2024-01-01T12:00:00Z",
      "updated": "2024-01-01T12:30:00Z",
      "size": 1024000
    }
  ],
  "total": 1,
  "limit": 50,
  "offset": 0
}
```

#### POST /api/v1/documents
Create a new document.

**Request:**
```json
{
  "title": "My Tutorial",
  "content": "# Tutorial Content\n\nThis is my tutorial content...",
  "template": "professional",
  "metadata": {
    "author": "John Doe",
    "tags": ["tutorial", "programming"]
  }
}
```

**Response:**
```json
{
  "document_id": "doc123",
  "title": "My Tutorial",
  "created": "2024-01-01T12:00:00Z",
  "status": "created"
}
```

#### GET /api/v1/documents/{document_id}
Get document details.

**Response:**
```json
{
  "id": "doc123",
  "title": "My Tutorial",
  "content": "# Tutorial Content...",
  "template": "professional",
  "metadata": {
    "author": "John Doe",
    "tags": ["tutorial", "programming"]
  },
  "created": "2024-01-01T12:00:00Z",
  "updated": "2024-01-01T12:30:00Z"
}
```

#### PUT /api/v1/documents/{document_id}
Update document.

**Request:**
```json
{
  "title": "Updated Tutorial",
  "content": "# Updated Content...",
  "metadata": {
    "tags": ["tutorial", "programming", "updated"]
  }
}
```

**Response:**
```json
{
  "document_id": "doc123",
  "updated": "2024-01-01T12:30:00Z",
  "status": "updated"
}
```

#### DELETE /api/v1/documents/{document_id}
Delete document.

**Response:**
```json
{
  "document_id": "doc123",
  "status": "deleted"
}
```

### PDF Operations

#### POST /api/v1/pdf/generate
Generate PDF from content.

**Request:**
```json
{
  "content": "# My Document\n\nContent here...",
  "template": "professional",
  "title": "My Document",
  "options": {
    "page_size": "A4",
    "orientation": "portrait",
    "margins": {
      "top": 20,
      "bottom": 20,
      "left": 20,
      "right": 20
    },
    "include_toc": true,
    "include_headers": true
  }
}
```

**Response:**
```json
{
  "file_id": "file123",
  "download_url": "/api/v1/files/download/file123",
  "filename": "My Document.pdf",
  "size": 1024000,
  "pages": 5
}
```

#### POST /api/v1/pdf/extract
Extract text from PDF.

**Request:** (multipart/form-data)
- `file`: PDF file to extract from
- `method`: "text" or "ocr" (default: "text")
- `pages`: "all" or comma-separated page numbers (default: "all")

**Response:**
```json
{
  "text": "Extracted text content...",
  "pages": 5,
  "characters": 12345,
  "metadata": {
    "title": "Document Title",
    "author": "Author Name",
    "pages": 5,
    "size": 1024000
  }
}
```

#### POST /api/v1/pdf/watermark
Add watermark to PDF.

**Request:** (multipart/form-data)
- `file`: PDF file to watermark
- `watermark_text`: Text to use as watermark
- `watermark_type`: "text" or "image" (default: "text")
- `opacity`: Opacity level 0-1 (default: 0.3)
- `position`: "center", "diagonal", "header", "footer" (default: "diagonal")

**Response:**
```json
{
  "file_id": "file123",
  "download_url": "/api/v1/files/download/file123",
  "filename": "watermarked_document.pdf"
}
```

#### POST /api/v1/pdf/merge
Merge multiple PDFs.

**Request:** (multipart/form-data)
- `files`: Array of PDF files to merge
- `output_name`: Name for merged file (optional)

**Response:**
```json
{
  "file_id": "file123",
  "download_url": "/api/v1/files/download/file123",
  "filename": "merged_document.pdf",
  "total_pages": 25
}
```

#### POST /api/v1/pdf/split
Split PDF into multiple files.

**Request:** (multipart/form-data)
- `file`: PDF file to split
- `split_type`: "pages" or "ranges" (default: "pages")
- `pages_per_file`: Number of pages per split file (for "pages" type)
- `ranges`: Array of page ranges like ["1-5", "6-10"] (for "ranges" type)

**Response:**
```json
{
  "files": [
    {
      "file_id": "file123",
      "download_url": "/api/v1/files/download/file123",
      "filename": "document_part1.pdf",
      "pages": "1-5"
    },
    {
      "file_id": "file124",
      "download_url": "/api/v1/files/download/file124",
      "filename": "document_part2.pdf",
      "pages": "6-10"
    }
  ]
}
```

### AI Operations

#### POST /api/v1/ai/enhance
Enhance content with AI.

**Request:**
```json
{
  "content": "This is some content to enhance",
  "enhancement_type": "grammar",
  "options": {
    "language": "en",
    "tone": "professional",
    "length": "concise"
  }
}
```

**Available enhancement types:**
- `grammar`: Fix grammar and spelling
- `structure`: Improve document structure
- `clarity`: Enhance clarity and readability
- `seo`: Optimize for search engines
- `academic`: Format for academic writing
- `creative`: Add creative elements

**Response:**
```json
{
  "original_content": "This is some content to enhance",
  "enhanced_content": "This is the enhanced content with improved grammar and structure.",
  "enhancement_type": "grammar",
  "confidence": 0.95,
  "changes": [
    "Fixed grammar error",
    "Improved sentence structure"
  ]
}
```

#### POST /api/v1/ai/generate
Generate content with AI.

**Request:**
```json
{
  "prompt": "Write a tutorial about Python decorators",
  "content_type": "tutorial",
  "length": "medium",
  "style": "educational",
  "audience": "beginners",
  "include_examples": true
}
```

**Response:**
```json
{
  "generated_content": "# Python Decorators Tutorial\n\nDecorators are a powerful feature...",
  "content_type": "tutorial",
  "word_count": 850,
  "sections": 5,
  "metadata": {
    "reading_time": "5 minutes",
    "difficulty": "beginner"
  }
}
```

#### POST /api/v1/ai/summarize
Summarize content with AI.

**Request:**
```json
{
  "content": "Long document content here...",
  "summary_type": "executive",
  "length": "short",
  "format": "bullet_points"
}
```

**Summary types:**
- `executive`: High-level overview
- `key_points`: Main points and takeaways
- `abstract`: Academic-style abstract
- `tldr`: Very brief summary

**Response:**
```json
{
  "summary": "• Main point 1\n• Main point 2\n• Key takeaway",
  "summary_type": "key_points",
  "original_length": 2500,
  "summary_length": 150,
  "compression_ratio": 0.06
}
```

### Batch Operations

#### POST /api/v1/batch/process
Process multiple documents in batch.

**Request:**
```json
{
  "operations": [
    {
      "type": "generate_pdf",
      "content": "# Document 1\n\nContent...",
      "template": "professional"
    },
    {
      "type": "ai_enhance",
      "content": "Content to enhance...",
      "enhancement_type": "grammar"
    }
  ],
  "options": {
    "parallel": true,
    "max_concurrent": 5,
    "webhook_url": "https://example.com/webhook"
  }
}
```

**Response:**
```json
{
  "batch_id": "batch123",
  "status": "processing",
  "total_operations": 2,
  "completed": 0,
  "estimated_time": "30 seconds",
  "webhook_url": "https://example.com/webhook"
}
```

#### GET /api/v1/batch/status/{batch_id}
Get batch processing status.

**Response:**
```json
{
  "batch_id": "batch123",
  "status": "completed",
  "total_operations": 2,
  "completed": 2,
  "failed": 0,
  "results": [
    {
      "operation_id": "op1",
      "type": "generate_pdf",
      "status": "success",
      "result": {
        "file_id": "file123",
        "download_url": "/api/v1/files/download/file123"
      }
    },
    {
      "operation_id": "op2",
      "type": "ai_enhance",
      "status": "success",
      "result": {
        "enhanced_content": "Enhanced content..."
      }
    }
  ],
  "started_at": "2024-01-01T12:00:00Z",
  "completed_at": "2024-01-01T12:00:30Z"
}
```

### License Management

#### POST /api/v1/licenses
Create a new license.

**Request:**
```json
{
  "user_id": "user123",
  "user_name": "John Doe",
  "user_email": "john@example.com",
  "license_type": "personal",
  "content_id": "content123",
  "content_title": "My Tutorial",
  "duration_days": 365,
  "max_uses": 1000,
  "features": ["pdf_generation", "ai_enhancement"],
  "watermark_text": "Licensed to John Doe"
}
```

**License types:**
- `personal`: Single user license
- `commercial`: Commercial use license
- `enterprise`: Enterprise license
- `educational`: Educational institution license

**Response:**
```json
{
  "license_key": "KS-LIC-ABC123-XYZ789",
  "license_info": {
    "license_id": "lic123",
    "license_type": "personal",
    "user_id": "user123",
    "content_id": "content123",
    "created": "2024-01-01T12:00:00Z",
    "expires": "2025-01-01T12:00:00Z",
    "max_uses": 1000,
    "current_uses": 0,
    "features": ["pdf_generation", "ai_enhancement"],
    "status": "active"
  }
}
```

#### POST /api/v1/licenses/validate
Validate a license key.

**Request:**
```json
{
  "license_key": "KS-LIC-ABC123-XYZ789",
  "content_id": "content123",
  "user_id": "user123"
}
```

**Response:**
```json
{
  "valid": true,
  "license_info": {
    "license_id": "lic123",
    "license_type": "personal",
    "user_id": "user123",
    "content_id": "content123",
    "expires": "2025-01-01T12:00:00Z",
    "remaining_uses": 999,
    "features": ["pdf_generation", "ai_enhancement"],
    "status": "active"
  }
}
```

#### GET /api/v1/licenses/{license_id}
Get license details.

**Response:**
```json
{
  "license_id": "lic123",
  "license_key": "KS-LIC-ABC123-XYZ789",
  "license_type": "personal",
  "user_id": "user123",
  "content_id": "content123",
  "created": "2024-01-01T12:00:00Z",
  "expires": "2025-01-01T12:00:00Z",
  "max_uses": 1000,
  "current_uses": 5,
  "features": ["pdf_generation", "ai_enhancement"],
  "status": "active"
}
```

### Analytics

#### GET /api/v1/analytics/usage
Get usage analytics.

**Query Parameters:**
- `days` (integer): Number of days to analyze (default: 30)
- `user_id` (string): Filter by user ID
- `license_id` (string): Filter by license ID
- `event_type` (string): Filter by event type

**Response:**
```json
{
  "period": {
    "start": "2023-12-01T00:00:00Z",
    "end": "2024-01-01T00:00:00Z",
    "days": 30
  },
  "summary": {
    "total_requests": 15420,
    "total_users": 234,
    "total_licenses": 45,
    "total_revenue": 1234.56
  },
  "usage_by_day": [
    {
      "date": "2023-12-01",
      "requests": 512,
      "users": 23,
      "revenue": 45.67
    }
  ],
  "top_features": [
    {
      "feature": "pdf_generation",
      "usage_count": 8920,
      "percentage": 57.8
    }
  ],
  "license_distribution": {
    "personal": 120,
    "commercial": 89,
    "enterprise": 25
  }
}
```

#### GET /api/v1/analytics/revenue
Get revenue analytics.

**Query Parameters:**
- `days` (integer): Number of days to analyze (default: 30)
- `license_type` (string): Filter by license type
- `group_by` (string): Group results by "day", "week", "month" (default: "day")

**Response:**
```json
{
  "period": {
    "start": "2023-12-01T00:00:00Z",
    "end": "2024-01-01T00:00:00Z",
    "days": 30
  },
  "revenue": {
    "total": 5678.90,
    "by_license_type": {
      "personal": 1234.56,
      "commercial": 3456.78,
      "enterprise": 987.56
    },
    "by_period": [
      {
        "period": "2023-12-01",
        "revenue": 189.23,
        "transactions": 12
      }
    ],
    "growth_rate": 15.7
  },
  "transactions": {
    "total": 456,
    "average_value": 12.45,
    "by_payment_method": {
      "stripe": 389,
      "paypal": 67
    }
  }
}
```

### Webhooks

#### GET /api/v1/webhooks
List user webhooks.

**Response:**
```json
{
  "webhooks": [
    {
      "webhook_id": "web123",
      "url": "https://example.com/webhook",
      "events": ["batch.completed", "license.expired"],
      "active": true,
      "created": "2024-01-01T12:00:00Z"
    }
  ]
}
```

#### POST /api/v1/webhooks
Create a webhook.

**Request:**
```json
{
  "url": "https://example.com/webhook",
  "events": ["batch.completed", "license.expired"],
  "secret": "webhook_secret_for_verification"
}
```

**Available events:**
- `batch.completed`: Batch processing finished
- `batch.failed`: Batch processing failed
- `license.created`: New license created
- `license.expired`: License expired
- `license.nearing_expiry`: License expiring soon
- `document.created`: Document created
- `document.updated`: Document updated

**Response:**
```json
{
  "webhook_id": "web123",
  "url": "https://example.com/webhook",
  "events": ["batch.completed", "license.expired"],
  "active": true,
  "created": "2024-01-01T12:00:00Z"
}
```

#### DELETE /api/v1/webhooks/{webhook_id}
Delete a webhook.

**Response:**
```json
{
  "webhook_id": "web123",
  "status": "deleted"
}
```

### File Operations

#### POST /api/v1/files/upload
Upload a file.

**Request:** (multipart/form-data)
- `file`: File to upload
- `category`: "document", "image", "template" (default: "document")

**Response:**
```json
{
  "file_id": "file123",
  "filename": "document.pdf",
  "size": 1024000,
  "category": "document",
  "upload_url": "/api/v1/files/download/file123",
  "uploaded": "2024-01-01T12:00:00Z"
}
```

#### GET /api/v1/files/download/{file_id}
Download a file.

**Response:** File content with appropriate headers.

---

## Webhook Payloads

### Batch Completed
```json
{
  "event": "batch.completed",
  "batch_id": "batch123",
  "user_id": "user123",
  "timestamp": "2024-01-01T12:00:00Z",
  "results": [
    {
      "operation_id": "op1",
      "type": "generate_pdf",
      "status": "success",
      "result": {
        "file_id": "file123",
        "download_url": "/api/v1/files/download/file123"
      }
    }
  ]
}
```

### License Expired
```json
{
  "event": "license.expired",
  "license_id": "lic123",
  "license_key": "KS-LIC-ABC123-XYZ789",
  "user_id": "user123",
  "timestamp": "2024-01-01T12:00:00Z",
  "license_info": {
    "license_type": "personal",
    "content_id": "content123",
    "expired_at": "2024-01-01T12:00:00Z"
  }
}
```

---

## SDKs and Client Libraries

### Python SDK
```python
from kspdf_studio import KSClient

client = KSClient(api_key="your_api_key")

# Generate PDF
result = client.pdf.generate(
    content="# My Document\n\nContent here...",
    template="professional"
)

# Download PDF
client.files.download(result['file_id'], "output.pdf")
```

### JavaScript SDK
```javascript
const { KSClient } = require('ks-pdf-studio-sdk');

const client = new KSClient({ apiKey: 'your_api_key' });

// Generate PDF
const result = await client.pdf.generate({
  content: '# My Document\n\nContent here...',
  template: 'professional'
});

// Download PDF
await client.files.download(result.file_id, 'output.pdf');
```

### cURL Examples

#### Generate PDF
```bash
curl -X POST "https://api.kspdfstudio.com/v1/pdf/generate" \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "# My Document\n\nContent here...",
    "template": "professional",
    "title": "My Document"
  }'
```

#### Extract PDF Text
```bash
curl -X POST "https://api.kspdfstudio.com/v1/pdf/extract" \
  -H "X-API-Key: your_api_key" \
  -F "file=@document.pdf"
```

#### AI Enhancement
```bash
curl -X POST "https://api.kspdfstudio.com/v1/ai/enhance" \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "This is some content to enhance",
    "enhancement_type": "grammar"
  }'
```

---

## Rate Limits and Quotas

### Free Tier
- 1000 API requests per hour
- 10 GB file storage
- Basic AI features
- Community support

### Professional Tier ($29/month)
- 10000 API requests per hour
- 100 GB file storage
- Advanced AI features
- Priority support
- Webhook support

### Enterprise Tier (Custom pricing)
- Unlimited API requests
- Unlimited storage
- Custom AI models
- Dedicated support
- SLA guarantee
- On-premise deployment option

---

## Support

- **Documentation**: https://docs.kspdfstudio.com
- **API Reference**: https://api.kspdfstudio.com/docs
- **Community Forum**: https://community.kspdfstudio.com
- **Email Support**: support@kspdfstudio.com
- **Enterprise Support**: enterprise@kspdfstudio.com

---

## Changelog

### Version 2.0.0 (Current)
- Complete API redesign with RESTful architecture
- Added batch processing capabilities
- Enhanced AI integration with multiple models
- Comprehensive analytics and reporting
- Webhook support for real-time integrations
- Improved authentication and security

### Version 1.5.0
- Added AI content enhancement
- PDF extraction capabilities
- License management system
- Basic analytics

### Version 1.0.0
- Initial API release
- PDF generation
- Basic document management
- User authentication