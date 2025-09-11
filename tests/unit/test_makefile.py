# Tests for Makefile commands
import pytest
import subprocess
import os
import shutil
from pathlib import Path
from unittest.mock import patch, Mock


class TestMakefile:
    """Test cases for Makefile commands."""

    def test_makefile_exists(self):
        """Test that Makefile exists."""
        makefile_path = Path(__file__).parent.parent.parent / "Makefile"
        assert makefile_path.exists()
        assert makefile_path.is_file()

    @pytest.mark.skipif(not shutil.which("make"), reason="make command not available")
    @pytest.mark.skipif(not shutil.which("make"), reason="make command not available")
    def test_make_help(self):
        """Test make help command."""
        makefile_dir = Path(__file__).parent.parent.parent

        result = subprocess.run(
            ["make", "help"],
            capture_output=True,
            text=True,
            cwd=makefile_dir
        )

        assert result.returncode == 0
        assert "Docker FastAPI Auth Service - Available Commands:" in result.stdout
        assert "backup-create" in result.stdout
        assert "backup-list" in result.stdout
        assert "backup-hash" in result.stdout

    @pytest.mark.skipif(not shutil.which("make"), reason="make command not available")
    @pytest.mark.skipif(not shutil.which("make"), reason="make command not available")
    def test_make_backup_hash_without_password(self):
        """Test make backup-hash without password parameter."""
        makefile_dir = Path(__file__).parent.parent.parent

        result = subprocess.run(
            ["make", "backup-hash"],
            capture_output=True,
            text=True,
            cwd=makefile_dir
        )

        assert result.returncode == 2  # Make error
        assert "PASSWORD" in result.stderr

    @pytest.mark.skipif(not shutil.which("make"), reason="make command not available")
    @pytest.mark.skipif(not shutil.which("make"), reason="make command not available")
    def test_make_backup_hash_with_password(self):
        """Test make backup-hash with password parameter."""
        makefile_dir = Path(__file__).parent.parent.parent

        result = subprocess.run(
            ["make", "backup-hash", "PASSWORD=test123"],
            capture_output=True,
            text=True,
            cwd=makefile_dir
        )

        assert result.returncode == 0
        assert "SHA256 Hash for 'test123':" in result.stdout
        expected_hash = "ecd71870d1963316a97e3ac3408c9835ad8cf0f3c1bc703527c30265534f75ae"
        assert expected_hash in result.stdout

    @pytest.mark.skipif(not shutil.which("make"), reason="make command not available")
    def test_make_backup_create_without_username(self):
        """Test make backup-create without username."""
        makefile_dir = Path(__file__).parent.parent.parent

        result = subprocess.run(
            ["make", "backup-create", "PASSWORD=test123"],
            capture_output=True,
            text=True,
            cwd=makefile_dir
        )

        assert result.returncode == 2
        assert "USERNAME and PASSWORD are required" in result.stderr

    @pytest.mark.skipif(not shutil.which("make"), reason="make command not available")
    def test_make_backup_create_without_password(self):
        """Test make backup-create without password."""
        makefile_dir = Path(__file__).parent.parent.parent

        result = subprocess.run(
            ["make", "backup-create", "USERNAME=testuser"],
            capture_output=True,
            text=True,
            cwd=makefile_dir
        )

        assert result.returncode == 2
        assert "USERNAME and PASSWORD are required" in result.stderr

    @pytest.mark.skipif(not shutil.which("make"), reason="make command not available")
    def test_make_backup_create_with_minimal_params(self):
        """Test make backup-create with minimal required parameters."""
        makefile_dir = Path(__file__).parent.parent.parent

        result = subprocess.run(
            ["make", "backup-create", "USERNAME=testuser", "PASSWORD=testpass123"],
            capture_output=True,
            text=True,
            cwd=makefile_dir
        )

        assert result.returncode == 0
        assert "Creating backup user configuration:" in result.stdout
        assert "Username: testuser" in result.stdout
        assert "Password Hash:" in result.stdout

    @pytest.mark.skipif(not shutil.which("make"), reason="make command not available")
    def test_make_backup_create_with_all_params(self):
        """Test make backup-create with all parameters."""
        makefile_dir = Path(__file__).parent.parent.parent

        result = subprocess.run(
            ["make", "backup-create", "USERNAME=testuser", "PASSWORD=testpass123", "ADMIN=true", "PERMISSIONS={\"services\":[\"*\"]}"],
            capture_output=True,
            text=True,
            cwd=makefile_dir
        )

        assert result.returncode == 0
        assert "Username: testuser" in result.stdout
        assert "Is Admin: true" in result.stdout
        assert '"*"' in result.stdout

    @pytest.mark.skipif(not shutil.which("make"), reason="make command not available")
    def test_make_backup_list(self):
        """Test make backup-list command."""
        makefile_dir = Path(__file__).parent.parent.parent

        result = subprocess.run(
            ["make", "backup-list"],
            capture_output=True,
            text=True,
            cwd=makefile_dir
        )

        assert result.returncode == 0
        assert "Current Backup Users Configuration:" in result.stdout

    @pytest.mark.skipif(not shutil.which("make"), reason="make command not available")
    def test_make_backup_example(self):
        """Test make backup-example command."""
        makefile_dir = Path(__file__).parent.parent.parent

        result = subprocess.run(
            ["make", "backup-example"],
            capture_output=True,
            text=True,
            cwd=makefile_dir
        )

        assert result.returncode == 0
        assert "Example BACKUP_USERS configuration" in result.stdout
        assert "admin" in result.stdout
        assert "operator" in result.stdout

    @pytest.mark.skipif(not shutil.which("make"), reason="make command not available")
    def test_make_examples(self):
        """Test make examples command."""
        makefile_dir = Path(__file__).parent.parent.parent

        result = subprocess.run(
            ["make", "examples"],
            capture_output=True,
            text=True,
            cwd=makefile_dir
        )

        assert result.returncode == 0
        assert "Docker FastAPI Auth Service - Usage Examples:" in result.stdout
        assert "make setup" in result.stdout
        assert "make backup-create" in result.stdout

    @pytest.mark.skipif(not shutil.which("make"), reason="make command not available")
    def test_make_status_without_services(self):
        """Test make status when services are not running."""
        makefile_dir = Path(__file__).parent.parent.parent

        result = subprocess.run(
            ["make", "status"],
            capture_output=True,
            text=True,
            cwd=makefile_dir
        )

        # This might fail if services aren't running, but we test the command structure
        # The important thing is that make doesn't fail with syntax errors
        assert result.returncode in [0, 1]  # 0 for success, 1 for service issues

    @pytest.mark.skipif(not shutil.which("make"), reason="make command not available")
    def test_makefile_syntax(self):
        """Test that Makefile has valid syntax."""
        makefile_dir = Path(__file__).parent.parent.parent
        makefile_path = makefile_dir / "Makefile"

        # Check for basic syntax by trying to parse with make
        result = subprocess.run(
            ["make", "-n", "help"],  # -n means dry run
            capture_output=True,
            text=True,
            cwd=makefile_dir
        )

        # Should not have syntax errors
        assert "syntax error" not in result.stderr.lower()
        assert "missing separator" not in result.stderr.lower()
