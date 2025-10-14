"""
KS PDF Studio - Webhook Handler
Handles incoming webhooks for real-time integrations.

Author: Kalponic Studio
Version: 2.0.0
"""

import os
import json
import hmac
import hashlib
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable
from flask import Flask, request, jsonify
from pathlib import Path


class WebhookHandler:
    """
    Webhook handler for KS PDF Studio integrations.
    Handles incoming webhooks with signature verification and event routing.
    """

    def __init__(self, secret_key: str = None):
        """
        Initialize webhook handler.

        Args:
            secret_key: Secret key for webhook signature verification
        """
        self.secret_key = secret_key or os.environ.get('KS_WEBHOOK_SECRET', 'default_secret')
        self.event_handlers: Dict[str, List[Callable]] = {}
        self.webhook_log: List[Dict[str, Any]] = []

        # Setup Flask app for webhook endpoint
        self.app = Flask(__name__)
        self.app.add_url_rule('/webhook', 'webhook', self.handle_webhook, methods=['POST'])

    def register_handler(self, event_type: str, handler: Callable):
        """
        Register an event handler.

        Args:
            event_type: Event type to handle (e.g., 'batch.completed')
            handler: Handler function that takes event data
        """
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []

        self.event_handlers[event_type].append(handler)
        print(f"Registered handler for event: {event_type}")

    def verify_signature(self, payload: str, signature: str) -> bool:
        """
        Verify webhook signature.

        Args:
            payload: Raw request payload
            signature: Signature from X-KS-Signature header

        Returns:
            True if signature is valid
        """
        if not signature:
            return False

        # Expected format: sha256=signature
        if not signature.startswith('sha256='):
            return False

        expected_signature = signature[7:]  # Remove 'sha256=' prefix

        # Create HMAC signature
        hmac_obj = hmac.new(
            self.secret_key.encode(),
            payload.encode(),
            hashlib.sha256
        )
        computed_signature = hmac_obj.hexdigest()

        # Use constant-time comparison to prevent timing attacks
        return hmac.compare_digest(computed_signature, expected_signature)

    def handle_webhook(self):
        """Handle incoming webhook requests."""
        try:
            # Get raw payload
            payload = request.get_data(as_text=True)

            # Verify signature
            signature = request.headers.get('X-KS-Signature')
            if not self.verify_signature(payload, signature):
                return jsonify({'error': 'Invalid signature'}), 401

            # Parse payload
            try:
                event_data = json.loads(payload)
            except json.JSONDecodeError:
                return jsonify({'error': 'Invalid JSON payload'}), 400

            # Validate event structure
            if not isinstance(event_data, dict) or 'event' not in event_data:
                return jsonify({'error': 'Invalid event format'}), 400

            event_type = event_data['event']

            # Log webhook
            webhook_entry = {
                'timestamp': datetime.now().isoformat(),
                'event_type': event_type,
                'source_ip': request.remote_addr,
                'user_agent': request.headers.get('User-Agent'),
                'event_data': event_data
            }
            self.webhook_log.append(webhook_entry)

            # Keep only last 1000 entries
            if len(self.webhook_log) > 1000:
                self.webhook_log = self.webhook_log[-1000:]

            # Route to handlers
            if event_type in self.event_handlers:
                for handler in self.event_handlers[event_type]:
                    try:
                        handler(event_data)
                    except Exception as e:
                        print(f"Error in webhook handler for {event_type}: {e}")

            return jsonify({'status': 'received'}), 200

        except Exception as e:
            print(f"Webhook handling error: {e}")
            return jsonify({'error': 'Internal server error'}), 500

    def get_webhook_log(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get webhook log entries.

        Args:
            limit: Maximum number of entries to return

        Returns:
            List of webhook log entries
        """
        return self.webhook_log[-limit:]

    def clear_webhook_log(self):
        """Clear webhook log."""
        self.webhook_log.clear()


# Default webhook handlers
def batch_completed_handler(event_data: Dict[str, Any]):
    """Handle batch completion events."""
    batch_id = event_data.get('batch_id')
    status = event_data.get('status')
    results = event_data.get('results', [])

    print(f"Batch {batch_id} completed with status: {status}")
    print(f"Results: {len(results)} operations")

    # Here you could:
    # - Send notifications
    # - Update external systems
    # - Trigger follow-up processes
    # - Store results in database

    # Example: Send email notification
    # send_batch_completion_email(batch_id, status, results)


def license_expired_handler(event_data: Dict[str, Any]):
    """Handle license expiration events."""
    license_id = event_data.get('license_id')
    user_id = event_data.get('user_id')

    print(f"License {license_id} expired for user {user_id}")

    # Here you could:
    # - Send renewal reminders
    # - Disable user access
    # - Update billing systems
    # - Trigger re-licensing workflows


def document_created_handler(event_data: Dict[str, Any]):
    """Handle document creation events."""
    document_id = event_data.get('document_id')
    user_id = event_data.get('user_id')

    print(f"Document {document_id} created by user {user_id}")

    # Here you could:
    # - Index document for search
    # - Send notifications
    # - Update analytics
    # - Trigger automated processing


# Global webhook handler instance
webhook_handler = WebhookHandler()

# Register default handlers
webhook_handler.register_handler('batch.completed', batch_completed_handler)
webhook_handler.register_handler('license.expired', license_expired_handler)
webhook_handler.register_handler('document.created', document_created_handler)


def create_webhook_app() -> Flask:
    """
    Create Flask app for webhook handling.

    Returns:
        Flask application instance
    """
    return webhook_handler.app


def get_webhook_log(limit: int = 50) -> List[Dict[str, Any]]:
    """
    Get webhook log entries.

    Args:
        limit: Maximum number of entries to return

    Returns:
        List of webhook log entries
    """
    return webhook_handler.get_webhook_log(limit)


def clear_webhook_log():
    """Clear webhook log."""
    webhook_handler.clear_webhook_log()


if __name__ == "__main__":
    # Example webhook server
    app = create_webhook_app()

    print("🚀 Starting KS PDF Studio Webhook Handler")
    print("📡 Webhook endpoint: http://localhost:5001/webhook")
    print("🔐 Signature verification enabled")

    app.run(host='localhost', port=5001, debug=True)