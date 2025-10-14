"""
KS PDF Studio - License Management System
Comprehensive licensing and DRM for monetizable content.

Author: Kalponic Studio
Version: 2.0.0
"""

import os
import uuid
import json
import hashlib
import base64
from typing import Dict, List, Optional, Union, Any, Tuple
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import secrets
import hmac

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


@dataclass
class LicenseInfo:
    """License information data class."""
    license_id: str
    user_id: str
    user_name: str
    user_email: str
    license_type: str  # 'personal', 'commercial', 'educational', 'enterprise'
    content_id: str
    content_title: str
    issued_date: datetime
    expiry_date: Optional[datetime]
    max_uses: Optional[int]
    current_uses: int
    allowed_domains: List[str]
    features: List[str]
    restrictions: Dict[str, Any]
    signature: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['issued_date'] = self.issued_date.isoformat()
        if self.expiry_date:
            data['expiry_date'] = self.expiry_date.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LicenseInfo':
        """Create from dictionary."""
        data_copy = data.copy()
        data_copy['issued_date'] = datetime.fromisoformat(data['issued_date'])
        if data.get('expiry_date'):
            data_copy['expiry_date'] = datetime.fromisoformat(data['expiry_date'])
        return cls(**data_copy)

    def is_valid(self) -> bool:
        """Check if license is valid."""
        now = datetime.now()

        # Check expiry
        if self.expiry_date and now > self.expiry_date:
            return False

        # Check usage limits
        if self.max_uses and self.current_uses >= self.max_uses:
            return False

        return True

    def can_use_feature(self, feature: str) -> bool:
        """Check if a feature is allowed by this license."""
        return feature in self.features

    def increment_usage(self) -> bool:
        """Increment usage counter. Returns False if limit exceeded."""
        if self.max_uses and self.current_uses >= self.max_uses:
            return False
        self.current_uses += 1
        return True


class LicenseKey:
    """License key generation and validation."""

    @staticmethod
    def generate_key(license_info: LicenseInfo, master_key: str) -> str:
        """
        Generate a license key from license info.

        Args:
            license_info: License information
            master_key: Master encryption key

        Returns:
            str: Encrypted license key
        """
        # Create license data
        data = license_info.to_dict()
        data_str = json.dumps(data, sort_keys=True)

        # Generate signature
        signature = LicenseKey._generate_signature(data_str, master_key)
        license_info.signature = signature

        # Encrypt data
        encrypted_data = LicenseKey._encrypt_data(data_str, master_key)

        # Create license key format: KS-<base64_data>
        license_key = f"KS-{base64.b64encode(encrypted_data.encode()).decode()}"

        return license_key

    @staticmethod
    def validate_key(license_key: str, master_key: str) -> Optional[LicenseInfo]:
        """
        Validate and decrypt a license key.

        Args:
            license_key: License key to validate
            master_key: Master encryption key

        Returns:
            Optional[LicenseInfo]: License info if valid, None otherwise
        """
        try:
            # Check format
            if not license_key.startswith("KS-"):
                return None

            # Extract encrypted data
            encrypted_b64 = license_key[3:]
            encrypted_data = base64.b64decode(encrypted_b64).decode()

            # Decrypt data
            data_str = LicenseKey._decrypt_data(encrypted_data, master_key)
            if not data_str:
                return None

            # Parse data
            data = json.loads(data_str)

            # Create license info
            license_info = LicenseInfo.from_dict(data)

            # Verify signature
            data_without_sig = data.copy()
            data_without_sig.pop('signature', None)
            expected_sig = LicenseKey._generate_signature(
                json.dumps(data_without_sig, sort_keys=True), master_key
            )

            if license_info.signature != expected_sig:
                return None

            return license_info

        except Exception:
            return None

    @staticmethod
    def _generate_signature(data: str, key: str) -> str:
        """Generate HMAC signature for data."""
        return hmac.new(
            key.encode(),
            data.encode(),
            hashlib.sha256
        ).hexdigest()

    @staticmethod
    def _encrypt_data(data: str, key: str) -> str:
        """Encrypt data using Fernet."""
        # Derive encryption key from master key
        salt = b'ks_pdf_studio_salt'
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        encryption_key = base64.urlsafe_b64encode(kdf.derive(key.encode()))

        fernet = Fernet(encryption_key)
        return fernet.encrypt(data.encode()).decode()

    @staticmethod
    def _decrypt_data(encrypted_data: str, key: str) -> Optional[str]:
        """Decrypt data using Fernet."""
        try:
            # Derive encryption key from master key
            salt = b'ks_pdf_studio_salt'
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            encryption_key = base64.urlsafe_b64encode(kdf.derive(key.encode()))

            fernet = Fernet(encryption_key)
            return fernet.decrypt(encrypted_data.encode()).decode()
        except Exception:
            return None


class LicenseManager:
    """
    Comprehensive license management system.
    """

    def __init__(self, license_dir: Optional[str] = None, master_key: Optional[str] = None):
        """
        Initialize license manager.

        Args:
            license_dir: Directory to store license files
            master_key: Master encryption key (generated if not provided)
        """
        self.license_dir = Path(license_dir) if license_dir else Path.home() / ".ks_pdf_studio" / "licenses"
        self.license_dir.mkdir(parents=True, exist_ok=True)

        # Generate or use master key
        self.master_key = master_key or self._load_or_generate_master_key()

        self.active_licenses: Dict[str, LicenseInfo] = {}
        self._load_licenses()

    def _load_or_generate_master_key(self) -> str:
        """Load existing master key or generate a new one."""
        key_file = self.license_dir / "master.key"

        if key_file.exists():
            try:
                with open(key_file, 'r') as f:
                    return f.read().strip()
            except:
                pass

        # Generate new master key
        master_key = secrets.token_hex(32)
        try:
            with open(key_file, 'w') as f:
                f.write(master_key)
        except:
            pass

        return master_key

    def _load_licenses(self):
        """Load active licenses from disk."""
        license_file = self.license_dir / "active_licenses.json"

        if license_file.exists():
            try:
                with open(license_file, 'r') as f:
                    data = json.load(f)

                for license_id, license_data in data.items():
                    license_info = LicenseInfo.from_dict(license_data)
                    self.active_licenses[license_id] = license_info

            except Exception as e:
                print(f"Failed to load licenses: {e}")

    def _save_licenses(self):
        """Save active licenses to disk."""
        license_file = self.license_dir / "active_licenses.json"
        data = {}

        for license_id, license_info in self.active_licenses.items():
            data[license_id] = license_info.to_dict()

        try:
            with open(license_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Failed to save licenses: {e}")

    def create_license(
        self,
        user_id: str,
        user_name: str,
        user_email: str,
        license_type: str,
        content_id: str,
        content_title: str,
        duration_days: Optional[int] = None,
        max_uses: Optional[int] = None,
        allowed_domains: Optional[List[str]] = None,
        features: Optional[List[str]] = None
    ) -> Tuple[str, LicenseInfo]:
        """
        Create a new license.

        Args:
            user_id: Unique user identifier
            user_name: User's full name
            user_email: User's email address
            license_type: Type of license
            content_id: Content identifier
            content_title: Content title
            duration_days: License duration in days (None for perpetual)
            max_uses: Maximum number of uses (None for unlimited)
            allowed_domains: Allowed domains for web licenses
            features: List of allowed features

        Returns:
            Tuple[str, LicenseInfo]: (license_key, license_info)
        """
        # Generate license ID
        license_id = str(uuid.uuid4())

        # Set default values
        allowed_domains = allowed_domains or []
        features = features or self._get_default_features(license_type)

        # Calculate expiry date
        expiry_date = None
        if duration_days:
            expiry_date = datetime.now() + timedelta(days=duration_days)

        # Create license info
        license_info = LicenseInfo(
            license_id=license_id,
            user_id=user_id,
            user_name=user_name,
            user_email=user_email,
            license_type=license_type,
            content_id=content_id,
            content_title=content_title,
            issued_date=datetime.now(),
            expiry_date=expiry_date,
            max_uses=max_uses,
            current_uses=0,
            allowed_domains=allowed_domains,
            features=features,
            restrictions=self._get_license_restrictions(license_type),
            signature=""
        )

        # Generate license key
        license_key = LicenseKey.generate_key(license_info, self.master_key)

        # Store license
        self.active_licenses[license_id] = license_info
        self._save_licenses()

        return license_key, license_info

    def validate_license(self, license_key: str, content_id: str = None) -> Optional[LicenseInfo]:
        """
        Validate a license key.

        Args:
            license_key: License key to validate
            content_id: Content ID to check against (optional)

        Returns:
            Optional[LicenseInfo]: License info if valid, None otherwise
        """
        # Decrypt and validate key
        license_info = LicenseKey.validate_key(license_key, self.master_key)
        if not license_info:
            return None

        # Check if license exists in active licenses
        if license_info.license_id not in self.active_licenses:
            return None

        stored_license = self.active_licenses[license_info.license_id]

        # Check content ID if provided
        if content_id and stored_license.content_id != content_id:
            return None

        # Check validity
        if not stored_license.is_valid():
            return None

        return stored_license

    def use_license(self, license_key: str, feature: str = None) -> bool:
        """
        Record license usage.

        Args:
            license_key: License key
            feature: Feature being used (optional)

        Returns:
            bool: True if usage allowed, False otherwise
        """
        license_info = self.validate_license(license_key)
        if not license_info:
            return False

        # Check feature access
        if feature and not license_info.can_use_feature(feature):
            return False

        # Increment usage
        if not license_info.increment_usage():
            return False

        # Save updated license
        self._save_licenses()

        return True

    def revoke_license(self, license_id: str) -> bool:
        """
        Revoke a license.

        Args:
            license_id: License ID to revoke

        Returns:
            bool: True if revoked successfully
        """
        if license_id in self.active_licenses:
            del self.active_licenses[license_id]
            self._save_licenses()
            return True
        return False

    def get_license_info(self, license_key: str) -> Optional[LicenseInfo]:
        """
        Get license information from key.

        Args:
            license_key: License key

        Returns:
            Optional[LicenseInfo]: License information
        """
        return self.validate_license(license_key)

    def list_licenses(self, user_id: Optional[str] = None) -> List[LicenseInfo]:
        """
        List active licenses.

        Args:
            user_id: Filter by user ID (optional)

        Returns:
            List[LicenseInfo]: List of licenses
        """
        licenses = list(self.active_licenses.values())

        if user_id:
            licenses = [lic for lic in licenses if lic.user_id == user_id]

        return licenses

    def _get_default_features(self, license_type: str) -> List[str]:
        """Get default features for a license type."""
        base_features = ['view', 'print']

        if license_type == 'personal':
            return base_features + ['edit', 'share']
        elif license_type == 'commercial':
            return base_features + ['edit', 'commercial_use', 'redistribution']
        elif license_type == 'educational':
            return base_features + ['edit', 'share', 'educational_use']
        elif license_type == 'enterprise':
            return base_features + ['edit', 'commercial_use', 'redistribution', 'api_access']
        else:
            return base_features

    def _get_license_restrictions(self, license_type: str) -> Dict[str, Any]:
        """Get license restrictions."""
        if license_type == 'personal':
            return {
                'commercial_use': False,
                'redistribution': False,
                'max_devices': 3
            }
        elif license_type == 'commercial':
            return {
                'redistribution': True,
                'max_devices': 10
            }
        elif license_type == 'educational':
            return {
                'commercial_use': False,
                'redistribution': False,
                'educational_only': True
            }
        elif license_type == 'enterprise':
            return {
                'max_devices': 100
            }
        else:
            return {}

    def create_trial_license(self, user_id: str, user_name: str, user_email: str,
                           content_id: str, content_title: str) -> Tuple[str, LicenseInfo]:
        """
        Create a trial license (30 days, limited features).

        Args:
            user_id: User ID
            user_name: User name
            user_email: User email
            content_id: Content ID
            content_title: Content title

        Returns:
            Tuple[str, LicenseInfo]: (license_key, license_info)
        """
        return self.create_license(
            user_id=user_id,
            user_name=user_name,
            user_email=user_email,
            license_type='trial',
            content_id=content_id,
            content_title=content_title,
            duration_days=30,
            max_uses=10,
            features=['view', 'print']
        )

    def upgrade_license(self, license_key: str, new_license_type: str,
                       additional_days: int = 0) -> Optional[str]:
        """
        Upgrade an existing license.

        Args:
            license_key: Current license key
            new_license_type: New license type
            additional_days: Additional days to add

        Returns:
            Optional[str]: New license key if upgrade successful
        """
        license_info = self.validate_license(license_key)
        if not license_info:
            return None

        # Update license type
        license_info.license_type = new_license_type
        license_info.features = self._get_default_features(new_license_type)
        license_info.restrictions = self._get_license_restrictions(new_license_type)

        # Extend expiry if requested
        if additional_days > 0:
            if license_info.expiry_date:
                license_info.expiry_date += timedelta(days=additional_days)
            else:
                license_info.expiry_date = datetime.now() + timedelta(days=additional_days)

        # Generate new key
        new_key = LicenseKey.generate_key(license_info, self.master_key)

        # Update stored license
        self.active_licenses[license_info.license_id] = license_info
        self._save_licenses()

        return new_key


class LicenseEnforcement:
    """
    License enforcement and DRM system.
    """

    def __init__(self, license_manager: LicenseManager):
        """
        Initialize license enforcement.

        Args:
            license_manager: License manager instance
        """
        self.license_manager = license_manager

    def check_access(self, license_key: str, content_id: str, action: str) -> Dict[str, Any]:
        """
        Check if an action is allowed for a license.

        Args:
            license_key: License key
            content_id: Content ID
            action: Action to check ('view', 'print', 'edit', etc.)

        Returns:
            Dict[str, Any]: Access result with status and details
        """
        license_info = self.license_manager.validate_license(license_key, content_id)

        if not license_info:
            return {
                'allowed': False,
                'reason': 'invalid_license',
                'message': 'License is invalid or expired'
            }

        # Check feature access
        if not license_info.can_use_feature(action):
            return {
                'allowed': False,
                'reason': 'feature_not_allowed',
                'message': f'License does not allow {action}'
            }

        # Record usage
        if not self.license_manager.use_license(license_key, action):
            return {
                'allowed': False,
                'reason': 'usage_limit_exceeded',
                'message': 'License usage limit exceeded'
            }

        return {
            'allowed': True,
            'license_info': license_info.to_dict(),
            'remaining_uses': license_info.max_uses - license_info.current_uses if license_info.max_uses else None
        }

    def generate_protected_content(self, content_path: str, license_key: str) -> str:
        """
        Generate protected version of content.

        Args:
            content_path: Path to original content
            license_key: License key for protection

        Returns:
            str: Path to protected content
        """
        # This would integrate with watermarking system
        # For now, just return the original path
        return content_path

    def validate_content_access(self, content_path: str, license_key: str) -> bool:
        """
        Validate access to protected content.

        Args:
            content_path: Path to content
            license_key: License key

        Returns:
            bool: True if access allowed
        """
        # Extract content ID from path or metadata
        content_id = self._extract_content_id(content_path)

        result = self.check_access(license_key, content_id, 'view')
        return result['allowed']

    def _extract_content_id(self, content_path: str) -> str:
        """Extract content ID from file path or metadata."""
        # Simple implementation - use filename hash
        return hashlib.md5(os.path.basename(content_path).encode()).hexdigest()


# Convenience functions for common license types
def create_personal_license(license_manager: LicenseManager, user_info: Dict[str, Any],
                          content_info: Dict[str, Any]) -> Tuple[str, LicenseInfo]:
    """Create a personal license."""
    return license_manager.create_license(
        user_id=user_info['id'],
        user_name=user_info['name'],
        user_email=user_info['email'],
        license_type='personal',
        content_id=content_info['id'],
        content_title=content_info['title'],
        duration_days=None,  # Perpetual
        max_uses=None,  # Unlimited
        features=['view', 'print', 'edit', 'share']
    )


def create_commercial_license(license_manager: LicenseManager, user_info: Dict[str, Any],
                            content_info: Dict[str, Any]) -> Tuple[str, LicenseInfo]:
    """Create a commercial license."""
    return license_manager.create_license(
        user_id=user_info['id'],
        user_name=user_info['name'],
        user_email=user_info['email'],
        license_type='commercial',
        content_id=content_info['id'],
        content_title=content_info['title'],
        duration_days=365,  # 1 year
        max_uses=None,  # Unlimited
        features=['view', 'print', 'edit', 'commercial_use', 'redistribution']
    )


def create_enterprise_license(license_manager: LicenseManager, user_info: Dict[str, Any],
                            content_info: Dict[str, Any]) -> Tuple[str, LicenseInfo]:
    """Create an enterprise license."""
    return license_manager.create_license(
        user_id=user_info['id'],
        user_name=user_info['name'],
        user_email=user_info['email'],
        license_type='enterprise',
        content_id=content_info['id'],
        content_title=content_info['title'],
        duration_days=365,  # 1 year
        max_uses=None,  # Unlimited
        features=['view', 'print', 'edit', 'commercial_use', 'redistribution', 'api_access']
    )


if __name__ == "__main__":
    # Test the license management system
    license_manager = LicenseManager()

    # Create a test license
    user_info = {
        'id': 'user123',
        'name': 'John Doe',
        'email': 'john@example.com'
    }

    content_info = {
        'id': 'tutorial001',
        'title': 'Python Basics Tutorial'
    }

    print("Creating personal license...")
    license_key, license_info = create_personal_license(license_manager, user_info, content_info)

    print(f"License Key: {license_key}")
    print(f"License ID: {license_info.license_id}")
    print(f"License Type: {license_info.license_type}")
    print(f"Valid: {license_info.is_valid()}")

    # Test license validation
    print("\nValidating license...")
    validated_info = license_manager.validate_license(license_key, content_info['id'])
    if validated_info:
        print(f"Validation successful: {validated_info.user_name}")
    else:
        print("Validation failed")

    # Test license enforcement
    print("\nTesting license enforcement...")
    enforcement = LicenseEnforcement(license_manager)
    access_result = enforcement.check_access(license_key, content_info['id'], 'view')
    print(f"Access allowed: {access_result['allowed']}")

    print("\nLicense management system test completed!")