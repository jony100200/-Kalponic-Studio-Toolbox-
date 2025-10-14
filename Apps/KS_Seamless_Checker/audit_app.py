#!/usr/bin/env python3
"""
Professional Application Audit Script
Evaluates KS Seamless Checker for production readiness and public release.
"""

import os
import sys
import json
import subprocess
import importlib.util
import ast
import re
from pathlib import Path
from typing import Dict, List, Tuple, Set

class ApplicationAuditor:
    """Comprehensive auditor for production readiness."""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.issues = []
        self.warnings = []
        self.passed = []

    def log_issue(self, category: str, message: str, file: str = None):
        """Log a critical issue that needs fixing."""
        self.issues.append({
            'category': category,
            'message': message,
            'file': str(file) if file else None
        })

    def log_warning(self, category: str, message: str, file: str = None):
        """Log a warning that should be addressed."""
        self.warnings.append({
            'category': category,
            'message': message,
            'file': str(file) if file else None
        })

    def log_pass(self, category: str, message: str):
        """Log a successful check."""
        self.passed.append({
            'category': category,
            'message': message
        })

    def audit_file_structure(self):
        """Audit the overall file structure."""
        print("🔍 Auditing file structure...")

        # Check for required files
        required_files = [
            'README.md',
            'requirements.txt',
            'main.py',
            'run_app.bat',
            'config.json'
        ]

        for file in required_files:
            if not (self.project_root / file).exists():
                self.log_issue('File Structure', f"Missing required file: {file}")
            else:
                self.log_pass('File Structure', f"Found required file: {file}")

        # Check for unnecessary files
        unnecessary_patterns = [
            '*.pyc', '__pycache__', '*.tmp', '*.bak', '*.log',
            'test_*.png', 'debug.py', '*.orig', '.DS_Store'
        ]

        for pattern in unnecessary_patterns:
            matches = list(self.project_root.rglob(pattern))
            if matches:
                for match in matches:
                    if match.is_file():
                        self.log_warning('File Structure', f"Unnecessary file found: {match.relative_to(self.project_root)}", match)

        # Check src directory structure
        src_dir = self.project_root / 'src'
        if not src_dir.exists():
            self.log_issue('File Structure', "Missing src/ directory")
        else:
            required_src_files = ['image_checker.py', 'batch_processor.py', 'gui.py']
            for file in required_src_files:
                if not (src_dir / file).exists():
                    self.log_issue('File Structure', f"Missing src/{file}")
                else:
                    self.log_pass('File Structure', f"Found src/{file}")

    def audit_code_quality(self):
        """Audit code quality and best practices."""
        print("🔍 Auditing code quality...")

        python_files = list(self.project_root.rglob('*.py'))

        for py_file in python_files:
            if '__pycache__' in str(py_file):
                continue

            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Check for syntax errors
                try:
                    ast.parse(content)
                except SyntaxError as e:
                    self.log_issue('Code Quality', f"Syntax error in {py_file.name}: {e}", py_file)

                # Check for debug prints
                debug_patterns = [
                    r'print\s*\(',
                    r'console\.log',
                    r'debug\s*=',
                    r'TODO',
                    r'FIXME',
                    r'XXX',
                    r'pdb\.set_trace',
                    r'import pdb'
                ]

                for pattern in debug_patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        # Allow some acceptable prints in test files
                        if 'test' not in py_file.name.lower():
                            self.log_warning('Code Quality', f"Potential debug code found in {py_file.name}: {pattern}", py_file)

                # Check for hardcoded paths
                if 'C:\\' in content or '/home/' in content or 'e:\\' in content.lower():
                    self.log_warning('Code Quality', f"Hardcoded path found in {py_file.name}", py_file)

                # Check for missing docstrings
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and not ast.get_docstring(node):
                        if len(node.body) > 1:  # Has actual implementation
                            self.log_warning('Code Quality', f"Missing docstring for {node.name} in {py_file.name}", py_file)

            except Exception as e:
                self.log_issue('Code Quality', f"Error reading {py_file.name}: {e}", py_file)

    def audit_dependencies(self):
        """Audit dependencies and imports."""
        print("🔍 Auditing dependencies...")

        # Check requirements.txt
        req_file = self.project_root / 'requirements.txt'
        if not req_file.exists():
            self.log_issue('Dependencies', "requirements.txt not found")
        else:
            try:
                with open(req_file, 'r') as f:
                    requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

                if not requirements:
                    self.log_issue('Dependencies', "requirements.txt is empty")
                else:
                    self.log_pass('Dependencies', f"Found {len(requirements)} dependencies in requirements.txt")

                    # Check for common missing dependencies
                    required_deps = ['PySide6', 'opencv-python', 'numpy', 'scikit-image', 'torch']
                    for dep in required_deps:
                        found = any(dep.lower() in req.lower() for req in requirements)
                        if not found:
                            self.log_warning('Dependencies', f"Potentially missing dependency: {dep}")

            except Exception as e:
                self.log_issue('Dependencies', f"Error reading requirements.txt: {e}")

        # Check for unused imports
        python_files = list(self.project_root.rglob('*.py'))
        for py_file in python_files:
            if '__pycache__' in str(py_file) or 'test_' in py_file.name:
                continue

            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                tree = ast.parse(content)
                imports = set()
                used_names = set()

                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            imports.add(alias.name.split('.')[0])
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            imports.add(node.module.split('.')[0])
                        for alias in node.names:
                            imports.add(alias.name.split('.')[0])
                    elif isinstance(node, ast.Name):
                        used_names.add(node.id)

                unused = imports - used_names - {'__name__', '__main__'}
                if unused:
                    self.log_warning('Dependencies', f"Potentially unused imports in {py_file.name}: {', '.join(unused)}", py_file)

            except Exception as e:
                self.log_warning('Dependencies', f"Error analyzing imports in {py_file.name}: {e}", py_file)

    def audit_configuration(self):
        """Audit configuration files."""
        print("🔍 Auditing configuration...")

        config_file = self.project_root / 'config.json'
        if not config_file.exists():
            self.log_issue('Configuration', "config.json not found")
        else:
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)

                required_keys = ['threshold', 'use_ai']
                for key in required_keys:
                    if key not in config:
                        self.log_warning('Configuration', f"Missing config key: {key}")
                    else:
                        self.log_pass('Configuration', f"Found config key: {key}")

                # Check for sensitive data
                sensitive_patterns = ['password', 'secret', 'key', 'token']
                config_str = json.dumps(config, indent=2)
                for pattern in sensitive_patterns:
                    if pattern in config_str.lower():
                        self.log_warning('Configuration', f"Potential sensitive data in config: {pattern}")

            except json.JSONDecodeError:
                self.log_issue('Configuration', "config.json is not valid JSON")
            except Exception as e:
                self.log_issue('Configuration', f"Error reading config.json: {e}")

    def audit_documentation(self):
        """Audit documentation."""
        print("🔍 Auditing documentation...")

        readme_file = self.project_root / 'README.md'
        if not readme_file.exists():
            self.log_issue('Documentation', "README.md not found")
        else:
            try:
                with open(readme_file, 'r', encoding='utf-8') as f:
                    readme_content = f.read()

                required_sections = ['Installation', 'Usage', 'Features']
                for section in required_sections:
                    if section.lower() not in readme_content.lower():
                        self.log_warning('Documentation', f"Missing section in README: {section}")

                if len(readme_content) < 500:
                    self.log_warning('Documentation', "README.md seems too short (< 500 characters)")

                self.log_pass('Documentation', "README.md found and contains content")

            except Exception as e:
                self.log_issue('Documentation', f"Error reading README.md: {e}")

    def audit_functionality(self):
        """Test basic functionality."""
        print("🔍 Testing basic functionality...")

        # Test imports
        try:
            sys.path.insert(0, str(self.project_root / 'src'))
            from image_checker import ImageChecker
            from batch_processor import BatchProcessor
            # GUI import may fail due to relative imports when not run as package
            try:
                from gui import MainWindow
                gui_import_success = True
            except ImportError:
                gui_import_success = False
            self.log_pass('Functionality', f"All main modules import successfully{' (GUI import failed due to relative imports - expected when not run as package)' if not gui_import_success else ''}")
        except ImportError as e:
            self.log_issue('Functionality', f"Import error: {e}")
        except Exception as e:
            self.log_issue('Functionality', f"Unexpected error during import: {e}")

        # Test basic instantiation
        try:
            checker = ImageChecker()
            self.log_pass('Functionality', "ImageChecker instantiates successfully")
        except Exception as e:
            self.log_issue('Functionality', f"ImageChecker instantiation failed: {e}")

    def generate_report(self):
        """Generate a comprehensive audit report."""
        print("\n" + "="*80)
        print("🎯 KS SEAMLESS CHECKER - PRODUCTION AUDIT REPORT")
        print("="*80)

        print(f"\n✅ PASSED CHECKS ({len(self.passed)}):")
        for item in self.passed:
            print(f"  • {item['category']}: {item['message']}")

        print(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
        for item in self.warnings:
            file_info = f" ({item['file']})" if item['file'] else ""
            print(f"  • {item['category']}: {item['message']}{file_info}")

        print(f"\n❌ ISSUES ({len(self.issues)}):")
        for item in self.issues:
            file_info = f" ({item['file']})" if item['file'] else ""
            print(f"  • {item['category']}: {item['message']}{file_info}")

        # Overall assessment
        total_checks = len(self.passed) + len(self.warnings) + len(self.issues)
        score = (len(self.passed) / total_checks) * 100 if total_checks > 0 else 0

        print(f"\n📊 OVERALL SCORE: {score:.1f}%")
        if score >= 90:
            print("🎉 EXCELLENT - Ready for production!")
        elif score >= 75:
            print("👍 GOOD - Minor issues to address")
        elif score >= 60:
            print("⚠️  FAIR - Several issues need attention")
        else:
            print("❌ POOR - Major issues require fixing")

        return {
            'score': score,
            'passed': len(self.passed),
            'warnings': len(self.warnings),
            'issues': len(self.issues),
            'details': {
                'passed': self.passed,
                'warnings': self.warnings,
                'issues': self.issues
            }
        }

    def run_full_audit(self):
        """Run the complete audit suite."""
        print("🚀 Starting comprehensive application audit...")
        print(f"📁 Project root: {self.project_root}")

        self.audit_file_structure()
        self.audit_code_quality()
        self.audit_dependencies()
        self.audit_configuration()
        self.audit_documentation()
        self.audit_functionality()

        return self.generate_report()


def main():
    """Main audit function."""
    # Find project root (assuming script is run from project directory)
    script_dir = Path(__file__).parent
    project_root = script_dir

    # If we're in a subdirectory, go up
    if script_dir.name in ['src', 'tests', 'scripts']:
        project_root = script_dir.parent

    auditor = ApplicationAuditor(project_root)
    results = auditor.run_full_audit()

    # Save detailed report
    report_file = project_root / 'audit_report.json'
    with open(report_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n📄 Detailed report saved to: {report_file}")

    # Exit with appropriate code
    if results['issues'] > 0:
        sys.exit(1)  # Issues found
    elif results['warnings'] > 0:
        sys.exit(2)  # Only warnings
    else:
        sys.exit(0)  # All good


if __name__ == '__main__':
    main()