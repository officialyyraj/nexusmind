"""Hostile Tests for Deployment Gate.

These tests attempt to prove the deployment gate fails
when it should and passes when it should.

Test Categories:
1. Secrets - Must reject weak/default keys
2. Database - Must reject default credentials
3. CORS - Must reject wildcards and localhost in prod
4. Production Mode - Must enforce all CRITICAL checks
5. Development Mode - Should be lenient
"""

import os
import pytest
from unittest.mock import MagicMock, patch
from dataclasses import dataclass


def make_settings(**kwargs):
    """Create a mock settings object with defaults."""
    defaults = {
        'secret_key': 'a-secure-random-string-that-is-long-enough-for-production',
        'encryption_master_key': 'a' * 64,  # 32 bytes in hex
        'database_url': 'postgresql://user:password@db.example.com:5432/nexusmind',
        'cors_origins': ['https://app.example.com'],
        'rate_limit_per_minute': 100,
        'log_level': 'INFO',
        'redis_url': 'redis://redis.example.com:6379/0',
        'environment': 'production',
        'is_production': True,
        'sandbox_docker_image': 'nexusmind-sandbox:latest',
        'sandbox_timeout_seconds': 300,
        'app_name': 'NexusMind',
        'jwt_algorithm': 'HS256',
    }
    defaults.update(kwargs)
    
    settings = MagicMock()
    for key, value in defaults.items():
        setattr(settings, key, value)
    return settings


class TestSecretsValidation:
    """Tests for secrets validation."""
    
    def test_reject_empty_secret_key(self):
        """CRITICAL: Empty SECRET_KEY must fail."""
        from app.security.deployment_gate import DeploymentGate
        
        settings = make_settings(secret_key='')
        gate = DeploymentGate(settings)
        gate._check_jwt_secret()
        
        result = gate.checks[-1]
        assert result.passed is False
        assert result.severity.value == "critical"
        assert "not configured" in result.message.lower()
    
    def test_reject_change_me_secret(self):
        """CRITICAL: 'change-me' SECRET_KEY must fail."""
        from app.security.deployment_gate import DeploymentGate
        
        settings = make_settings(secret_key='change-me-in-production-use-strong-secret')
        gate = DeploymentGate(settings)
        gate._check_jwt_secret()
        
        result = gate.checks[-1]
        assert result.passed is False
        assert "insecure" in result.message.lower() or "default" in result.message.lower()
    
    def test_reject_short_secret(self):
        """CRITICAL: Short SECRET_KEY must fail."""
        from app.security.deployment_gate import DeploymentGate
        
        settings = make_settings(secret_key='tooshort')
        gate = DeploymentGate(settings)
        gate._check_jwt_secret()
        
        result = gate.checks[-1]
        assert result.passed is False
        assert "too short" in result.message.lower()
    
    def test_accept_strong_secret(self):
        """CRITICAL: Strong SECRET_KEY must pass."""
        from app.security.deployment_gate import DeploymentGate
        
        settings = make_settings(secret_key='a-very-long-and-secure-random-string-32-chars-min')
        gate = DeploymentGate(settings)
        gate._check_jwt_secret()
        
        result = gate.checks[-1]
        assert result.passed is True
    
    def test_reject_empty_master_key_in_production(self):
        """CRITICAL: Empty ENCRYPTION_MASTER_KEY fails in production."""
        from app.security.deployment_gate import DeploymentGate
        
        settings = make_settings(
            encryption_master_key='',
            is_production=True,
            environment='production'
        )
        gate = DeploymentGate(settings)
        gate._check_encryption_key()
        
        result = gate.checks[-1]
        assert result.passed is False
        assert result.severity.value == "critical"
    
    def test_warn_missing_master_key_in_dev(self):
        """MEDIUM: Missing ENCRYPTION_MASTER_KEY warns in dev."""
        from app.security.deployment_gate import DeploymentGate
        
        settings = make_settings(
            encryption_master_key='',
            is_production=False,
            environment='development'
        )
        gate = DeploymentGate(settings)
        gate._check_encryption_key()
        
        result = gate.checks[-1]
        # In dev, it should pass with a warning
        assert result.passed is True
        assert "dev" in result.message.lower()


class TestDatabaseValidation:
    """Tests for database validation."""
    
    def test_reject_default_postgres_credentials(self):
        """CRITICAL: 'postgres:postgres' credentials must fail in production."""
        from app.security.deployment_gate import DeploymentGate
        
        settings = make_settings(
            database_url='postgresql://postgres:postgres@localhost:5432/nexusmind',
            is_production=True,
            environment='production'
        )
        gate = DeploymentGate(settings)
        gate._check_database_url()
        
        result = gate.checks[-1]
        assert result.passed is False
        assert "default credentials" in result.message.lower()
    
    def test_accept_strong_credentials(self):
        """CRITICAL: Strong credentials must pass."""
        from app.security.deployment_gate import DeploymentGate
        
        settings = make_settings(
            database_url='postgresql://app_user:S3cur3P@ss!@db.example.com:5432/nexusmind'
        )
        gate = DeploymentGate(settings)
        gate._check_database_url()
        
        result = gate.checks[-1]
        assert result.passed is True
    
    def test_warn_localhost_in_production(self):
        """MEDIUM: Localhost URL warns in production."""
        from app.security.deployment_gate import DeploymentGate
        
        settings = make_settings(
            database_url='postgresql://user:pass@localhost:5432/nexusmind',
            is_production=True,
            environment='production'
        )
        gate = DeploymentGate(settings)
        gate._check_database_url()
        
        result = gate.checks[-1]
        # Should pass but with warning about localhost
        assert "localhost" in result.message.lower()


class TestCORSValidation:
    """Tests for CORS validation."""
    
    def test_reject_empty_cors(self):
        """CRITICAL: Empty CORS must fail."""
        from app.security.deployment_gate import DeploymentGate
        
        settings = make_settings(cors_origins=[])
        gate = DeploymentGate(settings)
        gate._check_cors_origins()
        
        result = gate.checks[-1]
        assert result.passed is False
        assert "empty" in result.message.lower()
    
    def test_reject_wildcard_cors(self):
        """CRITICAL: Wildcard CORS must fail."""
        from app.security.deployment_gate import DeploymentGate
        
        settings = make_settings(cors_origins=['*'])
        gate = DeploymentGate(settings)
        gate._check_cors_origins()
        
        result = gate.checks[-1]
        assert result.passed is False
        assert "wildcard" in result.message.lower()
    
    def test_reject_localhost_in_production(self):
        """CRITICAL: Localhost CORS must fail in production."""
        from app.security.deployment_gate import DeploymentGate
        
        settings = make_settings(
            cors_origins=['http://localhost:3000'],
            is_production=True,
            environment='production'
        )
        gate = DeploymentGate(settings)
        gate._check_cors_origins()
        
        result = gate.checks[-1]
        assert result.passed is False
        assert "localhost" in result.message.lower()
    
    def test_accept_production_cors(self):
        """CRITICAL: Production CORS must pass."""
        from app.security.deployment_gate import DeploymentGate
        
        settings = make_settings(cors_origins=['https://app.example.com'])
        gate = DeploymentGate(settings)
        gate._check_cors_origins()
        
        result = gate.checks[-1]
        assert result.passed is True


class TestRateLimiting:
    """Tests for rate limiting validation."""
    
    def test_reject_disabled_rate_limit(self):
        """HIGH: Disabled rate limiting must fail."""
        from app.security.deployment_gate import DeploymentGate
        
        settings = make_settings(rate_limit_per_minute=0)
        gate = DeploymentGate(settings)
        gate._check_rate_limiting()
        
        result = gate.checks[-1]
        assert result.passed is False
        assert "disabled" in result.message.lower()
    
    def test_accept_configured_rate_limit(self):
        """HIGH: Configured rate limiting must pass."""
        from app.security.deployment_gate import DeploymentGate
        
        settings = make_settings(rate_limit_per_minute=100)
        gate = DeploymentGate(settings)
        gate._check_rate_limiting()
        
        result = gate.checks[-1]
        assert result.passed is True


class TestProductionMode:
    """Tests for production mode enforcement."""
    
    def test_all_critical_checks_required_in_production(self):
        """CRITICAL: All critical checks must fail in production."""
        from app.security.deployment_gate import DeploymentGate
        
        # Create settings with all defaults (should fail)
        settings = make_settings(
            secret_key='change-me',
            encryption_master_key='',
            database_url='postgresql://postgres:postgres@localhost:5432/nexusmind',
            cors_origins=['http://localhost:3000'],
            rate_limit_per_minute=0,
            is_production=True,
            environment='production'
        )
        
        gate = DeploymentGate(settings)
        report = gate.validate_all()
        
        # Should have critical failures
        assert len(report.critical_failures) > 0
    
    def test_report_shows_critical_failures(self):
        """Report must clearly show critical failures."""
        from app.security.deployment_gate import DeploymentGate
        
        settings = make_settings(
            secret_key='',
            is_production=True,
            environment='production'
        )
        
        gate = DeploymentGate(settings)
        report = gate.validate_all()
        
        assert report.all_passed is False
        assert len(report.critical_failures) > 0
        
        formatted = report.format_report()
        assert "CRITICAL" in formatted or "critical" in formatted.lower()


class TestDevelopmentMode:
    """Tests for development mode leniency."""
    
    def test_lenient_checks_in_development(self):
        """Development mode should be more lenient."""
        from app.security.deployment_gate import DeploymentGate
        
        settings = make_settings(
            secret_key='short',
            encryption_master_key='',
            is_production=False,
            environment='development'
        )
        
        gate = DeploymentGate(settings)
        report = gate.validate_all()
        
        # Should have fewer critical failures in dev
        # At minimum, the short secret should still fail
        critical_count = len([c for c in report.checks if c.severity.value == "critical" and not c.passed])
        
        # The JWT secret should still fail (it's too short)
        jwt_check = [c for c in report.checks if c.name == "JWT_SECRET_KEY"][0]
        assert jwt_check.passed is False


class TestHostileScenarios:
    """Hostile scenarios attempting to bypass validation."""
    
    def test_bypass_via_whitespace(self):
        """Attempt to bypass with whitespace in secret."""
        from app.security.deployment_gate import DeploymentGate
        
        settings = make_settings(secret_key='   change-me   ')
        gate = DeploymentGate(settings)
        gate._check_jwt_secret()
        
        result = gate.checks[-1]
        # Whitespace should be stripped, revealing the default
        assert result.passed is False
    
    def test_bypass_via_case_variation(self):
        """Attempt to bypass with case variation."""
        from app.security.deployment_gate import DeploymentGate
        
        settings = make_settings(secret_key='CHANGE-ME-In-Production')
        gate = DeploymentGate(settings)
        gate._check_jwt_secret()
        
        result = gate.checks[-1]
        assert result.passed is False
    
    def test_bypass_via_encoding(self):
        """Attempt to bypass with URL-encoded characters."""
        from app.security.deployment_gate import DeploymentGate
        
        # URL-encoded version of 'change-me'
        settings = make_settings(secret_key='change%2Dme')
        gate = DeploymentGate(settings)
        gate._check_jwt_secret()
        
        result = gate.checks[-1]
        # The regex should catch this
        assert result.passed is False


class TestDeploymentReport:
    """Tests for the deployment report."""
    
    def test_report_includes_all_checks(self):
        """Report must include all validation checks."""
        from app.security.deployment_gate import DeploymentGate
        
        settings = make_settings()
        gate = DeploymentGate(settings)
        report = gate.validate_all()
        
        # Should have checks for all categories
        categories = set(c.category for c in report.checks)
        
        expected = {'SECRETS', 'DATABASE', 'CACHE', 'REGISTRIES', 'ENGINE', 'SANDBOX', 'SECURITY', 'CONFIGURATION'}
        assert expected.issubset(categories), f"Missing categories: {expected - categories}"
    
    def test_report_format_includes_summary(self):
        """Formatted report must include summary."""
        from app.security.deployment_gate import DeploymentGate
        
        settings = make_settings()
        gate = DeploymentGate(settings)
        report = gate.validate_all()
        
        formatted = report.format_report()
        
        assert "DEPLOYMENT GATE REPORT" in formatted
        assert "Environment:" in formatted
        assert "Production Mode:" in formatted
        assert "Total Checks:" in formatted


class TestStartupError:
    """Tests for StartupError exception."""
    
    def test_startup_error_contains_report(self):
        """StartupError must contain the report."""
        from app.security.deployment_gate import run_deployment_gate, StartupError
        
        settings = make_settings(
            secret_key='weak',
            is_production=True,
            environment='production'
        )
        
        with pytest.raises(StartupError) as exc_info:
            run_deployment_gate(settings, raise_on_failure=True)
        
        assert exc_info.value.report is not None
        assert exc_info.value.report.all_passed is False


class TestDeploymentChecklist:
    """Tests for the deployment checklist."""
    
    def test_checklist_prints(self):
        """Checklist should print without error."""
        from app.security.deployment_gate import print_deployment_checklist
        
        # Should not raise
        print_deployment_checklist()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
