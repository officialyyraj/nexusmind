# Plugin System Documentation

The plugin system enables extensibility through modular components with hot loading, dependency management, and permission control.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Plugin Manager                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │   Tool   │  │  Agent   │  │ Workflow │  │   API    │  │
│  │  Plugin  │  │  Plugin  │  │  Plugin  │  │  Plugin  │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐ │
│  │                    Hot Loader                         │ │
│  └──────────────────────────────────────────────────────┘ │
│  ┌──────────────────────────────────────────────────────┐ │
│  │               Dependency Resolver                     │ │
│  └──────────────────────────────────────────────────────┘ │
│  ┌──────────────────────────────────────────────────────┐ │
│  │              Permission Manager                        │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Plugin Types

| Type | Description |
|------|-------------|
| `tool` | Extends agent capabilities |
| `agent` | Custom agent implementations |
| `workflow` | Custom workflow patterns |
| `api` | Additional API routes |
| `ui_panel` | Frontend UI components |
| `integration` | External integrations |

## Plugin Manifest

```json
{
  "manifest_version": "1.0",
  "metadata": {
    "id": "my-plugin",
    "name": "My Plugin",
    "version": "1.0.0",
    "description": "A useful plugin",
    "author": "Developer",
    "license": "MIT",
    "plugin_type": "tool",
    "permissions": ["read_files", "network_access"],
    "dependencies": [
      {"name": "other-plugin", "version": "^1.0.0", "optional": false}
    ],
    "min_app_version": "0.1.0",
    "tags": ["productivity", "automation"]
  }
}
```

## Creating a Plugin

### Tool Plugin

```python
from app.plugins.system import PluginInterface, PluginManifest, PluginMetadata, PluginType

class MyToolPlugin(PluginInterface):
    async def initialize(self):
        # Setup resources
        pass
    
    async def shutdown(self):
        # Cleanup
        pass
    
    async def health_check(self):
        return PluginHealth(healthy=True)
    
    def get_tools(self):
        return [
            {
                "name": "my_tool",
                "description": "Does something useful",
                "handler": self.handle_tool,
            }
        ]
    
    async def handle_tool(self, **kwargs):
        return {"result": "success"}
```

### Using the Decorator

```python
from app.plugins.system import plugin, ToolPluginInterface

@plugin("my-plugin", "1.0.0", "tool")
class MyPlugin(ToolPluginInterface):
    ...
```

## Plugin Manager

### Basic Operations

```python
from app.plugins.system import get_plugin_manager

manager = get_plugin_manager()

# Register a plugin
manager.register_plugin(manifest, instance)

# Enable plugin
await manager.enable_plugin("plugin-id")

# Disable plugin
await manager.disable_plugin("plugin-id")

# Hot reload
await manager.reload_plugin("plugin-id")

# Uninstall
await manager.uninstall_plugin("plugin-id")
```

### Loading from Directory

```python
from pathlib import Path

plugin_dir = Path("/path/to/plugins/my-plugin")
await manager.load_from_directory(plugin_dir)
```

### Loading All Plugins

```python
await manager.load_all_plugins()  # From plugins directory
```

## Permissions

### Available Permissions

| Permission | Description |
|------------|-------------|
| `read_files` | Read from filesystem |
| `write_files` | Write to filesystem |
| `execute_code` | Run code |
| `network_access` | Make HTTP requests |
| `web_search` | Search the web |
| `execute_commands` | Run shell commands |
| `access_secrets` | Access secrets |
| `access_memory` | Access memory store |
| `access_sessions` | Access sessions |
| `manage_plugins` | Manage other plugins |

### Permission Checking

```python
# Set active permissions
manager.set_active_permissions({Permission.READ_FILES, Permission.NETWORK_ACCESS})

# Check permission
if manager.check_permission(Permission.WRITE_FILES):
    write_file()

# Check plugin permissions
if manager.check_plugin_permissions("plugin-id", [Permission.READ_FILES]):
    proceed()
```

## Dependencies

### Declaring Dependencies

```python
metadata = PluginMetadata(
    id="my-plugin",
    name="My Plugin",
    version="1.0.0",
    plugin_type=PluginType.TOOL,
    dependencies=[
        Dependency(name="base-plugin", version="^1.0.0", optional=False),
        Dependency(name="optional-plugin", version="^2.0.0", optional=True),
    ],
)
```

### Automatic Resolution

```python
# Dependencies are checked automatically when loading
await manager.load_plugin("my-plugin")
# Raises DependencyError if requirements not met
```

## Versioning

### Semantic Versioning

```python
from app.plugins.system import Version

v = Version.parse("1.2.3")
print(v)  # "1.2.3"

# Check compatibility
v1 = Version.parse("1.3.0")
v2 = Version.parse("1.2.0")
assert v1.is_compatible(v2)  # True (1.3.0 >= 1.2.0)
```

### Version Requirements

```
^1.0.0  - Compatible (>= 1.0.0, < 2.0.0)
~1.0.0  - Patch level (>= 1.0.0, < 1.1.0)
1.0.0   - Exact match
>=1.0.0 - Minimum version
```

## Hot Loading

### File Watching

```python
# Plugins are reloaded automatically when files change
# Or manually reload:
await manager.reload_plugin("plugin-id")
```

### Lifecycle Hooks

```python
manager.add_hook("before_load", my_callback)
manager.add_hook("after_load", my_callback)
manager.add_hook("before_unload", my_callback)
manager.add_hook("after_unload", my_callback)
```

## Marketplace

### Remote Marketplace

```python
from app.plugins.system import get_marketplace

marketplace = get_marketplace()

# Search
results = await marketplace.search(query="github", plugin_type="tool")

# Get listing
listing = await marketplace.get_listing("plugin-id")

# Install
result = await marketplace.download_plugin("plugin-id", version="1.0.0")
```

### Local Marketplace (Development)

```python
from app.plugins.system import LocalMarketplace

marketplace = LocalMarketplace("/path/to/marketplace")

# Add plugin
marketplace.add_plugin(manifest, files={"plugin.py": code})

# List plugins
plugins = marketplace.list_all()

# Get plugin
manifest = marketplace.get_manifest("plugin-id")
```

## REST API

### Plugin Management

```bash
# List plugins
GET /api/v1/plugins

# Get plugin
GET /api/v1/plugins/{plugin_id}

# Enable plugin
POST /api/v1/plugins/{plugin_id}/enable

# Disable plugin
POST /api/v1/plugins/{plugin_id}/disable

# Reload plugin (hot loading)
POST /api/v1/plugins/{plugin_id}/reload

# Uninstall
DELETE /api/v1/plugins/{plugin_id}
```

### Health & Exports

```bash
# Health check
GET /api/v1/plugins/{plugin_id}/health

# Get exports
GET /api/v1/plugins/{plugin_id}/exports

# All exports
GET /api/v1/plugins/exports/all

# All health
GET /api/v1/plugins/health/all
```

### Marketplace

```bash
# Search
GET /api/v1/plugins/marketplace/search?q=github&type=tool

# Featured
GET /api/v1/plugins/marketplace/featured

# Install
POST /api/v1/plugins/marketplace/install/{plugin_id}
```

## Exports

### Plugin Exports

```python
class MyPlugin(ToolPluginInterface):
    def _create_export(self):
        return PluginExport(
            tools=[
                {"name": "tool1", "handler": self.tool1},
            ],
            agents=[
                {"name": "agent1", "type": "custom"},
            ],
            workflows=[
                {"name": "workflow1", "steps": [...]},
            ],
            api_routes=[
                {"path": "/api/my-plugin", "handler": self.handle_api},
            ],
        )
```

### Getting Exports

```python
# Single plugin
exports = manager.get_exports("plugin-id")

# All plugins combined
all_exports = manager.get_all_exports()
```

## Plugin Directory Structure

```
plugins/
└── my-plugin/
    ├── plugin.json       # Manifest
    ├── plugin.py        # Main code
    ├── requirements.txt # Dependencies
    └── assets/
        └── icon.png
```

## Best Practices

1. **Use semantic versioning**
2. **Declare dependencies explicitly**
3. **Request minimal permissions**
4. **Implement health checks**
5. **Handle errors gracefully**
6. **Clean up on shutdown**

## Example: Complete Plugin

```python
# plugin.py
from app.plugins.system import (
    PluginInterface,
    PluginManifest,
    PluginMetadata,
    PluginType,
    Permission,
    PluginHealth,
    PluginExport,
    plugin,
)

@plugin("example-tool", "1.0.0", "tool")
class ExampleToolPlugin(PluginInterface):
    def __init__(self, manifest):
        super().__init__(manifest)
        self._cache = {}
    
    async def initialize(self):
        print(f"Initializing {self.manifest.metadata.name}")
    
    async def shutdown(self):
        print(f"Shutting down {self.manifest.metadata.name}")
        self._cache.clear()
    
    async def health_check(self) -> PluginHealth:
        return PluginHealth(healthy=True, message="OK")
    
    def _create_export(self) -> PluginExport:
        return PluginExport(
            tools=[
                {
                    "name": "example_tool",
                    "description": "An example tool",
                    "parameters": {"type": "object", "properties": {}},
                    "handler": self.example_tool,
                }
            ],
        )
    
    async def example_tool(self, **kwargs):
        return {"result": "Hello from example tool!"}
```

```json
// plugin.json
{
  "manifest_version": "1.0",
  "metadata": {
    "id": "example-tool",
    "name": "Example Tool",
    "version": "1.0.0",
    "description": "An example tool plugin",
    "author": "Developer",
    "plugin_type": "tool",
    "permissions": ["read_files"],
    "dependencies": [],
    "min_app_version": "0.1.0"
  }
}
```
