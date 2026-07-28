"""Enterprise security module for NexusMind."""

from app.security.rbac import (
    Role,
    Permission,
    check_permission,
    require_permission,
    RBACService,
    get_rbac_service,
)
from app.security.audit import AuditService, AuditLog, AuditAction, get_audit_service
from app.security.secrets import SecretsManager, get_secrets_manager
from app.security.csrf import CSRFService, get_csrf_service
from app.security.validation import InputValidator, get_input_validator
from app.security.middleware import setup_security_middleware
from app.security.deployment_gate import (
    DeploymentGate,
    DeploymentReport,
    CheckResult,
    Severity,
    run_deployment_gate,
    StartupError,
    print_deployment_checklist,
)
from app.security.startup_validator import (
    StartupValidator,
    validate_startup,
    ValidationReport,
    ValidationSeverity,
)

__all__ = [
    # RBAC
    "Role",
    "Permission",
    "check_permission",
    "require_permission",
    "RBACService",
    "get_rbac_service",
    # Audit
    "AuditService",
    "AuditLog",
    "AuditAction",
    "get_audit_service",
    # Secrets
    "SecretsManager",
    "get_secrets_manager",
    # CSRF
    "CSRFService",
    "get_csrf_service",
    # Validation
    "InputValidator",
    "get_input_validator",
    # Middleware
    "setup_security_middleware",
    # Deployment Gate (Phase 5.5)
    "DeploymentGate",
    "DeploymentReport",
    "CheckResult",
    "Severity",
    "run_deployment_gate",
    "StartupError",
    "print_deployment_checklist",
    # Legacy (backwards compat)
    "StartupValidator",
    "validate_startup",
    "ValidationReport",
    "ValidationSeverity",
]
