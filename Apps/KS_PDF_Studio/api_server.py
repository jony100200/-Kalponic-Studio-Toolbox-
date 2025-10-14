"""
KS PDF Studio - REST API Server
Comprehensive API for external integrations and automation.

Author: Kalponic Studio
Version: 2.0.0
"""

import os
import sys
import json
import uuid
import base64
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
from functools import wraps

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from flask import Flask, request, jsonify, send_file, g
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

# Import KS PDF Studio components
from core.pdf_engine import KSPDFEngine
from core.markdown_parser import KSMarkdownParser
from core.pdf_extractor import KSPDFExtractor, PDFExtractorUtils
from ai.ai_manager import AIModelManager
from ai.ai_enhancement import AIEnhancer
from monetization.watermarking import PDFWatermarker, WatermarkConfig
from monetization.license_manager import LicenseManager, LicenseEnforcement
from monetization.analytics import AnalyticsTracker, AnalyticsDashboard


class KSAPIServer:
    """
    REST API server for KS PDF Studio enterprise integrations.
    """

    def __init__(self, host: str = 'localhost', port: int = 5000, debug: bool = False):
        """
        Initialize the API server.

        Args:
            host: Server host
            port: Server port
            debug: Debug mode
        """
        self.host = host
        self.port = port
        self.debug = debug

        # Initialize Flask app
        self.app = Flask(__name__)
        self.app.secret_key = os.environ.get('KS_API_SECRET_KEY', secrets.token_hex(32))
        CORS(self.app)

        # API configuration
        self.api_keys: Dict[str, Dict[str, Any]] = {}
        self.rate_limits: Dict[str, Dict[str, Any]] = {}
        self.webhooks: Dict[str, str] = {}

        # Initialize core components
        self._init_components()

        # Setup middleware
        self._setup_middleware()

        # Setup routes
        self._setup_routes()

        # Load configuration
        self._load_config()

    def _init_components(self):
        """Initialize all KS PDF Studio components."""
        try:
            # Core components
            self.pdf_engine = KSPDFEngine()
            self.markdown_parser = KSMarkdownParser()
            self.pdf_extractor = KSPDFExtractor()
            self.ai_manager = AIModelManager()
            self.ai_enhancer = AIEnhancer(self.ai_manager)

            # Monetization components
            self.watermarker = PDFWatermarker()
            self.license_manager = LicenseManager()
            self.license_enforcement = LicenseEnforcement(self.license_manager)
            self.analytics_tracker = AnalyticsTracker()
            self.analytics_dashboard = AnalyticsDashboard(self.analytics_tracker)

            # File handling
            self.upload_folder = Path("data/uploads")
            self.output_folder = Path("data/outputs")
            self.upload_folder.mkdir(parents=True, exist_ok=True)
            self.output_folder.mkdir(parents=True, exist_ok=True)

        except Exception as e:
            print(f"Failed to initialize components: {e}")
            raise

    def _setup_middleware(self):
        """Setup Flask middleware."""

        @self.app.before_request
        def before_request():
            """Setup request context."""
            g.request_id = str(uuid.uuid4())
            g.start_time = datetime.now()

        @self.app.after_request
        def after_request(response):
            """Log request completion."""
            duration = (datetime.now() - g.start_time).total_seconds()
            self.analytics_tracker.track_usage(
                user_id=getattr(g, 'user_id', 'api_user'),
                license_id=getattr(g, 'license_id', 'api_license'),
                content_id=f"api_request_{g.request_id}",
                event_type='api_call',
                metadata={
                    'endpoint': request.endpoint,
                    'method': request.method,
                    'duration': duration,
                    'status_code': response.status_code
                }
            )
            return response

    def _setup_routes(self):
        """Setup API routes."""

        # Health and info
        self.app.add_url_rule('/api/v1/health', 'health', self.health_check, methods=['GET'])
        self.app.add_url_rule('/api/v1/info', 'info', self.api_info, methods=['GET'])

        # Authentication
        self.app.add_url_rule('/api/v1/auth/login', 'login', self.login, methods=['POST'])
        self.app.add_url_rule('/api/v1/auth/register', 'register', self.register, methods=['POST'])
        self.app.add_url_rule('/api/v1/auth/validate', 'validate_token', self.validate_token, methods=['GET'])

        # Document management
        self.app.add_url_rule('/api/v1/documents', 'list_documents', self.list_documents, methods=['GET'])
        self.app.add_url_rule('/api/v1/documents', 'create_document', self.create_document, methods=['POST'])
        self.app.add_url_rule('/api/v1/documents/<doc_id>', 'get_document', self.get_document, methods=['GET'])
        self.app.add_url_rule('/api/v1/documents/<doc_id>', 'update_document', self.update_document, methods=['PUT'])
        self.app.add_url_rule('/api/v1/documents/<doc_id>', 'delete_document', self.delete_document, methods=['DELETE'])

        # PDF operations
        self.app.add_url_rule('/api/v1/pdf/generate', 'generate_pdf', self.generate_pdf, methods=['POST'])
        self.app.add_url_rule('/api/v1/pdf/extract', 'extract_pdf', self.extract_pdf, methods=['POST'])
        self.app.add_url_rule('/api/v1/pdf/watermark', 'add_watermark', self.add_watermark, methods=['POST'])
        self.app.add_url_rule('/api/v1/pdf/merge', 'merge_pdfs', self.merge_pdfs, methods=['POST'])
        self.app.add_url_rule('/api/v1/pdf/split', 'split_pdf', self.split_pdf, methods=['POST'])

        # AI operations
        self.app.add_url_rule('/api/v1/ai/enhance', 'ai_enhance', self.ai_enhance, methods=['POST'])
        self.app.add_url_rule('/api/v1/ai/generate', 'ai_generate', self.ai_generate, methods=['POST'])
        self.app.add_url_rule('/api/v1/ai/summarize', 'ai_summarize', self.ai_summarize, methods=['POST'])

        # Batch operations
        self.app.add_url_rule('/api/v1/batch/process', 'batch_process', self.batch_process, methods=['POST'])
        self.app.add_url_rule('/api/v1/batch/status/<batch_id>', 'batch_status', self.batch_status, methods=['GET'])

        # License management
        self.app.add_url_rule('/api/v1/licenses', 'create_license', self.create_license, methods=['POST'])
        self.app.add_url_rule('/api/v1/licenses/validate', 'validate_license', self.validate_license, methods=['POST'])
        self.app.add_url_rule('/api/v1/licenses/<license_id>', 'get_license', self.get_license, methods=['GET'])

        # Analytics
        self.app.add_url_rule('/api/v1/analytics/usage', 'usage_analytics', self.usage_analytics, methods=['GET'])
        self.app.add_url_rule('/api/v1/analytics/revenue', 'revenue_analytics', self.revenue_analytics, methods=['GET'])

        # Webhooks
        self.app.add_url_rule('/api/v1/webhooks', 'list_webhooks', self.list_webhooks, methods=['GET'])
        self.app.add_url_rule('/api/v1/webhooks', 'create_webhook', self.create_webhook, methods=['POST'])
        self.app.add_url_rule('/api/v1/webhooks/<webhook_id>', 'delete_webhook', self.delete_webhook, methods=['DELETE'])

        # File operations
        self.app.add_url_rule('/api/v1/files/upload', 'upload_file', self.upload_file, methods=['POST'])
        self.app.add_url_rule('/api/v1/files/download/<file_id>', 'download_file', self.download_file, methods=['GET'])

    def _load_config(self):
        """Load API configuration."""
        config_file = Path("data/api_config.json")
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    self.api_keys = config.get('api_keys', {})
                    self.webhooks = config.get('webhooks', {})
            except Exception as e:
                print(f"Failed to load API config: {e}")

    def _save_config(self):
        """Save API configuration."""
        config_file = Path("data/api_config.json")
        config_file.parent.mkdir(parents=True, exist_ok=True)

        config = {
            'api_keys': self.api_keys,
            'webhooks': self.webhooks
        }

        try:
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            print(f"Failed to save API config: {e}")

    # Authentication decorators
    @staticmethod
    def require_auth(f):
        """Decorator to require API authentication."""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            auth_header = request.headers.get('Authorization', '')
            api_key = request.headers.get('X-API-Key', '')

            if not auth_header and not api_key:
                return jsonify({'error': 'Authentication required'}), 401

            # Check API key
            if api_key:
                # Get instance from first argument (self)
                instance = args[0] if args else None
                if instance:
                    user_info = instance._validate_api_key(api_key)
                    if not user_info:
                        return jsonify({'error': 'Invalid API key'}), 401
                    g.user_id = user_info['user_id']
                    g.license_id = user_info.get('license_id', 'api_license')
                    return f(*args, **kwargs)

            # Check Bearer token
            if auth_header.startswith('Bearer '):
                token = auth_header[7:]
                # Get instance from first argument (self)
                instance = args[0] if args else None
                if instance:
                    user_info = instance._validate_token(token)
                    if not user_info:
                        return jsonify({'error': 'Invalid token'}), 401
                    g.user_id = user_info['user_id']
                    g.license_id = user_info.get('license_id', 'api_license')
                    return f(*args, **kwargs)

            return jsonify({'error': 'Invalid authentication'}), 401
        return decorated_function

    def _validate_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """Validate API key."""
        for user_id, user_data in self.api_keys.items():
            if user_data.get('api_key') == api_key:
                return {
                    'user_id': user_id,
                    'license_id': user_data.get('license_id', 'api_license'),
                    'permissions': user_data.get('permissions', [])
                }
        return None

    def _validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate JWT token (simplified implementation)."""
        # In production, use proper JWT validation
        try:
            # Simple token validation - in production use proper JWT
            token_data = json.loads(base64.b64decode(token.split('.')[1] + '==').decode())
            if token_data.get('exp', 0) > datetime.now().timestamp():
                return token_data
        except:
            pass
        return None

    # Route handlers
    def health_check(self):
        """Health check endpoint."""
        return jsonify({
            'status': 'healthy',
            'version': '2.0.0',
            'timestamp': datetime.now().isoformat(),
            'services': {
                'pdf_engine': 'available',
                'ai_manager': 'available',
                'license_manager': 'available',
                'analytics': 'available'
            }
        })

    def api_info(self):
        """API information endpoint."""
        return jsonify({
            'name': 'KS PDF Studio API',
            'version': 'v1',
            'description': 'REST API for KS PDF Studio enterprise integrations',
            'documentation': '/api/v1/docs',
            'endpoints': [
                '/api/v1/documents',
                '/api/v1/pdf',
                '/api/v1/ai',
                '/api/v1/licenses',
                '/api/v1/analytics'
            ]
        })

    def login(self):
        """User login."""
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        # Simplified login - in production, validate against user database
        if username and password:
            token = self._generate_token({'user_id': username, 'exp': (datetime.now() + timedelta(hours=24)).timestamp()})
            return jsonify({'token': token, 'user_id': username})

        return jsonify({'error': 'Invalid credentials'}), 401

    def register(self):
        """User registration."""
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        email = data.get('email')

        if not all([username, password, email]):
            return jsonify({'error': 'Username, password, and email required'}), 400

        # Generate API key
        api_key = secrets.token_hex(32)

        self.api_keys[username] = {
            'email': email,
            'password_hash': generate_password_hash(password),
            'api_key': api_key,
            'license_id': 'enterprise_trial',
            'permissions': ['read', 'write', 'ai', 'pdf'],
            'created': datetime.now().isoformat()
        }

        self._save_config()

        return jsonify({
            'user_id': username,
            'api_key': api_key,
            'message': 'Registration successful'
        })

    def validate_token(self):
        """Validate authentication token."""
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'valid': False}), 401

        token = auth_header[7:]
        user_info = self._validate_token(token)

        if user_info:
            return jsonify({'valid': True, 'user': user_info})
        return jsonify({'valid': False}), 401

    @require_auth
    def list_documents(self):
        """List user documents."""
        # Simplified - in production, query document database
        return jsonify({
            'documents': [],
            'total': 0
        })

    @require_auth
    def create_document(self):
        """Create a new document."""
        data = request.get_json()
        title = data.get('title', 'Untitled Document')
        content = data.get('content', '')

        doc_id = str(uuid.uuid4())

        # Track creation
        self.analytics_tracker.track_usage(
            user_id=g.user_id,
            license_id=g.license_id,
            content_id=doc_id,
            event_type='document_create',
            metadata={'title': title}
        )

        return jsonify({
            'document_id': doc_id,
            'title': title,
            'created': datetime.now().isoformat()
        })

    @require_auth
    def get_document(self, doc_id):
        """Get document details."""
        # Simplified - in production, query document database
        return jsonify({
            'document_id': doc_id,
            'title': 'Sample Document',
            'content': 'Document content here',
            'created': datetime.now().isoformat()
        })

    @require_auth
    def update_document(self, doc_id):
        """Update document."""
        data = request.get_json()
        # Simplified - in production, update document database
        return jsonify({
            'document_id': doc_id,
            'updated': datetime.now().isoformat(),
            'message': 'Document updated successfully'
        })

    @require_auth
    def delete_document(self, doc_id):
        """Delete document."""
        # Simplified - in production, delete from document database
        return jsonify({
            'document_id': doc_id,
            'message': 'Document deleted successfully'
        })

    @require_auth
    def generate_pdf(self):
        """Generate PDF from content."""
        data = request.get_json()
        content = data.get('content', '')
        template = data.get('template', 'professional')
        title = data.get('title', 'Document')

        if not content.strip():
            return jsonify({'error': 'Content is required'}), 400

        try:
            # Generate unique filename
            output_filename = f"{uuid.uuid4()}.pdf"
            output_path = self.output_folder / output_filename

            # Generate PDF (simplified)
            success = self._generate_pdf_from_content(content, str(output_path), template)

            if success:
                # Store file info for download
                file_id = str(uuid.uuid4())
                file_info = {
                    'file_id': file_id,
                    'filename': output_filename,
                    'original_name': f"{title}.pdf",
                    'path': str(output_path),
                    'created': datetime.now().isoformat(),
                    'user_id': g.user_id
                }

                # In production, store in database
                self._store_file_info(file_id, file_info)

                # Track generation
                self.analytics_tracker.track_usage(
                    user_id=g.user_id,
                    license_id=g.license_id,
                    content_id=file_id,
                    event_type='pdf_generate',
                    metadata={'template': template, 'content_length': len(content)}
                )

                return jsonify({
                    'file_id': file_id,
                    'download_url': f'/api/v1/files/download/{file_id}',
                    'filename': f"{title}.pdf"
                })
            else:
                return jsonify({'error': 'PDF generation failed'}), 500

        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @require_auth
    def extract_pdf(self):
        """Extract text from PDF."""
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        # Save uploaded file
        filename = secure_filename(file.filename)
        upload_path = self.upload_folder / f"{uuid.uuid4()}_{filename}"
        file.save(upload_path)

        try:
            # Extract text
            result = self.pdf_extractor.extract_text(str(upload_path))

            # Clean up
            upload_path.unlink(missing_ok=True)

            if result['success']:
                # Track extraction
                self.analytics_tracker.track_usage(
                    user_id=g.user_id,
                    license_id=g.license_id,
                    content_id=f"extract_{uuid.uuid4()}",
                    event_type='pdf_extract',
                    metadata={'pages': result['page_count'], 'chars': len(result['text'])}
                )

                return jsonify({
                    'text': result['text'],
                    'pages': result['page_count'],
                    'characters': len(result['text']),
                    'metadata': result['metadata']
                })
            else:
                return jsonify({'error': result['error']}), 500

        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @require_auth
    def ai_enhance(self):
        """Enhance content with AI."""
        data = request.get_json()
        content = data.get('content', '')
        enhancement_type = data.get('type', 'general')

        if not content.strip():
            return jsonify({'error': 'Content is required'}), 400

        try:
            # AI enhancement (simplified)
            enhanced_content = self._enhance_content(content, enhancement_type)

            # Track enhancement
            self.analytics_tracker.track_usage(
                user_id=g.user_id,
                license_id=g.license_id,
                content_id=f"ai_{uuid.uuid4()}",
                event_type='ai_enhance',
                metadata={'enhancement_type': enhancement_type}
            )

            return jsonify({
                'original_content': content,
                'enhanced_content': enhanced_content,
                'enhancement_type': enhancement_type
            })

        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @require_auth
    def add_watermark(self):
        """Add watermark to PDF."""
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400

        file = request.files['file']
        watermark_text = request.form.get('watermark_text', 'CONFIDENTIAL')

        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        # Save uploaded file
        filename = secure_filename(file.filename)
        upload_path = self.upload_folder / f"{uuid.uuid4()}_{filename}"
        file.save(upload_path)

        try:
            # Add watermark
            output_filename = f"watermarked_{uuid.uuid4()}.pdf"
            output_path = self.output_folder / output_filename

            success = self.pdf_watermarker.add_watermark(
                str(upload_path), str(output_path), watermark_text
            )

            # Clean up upload
            upload_path.unlink(missing_ok=True)

            if success:
                # Store file info
                file_id = str(uuid.uuid4())
                file_info = {
                    'file_id': file_id,
                    'filename': output_filename,
                    'original_name': f"watermarked_{filename}",
                    'path': str(output_path),
                    'created': datetime.now().isoformat(),
                    'user_id': g.user_id
                }
                self._store_file_info(file_id, file_info)

                return jsonify({
                    'file_id': file_id,
                    'download_url': f'/api/v1/files/download/{file_id}',
                    'filename': f"watermarked_{filename}"
                })
            else:
                return jsonify({'error': 'Watermarking failed'}), 500

        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @require_auth
    def merge_pdfs(self):
        """Merge multiple PDFs."""
        if 'files' not in request.files:
            return jsonify({'error': 'No files uploaded'}), 400

        files = request.files.getlist('files')
        if len(files) < 2:
            return jsonify({'error': 'At least 2 files required for merging'}), 400

        # Save uploaded files
        upload_paths = []
        for file in files:
            if file.filename == '':
                continue
            filename = secure_filename(file.filename)
            upload_path = self.upload_folder / f"{uuid.uuid4()}_{filename}"
            file.save(upload_path)
            upload_paths.append(upload_path)

        try:
            # Merge PDFs
            output_filename = f"merged_{uuid.uuid4()}.pdf"
            output_path = self.output_folder / output_filename

            success = self.pdf_engine.merge_pdfs(
                [str(p) for p in upload_paths], str(output_path)
            )

            # Clean up uploads
            for path in upload_paths:
                path.unlink(missing_ok=True)

            if success:
                # Store file info
                file_id = str(uuid.uuid4())
                file_info = {
                    'file_id': file_id,
                    'filename': output_filename,
                    'original_name': 'merged_document.pdf',
                    'path': str(output_path),
                    'created': datetime.now().isoformat(),
                    'user_id': g.user_id
                }
                self._store_file_info(file_id, file_info)

                return jsonify({
                    'file_id': file_id,
                    'download_url': f'/api/v1/files/download/{file_id}',
                    'filename': 'merged_document.pdf'
                })
            else:
                return jsonify({'error': 'PDF merging failed'}), 500

        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @require_auth
    def split_pdf(self):
        """Split PDF into multiple files."""
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400

        file = request.files['file']
        split_type = request.form.get('split_type', 'pages')
        pages_per_file = request.form.get('pages_per_file')

        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        # Save uploaded file
        filename = secure_filename(file.filename)
        upload_path = self.upload_folder / f"{uuid.uuid4()}_{filename}"
        file.save(upload_path)

        try:
            # Split PDF
            output_dir = self.output_folder / f"split_{uuid.uuid4()}"
            output_dir.mkdir(exist_ok=True)

            if split_type == 'pages' and pages_per_file:
                success = self.pdf_engine.split_pdf_by_pages(
                    str(upload_path), str(output_dir), int(pages_per_file)
                )
            else:
                return jsonify({'error': 'Invalid split parameters'}), 400

            # Clean up upload
            upload_path.unlink(missing_ok=True)

            if success:
                # Get output files
                output_files = list(output_dir.glob("*.pdf"))
                file_ids = []

                for output_file in output_files:
                    file_id = str(uuid.uuid4())
                    file_info = {
                        'file_id': file_id,
                        'filename': output_file.name,
                        'original_name': output_file.name,
                        'path': str(output_file),
                        'created': datetime.now().isoformat(),
                        'user_id': g.user_id
                    }
                    self._store_file_info(file_id, file_info)
                    file_ids.append({
                        'file_id': file_id,
                        'download_url': f'/api/v1/files/download/{file_id}',
                        'filename': output_file.name
                    })

                return jsonify({
                    'files': file_ids,
                    'total_files': len(file_ids)
                })
            else:
                return jsonify({'error': 'PDF splitting failed'}), 500

        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @require_auth
    def ai_generate(self):
        """Generate content with AI."""
        data = request.get_json()
        prompt = data.get('prompt', '')
        content_type = data.get('content_type', 'article')

        if not prompt.strip():
            return jsonify({'error': 'Prompt is required'}), 400

        try:
            # AI content generation (simplified)
            generated_content = self._generate_content(prompt, content_type)

            # Track generation
            self.analytics_tracker.track_usage(
                user_id=g.user_id,
                license_id=g.license_id,
                content_id=f"ai_gen_{uuid.uuid4()}",
                event_type='ai_generate',
                metadata={'content_type': content_type}
            )

            return jsonify({
                'prompt': prompt,
                'generated_content': generated_content,
                'content_type': content_type
            })

        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @require_auth
    def ai_summarize(self):
        """Summarize content with AI."""
        data = request.get_json()
        content = data.get('content', '')
        summary_type = data.get('summary_type', 'key_points')

        if not content.strip():
            return jsonify({'error': 'Content is required'}), 400

        try:
            # AI summarization (simplified)
            summary = self._summarize_content(content, summary_type)

            # Track summarization
            self.analytics_tracker.track_usage(
                user_id=g.user_id,
                license_id=g.license_id,
                content_id=f"ai_sum_{uuid.uuid4()}",
                event_type='ai_summarize',
                metadata={'summary_type': summary_type}
            )

            return jsonify({
                'original_content': content,
                'summary': summary,
                'summary_type': summary_type
            })

        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @require_auth
    def batch_process(self):
        """Process batch operations."""
        data = request.get_json()
        operations = data.get('operations', [])
        options = data.get('options', {})

        if not operations:
            return jsonify({'error': 'Operations are required'}), 400

        try:
            # Submit batch job
            batch_id = self.batch_processor.submit_batch(
                operations, g.user_id, g.license_id, options
            )

            return jsonify({
                'batch_id': batch_id,
                'status': 'submitted',
                'message': 'Batch processing started'
            })

        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @require_auth
    def batch_status(self, batch_id):
        """Get batch processing status."""
        try:
            status = self.batch_processor.get_batch_status(batch_id)

            if status:
                return jsonify(status)
            else:
                return jsonify({'error': 'Batch not found'}), 404

        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @require_auth
    def validate_license(self):
        """Validate a license key."""
        data = request.get_json()
        license_key = data.get('license_key')

        if not license_key:
            return jsonify({'error': 'License key is required'}), 400

        try:
            is_valid = self.license_manager.validate_license(license_key) is not None

            if is_valid:
                license_info = self.license_manager.validate_license(license_key)
                return jsonify({
                    'valid': True,
                    'license_info': license_info.to_dict() if hasattr(license_info, 'to_dict') else license_info
                })
            else:
                return jsonify({'valid': False, 'error': 'Invalid license'}), 400

        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @require_auth
    def get_license(self, license_id):
        """Get license details."""
        try:
            license_info = self.license_manager.get_license_info(license_id)

            if license_info:
                return jsonify(license_info.to_dict() if hasattr(license_info, 'to_dict') else license_info)
            else:
                return jsonify({'error': 'License not found'}), 404

        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @require_auth
    def create_license(self):
        """Create a new license."""
        data = request.get_json()

        try:
            license_key, license_info = self.license_manager.create_license(
                user_id=data.get('user_id', g.user_id),
                user_name=data.get('user_name', 'API User'),
                user_email=data.get('user_email', 'api@example.com'),
                license_type=data.get('license_type', 'personal'),
                content_id=data.get('content_id', str(uuid.uuid4())),
                content_title=data.get('content_title', 'API Generated Content'),
                duration_days=data.get('duration_days'),
                max_uses=data.get('max_uses'),
                features=data.get('features', [])
            )

            return jsonify({
                'license_key': license_key,
                'license_info': license_info.to_dict()
            })

        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @require_auth
    def usage_analytics(self):
        """Get usage analytics."""
        days = int(request.args.get('days', 30))

        try:
            data = self.analytics_dashboard.get_dashboard_data(days)
            return jsonify(data)
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @require_auth
    def revenue_analytics(self):
        """Get revenue analytics."""
        days = int(request.args.get('days', 30))

        try:
            data = self.analytics_dashboard.get_dashboard_data(days)
            # Focus on revenue data
            revenue_data = {
                'revenue': data.get('revenue', {}),
                'period': data.get('generated_at', datetime.now().isoformat())
            }
            return jsonify(revenue_data)
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @require_auth
    def list_webhooks(self):
        """List user webhooks."""
        try:
            user_webhooks = []
            for webhook_id, webhook_data in self.webhooks.items():
                if webhook_data.get('user_id') == g.user_id:
                    user_webhooks.append({
                        'webhook_id': webhook_id,
                        'url': webhook_data.get('url'),
                        'events': webhook_data.get('events', []),
                        'created': webhook_data.get('created')
                    })

            return jsonify({'webhooks': user_webhooks})

        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @require_auth
    def create_webhook(self):
        """Create a webhook."""
        data = request.get_json()
        url = data.get('url')
        events = data.get('events', [])
        secret = data.get('secret')

        if not url or not events:
            return jsonify({'error': 'URL and events are required'}), 400

        try:
            webhook_id = str(uuid.uuid4())

            self.webhooks[webhook_id] = {
                'webhook_id': webhook_id,
                'user_id': g.user_id,
                'url': url,
                'events': events,
                'secret': secret,
                'created': datetime.now().isoformat(),
                'active': True
            }

            self._save_config()

            return jsonify({
                'webhook_id': webhook_id,
                'url': url,
                'events': events,
                'message': 'Webhook created successfully'
            })

        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @require_auth
    def delete_webhook(self, webhook_id):
        """Delete a webhook."""
        try:
            if webhook_id not in self.webhooks:
                return jsonify({'error': 'Webhook not found'}), 404

            webhook_data = self.webhooks[webhook_id]
            if webhook_data.get('user_id') != g.user_id:
                return jsonify({'error': 'Unauthorized'}), 403

            del self.webhooks[webhook_id]
            self._save_config()

            return jsonify({'message': 'Webhook deleted successfully'})

        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @require_auth
    def upload_file(self):
        """Upload a file."""
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400

        file = request.files['file']
        category = request.form.get('category', 'document')

        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        # Save uploaded file
        filename = secure_filename(file.filename)
        upload_path = self.upload_folder / f"{uuid.uuid4()}_{filename}"
        file.save(upload_path)

        try:
            # Store file info
            file_id = str(uuid.uuid4())
            file_info = {
                'file_id': file_id,
                'filename': upload_path.name,
                'original_name': filename,
                'path': str(upload_path),
                'category': category,
                'size': upload_path.stat().st_size,
                'created': datetime.now().isoformat(),
                'user_id': g.user_id
            }
            self._store_file_info(file_id, file_info)

            return jsonify({
                'file_id': file_id,
                'filename': filename,
                'size': file_info['size'],
                'category': category
            })

        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @require_auth
    def download_file(self, file_id):
        """Download a file."""
        try:
            # In production, retrieve file info from database
            # For now, return a simple response
            return jsonify({
                'file_id': file_id,
                'message': 'File download endpoint - implement file serving logic'
            })

        except Exception as e:
            return jsonify({'error': str(e)}), 500

    # Helper methods
    def _generate_token(self, payload: Dict[str, Any]) -> str:
        """Generate JWT-like token (simplified)."""
        # In production, use proper JWT library
        token_data = base64.b64encode(json.dumps(payload).encode()).decode()
        return f"header.{token_data}.signature"

    def _generate_pdf_from_content(self, content: str, output_path: str, template: str) -> bool:
        """Generate PDF from content (simplified implementation)."""
        try:
            # This is a placeholder - integrate with actual PDF engine
            with open(output_path, 'wb') as f:
                # Write a minimal PDF
                f.write(b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n/Contents 4 0 R\n>>\nendobj\n4 0 obj\n<<\n/Length 44\n>>\nstream\nBT\n/F1 12 Tf\n72 720 Td\n(API Generated PDF) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000200 00000 n \ntrailer\n<<\n/Size 5\n/Root 1 0 R\n>>\nstartxref\n284\n%%EOF')
            return True
        except Exception as e:
            print(f"PDF generation error: {e}")
            return False

    def _enhance_content(self, content: str, enhancement_type: str) -> str:
        """Enhance content with AI (simplified)."""
        if enhancement_type == 'grammar':
            return f"Enhanced content:\n\n{content}"
        elif enhancement_type == 'structure':
            return f"# Enhanced Structure\n\n{content}"
        else:
            return f"AI Enhanced:\n\n{content}"

    def _generate_content(self, prompt: str, content_type: str) -> str:
        """Generate content with AI (simplified)."""
        if content_type == 'article':
            return f"# Generated Article\n\nBased on your prompt: {prompt}\n\nThis is AI-generated content for an article."
        elif content_type == 'tutorial':
            return f"# Tutorial: {prompt}\n\n## Introduction\n\nThis tutorial covers: {prompt}"
        else:
            return f"Generated content for: {prompt}"

    def _summarize_content(self, content: str, summary_type: str) -> str:
        """Summarize content with AI (simplified)."""
        if summary_type == 'key_points':
            return f"Key points from content:\n• Main topic: {content[:50]}...\n• Length: {len(content)} characters"
        elif summary_type == 'brief':
            return f"Brief summary: {content[:100]}..."
        else:
            return f"Summary: {content[:200]}..."

    def _store_file_info(self, file_id: str, info: Dict[str, Any]):
        """Store file information (simplified - in production use database)."""
        # In production, store in database
        pass

    def run(self):
        """Run the API server."""
        print(f"🚀 Starting KS PDF Studio API Server")
        print(f"📡 API available at: http://{self.host}:{self.port}")
        print(f"📚 API Documentation: http://{self.host}:{self.port}/api/v1/docs")
        print(f"🔧 Debug mode: {self.debug}")

        self.app.run(host=self.host, port=self.port, debug=self.debug, threaded=True)


# CLI interface for the API server
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='KS PDF Studio API Server')
    parser.add_argument('--host', default='localhost', help='Server host')
    parser.add_argument('--port', type=int, default=5000, help='Server port')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')

    args = parser.parse_args()

    # Create data directories
    Path("data/uploads").mkdir(parents=True, exist_ok=True)
    Path("data/outputs").mkdir(parents=True, exist_ok=True)

    # Start API server
    api_server = KSAPIServer(host=args.host, port=args.port, debug=args.debug)
    api_server.run()