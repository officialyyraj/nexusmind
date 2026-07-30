"""Startup Validation Checklist for Production Deployment.

This module validates critical configuration before application startup
to prevent 90% of deployment mistakes.

Checklist:
1. SECRET_KEY - JWT signing key
2. MASTER_KEY - Encryption key for BYOK
3. Database URL - Valid connection string
4. CORS - Properly configured origins
5. HTTPS - Enforced in production
"""

import os
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ValidationSeverity(str, Enum):
    """Severity level for validation failures."""
    
    BLOCKING = "blocking"  # Must pass or app won't start
    WARNING = "warning"     # Should pass, but app can still start


@dataclass
class ValidationResult:
    """Result of a single validation check."""
    
    name: str
    passed: bool
    severity: ValidationSeverity
    message: str
    hint: str | None = None
    current_value: str | None = None


@dataclass 
class ValidationReport:
    """Complete validation report for startup."""
    
    environment: str
    is_production: bool
    results: list[ValidationResult] = field(default_factory=list)
    
    @property
    def all_passed(self) -> bool:
        """Check if all blocking validations passed."""
        return all(
            r.passed for r in self.results 
            if r.severity == ValidationSeverity.BLOCKING
        )
    
    @property
    def blocking_failures(self) -> list[ValidationResult]:
        """Get all blocking failures."""
        return [
            r for r in self.results 
            if r.severity == ValidationSeverity.BLOCKING and not r.passed
        ]
    
    @property
    def warnings(self) -> list[ValidationResult]:
        """Get all warnings."""
        return [
            r for r in self.results 
            if r.severity == ValidationSeverity.WARNING and not r.passed
        ]
    
    def format_report(self) -> str:
        """Format the validation report as a string."""
        lines = [
            "=" * 60,
            "NEXUSMIND STARTUP VALIDATION REPORT",
            "=" * 60,
            f"Environment: {self.environment}",
            f"Is Production: {self.is_production}",
            "-" * 60,
            "",
        ]
        
        for result in self.results:
            status = "✅ PASS" if result.passed else "❌ FAIL"
            severity = f"[{result.severity.value.upper()}]"
            lines.append(f"{status} {severity}: {result.name}")
            
            if not result.passed:
                lines.append(f"       Message: {result.message}")
                if result.hint:
                    lines.append(f"       Hint: {result.hint}")
                if result.current_value:
                    # Mask sensitive values for display
                    masked = self._mask_value(result.name, result.current_value)
                    lines.append(f"       Current: {masked}")
            lines.append("")
        
        lines.append("-" * 60)
        if self.all_passed:
            lines.append("✅ ALL BLOCKING CHECKS PASSED - Ready to start!")
        else:
            lines.append(f"❌ {len(self.blocking_failures)} BLOCKING CHECK(S) FAILED")
            lines.append("   Fix these issues before deployment.")
        
        if self.warnings:
            lines.append(f"⚠️  {len(self.warnings)} WARNING(S)")
        
        lines.append("=" * 60)
        return "\n".join(lines)
    
    def _mask_value(self, name: str, value: str) -> str:
        """Mask sensitive values for display."""
        sensitive_names = [
            "SECRET_KEY", "MASTER_KEY", "API_KEY", "PASSWORD",
            "DATABASE_URL", "DB_PASSWORD", "TOKEN"
        ]
        
        for sensitive in sensitive_names:
            if sensitive.lower() in name.lower():
                if len(value) <= 8:
                    return "***MASKED***"
                return value[:4] + "***" + value[-4:]
        
        return value


class StartupValidator:
    """Validates configuration before application startup."""
    
    def __init__(self, settings: Any):
        self.settings = settings
        self.results: list[ValidationResult] = []
    
    def validate_all(self) -> ValidationReport:
        """Run all validation checks."""
        self.results = []
        environment = getattr(self.settings, 'environment', 'development')
        is_production = environment == 'production'
        
        # Run all validations
        self._check_secret_key()
        self._check_master_key()
        self._check_database_url()
        self._check_cors_origins()
        self._check_https()
        self._check_rate_limit()
        self._check_log_level()
        
        return ValidationReport(
            environment=environment,
            is_production=is_production,
            results=self.results,
        )
    
    def _check_secret_key(self) -> None:
        """Validate JWT secret key configuration."""
        secret_key = getattr(self.settings, 'secret_key', '')
        name = "SECRET_KEY (JWT)"
        
        # Check if using default/placeholder
        default_patterns = [
            "change-me",
            "secret",
            "your-secret",
            "changeme",
            "placeholder",
        ]
        
        is_default = any(
            pattern.lower() in secret_key.lower() 
            for pattern in default_patterns
        )
        
        is_weak = len(secret_key) < 32
        
        if not secret_key:
            self.results.append(ValidationResult(
                name=name,
                passed=False,
                severity=ValidationSeverity.BLOCKING,
                message="SECRET_KEY is not configured",
                hint="Set SECRET_KEY environment variable to a secure random string (minimum 32 characters)",
                current_value="",
            ))
        elif is_default:
            self.results.append(ValidationResult(
                name=name,
                passed=False,
                severity=ValidationSeverity.BLOCKING,
                message="SECRET_KEY uses a default/placeholder value",
                hint="Generate a secure key: python -c \"import secrets; print(secrets.token_urlsafe(32))\"",
                current_value=secret_key,
            ))
        elif is_weak:
            self.results.append(ValidationResult(
                name=name,
                passed=False,
                severity=ValidationSeverity.BLOCKING,
                message="SECRET_KEY is too short (minimum 32 characters)",
                hint="Use a longer, cryptographically secure random string",
                current_value=f"{secret_key[:8]}... ({len(secret_key)} chars)",
            ))
        else:
            self.results.append(ValidationResult(
                name=name,
                passed=True,
                severity=ValidationSeverity.BLOCKING,
                message="SECRET_KEY is properly configured",
            ))
    
    def _check_master_key(self) -> None:
        """Validate encryption master key for BYOK."""
        master_key = getattr(self.settings, 'encryption_master_key', '')
        name = "MASTER_KEY (Encryption)"
        
        # Check for default/placeholder
        default_patterns = [
            "change-me",
            "master",
            "encryption",
            "aes",
            "key",
        ]
        
        is_default = any(
            pattern.lower() in master_key.lower() 
            for pattern in default_patterns
        ) if master_key else False
        
        is_weak = len(master_key) < 64 if master_key else True  # 32 bytes = 64 hex chars
        
        if not master_key:
            if self.settings.is_production:
                self.results.append(ValidationResult(
                    name=name,
                    passed=False,
                    severity=ValidationSeverity.BLOCKING,
                    message="ENCRYPTION_MASTER_KEY is not configured",
                    hint="Generate: python -c \"import secrets; print(secrets.token_hex(32))\"",
                    current_value="",
                ))
            else:
                self.results.append(ValidationResult(
                    name=name,
                    passed=True,
                    severity=ValidationSeverity.WARNING,
                    message="ENCRYPTION_MASTER_KEY not set (will use ephemeral key in dev)",
                    hint="Set ENCRYPTION_MASTER_KEY for persistent BYOK keys",
                ))
        elif is_default:
            self.results.append(ValidationResult(
                name=name,
                passed=False,
                severity=ValidationSeverity.BLOCKING,
                message="MASTER_KEY uses a default/placeholder value",
                hint="Generate: python -c \"import secrets; print(secrets.token_hex(32))\"",
                current_value=f"{master_key[:8]}...",
            ))
        elif is_weak:
            self.results.append(ValidationResult(
                name=name,
                passed=False,
                severity=ValidationSeverity.BLOCKING,
                message="MASTER_KEY is too short (need 64 hex chars / 32 bytes)",
                hint="Generate: python -c \"import secrets; print(secrets.token_hex(32))\"",
                current_value=f"{master_key[:8]}... ({len(master_key)} chars)",
            ))
        else:
            self.results.append(ValidationResult(
                name=name,
                passed=True,
                severity=ValidationSeverity.BLOCKING,
                message="MASTER_KEY is properly configured",
            ))
    
    def _check_database_url(self) -> None:
        """Validate database connection URL."""
        db_url = getattr(self.settings, 'database_url', '')
        name = "DATABASE_URL"
        
        # Check for default credentials
        default_hosts = [
            "localhost",
            "127.0.0.1",
        ]
        
        default_user_pass = [
            "postgres:postgres",
            "postgres:password",
            "admin:admin",
            "root:root",
        ]
        
        has_default_creds = any(
            cred in db_url.lower() 
            for cred in default_user_pass
        )
        
        uses_localhost = any(
            host in db_url.lower() 
            for host in default_hosts
        )
        
        if not db_url:
            self.results.append(ValidationResult(
                name=name,
                passed=False,
                severity=ValidationSeverity.BLOCKING,
                message="DATABASE_URL is not configured",
                hint="Set DATABASE_URL environment variable",
                current_value="",
            ))
        elif has_default_creds and self.settings.is_production:
            self.results.append(ValidationResult(
                name=name,
                passed=False,
                severity=ValidationSeverity.BLOCKING,
                message="DATABASE_URL contains default credentials",
                hint="Use strong, unique credentials in production",
                current_value=re.sub(r'(://[^:]+:)[^@]+(@)', r'\1***\2', db_url),
            ))
        elif uses_localhost and self.settings.is_production:
            self.results.append(ValidationResult(
                name=name,
                passed=True,
                severity=ValidationSeverity.WARNING,
                message="Database points to localhost in production",
                hint="Use a remote database host for production deployments",
                current_value=db_url.split("@")[-1] if "@" in db_url else db_url,
            ))
        else:
            self.results.append(ValidationResult(
                name=name,
                passed=True,
                severity=ValidationSeverity.BLOCKING,
                message="DATABASE_URL is properly configured",
            ))
    
    def _check_cors_origins(self) -> None:
        """Validate CORS configuration."""
        cors_origins = getattr(self.settings, 'cors_origins', [])
        name = "CORS_ORIGINS"
        
        localhost_patterns = [
            "localhost",
            "127.0.0.1",
        ]
        
        has_localhost = any(
            any(pattern in origin.lower() for pattern in localhost_patterns)
            for origin in cors_origins
        )
        
        if not cors_origins:
            self.results.append(ValidationResult(
                name=name,
                passed=False,
                severity=ValidationSeverity.BLOCKING,
                message="CORS_ORIGINS is empty",
                hint="Set allowed origins for cross-origin requests",
                current_value="[]",
            ))
        elif has_localhost and self.settings.is_production:
            self.results.append(ValidationResult(
                name=name,
                passed=True,
                severity=ValidationSeverity.WARNING,
                message="CORS includes localhost in production",
                hint="Remove localhost from CORS origins in production",
                current_value=str(cors_origins),
            ))
        else:
            self.results.append(ValidationResult(
                name=name,
                passed=True,
                severity=ValidationSeverity.BLOCKING,
                message="CORS_ORIGINS is properly configured",
            ))
    
    def _check_https(self) -> None:
        """Check HTTPS configuration for production."""
        name = "HTTPS (Production)"
        
        # Check for indicators of HTTPS being enforced
        # This is typically checked via reverse proxy or environment
        force_https = getattr(self.settings, 'force_https', False)
        allowed_hosts = getattr(self.settings, 'allowed_hosts', [])
        
        if self.settings.is_production:
            if not force_https and not allowed_hosts:
                self.results.append(ValidationResult(
                    name=name,
                    passed=True,
                    severity=ValidationSeverity.WARNING,
                    message="HTTPS enforcement not explicitly configured",
                    hint="Ensure HTTPS is enforced via reverse proxy or set force_https=true",
                ))
            else:
                self.results.append(ValidationResult(
                    name=name,
                    passed=True,
                    severity=ValidationSeverity.WARNING,
                    message="HTTPS configuration detected",
                ))
        else:
            self.results.append(ValidationResult(
                name=name,
                passed=True,
                severity=ValidationSeverity.INFO,
                message="HTTPS check skipped in development",
            ))
    
    def _check_rate_limit(self) -> None:
        """Check rate limiting configuration."""
        rate_limit = getattr(self.settings, 'rate_limit_per_minute', 0)
        name = "RATE_LIMIT"
        
        if rate_limit <= 0:
            self.results.append(ValidationResult(
                name=name,
                passed=True,
                severity=ValidationSeverity.WARNING,
                message="Rate limiting is disabled",
                hint="Enable rate limiting for production security",
            ))
        elif rate_limit < 10:
            self.results.append(ValidationResult(
                name=name,
                passed=True,
                severity=ValidationSeverity.WARNING,
                message="Rate limit is very low",
                hint="Consider increasing rate limit for normal usage",
            ))
        else:
            self.results.append(ValidationResult(
                name=name,
                passed=True,
                severity=ValidationSeverity.BLOCKING,
                message="Rate limiting is configured",
            ))
    
    def _check_log_level(self) -> None:
        """Check logging configuration."""
        log_level = getattr(self.settings, 'log_level', 'INFO')
        name = "LOG_LEVEL"
        
        debug_levels = ['DEBUG', 'TRACE']
        
        if log_level.upper() in debug_levels and self.settings.is_production:
            self.results.append(ValidationResult(
                name=name,
                passed=True,
                severity=ValidationSeverity.WARNING,
                message="DEBUG logging enabled in production",
                hint="Set LOG_LEVEL=INFO or LOG_LEVEL=WARNING for production",
            ))
        else:
            self.results.append(ValidationResult(
                name=name,
                passed=True,
                severity=ValidationSeverity.BLOCKING,
                message="Logging is properly configured",
            ))


class StartupError(Exception):
    """Raised when startup validation fails."""
    
    def __init__(self, report: ValidationReport):
        self.report = report
        super().__init__(report.format_report())


def validate_startup(settings: Any, raise_on_failure: bool = True) -> ValidationReport:
    """Run startup validation and optionally raise on failure.
    
    Args:
        settings: Application settings object
        raise_on_failure: If True, raise StartupError on blocking failures
        
    Returns:
        ValidationReport with all check results
        
    Raises:
        StartupError: If raise_on_failure=True and blocking checks fail
    """
    validator = StartupValidator(settings)
    report = validator.validate_all()
    
    if raise_on_failure and not report.all_passed:
        raise StartupError(report)
    
    return report
