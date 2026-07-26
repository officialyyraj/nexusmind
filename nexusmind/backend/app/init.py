"""Zero-touch deployment initialization for NexusMind.

This module handles all startup tasks:
- Auto-generate secrets if missing
- Create required directories
- Wait for dependencies (PostgreSQL, Redis, ChromaDB)
- Initialize ChromaDB collections
- Run database migrations
"""

import os
import secrets
import sys
import time
from pathlib import Path
from typing import Any

import httpx
from pydantic_settings import BaseSettings, SettingsConfigDict


class StartupSettings(BaseSettings):
    """Startup configuration settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Dependency timeouts
    startup_db_timeout: int = 60
    startup_redis_timeout: int = 30
    startup_chromadb_timeout: int = 60
    startup_poll_interval: int = 2

    # Auto-generation
    auto_generate_secrets: bool = True
    secret_key_length: int = 32

    # Migrations
    run_migrations: bool = True

    # Database URL for migrations
    database_url: str = "postgresql://postgres:postgres@localhost:5432/nexusmind"

    # Redis URL for health check
    redis_url: str = "redis://localhost:6379/0"

    # ChromaDB URL
    chromadb_url: str = ""

    # ChromaDB persist directory
    chromadb_persist_directory: str = "./data/chromadb"

    # Directories
    workspace_root: str = "./workspace"
    plugins_directory: str = "./plugins"
    temp_directory: str = "/tmp/nexusmind"


class StartupError(Exception):
    """Raised when startup initialization fails."""

    def __init__(self, message: str, service: str | None = None, hint: str | None = None):
        self.service = service
        self.hint = hint
        super().__init__(message)


def log(msg: str, level: str = "INFO") -> None:
    """Print a log message."""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {msg}", flush=True)


def log_step(step: str) -> None:
    """Log a startup step."""
    print(f"\n{'='*60}", flush=True)
    print(f"  {step}", flush=True)
    print(f"{'='*60}\n", flush=True)


def generate_secret_key(length: int = 32) -> str:
    """Generate a secure random secret key."""
    return secrets.token_hex(length)


def ensure_directories(settings: StartupSettings) -> None:
    """Create required directories."""
    log_step("Creating Directories")

    directories = [
        Path(settings.workspace_root),
        Path(settings.plugins_directory),
        Path(settings.temp_directory),
        Path(settings.chromadb_persist_directory),
    ]

    for directory in directories:
        try:
            directory.mkdir(parents=True, exist_ok=True)
            log(f"Created/verified directory: {directory}")
        except PermissionError:
            log(f"Warning: Cannot create {directory} - permission denied", "WARN")
        except Exception as e:
            log(f"Warning: Cannot create {directory}: {e}", "WARN")


def generate_secrets(settings: StartupSettings) -> dict[str, str]:
    """Generate missing secrets."""
    log_step("Generating Secrets")

    generated = {}

    # Check SECRET_KEY
    secret_key = os.environ.get("SECRET_KEY", "").strip()
    if not secret_key or secret_key == "change-me-in-production-use-strong-secret":
        if settings.auto_generate_secrets:
            secret_key = generate_secret_key(settings.secret_key_length)
            os.environ["SECRET_KEY"] = secret_key
            generated["SECRET_KEY"] = secret_key
            log("Generated SECRET_KEY")
        else:
            raise StartupError(
                "SECRET_KEY is not set",
                service="security",
                hint="Set the SECRET_KEY environment variable or enable auto_generate_secrets"
            )
    else:
        log("SECRET_KEY: already configured")

    # Check SESSION_SECRET
    session_secret = os.environ.get("SESSION_SECRET", "").strip()
    if not session_secret:
        if settings.auto_generate_secrets:
            session_secret = generate_secret_key(settings.secret_key_length)
            os.environ["SESSION_SECRET"] = session_secret
            generated["SESSION_SECRET"] = session_secret
            log("Generated SESSION_SECRET")
        else:
            raise StartupError(
                "SESSION_SECRET is not set",
                service="security",
                hint="Set the SESSION_SECRET environment variable or enable auto_generate_secrets"
            )
    else:
        log("SESSION_SECRET: already configured")

    return generated


async def wait_for_postgres(settings: StartupSettings) -> bool:
    """Wait for PostgreSQL to become available."""
    log_step("Waiting for PostgreSQL")

    db_url = settings.database_url
    if not db_url:
        raise StartupError(
            "DATABASE_URL is not configured",
            service="postgresql",
            hint="Set DATABASE_URL to your PostgreSQL connection string"
        )

    # Parse connection info from URL
    try:
        from urllib.parse import urlparse
        parsed = urlparse(db_url.replace("postgresql://", "http://").replace("postgres://", "http://"))
        host = parsed.hostname or "localhost"
        port = parsed.port or 5432
        db_name = parsed.path.lstrip("/") if parsed.path else "nexusmind"
    except Exception as e:
        raise StartupError(
            f"Failed to parse DATABASE_URL: {e}",
            service="postgresql",
            hint="Ensure DATABASE_URL is in format: postgresql://user:pass@host:port/database"
        )

    log(f"Connecting to PostgreSQL at {host}:{port}/{db_name}")

    timeout = settings.startup_db_timeout
    poll_interval = settings.startup_poll_interval
    elapsed = 0

    while elapsed < timeout:
        try:
            import asyncpg
            conn = await asyncpg.connect(
                host=host,
                port=port,
                database=db_name,
                user=parsed.username or "postgres",
                password=parsed.password or "postgres",
                timeout=5,
            )
            await conn.close()
            log(f"PostgreSQL is ready!")
            return True
        except asyncpg.InvalidCatalogNameError:
            # Database doesn't exist yet - try connecting without specifying database
            try:
                import asyncpg
                conn = await asyncpg.connect(
                    host=host,
                    port=port,
                    user=parsed.username or "postgres",
                    password=parsed.password or "postgres",
                    timeout=5,
                )
                # Create database if it doesn't exist
                await conn.execute(f'CREATE DATABASE "{db_name}"')
                await conn.close()
                log(f"Created database: {db_name}")
                return True
            except Exception as e:
                log(f"Database not ready (will retry): {e}", "WARN")
        except ConnectionRefusedError:
            log(f"Connection refused - waiting... ({elapsed}s/{timeout}s)", "WARN")
        except Exception as e:
            log(f"Connection error - waiting... ({elapsed}s/{timeout}s): {e}", "WARN")

        time.sleep(poll_interval)
        elapsed += poll_interval

    raise StartupError(
        f"PostgreSQL did not become available within {timeout} seconds",
        service="postgresql",
        hint=f"Check that PostgreSQL is running at {host}:{port} and the connection credentials are correct"
    )


async def wait_for_redis(settings: StartupSettings) -> bool:
    """Wait for Redis to become available."""
    log_step("Waiting for Redis")

    redis_url = settings.redis_url
    if not redis_url:
        raise StartupError(
            "REDIS_URL is not configured",
            service="redis",
            hint="Set REDIS_URL to your Redis connection string"
        )

    # Parse connection info
    try:
        from urllib.parse import urlparse
        parsed = urlparse(redis_url.replace("redis://", "http://"))
        host = parsed.hostname or "localhost"
        port = parsed.port or 6379
        db = parsed.path.lstrip("/") if parsed.path else "0"
    except Exception as e:
        raise StartupError(
            f"Failed to parse REDIS_URL: {e}",
            service="redis",
            hint="Ensure REDIS_URL is in format: redis://host:port/db"
        )

    log(f"Connecting to Redis at {host}:{port}/{db}")

    timeout = settings.startup_redis_timeout
    poll_interval = settings.startup_poll_interval
    elapsed = 0

    while elapsed < timeout:
        try:
            import redis.asyncio as redis
            client = redis.Redis(
                host=host,
                port=port,
                db=int(db) if db.isdigit() else 0,
                socket_connect_timeout=5,
                socket_timeout=5,
            )
            await client.ping()
            await client.aclose()
            log("Redis is ready!")
            return True
        except ConnectionRefusedError:
            log(f"Connection refused - waiting... ({elapsed}s/{timeout}s)", "WARN")
        except Exception as e:
            log(f"Connection error - waiting... ({elapsed}s/{timeout}s): {e}", "WARN")

        time.sleep(poll_interval)
        elapsed += poll_interval

    raise StartupError(
        f"Redis did not become available within {timeout} seconds",
        service="redis",
        hint=f"Check that Redis is running at {host}:{port}"
    )


async def wait_for_chromadb(settings: StartupSettings) -> bool:
    """Wait for ChromaDB to become available."""
    log_step("Waiting for ChromaDB")

    chromadb_url = settings.chromadb_url
    if not chromadb_url:
        # Using local ChromaDB - just verify the directory exists
        log("Using local ChromaDB (no URL specified)")
        persist_dir = Path(settings.chromadb_persist_directory)
        persist_dir.mkdir(parents=True, exist_ok=True)
        log(f"Verified ChromaDB persist directory: {persist_dir}")
        return True

    # Ensure URL has proper format
    if not chromadb_url.startswith("http"):
        chromadb_url = f"http://{chromadb_url}"
    if not chromadb_url.endswith("/"):
        chromadb_url = f"{chromadb_url}/"

    log(f"Connecting to ChromaDB at {chromadb_url}")

    timeout = settings.startup_chromadb_timeout
    poll_interval = settings.startup_poll_interval
    elapsed = 0

    while elapsed < timeout:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{chromadb_url}api/v1/heartbeat")
                if response.status_code == 200:
                    log("ChromaDB is ready!")
                    return True
        except httpx.ConnectError:
            log(f"Connection refused - waiting... ({elapsed}s/{timeout}s)", "WARN")
        except Exception as e:
            log(f"Connection error - waiting... ({elapsed}s/{timeout}s): {e}", "WARN")

        time.sleep(poll_interval)
        elapsed += poll_interval

    raise StartupError(
        f"ChromaDB did not become available within {timeout} seconds",
        service="chromadb",
        hint=f"Check that ChromaDB is running and accessible at {chromadb_url}"
    )


async def initialize_chromadb(settings: StartupSettings) -> bool:
    """Initialize ChromaDB collections."""
    log_step("Initializing ChromaDB Collections")

    try:
        import chromadb
        from chromadb.config import Settings

        chromadb_url = settings.chromadb_url
        if chromadb_url and chromadb_url.startswith("http"):
            # Remote ChromaDB
            client = chromadb.HttpClient(
                host=chromadb_url.replace("http://", "").replace("https://", "").split("/")[0],
                settings=Settings(anonymized_telemetry=False),
            )
            log("Using remote ChromaDB")
        else:
            # Local ChromaDB
            persist_dir = settings.chromadb_persist_directory
            Path(persist_dir).mkdir(parents=True, exist_ok=True)
            client = chromadb.PersistentClient(path=persist_dir)
            log(f"Using local ChromaDB at {persist_dir}")

        # Create collections
        collections = [
            "conversations",
            "plans",
            "fixes",
            "outputs",
            "embeddings",
            "code",
            "documentation",
            "tasks",
        ]

        for name in collections:
            client.get_or_create_collection(
                name=name,
                metadata={"description": f"NexusMind {name} collection"}
            )
            log(f"  - {name}: OK")

        log("All ChromaDB collections initialized")
        return True

    except Exception as e:
        raise StartupError(
            f"Failed to initialize ChromaDB: {e}",
            service="chromadb",
            hint="Check ChromaDB configuration and permissions"
        )


async def run_migrations(settings: StartupSettings) -> bool:
    """Run Alembic database migrations."""
    log_step("Running Database Migrations")

    if not settings.run_migrations:
        log("Migrations skipped (RUN_MIGRATIONS=false)")
        return True

    try:
        from alembic.config import Config
        from alembic import command

        # Get the alembic.ini path
        alembic_ini = Path(__file__).parent.parent / "alembic.ini"
        if not alembic_ini.exists():
            log("No alembic.ini found - skipping migrations", "WARN")
            return True

        # Create Alembic config
        alembic_cfg = Config(str(alembic_ini))

        # Set the SQLAlchemy URL
        alembic_cfg.set_main_option("sqlalchemy.url", settings.database_url)

        log("Running alembic upgrade head...")
        command.upgrade(alembic_cfg, "head")
        log("Migrations completed successfully")
        return True

    except Exception as e:
        raise StartupError(
            f"Failed to run migrations: {e}",
            service="database",
            hint="Check that the database is accessible and the migration files are valid"
        )


async def initialize_all() -> dict[str, Any]:
    """
    Run all initialization steps.

    Returns a dict with information about what was initialized.
    """
    log_step("NexusMind Zero-Touch Deployment Initialization")
    log(f"Python: {sys.version.split()[0]}")
    log(f"Working directory: {os.getcwd()}")

    results: dict[str, Any] = {
        "initialized": [],
        "warnings": [],
        "generated_secrets": {},
    }

    settings = StartupSettings()

    # 1. Generate secrets
    try:
        generated = generate_secrets(settings)
        results["generated_secrets"] = generated
        results["initialized"].append("secrets")
    except StartupError as e:
        log(f"Failed to generate secrets: {e}", "ERROR")
        raise

    # 2. Create directories
    try:
        ensure_directories(settings)
        results["initialized"].append("directories")
    except Exception as e:
        log(f"Warning: Directory creation issue: {e}", "WARN")
        results["warnings"].append(f"directories: {e}")

    # 3. Wait for PostgreSQL
    try:
        await wait_for_postgres(settings)
        results["initialized"].append("postgresql")
    except StartupError as e:
        log(f"PostgreSQL not available: {e}", "ERROR")
        raise

    # 4. Run migrations
    try:
        await run_migrations(settings)
        results["initialized"].append("migrations")
    except StartupError as e:
        log(f"Migration failed: {e}", "ERROR")
        raise

    # 5. Wait for Redis
    try:
        await wait_for_redis(settings)
        results["initialized"].append("redis")
    except StartupError as e:
        log(f"Redis not available: {e}", "ERROR")
        raise

    # 6. Wait for ChromaDB
    try:
        await wait_for_chromadb(settings)
        results["initialized"].append("chromadb")
    except StartupError as e:
        log(f"ChromaDB not available: {e}", "ERROR")
        raise

    # 7. Initialize ChromaDB collections
    try:
        await initialize_chromadb(settings)
        results["initialized"].append("chromadb_collections")
    except StartupError as e:
        log(f"ChromaDB initialization failed: {e}", "ERROR")
        raise

    log_step("Initialization Complete")
    log(f"Initialized: {', '.join(results['initialized'])}")
    if results["warnings"]:
        log(f"Warnings: {', '.join(results['warnings'])}", "WARN")

    return results


def print_diagnostic_report() -> None:
    """Print a diagnostic report showing all environment variables and their status."""
    print("\n" + "=" * 60)
    print("  NexusMind Environment Diagnostic Report")
    print("=" * 60 + "\n")

    settings = StartupSettings()

    # Required secrets
    print("REQUIRED SECRETS:")
    print("-" * 40)
    secret_key = os.environ.get("SECRET_KEY", "").strip()
    session_secret = os.environ.get("SESSION_SECRET", "").strip()

    status = "✓ Configured" if secret_key else "✗ Missing (will be auto-generated)"
    print(f"  SECRET_KEY:       {status}")

    status = "✓ Configured" if session_secret else "✗ Missing (will be auto-generated)"
    print(f"  SESSION_SECRET:   {status}")

    # Database
    print("\nDATABASE:")
    print("-" * 40)
    print(f"  DATABASE_URL:     {'✓ Configured' if settings.database_url else '✗ Missing'}")
    print(f"  Timeout:         {settings.startup_db_timeout}s")

    # Redis
    print("\nREDIS:")
    print("-" * 40)
    print(f"  REDIS_URL:       {'✓ Configured' if settings.redis_url else '✗ Missing'}")
    print(f"  Timeout:         {settings.startup_redis_timeout}s")

    # ChromaDB
    print("\nCHROMADB:")
    print("-" * 40)
    if settings.chromadb_url:
        print(f"  CHROMADB_URL:     ✓ Configured ({settings.chromadb_url})")
    else:
        print(f"  CHROMADB_URL:     ⊘ Not configured (using local)")
    print(f"  Persist Dir:     {settings.chromadb_persist_directory}")
    print(f"  Timeout:         {settings.startup_chromadb_timeout}s")

    # Directories
    print("\nDIRECTORIES:")
    print("-" * 40)
    dirs = [
        settings.workspace_root,
        settings.plugins_directory,
        settings.temp_directory,
        settings.chromadb_persist_directory,
    ]
    for d in dirs:
        exists = "✓" if Path(d).exists() else "⊘"
        print(f"  {exists} {d}")

    # Optional
    print("\nOPTIONAL CONFIGURATION:")
    print("-" * 40)
    print(f"  OLLAMA_BASE_URL:   {settings.redis_url or 'Not configured'}")
    print(f"  OPENAI_API_KEY:    {'✓ Configured' if os.environ.get('OPENAI_API_KEY') else '⊘ Not configured'}")
    print(f"  ANTHROPIC_API_KEY: {'✓ Configured' if os.environ.get('ANTHROPIC_API_KEY') else '⊘ Not configured'}")

    print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    import asyncio

    print_diagnostic_report()

    print("Starting initialization...\n")
    try:
        results = asyncio.run(initialize_all())
        print("\n✓ All initialization steps completed successfully!")
    except StartupError as e:
        print(f"\n✗ Initialization failed: {e}")
        if e.service:
            print(f"  Service: {e.service}")
        if e.hint:
            print(f"  Hint: {e.hint}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        sys.exit(1)
