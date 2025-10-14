"""
KS PDF Studio - Batch Processing Engine
Advanced batch processing capabilities for enterprise workflows.

Author: Kalponic Studio
Version: 2.0.0
"""

import os
import json
import uuid
import time
import threading
import queue
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

# Import KS PDF Studio components
from core.pdf_engine import KSPDFEngine
from core.markdown_parser import KSMarkdownParser
from ai.ai_manager import AIModelManager
from ai.ai_enhancement import AIEnhancer
from monetization.watermarking import PDFWatermarker
from monetization.license_manager import LicenseManager
from src.monetization.analytics import AnalyticsTracker


class BatchProcessor:
    """
    Advanced batch processing engine for KS PDF Studio.
    Handles large-scale document processing with parallel execution.
    """

    def __init__(self, max_workers: int = 4, max_queue_size: int = 1000):
        """
        Initialize batch processor.

        Args:
            max_workers: Maximum number of concurrent workers
            max_queue_size: Maximum queue size for batch jobs
        """
        self.max_workers = max_workers
        self.max_queue_size = max_queue_size

        # Initialize components
        self.pdf_engine = KSPDFEngine()
        self.markdown_parser = KSMarkdownParser()
        self.ai_manager = AIModelManager()
        self.ai_enhancer = AIEnhancer(self.ai_manager)
        self.watermarker = PDFWatermarker()
        self.license_manager = LicenseManager()
        self.analytics_tracker = AnalyticsTracker()

        # Batch job management
        self.active_batches: Dict[str, BatchJob] = {}
        self.completed_batches: Dict[str, BatchJob] = {}
        self.batch_queue = queue.Queue(maxsize=max_queue_size)

        # Thread pool for parallel processing
        self.executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="BatchWorker")

        # Webhook support
        self.webhook_handlers: Dict[str, Callable] = {}

        # Start batch processing thread
        self.processing_thread = threading.Thread(target=self._process_batch_queue, daemon=True)
        self.processing_thread.start()

    def submit_batch(
        self,
        operations: List[Dict[str, Any]],
        user_id: str,
        license_id: str,
        options: Dict[str, Any] = None
    ) -> str:
        """
        Submit a batch job for processing.

        Args:
            operations: List of operations to perform
            user_id: User ID submitting the batch
            license_id: License ID for the batch
            options: Batch processing options

        Returns:
            Batch ID for tracking
        """
        batch_id = str(uuid.uuid4())

        # Validate operations
        if not operations or len(operations) == 0:
            raise ValueError("At least one operation is required")

        if len(operations) > 100:  # Limit batch size
            raise ValueError("Maximum 100 operations per batch")

        # Create batch job
        batch_job = BatchJob(
            batch_id=batch_id,
            operations=operations,
            user_id=user_id,
            license_id=license_id,
            options=options or {},
            created_at=datetime.now()
        )

        # Check queue capacity
        if self.batch_queue.full():
            raise RuntimeError("Batch queue is full. Please try again later.")

        # Add to active batches and queue
        self.active_batches[batch_id] = batch_job
        self.batch_queue.put(batch_id)

        # Track batch submission
        self.analytics_tracker.track_usage(
            user_id=user_id,
            license_id=license_id,
            content_id=batch_id,
            event_type='batch_submitted',
            metadata={
                'operation_count': len(operations),
                'parallel': options.get('parallel', False) if options else False
            }
        )

        return batch_id

    def get_batch_status(self, batch_id: str) -> Optional[Dict[str, Any]]:
        """
        Get status of a batch job.

        Args:
            batch_id: Batch job ID

        Returns:
            Batch status information or None if not found
        """
        # Check active batches
        if batch_id in self.active_batches:
            batch = self.active_batches[batch_id]
            return batch.to_dict()

        # Check completed batches
        if batch_id in self.completed_batches:
            batch = self.completed_batches[batch_id]
            return batch.to_dict()

        return None

    def cancel_batch(self, batch_id: str, user_id: str) -> bool:
        """
        Cancel a batch job.

        Args:
            batch_id: Batch job ID
            user_id: User ID requesting cancellation

        Returns:
            True if cancelled, False otherwise
        """
        if batch_id not in self.active_batches:
            return False

        batch = self.active_batches[batch_id]

        # Only allow cancellation by the owner
        if batch.user_id != user_id:
            return False

        # Mark as cancelled
        batch.status = 'cancelled'
        batch.completed_at = datetime.now()

        # Move to completed
        self.completed_batches[batch_id] = batch
        del self.active_batches[batch_id]

        # Track cancellation
        self.analytics_tracker.track_usage(
            user_id=user_id,
            license_id=batch.license_id,
            content_id=batch_id,
            event_type='batch_cancelled',
            metadata={'operation_count': len(batch.operations)}
        )

        return True

    def _process_batch_queue(self):
        """Process batch jobs from the queue."""
        while True:
            try:
                # Get next batch ID from queue
                batch_id = self.batch_queue.get(timeout=1)

                # Process the batch
                if batch_id in self.active_batches:
                    batch = self.active_batches[batch_id]
                    self._process_batch(batch)

                self.batch_queue.task_done()

            except queue.Empty:
                continue
            except Exception as e:
                print(f"Error processing batch queue: {e}")
                time.sleep(1)

    def _process_batch(self, batch: 'BatchJob'):
        """Process a single batch job."""
        try:
            batch.status = 'processing'
            batch.started_at = datetime.now()

            operations = batch.operations
            options = batch.options

            # Determine processing mode
            parallel = options.get('parallel', False)
            max_concurrent = min(options.get('max_concurrent', 2), self.max_workers)

            if parallel and len(operations) > 1:
                # Parallel processing
                self._process_parallel(batch, max_concurrent)
            else:
                # Sequential processing
                self._process_sequential(batch)

            # Mark as completed
            batch.status = 'completed'
            batch.completed_at = datetime.now()

            # Calculate duration
            duration = (batch.completed_at - batch.started_at).total_seconds()
            batch.metadata['duration'] = duration

            # Track completion
            self.analytics_tracker.track_usage(
                user_id=batch.user_id,
                license_id=batch.license_id,
                content_id=batch.batch_id,
                event_type='batch_completed',
                metadata={
                    'operation_count': len(operations),
                    'successful_operations': len([r for r in batch.results if r.get('status') == 'success']),
                    'failed_operations': len([r for r in batch.results if r.get('status') == 'failed']),
                    'duration': duration
                }
            )

            # Trigger webhook if configured
            webhook_url = options.get('webhook_url')
            if webhook_url:
                self._trigger_webhook(batch, webhook_url)

        except Exception as e:
            # Mark as failed
            batch.status = 'failed'
            batch.error = str(e)
            batch.completed_at = datetime.now()

            # Track failure
            self.analytics_tracker.track_usage(
                user_id=batch.user_id,
                license_id=batch.license_id,
                content_id=batch.batch_id,
                event_type='batch_failed',
                metadata={
                    'operation_count': len(batch.operations),
                    'error': str(e)
                }
            )

        finally:
            # Move to completed batches
            self.completed_batches[batch.batch_id] = batch
            if batch.batch_id in self.active_batches:
                del self.active_batches[batch.batch_id]

            # Clean up old completed batches (keep last 1000)
            if len(self.completed_batches) > 1000:
                oldest = min(self.completed_batches.keys(),
                           key=lambda x: self.completed_batches[x].completed_at)
                del self.completed_batches[oldest]

    def _process_sequential(self, batch: 'BatchJob'):
        """Process operations sequentially."""
        for i, operation in enumerate(batch.operations):
            operation_id = f"op_{i+1}"

            try:
                result = self._execute_operation(operation, batch.user_id, batch.license_id)
                batch.results.append({
                    'operation_id': operation_id,
                    'status': 'success',
                    'result': result
                })

            except Exception as e:
                batch.results.append({
                    'operation_id': operation_id,
                    'status': 'failed',
                    'error': str(e)
                })

    def _process_parallel(self, batch: 'BatchJob', max_concurrent: int):
        """Process operations in parallel."""
        futures = []

        # Submit operations to thread pool
        for i, operation in enumerate(batch.operations):
            future = self.executor.submit(
                self._execute_operation,
                operation,
                batch.user_id,
                batch.license_id
            )
            futures.append((i, future))

        # Collect results
        for i, future in futures:
            operation_id = f"op_{i+1}"

            try:
                result = future.result(timeout=300)  # 5 minute timeout per operation
                batch.results.append({
                    'operation_id': operation_id,
                    'status': 'success',
                    'result': result
                })

            except Exception as e:
                batch.results.append({
                    'operation_id': operation_id,
                    'status': 'failed',
                    'error': str(e)
                })

    def _execute_operation(self, operation: Dict[str, Any], user_id: str, license_id: str) -> Any:
        """
        Execute a single operation.

        Args:
            operation: Operation definition
            user_id: User ID
            license_id: License ID

        Returns:
            Operation result
        """
        operation_type = operation.get('type')
        operation_data = operation.get('data', {})

        # Track operation execution
        self.analytics_tracker.track_usage(
            user_id=user_id,
            license_id=license_id,
            content_id=f"operation_{uuid.uuid4()}",
            event_type=f'operation_{operation_type}',
            metadata={'operation_type': operation_type}
        )

        if operation_type == 'generate_pdf':
            return self._generate_pdf(operation_data, user_id, license_id)
        elif operation_type == 'extract_pdf':
            return self._extract_pdf(operation_data, user_id, license_id)
        elif operation_type == 'enhance_content':
            return self._enhance_content(operation_data, user_id, license_id)
        elif operation_type == 'watermark_pdf':
            return self._watermark_pdf(operation_data, user_id, license_id)
        else:
            raise ValueError(f"Unsupported operation type: {operation_type}")

    def _generate_pdf(self, data: Dict[str, Any], user_id: str, license_id: str) -> Dict[str, Any]:
        """Generate PDF from content."""
        content = data.get('content', '')
        template = data.get('template', 'professional')
        title = data.get('title', 'Document')

        if not content.strip():
            raise ValueError("Content is required for PDF generation")

        # Generate unique filename
        output_filename = f"batch_{uuid.uuid4()}.pdf"
        output_path = Path("data/batch_outputs") / output_filename
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Generate PDF (simplified - integrate with actual engine)
        success = self._create_pdf_file(content, str(output_path), template)

        if success:
            return {
                'file_id': str(uuid.uuid4()),
                'filename': f"{title}.pdf",
                'path': str(output_path),
                'size': output_path.stat().st_size if output_path.exists() else 0
            }
        else:
            raise RuntimeError("PDF generation failed")

    def _extract_pdf(self, data: Dict[str, Any], user_id: str, license_id: str) -> Dict[str, Any]:
        """Extract text from PDF."""
        file_path = data.get('file_path')
        if not file_path or not Path(file_path).exists():
            raise ValueError("Valid file path is required for PDF extraction")

        # Extract text (simplified - integrate with actual extractor)
        extracted_text = f"Extracted text from {file_path}"  # Placeholder

        return {
            'text': extracted_text,
            'pages': 1,
            'characters': len(extracted_text)
        }

    def _enhance_content(self, data: Dict[str, Any], user_id: str, license_id: str) -> Dict[str, Any]:
        """Enhance content with AI."""
        content = data.get('content', '')
        enhancement_type = data.get('enhancement_type', 'general')

        if not content.strip():
            raise ValueError("Content is required for AI enhancement")

        # Enhance content (simplified - integrate with actual AI)
        enhanced = f"Enhanced: {content}"

        return {
            'original_content': content,
            'enhanced_content': enhanced,
            'enhancement_type': enhancement_type
        }

    def _watermark_pdf(self, data: Dict[str, Any], user_id: str, license_id: str) -> Dict[str, Any]:
        """Add watermark to PDF."""
        file_path = data.get('file_path')
        watermark_text = data.get('watermark_text', 'CONFIDENTIAL')

        if not file_path or not Path(file_path).exists():
            raise ValueError("Valid file path is required for watermarking")

        # Add watermark (simplified - integrate with actual watermarker)
        output_filename = f"watermarked_{uuid.uuid4()}.pdf"
        output_path = Path("data/batch_outputs") / output_filename

        # Copy file as placeholder
        import shutil
        shutil.copy(file_path, output_path)

        return {
            'file_id': str(uuid.uuid4()),
            'filename': output_filename,
            'path': str(output_path)
        }

    def _create_pdf_file(self, content: str, output_path: str, template: str) -> bool:
        """Create a PDF file (placeholder implementation)."""
        try:
            # This is a placeholder - integrate with actual PDF engine
            with open(output_path, 'w') as f:
                f.write(f"PDF Content: {content[:100]}...")
            return True
        except Exception as e:
            print(f"PDF creation error: {e}")
            return False

    def _trigger_webhook(self, batch: 'BatchJob', webhook_url: str):
        """Trigger webhook for batch completion."""
        try:
            import requests

            payload = {
                'event': 'batch.completed',
                'batch_id': batch.batch_id,
                'user_id': batch.user_id,
                'timestamp': batch.completed_at.isoformat(),
                'results': batch.results,
                'status': batch.status
            }

            response = requests.post(webhook_url, json=payload, timeout=10)

            if response.status_code >= 200 and response.status_code < 300:
                print(f"Webhook triggered successfully for batch {batch.batch_id}")
            else:
                print(f"Webhook failed for batch {batch.batch_id}: {response.status_code}")

        except Exception as e:
            print(f"Webhook error for batch {batch.batch_id}: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get batch processing statistics."""
        return {
            'active_batches': len(self.active_batches),
            'completed_batches': len(self.completed_batches),
            'queue_size': self.batch_queue.qsize(),
            'max_workers': self.max_workers,
            'executor_active': self.executor._threads and len(self.executor._threads) > 0
        }


class BatchJob:
    """Represents a batch processing job."""

    def __init__(
        self,
        batch_id: str,
        operations: List[Dict[str, Any]],
        user_id: str,
        license_id: str,
        options: Dict[str, Any],
        created_at: datetime
    ):
        self.batch_id = batch_id
        self.operations = operations
        self.user_id = user_id
        self.license_id = license_id
        self.options = options
        self.created_at = created_at

        # Processing state
        self.status = 'queued'  # queued, processing, completed, failed, cancelled
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.results: List[Dict[str, Any]] = []
        self.error: Optional[str] = None
        self.metadata: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert batch job to dictionary."""
        return {
            'batch_id': self.batch_id,
            'status': self.status,
            'total_operations': len(self.operations),
            'completed_operations': len(self.results),
            'successful_operations': len([r for r in self.results if r.get('status') == 'success']),
            'failed_operations': len([r for r in self.results if r.get('status') == 'failed']),
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'results': self.results,
            'error': self.error,
            'metadata': self.metadata
        }


# Global batch processor instance
batch_processor = BatchProcessor()


def submit_batch_job(operations: List[Dict[str, Any]], user_id: str, license_id: str, options: Dict[str, Any] = None) -> str:
    """
    Submit a batch job for processing.

    Args:
        operations: List of operations to perform
        user_id: User ID submitting the batch
        license_id: License ID for the batch
        options: Batch processing options

    Returns:
        Batch ID for tracking
    """
    return batch_processor.submit_batch(operations, user_id, license_id, options)


def get_batch_status(batch_id: str) -> Optional[Dict[str, Any]]:
    """
    Get status of a batch job.

    Args:
        batch_id: Batch job ID

    Returns:
        Batch status information or None if not found
    """
    return batch_processor.get_batch_status(batch_id)


def cancel_batch_job(batch_id: str, user_id: str) -> bool:
    """
    Cancel a batch job.

    Args:
        batch_id: Batch job ID
        user_id: User ID requesting cancellation

    Returns:
        True if cancelled, False otherwise
    """
    return batch_processor.cancel_batch(batch_id, user_id)


def get_batch_stats() -> Dict[str, Any]:
    """Get batch processing statistics."""
    return batch_processor.get_stats()


if __name__ == "__main__":
    # Example usage
    operations = [
        {
            'type': 'generate_pdf',
            'data': {
                'content': '# Test Document\n\nThis is a test document for batch processing.',
                'template': 'professional',
                'title': 'Batch Test Document'
            }
        },
        {
            'type': 'enhance_content',
            'data': {
                'content': 'This is some content to enhance with AI.',
                'enhancement_type': 'grammar'
            }
        }
    ]

    # Submit batch
    batch_id = submit_batch_job(operations, 'user123', 'license123', {'parallel': True})

    print(f"Submitted batch: {batch_id}")

    # Monitor progress
    while True:
        status = get_batch_status(batch_id)
        if status:
            print(f"Batch status: {status['status']} ({status['completed_operations']}/{status['total_operations']})")

            if status['status'] in ['completed', 'failed', 'cancelled']:
                print("Batch finished!")
                print(f"Results: {status['results']}")
                break

        time.sleep(2)