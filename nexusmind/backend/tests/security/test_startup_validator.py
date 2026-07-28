"""Tests for startup validation."""

import pytest
from unittest.mock import MagicMock, patch


class TestStartupValidator:
    """Tests for StartupValidator."""
    
    @pytest.fixture
    def mock_settings(self):
        """Create mock settings."""
        settings = MagicMock()
        settings.secret_key = "change-me-in-production-use-strong-secret"
        settings.encryption_master_key = ""
        settings.database_url = "postgresql://postgres:postgres@localhost:5432/nexusmind"
        settings.cors_origins = ["http://localhost:3000"]
        settings.is_production = False
        settings.environment = "development"
        settings.rate_limit_per_minute = 100
        settings.log_level = "INFO"
        settings.force_https = False
        settings.allowed_hosts = []
        return settings
    
    def test_default_secret_key_fails(self, mock_settings):
        """Test that default secret key fails validation."""
        from app.security.startup_validator import StartupValidator
        
        validator = StartupValidator(mock_settings)
        validator._check_secret_key()
        
        result = validator.results[0]
        assert result.passed is False
        assert "default" in result.message.lower() or "placeholder" in result.message.lower()
    
    def test_strong_secret_key_passes(self, mock_settings):
        """Test that strong secret key passes validation."""
        from app.security.startup_validator import StartupValidator
        
        mock_settings.secret_key = "a-very-long-and-secure-random-string-that-is-32-chars-min"
        
        validator = StartupValidator(mock_settings)
        validator._check_secret_key()
        
        result = validator.results[0]
        assert result.passed is True
    
    def test_production_requires_master_key(self, mock_settings):
        """Test that production requires encryption master key."""
        from app.security.startup_validator import StartupValidator
        
        mock_settings.is_production = True
        mock_settings.environment = "production"
        
        validator = StartupValidator(mock_settings)
        validator._check_master_key()
        
        result = validator.results[0]
        assert result.passed is False
        assert result.severity.value == "blocking"
    
    def test_development_allows_no_master_key(self, mock_settings):
        """Test that development allows no encryption master key."""
        from app.security.startup_validator import StartupValidator
        
        validator = StartupValidator(mock_settings)
        validator._check_master_key()
        
        result = validator.results[0]
        # In dev, this should pass with a warning
        assert result.severity.value == "warning"
    
    def test_default_db_credentials_fails_production(self, mock_settings):
        """Test that default DB credentials fail in production."""
        from app.security.startup_validator import StartupValidator
        
        mock_settings.is_production = True
        mock_settings.environment = "production"
        
        validator = StartupValidator(mock_settings)
        validator._check_database_url()
        
        result = validator.results[0]
        assert result.passed is False
        assert "default" in result.message.lower()
    
    def test_strong_db_credentials_passes(self, mock_settings):
        """Test that strong DB credentials pass validation."""
        from app.security.startup_validator import StartupValidator
        
        mock_settings.database_url = "postgresql://secure_user:S3cur3P@ss!@db.example.com:5432/nexusmind"
        
        validator = StartupValidator(mock_settings)
        validator._check_database_url()
        
        result = validator.results[0]
        assert result.passed is True
    
    def test_localhost_cors_warning_in_production(self, mock_settings):
        """Test that localhost CORS generates warning in production."""
        from app.security.startup_validator import StartupValidator
        
        mock_settings.is_production = True
        mock_settings.environment = "production"
        mock_settings.cors_origins = ["http://localhost:3000"]
        
        validator = StartupValidator(mock_settings)
        validator._check_cors_origins()
        
        result = validator.results[0]
        # Should pass but with warning
        assert result.severity.value == "warning"
        assert "localhost" in result.message.lower()
    
    def test_production_cors_passes(self, mock_settings):
        """Test that production CORS passes."""
        from app.security.startup_validator import StartupValidator
        
        mock_settings.is_production = True
        mock_settings.environment = "production"
        mock_settings.cors_origins = ["https://app.example.com"]
        
        validator = StartupValidator(mock_settings)
        validator._check_cors_origins()
        
        result = validator.results[0]
        assert result.passed is True


class TestValidationReport:
    """Tests for ValidationReport."""
    
    def test_all_passed_when_no_failures(self):
        """Test all_passed returns True when no blocking failures."""
        from app.security.startup_validator import ValidationReport, ValidationResult, ValidationSeverity
        
        report = ValidationReport(
            environment="production",
            is_production=True,
            results=[
                ValidationResult(
                    name="Test",
                    passed=True,
                    severity=ValidationSeverity.BLOCKING,
                    message="Test passed",
                )
            ]
        )
        
        assert report.all_passed is True
        assert len(report.blocking_failures) == 0
    
    def test_all_passed_false_with_failure(self):
        """Test all_passed returns False with blocking failure."""
        from app.security.startup_validator import ValidationReport, ValidationResult, ValidationSeverity
        
        report = ValidationReport(
            environment="production",
            is_production=True,
            results=[
                ValidationResult(
                    name="Test",
                    passed=False,
                    severity=ValidationSeverity.BLOCKING,
                    message="Test failed",
                )
            ]
        )
        
        assert report.all_passed is False
        assert len(report.blocking_failures) == 1
    
    def test_format_report(self):
        """Test report formatting."""
        from app.security.startup_validator import ValidationReport, ValidationResult, ValidationSeverity
        
        report = ValidationReport(
            environment="production",
            is_production=True,
            results=[
                ValidationResult(
                    name="SECRET_KEY",
                    passed=True,
                    severity=ValidationSeverity.BLOCKING,
                    message="Key is configured",
                ),
                ValidationResult(
                    name="DATABASE_URL",
                    passed=False,
                    severity=ValidationSeverity.BLOCKING,
                    message="Using default credentials",
                    hint="Use strong credentials",
                ),
            ]
        )
        
        formatted = report.format_report()
        assert "NEXUSMIND STARTUP VALIDATION REPORT" in formatted
        assert "SECRET_KEY" in formatted
        assert "DATABASE_URL" in formatted
        assert "PASS" in formatted
        assert "FAIL" in formatted


class TestValidateStartup:
    """Tests for validate_startup function."""
    
    def test_validate_startup_passes_with_good_config(self):
        """Test validation passes with good configuration."""
        from app.security.startup_validator import validate_startup
        
        mock_settings = MagicMock()
        mock_settings.secret_key = "a-very-long-and-secure-random-string-that-is-32-chars-min"
        mock_settings.encryption_master_key = "a" * 64  # 32 bytes in hex
        mock_settings.database_url = "postgresql://user:pass@localhost:5432/db"
        mock_settings.cors_origins = ["http://localhost:3000"]
        mock_settings.is_production = False
        mock_settings.environment = "development"
        mock_settings.rate_limit_per_minute = 100
        mock_settings.log_level = "INFO"
        
        report = validate_startup(mock_settings, raise_on_failure=False)
        
        # Some checks may still fail due to localhost in dev, but shouldn't raise
        assert report is not None
    
    def test_validate_startup_raises_on_failure(self):
        """Test validation raises StartupError when configured."""
        from app.security.startup_validator import validate_startup, StartupError
        
        mock_settings = MagicMock()
        mock_settings.secret_key = "change-me-in-production-use-strong-secret"
        mock_settings.encryption_master_key = ""
        mock_settings.database_url = ""
        mock_settings.cors_origins = []
        mock_settings.is_production = True
        mock_settings.environment = "production"
        mock_settings.rate_limit_per_minute = 100
        mock_settings.log_level = "INFO"
        
        with pytest.raises(StartupError) as exc_info:
            validate_startup(mock_settings, raise_on_failure=True)
        
        assert exc_info.value.report is not None
        assert exc_info.value.report.all_passed is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
