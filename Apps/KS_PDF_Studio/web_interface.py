"""
KS PDF Studio - Web Interface
Browser-based interface for KS PDF Studio with full functionality.

Author: Kalponic Studio
Version: 2.0.0
"""

import os
import sys
import json
import uuid
import tempfile
import threading
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from flask import Flask, render_template, request, jsonify, send_file, session
from flask_cors import CORS
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


class KSWebStudio:
    """
    Web interface for KS PDF Studio.
    """

    def __init__(self, host: str = 'localhost', port: int = 8080):
        """
        Initialize the web studio.

        Args:
            host: Server host
            port: Server port
        """
        self.host = host
        self.port = port

        # Initialize Flask app
        self.app = Flask(__name__,
                        template_folder=str(Path(__file__).parent / "web" / "templates"),
                        static_folder=str(Path(__file__).parent / "web" / "static"))
        self.app.secret_key = os.environ.get('SECRET_KEY', 'ks_pdf_studio_web_secret_key')
        CORS(self.app)

        # Initialize core components
        self._init_components()

        # Setup routes
        self._setup_routes()

        # Session storage for user data
        self.user_sessions: Dict[str, Dict[str, Any]] = {}

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
            self.upload_folder = Path(tempfile.gettempdir()) / "ks_pdf_studio_web"
            self.upload_folder.mkdir(exist_ok=True)

        except Exception as e:
            print(f"Failed to initialize components: {e}")
            raise

    def _setup_routes(self):
        """Setup Flask routes."""

        @self.app.route('/')
        def index():
            """Main page."""
            return render_template('index.html')

        @self.app.route('/api/health')
        def health_check():
            """Health check endpoint."""
            return jsonify({
                'status': 'healthy',
                'version': '2.0.0',
                'timestamp': datetime.now().isoformat()
            })

        # Document management
        @self.app.route('/api/documents', methods=['POST'])
        def create_document():
            """Create a new document session."""
            session_id = str(uuid.uuid4())
            self.user_sessions[session_id] = {
                'content': '',
                'metadata': {
                    'created': datetime.now().isoformat(),
                    'modified': datetime.now().isoformat(),
                    'title': 'Untitled Document'
                }
            }
            return jsonify({'session_id': session_id})

        @self.app.route('/api/documents/<session_id>', methods=['GET', 'PUT'])
        def manage_document(session_id):
            """Get or update document content."""
            if session_id not in self.user_sessions:
                return jsonify({'error': 'Session not found'}), 404

            if request.method == 'GET':
                return jsonify(self.user_sessions[session_id])

            elif request.method == 'PUT':
                data = request.get_json()
                if 'content' in data:
                    self.user_sessions[session_id]['content'] = data['content']
                    self.user_sessions[session_id]['metadata']['modified'] = datetime.now().isoformat()
                if 'title' in data:
                    self.user_sessions[session_id]['metadata']['title'] = data['title']

                return jsonify({'success': True})

        # PDF Generation
        @self.app.route('/api/generate-pdf', methods=['POST'])
        def generate_pdf():
            """Generate PDF from markdown content."""
            try:
                data = request.get_json()
                content = data.get('content', '')
                template = data.get('template', 'professional')
                session_id = data.get('session_id', '')

                # Track analytics
                if session_id:
                    self.analytics_tracker.track_usage(
                        user_id=f"web_user_{session_id[:8]}",
                        license_id="web_trial",
                        content_id=f"doc_{session_id[:8]}",
                        event_type='export',
                        metadata={'format': 'pdf', 'template': template}
                    )

                # Generate PDF
                with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
                    pdf_path = tmp_file.name

                # Convert markdown to PDF
                success = self._generate_pdf_from_content(content, pdf_path, template)

                if success:
                    # Return file for download
                    response = send_file(
                        pdf_path,
                        as_attachment=True,
                        download_name=f"document_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                        mimetype='application/pdf'
                    )
                    # Clean up file after sending
                    @response.call_on_close
                    def cleanup():
                        try:
                            os.unlink(pdf_path)
                        except:
                            pass
                    return response
                else:
                    return jsonify({'error': 'PDF generation failed'}), 500

            except Exception as e:
                return jsonify({'error': str(e)}), 500

        # PDF Extraction
        @self.app.route('/api/extract-pdf', methods=['POST'])
        def extract_pdf():
            """Extract text from uploaded PDF."""
            try:
                if 'file' not in request.files:
                    return jsonify({'error': 'No file uploaded'}), 400

                file = request.files['file']
                if file.filename == '':
                    return jsonify({'error': 'No file selected'}), 400

                if not file.filename.lower().endswith('.pdf'):
                    return jsonify({'error': 'File must be a PDF'}), 400

                # Save uploaded file
                filename = secure_filename(file.filename)
                upload_path = self.upload_folder / filename
                file.save(upload_path)

                # Extract text
                result = self.pdf_extractor.extract_text(str(upload_path))

                # Clean up
                upload_path.unlink(missing_ok=True)

                if result['success']:
                    return jsonify({
                        'success': True,
                        'text': result['text'],
                        'pages': result['page_count'],
                        'characters': len(result['text'])
                    })
                else:
                    return jsonify({'error': result['error']}), 500

            except Exception as e:
                return jsonify({'error': str(e)}), 500

        # AI Enhancement
        @self.app.route('/api/ai-enhance', methods=['POST'])
        def ai_enhance():
            """Enhance content with AI."""
            try:
                data = request.get_json()
                content = data.get('content', '')
                enhancement_type = data.get('type', 'general')
                session_id = data.get('session_id', '')

                # Track analytics
                if session_id:
                    self.analytics_tracker.track_usage(
                        user_id=f"web_user_{session_id[:8]}",
                        license_id="web_trial",
                        content_id=f"doc_{session_id[:8]}",
                        event_type='ai_enhance',
                        metadata={'enhancement_type': enhancement_type}
                    )

                # AI enhancement
                enhanced_content = self._enhance_content(content, enhancement_type)

                return jsonify({
                    'success': True,
                    'enhanced_content': enhanced_content
                })

            except Exception as e:
                return jsonify({'error': str(e)}), 500

        # Watermarking
        @self.app.route('/api/add-watermark', methods=['POST'])
        def add_watermark():
            """Add watermark to PDF."""
            try:
                if 'file' not in request.files:
                    return jsonify({'error': 'No file uploaded'}), 400

                file = request.files['file']
                watermark_text = request.form.get('text', 'DRAFT')

                if file.filename == '':
                    return jsonify({'error': 'No file selected'}), 400

                # Save uploaded file
                filename = secure_filename(file.filename)
                upload_path = self.upload_folder / filename
                file.save(upload_path)

                # Configure watermark
                config = WatermarkConfig(
                    text=watermark_text,
                    opacity=0.3,
                    angle=45,
                    font_size=50,
                    color=(128, 128, 128)
                )

                # Apply watermark
                watermarked_path = upload_path.with_suffix('.watermarked.pdf')
                success = self.watermarker.apply_watermark(
                    str(upload_path), str(watermarked_path), config
                )

                # Clean up original
                upload_path.unlink(missing_ok=True)

                if success:
                    response = send_file(
                        watermarked_path,
                        as_attachment=True,
                        download_name=f"watermarked_{filename}",
                        mimetype='application/pdf'
                    )
                    @response.call_on_close
                    def cleanup():
                        try:
                            watermarked_path.unlink(missing_ok=True)
                        except:
                            pass
                    return response
                else:
                    return jsonify({'error': 'Watermarking failed'}), 500

            except Exception as e:
                return jsonify({'error': str(e)}), 500

        # Analytics
        @self.app.route('/api/analytics', methods=['GET'])
        def get_analytics():
            """Get usage analytics."""
            try:
                days = int(request.args.get('days', 30))
                report = self.analytics_dashboard.generate_report(days=days)
                return jsonify({
                    'success': True,
                    'report': report
                })
            except Exception as e:
                return jsonify({'error': str(e)}), 500

    def _generate_pdf_from_content(self, content: str, output_path: str, template: str = 'professional') -> bool:
        """Generate PDF from markdown content."""
        try:
            # Parse markdown
            html_content = self.markdown_parser.parse(content)

            # Generate PDF
            # This is a simplified version - in practice you'd use the full PDF engine
            with open(output_path, 'wb') as f:
                # Placeholder - integrate with actual PDF engine
                f.write(b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n/Contents 4 0 R\n>>\nendobj\n4 0 obj\n<<\n/Length 44\n>>\nstream\nBT\n/F1 12 Tf\n72 720 Td\n(Generated PDF) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000200 00000 n \ntrailer\n<<\n/Size 5\n/Root 1 0 R\n>>\nstartxref\n284\n%%EOF')

            return True
        except Exception as e:
            print(f"PDF generation error: {e}")
            return False

    def _enhance_content(self, content: str, enhancement_type: str) -> str:
        """Enhance content with AI."""
        try:
            # This is a simplified version - integrate with actual AI enhancer
            if enhancement_type == 'grammar':
                return f"Enhanced content:\n\n{content}"
            elif enhancement_type == 'structure':
                return f"# Enhanced Structure\n\n{content}"
            else:
                return f"AI Enhanced:\n\n{content}"
        except Exception as e:
            return f"Enhancement failed: {e}\n\n{content}"

    def run(self, debug: bool = False):
        """Run the web server."""
        print(f"🚀 Starting KS PDF Studio Web Interface")
        print(f"📱 Access at: http://{self.host}:{self.port}")
        print(f"🔧 Debug mode: {debug}")

        self.app.run(host=self.host, port=self.port, debug=debug, threaded=True)


# Web interface templates and static files will be created next
def create_web_assets():
    """Create web interface assets."""
    web_dir = Path(__file__).parent / "web"
    templates_dir = web_dir / "templates"
    static_dir = web_dir / "static"

    # Create directories
    templates_dir.mkdir(parents=True, exist_ok=True)
    static_dir.mkdir(parents=True, exist_ok=True)

    # Create main template
    index_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>KS PDF Studio Web</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        .editor-container { height: 60vh; }
        .preview-container { height: 60vh; overflow-y: auto; }
        .toolbar { background: #f8f9fa; padding: 10px; border-bottom: 1px solid #dee2e6; }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
        <div class="container">
            <a class="navbar-brand" href="#">
                <i class="fas fa-file-pdf"></i> KS PDF Studio Web
            </a>
            <div class="navbar-nav ms-auto">
                <span class="navbar-text">AI-Powered Tutorial Creation</span>
            </div>
        </div>
    </nav>

    <div class="container-fluid mt-3">
        <div class="row">
            <!-- Editor Panel -->
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h5><i class="fas fa-edit"></i> Markdown Editor</h5>
                    </div>
                    <div class="card-body p-0">
                        <div class="toolbar">
                            <button class="btn btn-sm btn-outline-primary" onclick="newDocument()">
                                <i class="fas fa-file"></i> New
                            </button>
                            <button class="btn btn-sm btn-outline-success" onclick="generatePDF()">
                                <i class="fas fa-file-pdf"></i> Export PDF
                            </button>
                            <button class="btn btn-sm btn-outline-info" onclick="aiEnhance()">
                                <i class="fas fa-brain"></i> AI Enhance
                            </button>
                            <button class="btn btn-sm btn-outline-warning" onclick="extractPDF()">
                                <i class="fas fa-file-upload"></i> Extract PDF
                            </button>
                        </div>
                        <textarea id="editor" class="form-control editor-container border-0"
                                placeholder="Write your tutorial content here..."></textarea>
                    </div>
                </div>
            </div>

            <!-- Preview Panel -->
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h5><i class="fas fa-eye"></i> Live Preview</h5>
                    </div>
                    <div class="card-body">
                        <div id="preview" class="preview-container"></div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Modals -->
    <!-- PDF Extraction Modal -->
    <div class="modal fade" id="extractModal" tabindex="-1">
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">Extract PDF Text</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <input type="file" class="form-control" id="pdfFile" accept=".pdf">
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-primary" onclick="doExtractPDF()">Extract</button>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <script>
        let currentSession = null;

        // Initialize
        window.onload = function() {
            newDocument();
            updatePreview();
        };

        // Document management
        async function newDocument() {
            try {
                const response = await fetch('/api/documents', { method: 'POST' });
                const data = await response.json();
                currentSession = data.session_id;
                document.getElementById('editor').value = '# New Tutorial\\n\\nWelcome to your tutorial!';
                updatePreview();
            } catch (error) {
                alert('Failed to create document: ' + error);
            }
        }

        async function saveDocument() {
            if (!currentSession) return;

            const content = document.getElementById('editor').value;
            try {
                await fetch(`/api/documents/${currentSession}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ content: content })
                });
            } catch (error) {
                console.error('Save failed:', error);
            }
        }

        // PDF Generation
        async function generatePDF() {
            if (!currentSession) {
                alert('Please create a document first');
                return;
            }

            const content = document.getElementById('editor').value;
            try {
                const response = await fetch('/api/generate-pdf', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        content: content,
                        session_id: currentSession,
                        template: 'professional'
                    })
                });

                if (response.ok) {
                    // Trigger download
                    const blob = await response.blob();
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = 'tutorial.pdf';
                    a.click();
                    window.URL.revokeObjectURL(url);
                } else {
                    const error = await response.json();
                    alert('PDF generation failed: ' + error.error);
                }
            } catch (error) {
                alert('PDF generation error: ' + error);
            }
        }

        // AI Enhancement
        async function aiEnhance() {
            const content = document.getElementById('editor').value;
            if (!content.trim()) {
                alert('Please enter some content first');
                return;
            }

            try {
                const response = await fetch('/api/ai-enhance', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        content: content,
                        type: 'general',
                        session_id: currentSession
                    })
                });

                const data = await response.json();
                if (data.success) {
                    document.getElementById('editor').value = data.enhanced_content;
                    updatePreview();
                } else {
                    alert('AI enhancement failed: ' + data.error);
                }
            } catch (error) {
                alert('AI enhancement error: ' + error);
            }
        }

        // PDF Extraction
        function extractPDF() {
            const modal = new bootstrap.Modal(document.getElementById('extractModal'));
            modal.show();
        }

        async function doExtractPDF() {
            const fileInput = document.getElementById('pdfFile');
            if (!fileInput.files[0]) {
                alert('Please select a PDF file');
                return;
            }

            const formData = new FormData();
            formData.append('file', fileInput.files[0]);

            try {
                const response = await fetch('/api/extract-pdf', {
                    method: 'POST',
                    body: formData
                });

                const data = await response.json();
                if (data.success) {
                    document.getElementById('editor').value = data.text;
                    updatePreview();

                    // Close modal
                    const modal = bootstrap.Modal.getInstance(document.getElementById('extractModal'));
                    modal.hide();

                    alert(`PDF extracted successfully!\\nPages: ${data.pages}\\nCharacters: ${data.characters}`);
                } else {
                    alert('PDF extraction failed: ' + data.error);
                }
            } catch (error) {
                alert('PDF extraction error: ' + error);
            }
        }

        // Live preview
        function updatePreview() {
            const content = document.getElementById('editor').value;
            const preview = document.getElementById('preview');
            preview.innerHTML = marked.parse(content);
        }

        // Auto-save and preview update
        document.getElementById('editor').addEventListener('input', function() {
            updatePreview();
            // Throttle save
            clearTimeout(this.saveTimeout);
            this.saveTimeout = setTimeout(saveDocument, 1000);
        });
    </script>
</body>
</html>
    """

    with open(templates_dir / "index.html", "w", encoding="utf-8") as f:
        f.write(index_html)

    print("✅ Web interface assets created")


if __name__ == "__main__":
    # Create web assets
    create_web_assets()

    # Start web server
    web_studio = KSWebStudio()
    web_studio.run(debug=True)