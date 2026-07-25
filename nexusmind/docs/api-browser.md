# Browser Automation API Documentation

The browser automation module provides a complete API for controlling headless browsers using Playwright. It supports Chromium, Firefox, and WebKit browsers with full automation capabilities.

## Quick Start

```python
from app.tools.browser import BrowserTool, BrowserConfig

# Create tool
tool = BrowserTool()

# Launch browser
session = await tool.launch_browser(BrowserConfig(headless=True))

# Open page
page = await tool.open_page(session.session_id, "https://example.com")

# Take screenshot
result = await tool.screenshot(session.session_id)

# Cleanup
await tool.close_session(session.session_id)
await tool.stop()
```

## Configuration

### BrowserConfig

```python
from app.tools.browser import BrowserConfig, BrowserType

config = BrowserConfig(
    browser_type=BrowserType.CHROMIUM,  # chromium, firefox, webkit
    headless=True,                      # Run in headless mode
    viewport_width=1920,                # Viewport width
    viewport_height=1080,               # Viewport height
    user_agent="Custom User Agent",     # Custom user agent
    proxy="http://proxy:8080",          # Proxy server
    timeout=30000,                      # Timeout in ms
    ignore_https_errors=False,           # Ignore SSL errors
)
```

## REST API Endpoints

### Launch Browser

```bash
POST /api/v1/browser/sessions
Content-Type: application/json

{
    "browser_type": "chromium",
    "headless": true,
    "viewport_width": 1920,
    "viewport_height": 1080
}
```

### List Sessions

```bash
GET /api/v1/browser/sessions
```

### Get Session

```bash
GET /api/v1/browser/sessions/{session_id}
```

### Close Session

```bash
DELETE /api/v1/browser/sessions/{session_id}
```

### Open Page

```bash
POST /api/v1/browser/sessions/{session_id}/pages
Content-Type: application/json

{
    "url": "https://example.com"
}
```

### Click Element

```bash
POST /api/v1/browser/sessions/{session_id}/click
Content-Type: application/json

{
    "selector": "#button",
    "options": {
        "button": "left",
        "click_count": 1,
        "delay": 0
    }
}
```

### Fill Input

```bash
POST /api/v1/browser/sessions/{session_id}/fill
Content-Type: application/json

{
    "selector": "input[name='email']",
    "value": "user@example.com"
}
```

### Login

```bash
POST /api/v1/browser/sessions/{session_id}/login
Content-Type: application/json

{
    "username": "user@example.com",
    "password": "secret",
    "login_url": "https://example.com/login"
}
```

### Take Screenshot

```bash
POST /api/v1/browser/sessions/{session_id}/screenshot
Content-Type: application/json

{
    "full_page": false,
    "type": "png"
}
```

Response:
```json
{
    "success": true,
    "session_id": "...",
    "action": "screenshot",
    "data": {
        "image": "base64_encoded_image",
        "format": "png"
    }
}
```

### Execute JavaScript

```bash
POST /api/v1/browser/sessions/{session_id}/execute
Content-Type: application/json

{
    "script": "document.title"
}
```

### Extract Content

```bash
GET /api/v1/browser/sessions/{session_id}/content?selector=article
```

### Get Console Logs

```bash
GET /api/v1/browser/sessions/{session_id}/console
```

### Upload File

```bash
POST /api/v1/browser/sessions/{session_id}/upload
Content-Type: application/json

{
    "selector": "input[type='file']",
    "file_path": "/path/to/file.txt"
}
```

## BrowserTool Methods

### Launch & Session Management

| Method | Description |
|--------|-------------|
| `launch_browser(config)` | Launch new browser session |
| `close_session(session_id)` | Close a session |
| `open_page(session_id, url)` | Open URL in session |
| `get_session_info(session_id)` | Get session info |
| `list_sessions()` | List all sessions |

### Page Interactions

| Method | Description |
|--------|-------------|
| `click(session_id, selector, options)` | Click element |
| `fill(session_id, selector, value, options)` | Fill input field |
| `login(session_id, credentials)` | Perform login |
| `navigate(session_id, url)` | Navigate to URL |

### Screenshot & Downloads

| Method | Description |
|--------|-------------|
| `screenshot(session_id, options)` | Take screenshot |
| `download_file(session_id, url, filename)` | Download file |
| `upload_file(session_id, selector, path)` | Upload file |

### JavaScript & Content

| Method | Description |
|--------|-------------|
| `execute_javascript(session_id, script)` | Run JS code |
| `extract_content(session_id, selector)` | Get page content |

### Console Logs

| Method | Description |
|--------|-------------|
| `get_console_logs(session_id)` | Get browser console |
| `clear_console_logs(session_id)` | Clear console logs |

## Usage Examples

### Basic Navigation

```python
from app.tools.browser import BrowserTool, BrowserConfig

tool = BrowserTool()

# Launch browser
session = await tool.launch_browser(BrowserConfig(headless=True))

# Open page
await tool.open_page(session.session_id, "https://news.ycombinator.com")

# Get page title
result = await tool.execute_javascript(session.session_id, "document.title")
print(f"Title: {result.result}")

# Cleanup
await tool.close_session(session.session_id)
await tool.stop()
```

### Form Filling

```python
# Fill form
await tool.fill(session.session_id, "input[name='email']", "test@example.com")
await tool.fill(session.session_id, "input[name='password']", "password123")

# Submit
await tool.click(session.session_id, "button[type='submit']")
```

### Screenshot

```python
# Full page screenshot
result = await tool.screenshot(
    session.session_id,
    ScreenshotOptions(full_page=True, type="jpeg", quality=85)
)

# Save base64 to file
import base64
with open("screenshot.jpg", "wb") as f:
    f.write(base64.b64decode(result.data["image"]))
```

### Login Flow

```python
from app.tools.browser import LoginCredentials

creds = LoginCredentials(
    username="user@example.com",
    password="password",
    login_url="https://example.com/login",
    username_selector="input[name='username']",
    password_selector="input[name='password']",
    submit_selector="button.login",
)

result = await tool.login(session.session_id, creds)
if result.success:
    print("Logged in successfully!")
```

### Extract Data

```python
# Get all article titles
content = await tool.extract_content(session.session_id, "article h2")

# Print titles
for element in content.text.split("\n"):
    if element.strip():
        print(element)
```

### Handle Console Logs

```python
# Execute code that logs
await tool.execute_javascript(session.session_id, """
    console.log('Page loaded');
    console.warn('Slow resource');
    console.error('Failed to load image');
""")

# Get logs
logs = await tool.get_console_logs(session.session_id)
for log in logs:
    print(f"[{log.type}] {log.text}")
```

### File Upload

```python
await tool.upload_file(
    session.session_id,
    "input[type='file']",
    "/path/to/document.pdf"
)
```

## Error Handling

```python
from app.tools.browser import BrowserTool, BrowserConfig

tool = BrowserTool()

try:
    session = await tool.launch_browser(BrowserConfig(headless=True))
    
    # Try to click non-existent element
    result = await tool.click(session.session_id, "#nonexistent")
    if not result.success:
        print(f"Click failed: {result.error}")
    
    # Try to navigate to invalid URL
    page = await tool.open_page(session.session_id, "invalid://url")
    
except Exception as e:
    print(f"Error: {e}")
    
finally:
    await tool.stop()
```

## Browser Types

### Chromium (Default)

```python
config = BrowserConfig(browser_type=BrowserType.CHROMIUM)
```

### Firefox

```python
config = BrowserConfig(browser_type=BrowserType.FIREFOX)
```

### WebKit

```python
config = BrowserConfig(browser_type=BrowserType.WEBKIT)
```

## Options

### ClickOptions

```python
options = ClickOptions(
    button="left",      # left, right, middle
    click_count=1,      # 1 for single, 2 for double
    delay=100,          # ms delay between down/up
    position_x=100,     # click at x coordinate
    position_y=100,     # click at y coordinate
)
```

### FillOptions

```python
options = FillOptions(
    delay=50,            # ms between keystrokes
    force=False,         # bypass actionability checks
)
```

### ScreenshotOptions

```python
options = ScreenshotOptions(
    full_page=False,     # capture entire page
    path=None,           # save to file
    type="png",          # png or jpeg
    quality=90,          # for jpeg (1-100)
)
```

## Best Practices

1. **Always cleanup**: Close sessions and stop tool when done
2. **Use timeouts**: Set appropriate timeouts for slow pages
3. **Handle errors**: Check result.success before accessing data
4. **Headless mode**: Use headless=True for production
5. **Viewport sizing**: Set viewport to match your needs
6. **Proxy rotation**: Use proxies for high-volume scraping

## Environment Variables

```bash
# Browser automation uses system browsers
# No specific environment variables required
```
