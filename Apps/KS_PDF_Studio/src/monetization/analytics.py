"""
KS PDF Studio - Analytics Dashboard
Usage tracking and analytics for monetization insights.

Author: Kalponic Studio
Version: 2.0.0
"""

import os
import json
import sqlite3
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from collections import defaultdict, Counter
import threading
import time


@dataclass
class UsageEvent:
    """Usage event data class."""
    event_id: str
    user_id: str
    license_id: str
    content_id: str
    event_type: str  # 'view', 'print', 'edit', 'export', 'share'
    timestamp: datetime
    metadata: Dict[str, Any]
    session_id: str
    ip_address: Optional[str]
    user_agent: Optional[str]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UsageEvent':
        """Create from dictionary."""
        data_copy = data.copy()
        data_copy['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data_copy)


@dataclass
class RevenueEvent:
    """Revenue event data class."""
    event_id: str
    user_id: str
    license_id: str
    content_id: str
    amount: float
    currency: str
    payment_method: str
    transaction_type: str  # 'license_purchase', 'subscription', 'upgrade'
    timestamp: datetime
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RevenueEvent':
        """Create from dictionary."""
        data_copy = data.copy()
        data_copy['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data_copy)


class AnalyticsDatabase:
    """
    SQLite database for analytics data.
    """

    def __init__(self, db_path: str):
        """
        Initialize analytics database.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._persistent_conn = None
        if db_path != ":memory:":
            self.db_path = Path(db_path)
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
        else:
            # For in-memory databases, keep a persistent connection
            self._persistent_conn = sqlite3.connect(":memory:")
        self._init_db()

    def _get_connection(self):
        """Get database connection."""
        if self._persistent_conn:
            return self._persistent_conn
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        """Initialize database tables."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Usage events table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS usage_events (
                    event_id TEXT PRIMARY KEY,
                    user_id TEXT,
                    license_id TEXT,
                    content_id TEXT,
                    event_type TEXT,
                    timestamp TEXT,
                    metadata TEXT,
                    session_id TEXT,
                    ip_address TEXT,
                    user_agent TEXT
                )
            ''')

            # Revenue events table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS revenue_events (
                    event_id TEXT PRIMARY KEY,
                    user_id TEXT,
                    license_id TEXT,
                    content_id TEXT,
                    amount REAL,
                    currency TEXT,
                    payment_method TEXT,
                    transaction_type TEXT,
                    timestamp TEXT,
                    metadata TEXT
                )
            ''')

            # Content metadata table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS content_metadata (
                    content_id TEXT PRIMARY KEY,
                    title TEXT,
                    author TEXT,
                    category TEXT,
                    tags TEXT,
                    created_date TEXT,
                    last_modified TEXT,
                    file_size INTEGER,
                    page_count INTEGER,
                    word_count INTEGER
                )
            ''')

            conn.commit()

    def insert_usage_event(self, event: UsageEvent):
        """Insert usage event."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO usage_events
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                event.event_id,
                event.user_id,
                event.license_id,
                event.content_id,
                event.event_type,
                event.timestamp.isoformat(),
                json.dumps(event.metadata),
                event.session_id,
                event.ip_address,
                event.user_agent
            ))
            conn.commit()

    def insert_revenue_event(self, event: RevenueEvent):
        """Insert revenue event."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO revenue_events
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                event.event_id,
                event.user_id,
                event.license_id,
                event.content_id,
                event.amount,
                event.currency,
                event.payment_method,
                event.transaction_type,
                event.timestamp.isoformat(),
                json.dumps(event.metadata)
            ))
            conn.commit()

    def update_content_metadata(self, content_id: str, metadata: Dict[str, Any]):
        """Update content metadata."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO content_metadata
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                content_id,
                metadata.get('title', ''),
                metadata.get('author', ''),
                metadata.get('category', ''),
                json.dumps(metadata.get('tags', [])),
                metadata.get('created_date', datetime.now().isoformat()),
                metadata.get('last_modified', datetime.now().isoformat()),
                metadata.get('file_size', 0),
                metadata.get('page_count', 0),
                metadata.get('word_count', 0)
            ))
            conn.commit()

    def get_usage_stats(self, start_date: datetime, end_date: datetime,
                       content_id: Optional[str] = None) -> Dict[str, Any]:
        """Get usage statistics."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            query = '''
                SELECT event_type, COUNT(*) as count
                FROM usage_events
                WHERE timestamp BETWEEN ? AND ?
            '''
            params = [start_date.isoformat(), end_date.isoformat()]

            if content_id:
                query += ' AND content_id = ?'
                params.append(content_id)

            query += ' GROUP BY event_type'

            cursor.execute(query, params)
            event_counts = dict(cursor.fetchall())

            # Get unique users
            query = '''
                SELECT COUNT(DISTINCT user_id) as unique_users
                FROM usage_events
                WHERE timestamp BETWEEN ? AND ?
            '''
            params = [start_date.isoformat(), end_date.isoformat()]

            if content_id:
                query += ' AND content_id = ?'
                params.append(content_id)

            cursor.execute(query, params)
            unique_users = cursor.fetchone()[0]

            # Get total events
            total_events = sum(event_counts.values())

            return {
                'total_events': total_events,
                'unique_users': unique_users,
                'event_breakdown': event_counts,
                'period': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat()
                }
            }

    def get_revenue_stats(self, start_date: datetime, end_date: datetime,
                         currency: str = 'USD') -> Dict[str, Any]:
        """Get revenue statistics."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Total revenue
            cursor.execute('''
                SELECT SUM(amount) as total_revenue, COUNT(*) as transaction_count
                FROM revenue_events
                WHERE timestamp BETWEEN ? AND ?
                AND currency = ?
            ''', (start_date.isoformat(), end_date.isoformat(), currency))

            total_row = cursor.fetchone()
            total_revenue = total_row[0] or 0
            transaction_count = total_row[1] or 0

            # Revenue by transaction type
            cursor.execute('''
                SELECT transaction_type, SUM(amount) as revenue
                FROM revenue_events
                WHERE timestamp BETWEEN ? AND ?
                AND currency = ?
                GROUP BY transaction_type
            ''', (start_date.isoformat(), end_date.isoformat(), currency))

            revenue_by_type = dict(cursor.fetchall())

            # Average transaction value
            avg_transaction = total_revenue / transaction_count if transaction_count > 0 else 0

            return {
                'total_revenue': total_revenue,
                'transaction_count': transaction_count,
                'avg_transaction': avg_transaction,
                'revenue_by_type': revenue_by_type,
                'currency': currency,
                'period': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat()
                }
            }

    def get_top_content(self, start_date: datetime, end_date: datetime,
                       limit: int = 10) -> List[Dict[str, Any]]:
        """Get top content by usage."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute('''
                SELECT
                    u.content_id,
                    cm.title,
                    cm.author,
                    cm.category,
                    COUNT(*) as usage_count,
                    COUNT(DISTINCT u.user_id) as unique_users
                FROM usage_events u
                LEFT JOIN content_metadata cm ON u.content_id = cm.content_id
                WHERE u.timestamp BETWEEN ? AND ?
                GROUP BY u.content_id, cm.title, cm.author, cm.category
                ORDER BY usage_count DESC
                LIMIT ?
            ''', (start_date.isoformat(), end_date.isoformat(), limit))

            results = []
            for row in cursor.fetchall():
                results.append({
                    'content_id': row[0],
                    'title': row[1] or 'Unknown',
                    'author': row[2] or 'Unknown',
                    'category': row[3] or 'Uncategorized',
                    'usage_count': row[4],
                    'unique_users': row[5]
                })

            return results

    def get_user_engagement(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get user engagement metrics."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Daily active users
            cursor.execute('''
                SELECT DATE(timestamp) as date, COUNT(DISTINCT user_id) as dau
                FROM usage_events
                WHERE timestamp BETWEEN ? AND ?
                GROUP BY DATE(timestamp)
                ORDER BY date
            ''', (start_date.isoformat(), end_date.isoformat()))

            daily_active = [{'date': row[0], 'dau': row[1]} for row in cursor.fetchall()]

            # Session analysis
            cursor.execute('''
                SELECT
                    AVG(session_events) as avg_session_length,
                    MAX(session_events) as max_session_length,
                    COUNT(DISTINCT session_id) as total_sessions
                FROM (
                    SELECT session_id, COUNT(*) as session_events
                    FROM usage_events
                    WHERE timestamp BETWEEN ? AND ?
                    GROUP BY session_id
                )
            ''', (start_date.isoformat(), end_date.isoformat()))

            session_row = cursor.fetchone()
            session_stats = {
                'avg_session_length': session_row[0] or 0,
                'max_session_length': session_row[1] or 0,
                'total_sessions': session_row[2] or 0
            }

            return {
                'daily_active_users': daily_active,
                'session_stats': session_stats,
                'period': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat()
                }
            }


class AnalyticsTracker:
    """
    Analytics tracking system.
    """

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize analytics tracker.

        Args:
            db_path: Path to analytics database
        """
        if db_path is None:
            db_path = Path.home() / ".ks_pdf_studio" / "analytics.db"

        self.db = AnalyticsDatabase(str(db_path))
        self.session_id = None
        self._lock = threading.Lock()

    def start_session(self, user_id: str, session_id: Optional[str] = None) -> str:
        """
        Start a new analytics session.

        Args:
            user_id: User ID
            session_id: Optional session ID

        Returns:
            str: Session ID
        """
        self.session_id = session_id or f"{user_id}_{int(time.time())}"
        return self.session_id

    def track_usage(self, user_id: str, license_id: str, content_id: str,
                   event_type: str, metadata: Optional[Dict[str, Any]] = None,
                   ip_address: Optional[str] = None, user_agent: Optional[str] = None):
        """
        Track usage event.

        Args:
            user_id: User ID
            license_id: License ID
            content_id: Content ID
            event_type: Type of event
            metadata: Additional metadata
            ip_address: IP address
            user_agent: User agent string
        """
        with self._lock:
            event = UsageEvent(
                event_id=f"{user_id}_{content_id}_{int(time.time() * 1000)}",
                user_id=user_id,
                license_id=license_id,
                content_id=content_id,
                event_type=event_type,
                timestamp=datetime.now(),
                metadata=metadata or {},
                session_id=self.session_id or "unknown",
                ip_address=ip_address,
                user_agent=user_agent
            )

            self.db.insert_usage_event(event)

    def track_revenue(self, user_id: str, license_id: str, content_id: str,
                     amount: float, currency: str, payment_method: str,
                     transaction_type: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Track revenue event.

        Args:
            user_id: User ID
            license_id: License ID
            content_id: Content ID
            amount: Transaction amount
            currency: Currency code
            payment_method: Payment method
            transaction_type: Type of transaction
            metadata: Additional metadata
        """
        with self._lock:
            event = RevenueEvent(
                event_id=f"rev_{user_id}_{content_id}_{int(time.time() * 1000)}",
                user_id=user_id,
                license_id=license_id,
                content_id=content_id,
                amount=amount,
                currency=currency,
                payment_method=payment_method,
                transaction_type=transaction_type,
                timestamp=datetime.now(),
                metadata=metadata or {}
            )

            self.db.insert_revenue_event(event)

    def update_content_info(self, content_id: str, title: str, author: str,
                           category: str, tags: List[str], file_size: int = 0,
                           page_count: int = 0, word_count: int = 0):
        """
        Update content metadata.

        Args:
            content_id: Content ID
            title: Content title
            author: Content author
            category: Content category
            tags: Content tags
            file_size: File size in bytes
            page_count: Number of pages
            word_count: Number of words
        """
        metadata = {
            'title': title,
            'author': author,
            'category': category,
            'tags': tags,
            'created_date': datetime.now().isoformat(),
            'last_modified': datetime.now().isoformat(),
            'file_size': file_size,
            'page_count': page_count,
            'word_count': word_count
        }

        self.db.update_content_metadata(content_id, metadata)

    def get_dashboard_data(self, days: int = 30) -> Dict[str, Any]:
        """
        Get dashboard data for the specified period.

        Args:
            days: Number of days to look back

        Returns:
            Dict[str, Any]: Dashboard data
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        usage_stats = self.db.get_usage_stats(start_date, end_date)
        revenue_stats = self.db.get_revenue_stats(start_date, end_date)
        top_content = self.db.get_top_content(start_date, end_date, 10)
        engagement = self.db.get_user_engagement(start_date, end_date)

        return {
            'usage': usage_stats,
            'revenue': revenue_stats,
            'top_content': top_content,
            'engagement': engagement,
            'generated_at': datetime.now().isoformat()
        }


class AnalyticsDashboard:
    """
    Analytics dashboard for displaying insights.
    """

    def __init__(self, tracker: AnalyticsTracker):
        """
        Initialize analytics dashboard.

        Args:
            tracker: Analytics tracker instance
        """
        self.tracker = tracker

    def generate_report(self, days: int = 30) -> str:
        """
        Generate a text-based analytics report.

        Args:
            days: Number of days for the report

        Returns:
            str: Formatted report
        """
        data = self.tracker.get_dashboard_data(days)

        report = []
        report.append("=" * 60)
        report.append("KS PDF STUDIO ANALYTICS REPORT")
        report.append("=" * 60)
        report.append(f"Report Period: Last {days} days")
        report.append(f"Generated: {data['generated_at']}")
        report.append("")

        # Usage Statistics
        usage = data['usage']
        report.append("USAGE STATISTICS")
        report.append("-" * 20)
        report.append(f"Total Events: {usage['total_events']:,}")
        report.append(f"Unique Users: {usage['unique_users']:,}")
        report.append("")
        report.append("Event Breakdown:")
        for event_type, count in usage['event_breakdown'].items():
            report.append(f"  {event_type.title()}: {count:,}")
        report.append("")

        # Revenue Statistics
        revenue = data['revenue']
        report.append("REVENUE STATISTICS")
        report.append("-" * 20)
        report.append(f"Total Revenue: ${revenue['total_revenue']:,.2f} {revenue['currency']}")
        report.append(f"Transactions: {revenue['transaction_count']:,}")
        report.append(f"Average Transaction: ${revenue['avg_transaction']:,.2f}")
        report.append("")
        report.append("Revenue by Type:")
        for tx_type, amount in revenue['revenue_by_type'].items():
            report.append(f"  {tx_type.title()}: ${amount:,.2f}")
        report.append("")

        # Top Content
        top_content = data['top_content']
        report.append("TOP CONTENT")
        report.append("-" * 12)
        if top_content:
            for i, content in enumerate(top_content[:5], 1):
                report.append(f"{i}. {content['title']}")
                report.append(f"   Author: {content['author']}")
                report.append(f"   Usage: {content['usage_count']:,} views")
                report.append(f"   Unique Users: {content['unique_users']:,}")
                report.append("")
        else:
            report.append("No content usage data available")
        report.append("")

        # Engagement Metrics
        engagement = data['engagement']
        session_stats = engagement['session_stats']
        report.append("USER ENGAGEMENT")
        report.append("-" * 16)
        report.append(f"Total Sessions: {session_stats['total_sessions']:,}")
        report.append(f"Average Session Length: {session_stats['avg_session_length']:.1f} events")
        report.append(f"Max Session Length: {session_stats['max_session_length']:,} events")
        report.append("")

        # Daily Active Users (last 7 days)
        dau_data = engagement['daily_active_users'][-7:]
        if dau_data:
            report.append("Daily Active Users (Last 7 Days):")
            for day in dau_data:
                report.append(f"  {day['date']}: {day['dau']:,} users")
        report.append("")

        report.append("=" * 60)

        return "\n".join(report)

    def export_data(self, filepath: str, days: int = 30):
        """
        Export analytics data to JSON file.

        Args:
            filepath: Path to export file
            days: Number of days of data to export
        """
        data = self.tracker.get_dashboard_data(days)

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)


# Convenience functions
def create_sample_data(tracker: AnalyticsTracker):
    """Create sample analytics data for testing."""
    import random

    # Sample users and content
    users = [f"user_{i}" for i in range(1, 101)]
    content = [
        ("tutorial_001", "Python Basics", "John Doe", "Programming"),
        ("tutorial_002", "Web Development", "Jane Smith", "Web"),
        ("tutorial_003", "Data Science", "Bob Johnson", "Data"),
        ("tutorial_004", "Machine Learning", "Alice Brown", "AI"),
        ("tutorial_005", "Mobile Apps", "Charlie Wilson", "Mobile")
    ]

    # Update content metadata
    for content_id, title, author, category in content:
        tracker.update_content_info(
            content_id=content_id,
            title=title,
            author=author,
            category=category,
            tags=[category.lower()],
            page_count=random.randint(10, 50),
            word_count=random.randint(1000, 5000)
        )

    # Generate sample usage events
    for _ in range(1000):
        user = random.choice(users)
        content_id, _, _, _ = random.choice(content)
        event_type = random.choice(['view', 'print', 'edit', 'export'])

        tracker.track_usage(
            user_id=user,
            license_id=f"license_{user}",
            content_id=content_id,
            event_type=event_type,
            metadata={'duration': random.randint(30, 300)}
        )

    # Generate sample revenue events
    for _ in range(50):
        user = random.choice(users)
        content_id, _, _, _ = random.choice(content)
        amount = random.uniform(5.99, 49.99)
        tx_type = random.choice(['license_purchase', 'subscription', 'upgrade'])

        tracker.track_revenue(
            user_id=user,
            license_id=f"license_{user}",
            content_id=content_id,
            amount=round(amount, 2),
            currency='USD',
            payment_method=random.choice(['credit_card', 'paypal', 'stripe']),
            transaction_type=tx_type
        )


if __name__ == "__main__":
    # Test the analytics system
    tracker = AnalyticsTracker(":memory:")  # Use in-memory database for testing

    print("Creating sample analytics data...")
    create_sample_data(tracker)

    print("Generating analytics report...")
    dashboard = AnalyticsDashboard(tracker)
    report = dashboard.generate_report(days=30)
    print(report)

    print("Exporting data...")
    dashboard.export_data("analytics_export.json")

    print("Analytics system test completed!")