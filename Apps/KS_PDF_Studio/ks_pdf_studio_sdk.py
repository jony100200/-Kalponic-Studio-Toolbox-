"""
KS PDF Studio Python SDK
Official Python client library for KS PDF Studio API.

Author: Kalponic Studio
Version: 2.0.0
License: MIT
"""

import os
import json
import time
import requests
from typing import Dict, List, Optional, Union, Any, BinaryIO
from pathlib import Path
from urllib.parse import urljoin, urlparse
import mimetypes


class KSAPIError(Exception):
    """Base exception for KS API errors."""

    def __init__(self, message: str, status_code: int = None, response_data: Dict = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data or {}


class KSAuthenticationError(KSAPIError):
    """Authentication error."""
    pass


class KSValidationError(KSAPIError):
    """Validation error."""
    pass


class KSRateLimitError(KSAPIError):
    """Rate limit exceeded error."""
    pass


class KSClient:
    """
    KS PDF Studio API client.

    Args:
        api_key: Your API key
        base_url: API base URL (default: https://api.kspdfstudio.com/v1)
        timeout: Request timeout in seconds (default: 30)
        max_retries: Maximum number of retries for failed requests (default: 3)
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.kspdfstudio.com/v1",
        timeout: int = 30,
        max_retries: int = 3
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.max_retries = max_retries

        self.session = requests.Session()
        self.session.headers.update({
            'X-API-Key': self.api_key,
            'User-Agent': 'KS-PDF-Studio-Python-SDK/2.0.0'
        })

        # Initialize API modules
        self.pdf = PDFAPI(self)
        self.ai = AIAPI(self)
        self.documents = DocumentsAPI(self)
        self.licenses = LicensesAPI(self)
        self.analytics = AnalyticsAPI(self)
        self.files = FilesAPI(self)
        self.batch = BatchAPI(self)
        self.webhooks = WebhooksAPI(self)

    def _request(
        self,
        method: str,
        endpoint: str,
        data: Dict = None,
        files: Dict = None,
        params: Dict = None,
        json_data: Dict = None
    ) -> Dict:
        """Make API request with error handling and retries."""
        url = urljoin(self.base_url + '/', endpoint.lstrip('/'))

        for attempt in range(self.max_retries + 1):
            try:
                if json_data is not None:
                    response = self.session.request(
                        method=method,
                        url=url,
                        json=json_data,
                        params=params,
                        timeout=self.timeout
                    )
                elif files:
                    response = self.session.request(
                        method=method,
                        url=url,
                        data=data,
                        files=files,
                        params=params,
                        timeout=self.timeout
                    )
                else:
                    response = self.session.request(
                        method=method,
                        url=url,
                        data=data,
                        params=params,
                        timeout=self.timeout
                    )

                return self._handle_response(response)

            except requests.RequestException as e:
                if attempt == self.max_retries:
                    raise KSAPIError(f"Request failed after {self.max_retries + 1} attempts: {e}")
                time.sleep(2 ** attempt)  # Exponential backoff

    def _handle_response(self, response: requests.Response) -> Dict:
        """Handle API response and raise appropriate exceptions."""
        try:
            data = response.json()
        except ValueError:
            data = {}

        if response.status_code == 401:
            raise KSAuthenticationError("Authentication failed", response.status_code, data)
        elif response.status_code == 400:
            raise KSValidationError("Validation error", response.status_code, data)
        elif response.status_code == 429:
            raise KSRateLimitError("Rate limit exceeded", response.status_code, data)
        elif not response.ok:
            error_msg = data.get('error', f"API error: {response.status_code}")
            raise KSAPIError(error_msg, response.status_code, data)

        return data

    def health_check(self) -> Dict:
        """Check API health status."""
        return self._request('GET', '/health')

    def get_info(self) -> Dict:
        """Get API information."""
        return self._request('GET', '/info')


class PDFAPI:
    """PDF operations API."""

    def __init__(self, client: KSClient):
        self.client = client

    def generate(
        self,
        content: str,
        template: str = "professional",
        title: str = None,
        options: Dict = None
    ) -> Dict:
        """
        Generate PDF from content.

        Args:
            content: Document content (markdown or plain text)
            template: PDF template ("professional", "academic", "simple")
            title: Document title
            options: Additional PDF options

        Returns:
            Dict containing file_id, download_url, etc.
        """
        data = {
            'content': content,
            'template': template
        }

        if title:
            data['title'] = title
        if options:
            data['options'] = options

        return self.client._request('POST', '/pdf/generate', json_data=data)

    def extract(
        self,
        file_path: Union[str, Path, BinaryIO],
        method: str = "text",
        pages: str = "all"
    ) -> Dict:
        """
        Extract text from PDF.

        Args:
            file_path: Path to PDF file or file-like object
            method: Extraction method ("text" or "ocr")
            pages: Pages to extract ("all" or comma-separated numbers)

        Returns:
            Dict containing extracted text and metadata
        """
        files = {}
        data = {'method': method, 'pages': pages}

        if hasattr(file_path, 'read'):
            files['file'] = ('file.pdf', file_path, 'application/pdf')
        else:
            file_path = Path(file_path)
            files['file'] = (file_path.name, open(file_path, 'rb'), 'application/pdf')

        try:
            return self.client._request('POST', '/pdf/extract', files=files, data=data)
        finally:
            # Close file if we opened it
            if 'file' in files and hasattr(files['file'][1], 'close'):
                files['file'][1].close()

    def watermark(
        self,
        file_path: Union[str, Path, BinaryIO],
        watermark_text: str,
        watermark_type: str = "text",
        opacity: float = 0.3,
        position: str = "diagonal"
    ) -> Dict:
        """
        Add watermark to PDF.

        Args:
            file_path: Path to PDF file or file-like object
            watermark_text: Text to use as watermark
            watermark_type: "text" or "image"
            opacity: Opacity level (0-1)
            position: Watermark position

        Returns:
            Dict containing watermarked file info
        """
        files = {}
        data = {
            'watermark_text': watermark_text,
            'watermark_type': watermark_type,
            'opacity': opacity,
            'position': position
        }

        if hasattr(file_path, 'read'):
            files['file'] = ('file.pdf', file_path, 'application/pdf')
        else:
            file_path = Path(file_path)
            files['file'] = (file_path.name, open(file_path, 'rb'), 'application/pdf')

        try:
            return self.client._request('POST', '/pdf/watermark', files=files, data=data)
        finally:
            if 'file' in files and hasattr(files['file'][1], 'close'):
                files['file'][1].close()

    def merge(self, file_paths: List[Union[str, Path]], output_name: str = None) -> Dict:
        """
        Merge multiple PDFs.

        Args:
            file_paths: List of PDF file paths
            output_name: Name for merged file

        Returns:
            Dict containing merged file info
        """
        files = {}
        data = {}

        if output_name:
            data['output_name'] = output_name

        for i, file_path in enumerate(file_paths):
            file_path = Path(file_path)
            files[f'files'] = (file_path.name, open(file_path, 'rb'), 'application/pdf')

        try:
            return self.client._request('POST', '/pdf/merge', files=files, data=data)
        finally:
            for file_tuple in files.values():
                if hasattr(file_tuple[1], 'close'):
                    file_tuple[1].close()

    def split(
        self,
        file_path: Union[str, Path, BinaryIO],
        split_type: str = "pages",
        pages_per_file: int = None,
        ranges: List[str] = None
    ) -> Dict:
        """
        Split PDF into multiple files.

        Args:
            file_path: Path to PDF file or file-like object
            split_type: "pages" or "ranges"
            pages_per_file: Pages per file (for "pages" type)
            ranges: Page ranges like ["1-5", "6-10"] (for "ranges" type)

        Returns:
            Dict containing split file info
        """
        files = {}
        data = {'split_type': split_type}

        if hasattr(file_path, 'read'):
            files['file'] = ('file.pdf', file_path, 'application/pdf')
        else:
            file_path = Path(file_path)
            files['file'] = (file_path.name, open(file_path, 'rb'), 'application/pdf')

        if split_type == "pages" and pages_per_file:
            data['pages_per_file'] = pages_per_file
        elif split_type == "ranges" and ranges:
            data['ranges'] = json.dumps(ranges)

        try:
            return self.client._request('POST', '/pdf/split', files=files, data=data)
        finally:
            if 'file' in files and hasattr(files['file'][1], 'close'):
                files['file'][1].close()


class AIAPI:
    """AI operations API."""

    def __init__(self, client: KSClient):
        self.client = client

    def enhance(
        self,
        content: str,
        enhancement_type: str = "general",
        options: Dict = None
    ) -> Dict:
        """
        Enhance content with AI.

        Args:
            content: Content to enhance
            enhancement_type: Type of enhancement
            options: Additional options

        Returns:
            Dict containing enhanced content
        """
        data = {
            'content': content,
            'enhancement_type': enhancement_type
        }

        if options:
            data['options'] = options

        return self.client._request('POST', '/ai/enhance', json_data=data)

    def generate(
        self,
        prompt: str,
        content_type: str = "article",
        length: str = "medium",
        style: str = "professional",
        audience: str = "general",
        include_examples: bool = True
    ) -> Dict:
        """
        Generate content with AI.

        Args:
            prompt: Content generation prompt
            content_type: Type of content to generate
            length: Content length ("short", "medium", "long")
            style: Writing style
            audience: Target audience
            include_examples: Whether to include examples

        Returns:
            Dict containing generated content
        """
        data = {
            'prompt': prompt,
            'content_type': content_type,
            'length': length,
            'style': style,
            'audience': audience,
            'include_examples': include_examples
        }

        return self.client._request('POST', '/ai/generate', json_data=data)

    def summarize(
        self,
        content: str,
        summary_type: str = "key_points",
        length: str = "medium",
        format: str = "paragraph"
    ) -> Dict:
        """
        Summarize content with AI.

        Args:
            content: Content to summarize
            summary_type: Type of summary
            length: Summary length
            format: Output format

        Returns:
            Dict containing summary
        """
        data = {
            'content': content,
            'summary_type': summary_type,
            'length': length,
            'format': format
        }

        return self.client._request('POST', '/ai/summarize', json_data=data)


class DocumentsAPI:
    """Document management API."""

    def __init__(self, client: KSClient):
        self.client = client

    def list(
        self,
        limit: int = 50,
        offset: int = 0,
        sort_by: str = "created",
        sort_order: str = "desc"
    ) -> Dict:
        """List documents."""
        params = {
            'limit': limit,
            'offset': offset,
            'sort_by': sort_by,
            'sort_order': sort_order
        }
        return self.client._request('GET', '/documents', params=params)

    def create(self, title: str, content: str, template: str = "professional", metadata: Dict = None) -> Dict:
        """Create a new document."""
        data = {
            'title': title,
            'content': content,
            'template': template
        }
        if metadata:
            data['metadata'] = metadata

        return self.client._request('POST', '/documents', json_data=data)

    def get(self, document_id: str) -> Dict:
        """Get document details."""
        return self.client._request('GET', f'/documents/{document_id}')

    def update(self, document_id: str, **updates) -> Dict:
        """Update document."""
        return self.client._request('PUT', f'/documents/{document_id}', json_data=updates)

    def delete(self, document_id: str) -> Dict:
        """Delete document."""
        return self.client._request('DELETE', f'/documents/{document_id}')


class LicensesAPI:
    """License management API."""

    def __init__(self, client: KSClient):
        self.client = client

    def create(
        self,
        user_id: str,
        user_name: str,
        user_email: str,
        license_type: str,
        content_id: str,
        content_title: str,
        duration_days: int = None,
        max_uses: int = None,
        features: List[str] = None,
        watermark_text: str = None
    ) -> Dict:
        """Create a new license."""
        data = {
            'user_id': user_id,
            'user_name': user_name,
            'user_email': user_email,
            'license_type': license_type,
            'content_id': content_id,
            'content_title': content_title
        }

        if duration_days:
            data['duration_days'] = duration_days
        if max_uses:
            data['max_uses'] = max_uses
        if features:
            data['features'] = features
        if watermark_text:
            data['watermark_text'] = watermark_text

        return self.client._request('POST', '/licenses', json_data=data)

    def validate(self, license_key: str, content_id: str = None, user_id: str = None) -> Dict:
        """Validate a license key."""
        data = {'license_key': license_key}
        if content_id:
            data['content_id'] = content_id
        if user_id:
            data['user_id'] = user_id

        return self.client._request('POST', '/licenses/validate', json_data=data)

    def get(self, license_id: str) -> Dict:
        """Get license details."""
        return self.client._request('GET', f'/licenses/{license_id}')


class AnalyticsAPI:
    """Analytics API."""

    def __init__(self, client: KSClient):
        self.client = client

    def usage(
        self,
        days: int = 30,
        user_id: str = None,
        license_id: str = None,
        event_type: str = None
    ) -> Dict:
        """Get usage analytics."""
        params = {'days': days}
        if user_id:
            params['user_id'] = user_id
        if license_id:
            params['license_id'] = license_id
        if event_type:
            params['event_type'] = event_type

        return self.client._request('GET', '/analytics/usage', params=params)

    def revenue(
        self,
        days: int = 30,
        license_type: str = None,
        group_by: str = "day"
    ) -> Dict:
        """Get revenue analytics."""
        params = {'days': days, 'group_by': group_by}
        if license_type:
            params['license_type'] = license_type

        return self.client._request('GET', '/analytics/revenue', params=params)


class FilesAPI:
    """File operations API."""

    def __init__(self, client: KSClient):
        self.client = client

    def upload(self, file_path: Union[str, Path], category: str = "document") -> Dict:
        """Upload a file."""
        file_path = Path(file_path)
        with open(file_path, 'rb') as f:
            files = {'file': (file_path.name, f, mimetypes.guess_type(file_path.name)[0])}
            data = {'category': category}
            return self.client._request('POST', '/files/upload', files=files, data=data)

    def download(self, file_id: str, output_path: Union[str, Path]) -> None:
        """Download a file."""
        response = self.client.session.get(
            urljoin(self.client.base_url + '/', f'/files/download/{file_id}'),
            timeout=self.client.timeout
        )

        if response.status_code == 401:
            raise KSAuthenticationError("Authentication failed", response.status_code)
        elif not response.ok:
            raise KSAPIError(f"Download failed: {response.status_code}", response.status_code)

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'wb') as f:
            f.write(response.content)


class BatchAPI:
    """Batch operations API."""

    def __init__(self, client: KSClient):
        self.client = client

    def process(self, operations: List[Dict], options: Dict = None) -> Dict:
        """Process multiple operations in batch."""
        data = {'operations': operations}
        if options:
            data['options'] = options

        return self.client._request('POST', '/batch/process', json_data=data)

    def status(self, batch_id: str) -> Dict:
        """Get batch processing status."""
        return self.client._request('GET', f'/batch/status/{batch_id}')


class WebhooksAPI:
    """Webhooks API."""

    def __init__(self, client: KSClient):
        self.client = client

    def list(self) -> Dict:
        """List webhooks."""
        return self.client._request('GET', '/webhooks')

    def create(self, url: str, events: List[str], secret: str = None) -> Dict:
        """Create a webhook."""
        data = {
            'url': url,
            'events': events
        }
        if secret:
            data['secret'] = secret

        return self.client._request('POST', '/webhooks', json_data=data)

    def delete(self, webhook_id: str) -> Dict:
        """Delete a webhook."""
        return self.client._request('DELETE', f'/webhooks/{webhook_id}')


# Convenience functions
def create_client(api_key: str = None, **kwargs) -> KSClient:
    """
    Create KS PDF Studio API client.

    Args:
        api_key: API key (can also be set via KS_API_KEY environment variable)
        **kwargs: Additional client arguments

    Returns:
        KSClient instance
    """
    api_key = api_key or os.environ.get('KS_API_KEY')
    if not api_key:
        raise ValueError("API key is required. Set KS_API_KEY environment variable or pass api_key parameter.")

    return KSClient(api_key, **kwargs)


# Example usage
if __name__ == "__main__":
    # Example usage (requires valid API key)
    try:
        client = create_client("your_api_key_here")

        # Health check
        health = client.health_check()
        print(f"API Status: {health['status']}")

        # Generate PDF
        result = client.pdf.generate(
            content="# Hello World\n\nThis is a test document.",
            template="professional",
            title="Test Document"
        )
        print(f"Generated PDF: {result['file_id']}")

        # Download PDF
        client.files.download(result['file_id'], "output.pdf")
        print("PDF downloaded as output.pdf")

    except KSAPIError as e:
        print(f"API Error: {e}")
        if e.response_data:
            print(f"Details: {e.response_data}")