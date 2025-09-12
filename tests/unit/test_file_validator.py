"""
Tests for file validation utilities.

This module tests the FileValidator class and its security features.
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch

from repomap_tool.utils.file_validator import (
    FileValidator,
    validate_path,
    safe_read_text,
    safe_write_text,
    safe_create_directory,
    MAX_PATH_LENGTH,
    MAX_FILE_SIZE,
)
from repomap_tool.exceptions import ValidationError, FileAccessError


class TestFileValidator:
    """Test FileValidator class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.validator = FileValidator()
        self.temp_dir = Path(tempfile.mkdtemp())

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil

        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_validate_path_success(self):
        """Test successful path validation."""
        # Test with existing directory
        result = self.validator.validate_path(
            self.temp_dir, must_exist=True, must_be_dir=True
        )
        assert result == self.temp_dir.resolve()

    def test_validate_path_null_byte_rejection(self):
        """Test rejection of paths with null bytes."""
        with pytest.raises(ValidationError, match="forbidden character"):
            self.validator.validate_path("/some/path\x00/bad")

    def test_validate_path_traversal_rejection(self):
        """Test rejection of path traversal attempts."""
        with pytest.raises(ValidationError, match="forbidden pattern"):
            self.validator.validate_path("../../../etc/passwd")

    def test_validate_path_control_chars_rejection(self):
        """Test rejection of paths with control characters."""
        for char_code in [1, 2, 3, 7, 8, 15, 31]:
            with pytest.raises(ValidationError, match="forbidden character"):
                self.validator.validate_path(f"/path/with{chr(char_code)}/bad")

    def test_validate_path_too_long_rejection(self):
        """Test rejection of overly long paths."""
        long_path = "a" * (MAX_PATH_LENGTH + 1)
        with pytest.raises(ValidationError, match="Path too long"):
            self.validator.validate_path(long_path)

    def test_validate_path_parent_references_rejection(self):
        """Test rejection of parent directory references."""
        with pytest.raises(ValidationError, match="forbidden pattern"):
            self.validator.validate_path("some/../path")

    def test_validate_path_windows_reserved_names_rejection(self):
        """Test rejection of Windows reserved names (only on Windows)."""
        import platform

        reserved_names = ["CON", "PRN", "AUX", "NUL", "COM1", "LPT1"]
        for name in reserved_names:
            if platform.system() == "Windows":
                # On Windows, these should be rejected
                with pytest.raises(ValidationError, match="forbidden pattern"):
                    self.validator.validate_path(f"/path/{name}/file")
            else:
                # On non-Windows, these should be allowed
                result = self.validator.validate_path(f"/path/{name}/file")
                assert result == Path(f"/path/{name}/file")

    def test_validate_path_nonexistent_with_must_exist(self):
        """Test failure when path doesn't exist but must_exist=True."""
        nonexistent = self.temp_dir / "nonexistent"
        with pytest.raises(FileAccessError, match="does not exist"):
            self.validator.validate_path(nonexistent, must_exist=True)

    def test_validate_path_type_mismatch(self):
        """Test failure when path type doesn't match requirements."""
        # Create a file
        test_file = self.temp_dir / "test.txt"
        test_file.write_text("test")

        # Test file vs directory mismatch
        with pytest.raises(ValidationError, match="not a directory"):
            self.validator.validate_path(test_file, must_be_dir=True)

        with pytest.raises(ValidationError, match="not a file"):
            self.validator.validate_path(self.temp_dir, must_be_file=True)

    def test_validate_file_operation_read(self):
        """Test file operation validation for reading."""
        # Create test file
        test_file = self.temp_dir / "read_test.txt"
        test_file.write_text("test content")

        # Should succeed
        result = self.validator.validate_file_operation(test_file, "read")
        assert result == test_file.resolve()

        # Should fail for nonexistent file
        nonexistent = self.temp_dir / "nonexistent.txt"
        with pytest.raises(FileAccessError, match="does not exist"):
            self.validator.validate_file_operation(nonexistent, "read")

    def test_validate_file_operation_write(self):
        """Test file operation validation for writing."""
        # Test new file creation
        new_file = self.temp_dir / "new_file.txt"
        result = self.validator.validate_file_operation(new_file, "write")
        assert result == new_file.resolve()

    def test_validate_file_operation_invalid_operation(self):
        """Test rejection of invalid operation types."""
        test_file = self.temp_dir / "test.txt"
        with pytest.raises(ValidationError, match="Invalid operation"):
            self.validator.validate_file_operation(test_file, "invalid")

    def test_safe_read_text_success(self):
        """Test safe text reading."""
        test_file = self.temp_dir / "read_test.txt"
        test_content = "Hello, world! 🌍"
        test_file.write_text(test_content, encoding="utf-8")

        result = self.validator.safe_read_text(test_file)
        assert result == test_content

    def test_safe_read_text_encoding_error(self):
        """Test handling of encoding errors."""
        test_file = self.temp_dir / "binary_test.bin"
        # Write binary data that's not valid UTF-8
        test_file.write_bytes(b"\x80\x81\x82\x83")

        with pytest.raises(FileAccessError, match="Text decoding failed"):
            self.validator.safe_read_text(test_file)

    def test_safe_write_text_success(self):
        """Test safe text writing."""
        test_file = self.temp_dir / "write_test.txt"
        test_content = "Hello, world! 🌍"

        self.validator.safe_write_text(test_file, test_content)

        # Verify content was written correctly
        assert test_file.read_text(encoding="utf-8") == test_content

    def test_safe_write_text_content_too_large(self):
        """Test rejection of overly large content."""
        test_file = self.temp_dir / "large_test.txt"
        large_content = "a" * (MAX_FILE_SIZE + 1)

        with pytest.raises(ValidationError, match="Content too large"):
            self.validator.safe_write_text(test_file, large_content)

    def test_safe_create_directory_success(self):
        """Test safe directory creation."""
        new_dir = self.temp_dir / "new" / "nested" / "directory"

        result = self.validator.safe_create_directory(new_dir)
        assert result == new_dir.resolve()
        assert new_dir.exists()
        assert new_dir.is_dir()

    def test_sandbox_validation(self):
        """Test sandbox path validation."""
        # Create validator with project root restriction
        sandbox_validator = FileValidator(project_root=self.temp_dir)

        # Should allow path within sandbox
        internal_path = self.temp_dir / "internal" / "file.txt"
        result = sandbox_validator.validate_path(
            internal_path, must_exist=False, allow_create=True
        )
        # Use resolved paths for comparison (macOS /var vs /private/var symlink issue)
        assert str(result).startswith(str(self.temp_dir.resolve()))

        # Should reject path outside sandbox
        external_path = Path("/tmp/external/file.txt")
        with pytest.raises(ValidationError, match="outside project root"):
            sandbox_validator.validate_path(external_path)

    def test_file_size_validation(self):
        """Test file size validation."""
        # Create a file that's too large
        large_file = self.temp_dir / "large_file.txt"
        # Write content that's smaller than MAX_FILE_SIZE for this test
        large_content = "a" * 1000  # 1KB file
        large_file.write_text(large_content)

        # Should pass with default max size
        result = self.validator.validate_file_operation(large_file, "read")
        assert result == large_file.resolve()

        # Should fail with custom small max size
        with pytest.raises(ValidationError, match="File too large"):
            self.validator.validate_file_operation(large_file, "read", max_size=100)

    @patch("os.access")
    def test_permission_validation(self, mock_access):
        """Test file permission validation."""
        test_file = self.temp_dir / "permission_test.txt"
        test_file.write_text("test")

        # Mock no read permission
        mock_access.return_value = False
        with pytest.raises(FileAccessError, match="No read access"):
            self.validator.validate_file_operation(test_file, "read")


class TestConvenienceFunctions:
    """Test convenience functions."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil

        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_validate_path_convenience(self):
        """Test validate_path convenience function."""
        result = validate_path(self.temp_dir, must_exist=True, must_be_dir=True)
        assert result == self.temp_dir.resolve()

    def test_safe_read_text_convenience(self):
        """Test safe_read_text convenience function."""
        test_file = self.temp_dir / "test.txt"
        test_content = "Hello, world!"
        test_file.write_text(test_content)

        result = safe_read_text(test_file)
        assert result == test_content

    def test_safe_write_text_convenience(self):
        """Test safe_write_text convenience function."""
        test_file = self.temp_dir / "test.txt"
        test_content = "Hello, world!"

        safe_write_text(test_file, test_content)
        assert test_file.read_text() == test_content

    def test_safe_create_directory_convenience(self):
        """Test safe_create_directory convenience function."""
        new_dir = self.temp_dir / "new_directory"

        result = safe_create_directory(new_dir)
        assert result == new_dir.resolve()
        assert new_dir.exists()


class TestSecurityScenarios:
    """Test specific security scenarios."""

    def setup_method(self):
        """Set up test fixtures."""
        self.validator = FileValidator()
        self.temp_dir = Path(tempfile.mkdtemp())

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil

        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_path_injection_attempts(self):
        """Test various path injection attempts."""
        import os

        # Platform-independent malicious paths that should always be blocked
        malicious_paths = [
            "../../../etc/passwd",  # Should be blocked by ../
            "//server/share/file",  # Should be blocked by //
            "/dev/null",  # Should be blocked by /dev/
        ]

        # Add Windows-specific reserved names only on Windows
        if os.name == "nt":
            malicious_paths.extend(
                [
                    "CON",  # Should be blocked as reserved name
                    "PRN",  # Should be blocked as reserved name
                ]
            )

        blocked_count = 0
        for malicious_path in malicious_paths:
            try:
                self.validator.validate_path(malicious_path)
            except ValidationError:
                blocked_count += 1

        assert blocked_count == len(
            malicious_paths
        ), f"Expected to block {len(malicious_paths)} paths, but only blocked {blocked_count}"

    def test_unicode_normalization_attacks(self):
        """Test Unicode normalization attacks."""
        # Test various Unicode representations that could bypass filters
        unicode_attacks = [
            "test\u002e\u002e/passwd",  # Unicode dots
            "test\uff0e\uff0e/passwd",  # Fullwidth dots
            "test\u2024\u2024/passwd",  # One dot leaders
        ]

        # These may or may not be blocked depending on implementation
        # Just verify they don't cause crashes
        for attack_path in unicode_attacks:
            try:
                result = self.validator.validate_path(
                    attack_path, must_exist=False, allow_create=True
                )
                # If allowed, should be a valid Path object
                assert isinstance(result, Path)
            except ValidationError:
                # If blocked, that's also fine
                pass

    def test_zero_width_characters(self):
        """Test paths with zero-width characters."""
        zero_width_paths = [
            "test\u200b/file",  # Zero-width space
            "test\u200c/file",  # Zero-width non-joiner
            "test\u200d/file",  # Zero-width joiner
            "test\ufeff/file",  # Zero-width non-breaking space
        ]

        for zw_path in zero_width_paths:
            # These should be allowed (they're not in our forbidden list)
            # but we validate they don't cause issues
            try:
                result = self.validator.validate_path(
                    self.temp_dir / zw_path, must_exist=False, allow_create=True
                )
                assert isinstance(result, Path)
            except ValidationError:
                pass  # May be rejected for other reasons, that's fine

    def test_very_long_path_components(self):
        """Test paths with very long individual components."""
        # Most filesystems have a 255-byte limit for individual path components
        long_component = "a" * 300
        long_path = self.temp_dir / long_component / "file.txt"

        # This might be rejected by the OS or our validator
        with pytest.raises((ValidationError, OSError)):
            self.validator.validate_path(long_path, must_exist=False, allow_create=True)

    def test_symlink_validation(self):
        """Test validation of symbolic links."""
        if os.name != "nt":  # Skip on Windows where symlinks need special privileges
            # Create a symlink pointing outside the temp directory
            link_target = Path("/tmp")
            symlink_path = self.temp_dir / "bad_symlink"

            try:
                symlink_path.symlink_to(link_target, target_is_directory=True)

                # With sandbox restriction, this should be rejected
                sandbox_validator = FileValidator(project_root=self.temp_dir)

                # The symlink itself might pass validation, but following it should fail
                # (This tests that our resolve() call handles symlinks properly)
                try:
                    result = sandbox_validator.validate_path(
                        symlink_path, must_exist=True
                    )
                    # If it doesn't fail, make sure the resolved path is still in sandbox
                    assert str(result).startswith(str(self.temp_dir.resolve()))
                except (ValidationError, FileAccessError):
                    pass  # Expected to fail

            except OSError:
                # Skip if we can't create symlinks
                pytest.skip("Cannot create symlinks in this environment")
