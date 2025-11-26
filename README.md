# SMS REST Server

A comprehensive REST API service for sending SMS messages via GSM modem using the gammu library. Production-ready Python Flask application with systemd integration for Linux systems.

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![Flask](https://img.shields.io/badge/flask-2.3+-green.svg)
![Version](https://img.shields.io/badge/version-1.1.21-brightgreen.svg)

## Features

- ✅ **REST API**: Send SMS messages via HTTP POST with JSON request/response
- ✅ **Inbox Retrieval**: GET /inbox endpoint to read all received SMS messages
- ✅ **Grafana Integration**: Webhook endpoint for Grafana alertmanager notifications
- ✅ **Authentication**: Secure Basic HTTP authentication with bcrypt hashing
- ✅ **Async Reply Tracking**: Queue-based delivery with background GSM polling keeps HTTP requests non-blocking while still capturing replies
- ✅ **Message Validation**: Automatic length validation and truncation (160 chars)
- ✅ **Auto-Detection**: Intelligent GSM modem port detection with smart config validation
- ✅ **Phone Number Normalization**: Support for +52 Mexican country code variations
- ✅ **Persistent Connections**: Eliminates modem re-initialization overhead
- ✅ **Standardized Logging**: [PREFIX] format for easy parsing and monitoring
- ✅ **Automatic Cleanup**: SMS inbox cleanup on startup prevents old message confusion
- ✅ **Health Monitoring**: Built-in health check endpoint for service monitoring
- ✅ **System Integration**: Complete systemd service installation/uninstallation with proper signal handling
- ✅ **Production Ready**: Comprehensive error handling with machine-readable error codes
- ✅ **Config Preservation**: Smart reinstallation preserves existing settings and credentials

## Quick Start

### Installation

**One-Command Installation** (Recommended):
```bash
sudo python3 sms-rest-server.py --install
```

This will:
- Check all system prerequisites and dependencies
- Install service to `/usr/local/SMS-REST-Server/`
- Create systemd service file `/etc/systemd/system/sms-rest-server.service`
- Create data directory `/var/lib/sms-rest-server/`
- Create config file `/etc/default/sms-rest-server`
- Prompt you to create an htpasswd file (no credentials exist until you run `--create-htpasswd/--update-htpasswd`)

After installation, start the service:
```bash
sudo systemctl start sms-rest-server
sudo systemctl enable sms-rest-server  # Enable auto-start on boot
```

**Manual Installation**:
```bash
git clone https://github.com/geekinsanemx/SMS-REST-Server.git
cd SMS-REST-Server
pip install -r requirements.txt
python3 sms-rest-server.py --port 18180 --htpasswd /tmp/htpasswd --debug
```

### Usage

**Send SMS (Basic)** *(use any credentials stored in your htpasswd file)*:
```bash
curl -X POST http://localhost:18180/ \
     -u <user>:<password> \
     -H "Content-Type: application/json" \
     -d '{"number": "1234567890", "message": "Hello from SMS REST API"}'
```

**Send SMS with Reply Waiting**:
```bash
curl -X POST http://localhost:18180/ \
     -u <user>:<password> \
     -H "Content-Type: application/json" \
     -d '{"number": "1234567890", "message": "Please reply", "reply": true, "timeout": 120}'
```

**Health Check**:
```bash
curl http://localhost:18180/health
```

**Check Message Status**:
```bash
curl -u <user>:<password> "http://localhost:18180/status?message_id=<uuid>"
```

**Retrieve Inbox**:
```bash
# Get all messages
curl -u <user>:<password> "http://localhost:18180/inbox"

# Get only unread messages
curl -u <user>:<password> "http://localhost:18180/inbox?unread"

# Get and delete after reading
curl -u <user>:<password> "http://localhost:18180/inbox?unread&delete"

# Limit results
curl -u <user>:<password> "http://localhost:18180/inbox?limit=10"
```

## API Reference

### Endpoints

| Method | Endpoint | Auth Required | Description |
|--------|----------|---------------|-------------|
| POST | `/` | ✅ Yes | Queue an SMS send-and-reply job |
| GET | `/status` | ✅ Yes | Retrieve latest status for a `message_id` |
| GET | `/inbox` | ✅ Yes | Retrieve all SMS messages from modem inbox |
| POST | `/api/v1/alerts` | ❌ No | Grafana alertmanager webhook (if enabled) |
| GET | `/health` | ❌ No | Service health check |

### Request Format

**POST /** - Send SMS

```json
{
  "number": "1234567890",     // Required: Phone number (10 digits, optional +52 prefix)
  "message": "Your message",  // Required: SMS text (max 160 chars, auto-truncated)
  "reply": false,             // Optional: Wait for reply (default: false)
  "timeout": 60               // Optional: Reply timeout in seconds (default: 60, max: 600)
}
```

**Note**: Field names are **case-insensitive** (`Number`, `MESSAGE`, `Reply` all work).

**Phone Number Formats**:
- `1234567890` - 10 digits (standard)
- `+521234567890` - With +52 country code (Mexico)

**GET /inbox** - Retrieve SMS Messages

Query Parameters:
- `?unread` or `?unread_only=true` - Only return unread messages
- `?delete` or `?delete_after=true` - Delete messages after retrieval
- `?limit=N` - Limit number of messages returned

Response:
```json
{
  "status": "success",
  "count": 2,
  "messages": [
    {
      "number": "+521234567890",
      "datetime": "2025-11-26T07:30:00",
      "text": "Message content",
      "state": "UnRead",
      "location": 1,
      "folder": 0
    }
  ],
  "timestamp": "2025-11-26T07:35:00Z"
}
```

**POST /api/v1/alerts** - Grafana Webhook

Requires `GRAFANA_WEBHOOK=1` in config file. Accepts Grafana alertmanager webhook format.

Request (Grafana sends JSON array of alerts):
```json
[
  {
    "labels": {
      "alertname": "HighCPU",
      "number": "+521234567890"
    },
    "annotations": {
      "summary": "CPU usage above 80%"
    },
    "endsAt": "0001-01-01T00:00:00Z"
  }
]
```

Response:
```json
{
  "status": "completed",
  "total_alerts": 1,
  "successful": 1,
  "failed": 0,
  "results": [
    {
      "alert_index": 1,
      "alert_name": "HighCPU",
      "phone_number": "+521234567890",
      "message_id": "uuid",
      "status": "FIRING",
      "success": true
    }
  ],
  "timestamp": "2025-11-26T07:35:00Z"
}
```

### Response Format (v1.1.10)

`POST /` responds immediately with the queued job metadata:

```json
{
  "status": "queued",
  "message_id": "2df672c9-b8b6-4670-bd23-3e4bc427d986",
  "timestamp": "2025-11-14T22:25:28Z",
  "to": "1234567890",
  "from": "admin",
  "message": "Please reply",
  "reply": null
}
```

Use `GET /status?message_id=<uuid>` to observe transitions to `sent`, `failed`, `replied`, or `timeout`. When a reply arrives, the `reply` object contains the modem text, receipt timestamp, and `elapsed_seconds`; when the timeout window expires, `reply` remains `null` and the status is `timeout`.

### Architecture Notes

- HTTP handlers are fire-and-leave; the GSM worker thread is the only component that talks to the modem. It pulls jobs from an internal queue, polls for replies every `REPLY_POLL_INTERVAL` seconds, and enforces `SMS_REPLY_TIMEOUT` plus `TIMEOUT_SWEEP_INTERVAL` sweeps.
- All modem hygiene (startup inbox cleanup, reply deletion, final teardown) uses python-gammu directly—no `gammu deleteallsms` subprocesses.
- Runtime knobs such as `SMS_REPLY_TIMEOUT`, `REPLY_POLL_INTERVAL`, `TIMEOUT_SWEEP_INTERVAL`, `QUEUE_WAIT_SECONDS`, and `MESSAGE_RETENTION_SECONDS` live in `/etc/default/sms-rest-server` (or any config passed via `--config`).

**Message truncated** (auto-truncation at 160 chars):
```json
{
  "status": "sent",
  "message_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2025-11-14T07:40:00Z",
  "to": "1234567890",
  "from": "admin",
  "message": "Truncated message content (160 chars)...",
  "meta": {
    "truncated": true,
    "original_length": 200,
    "sent_length": 160
  }
}
```

**Error responses**:
```json
{
  "status": "failed",
  "message_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2025-11-14T07:40:00Z",
  "to": "1234567890",
  "from": "admin",
  "message": "Test message",
  "error_code": "MODEM_TIMEOUT",
  "error_message": "Timeout while sending SMS to 1234567890: Operation timed out"
}
```

**Error Codes**:
- `AUTHENTICATION_REQUIRED` - Missing or invalid credentials
- `INVALID_CONTENT_TYPE` - Content-Type must be application/json
- `INVALID_JSON` - Request body must contain valid JSON
- `MISSING_REQUIRED_FIELDS` - Missing required fields (number or message)
- `INVALID_PHONE_NUMBER` - Phone number format invalid
- `INVALID_TIMEOUT_VALUE` - Timeout must be between 1 and 600 seconds
- `INVALID_TIMEOUT_FORMAT` - Timeout must be a valid integer
- `MODEM_NOT_AVAILABLE` - Could not establish connection to GSM modem
- `MODEM_TIMEOUT` - Timeout while sending SMS
- `MODEM_DEVICE_ERROR` - Device not found
- `MODEM_PERMISSION_ERROR` - Permission denied
- `SEND_FAILED` - Failed to send SMS

## Command Line Options

```
Usage: sms-rest-server.py [OPTIONS]

Options:
  --port PORT              Port to run the service on (default: 18180)
  --htpasswd FILE          Path to htpasswd file for authentication
  --device DEVICE          Specific modem device (e.g., /dev/ttyUSB0)
  --config FILE            Load configuration from file
  --debug                  Enable debug mode with detailed logging
  --install                Install service system-wide with prerequisites check
  --uninstall              Uninstall service (prompts for data/user removal)
  --create-htpasswd FILE USER [PASS]  Create/update htpasswd entry (prompts for PASS if omitted)
  --update-htpasswd FILE USER [PASS]  Alias for --create-htpasswd
  --help                   Show help message
```

### Configuration File

Default location: `/etc/default/sms-rest-server`

Format: `KEY=VALUE` (shell-style)

Supported keys:
- `PORT` - Service port (default: 18180)
- `HTPASSWD_FILE` - Authentication file path
- `DEVICE` - Modem device path (optional, auto-detect if not set)
- `DEBUG` - Enable debug mode (true/false)
- `SMS_REPLY_TIMEOUT` - Reply timeout in seconds (default: 60)
- `REPLY_POLL_INTERVAL` - Polling interval in seconds (default: 5)
- `TIMEOUT_SWEEP_INTERVAL` - Timeout sweep interval (default: 5)
- `QUEUE_WAIT_SECONDS` - Queue wait seconds (default: 1)
- `MESSAGE_RETENTION_SECONDS` - Message retention window (default: 86400)
- `GRAFANA_WEBHOOK` - Enable Grafana webhook endpoint (0/1, default: 0)
- `GRAFANA_DEFAULT_NUMBER` - Default phone for alerts without number label
- `GRAFANA_MESSAGE_MAX_LENGTH` - Max message length for alerts (default: 150)

**Priority**: CLI arguments > --config file > /etc/default/sms-rest-server > defaults

Example configuration:
```bash
PORT=18180
HTPASSWD_FILE=/var/lib/sms-rest-server/htpasswd
DEVICE=/dev/ttyUSB0
# DEBUG=true

# Grafana webhook integration
GRAFANA_WEBHOOK=1
GRAFANA_DEFAULT_NUMBER=+521234567890
GRAFANA_MESSAGE_MAX_LENGTH=150
```

## System Service Management

After installation with `--install`:

```bash
# Service Control
sudo systemctl start sms-rest-server      # Start the service
sudo systemctl stop sms-rest-server       # Stop the service
sudo systemctl restart sms-rest-server    # Restart the service
sudo systemctl status sms-rest-server     # Check service status

# Auto-start Control
sudo systemctl enable sms-rest-server     # Enable auto-start on boot
sudo systemctl disable sms-rest-server    # Disable auto-start

# Logs and Monitoring
sudo journalctl -u sms-rest-server -f     # View real-time logs
sudo journalctl -u sms-rest-server --since "1 hour ago"  # Recent logs
```

### Log Output Format

The service uses standardized logging with prefixes for easy parsing:

- `[MODEM]` - Modem initialization and connection status
- `[CLEAN]` - SMS inbox cleanup operations
- `[SMS]` - SMS sending operations with detailed tracking
- `[REPLY]` - Reply waiting and received messages

Example log output:
```
[MODEM] Initializing connection...
[MODEM] Using existing config: /dev/ttyUSB2 (Sierra Wireless, Incorporated)
[CLEAN] Clearing SMS inbox...
[CLEAN] SMS inbox cleaned
[MODEM] Re-initializing for service...
[MODEM] Connection established
[SMS] 2025-11-14 01:40:00 | admin (127.0.0.1) → 1234567890 | SUCCESS (reply expected) | 'Test'
[REPLY] 2025-11-14 01:40:02 | Waiting for reply from 1234567890 | 60s timeout
[REPLY] 2025-11-14 01:40:10 | Reply from 1234567890 | 10s | 'OK'
```

## Authentication

The service uses Basic HTTP authentication with bcrypt password hashing.

### Creating Users

Create htpasswd file with the `--create-htpasswd` flag (you will be prompted for the password if it is omitted):

```bash
# Create new htpasswd file (interactive password prompt)
python3 sms-rest-server.py --create-htpasswd /var/lib/sms-rest-server/htpasswd admin

# Add or update additional users (alias works the same way)
python3 sms-rest-server.py --update-htpasswd /var/lib/sms-rest-server/htpasswd newuser
```

**Authentication note**: you must create an htpasswd file with `--create-htpasswd`/`--update-htpasswd` (the command prompts for a password; no credentials are shipped)

## Hardware Requirements

- **GSM Modem**: USB-connected GSM modem with SMS capability
- **SIM Card**: Active SIM card with SMS service enabled
- **Operating System**: Linux with systemd support
- **Python**: Version 3.8 or higher
- **Permissions**: User in 'dialout' group or root privileges
- **USB Connection**: Stable USB connection for modem

## Installation Paths

After system installation:
- **Installation directory**: `/usr/local/SMS-REST-Server/`
- **Service script**: `/usr/local/SMS-REST-Server/sms-rest-server.py`
- **Requirements**: `/usr/local/SMS-REST-Server/requirements.txt`
- **Service file**: `/etc/systemd/system/sms-rest-server.service`
- **Config file**: `/etc/default/sms-rest-server`
- **Data directory**: `/var/lib/sms-rest-server/`
- **Auth file**: `/var/lib/sms-rest-server/htpasswd`

## Dependencies

```
Flask>=2.3.0
Werkzeug>=2.3.0
bcrypt>=4.0.0
pyserial>=3.5
python-gammu>=3.2
```

Install with: `pip install -r requirements.txt`

System packages (Debian/Ubuntu):
```bash
sudo apt-get install python3-gammu python3-flask python3-bcrypt python3-serial
```

## Modem Setup

The service automatically handles modem initialization:

1. Validates existing gammu configuration (`~/.gammurc`) if present
2. Stops ModemManager service if modem detection is needed
3. Auto-detects modem port (`/dev/ttyUSB*`) only if config is invalid
4. Creates/updates gammu configuration
5. Initializes a persistent modem connection and clears the inbox via python-gammu (prevents old message confusion)
6. Hands off that live connection to the GSM worker (no re-init loops)

**Smart Configuration**:
- Reuses existing valid gammurc (no port scanning needed)
- Only auto-detects if configuration doesn't exist or fails validation
- Persistent connection eliminates re-initialization overhead

## Security

- **Authentication**: Basic HTTP Auth with bcrypt password hashing
- **Credential Management**: Run `python3 sms-rest-server.py --create-htpasswd /var/lib/sms-rest-server/htpasswd admin` (or `--update-htpasswd`) before starting the service and keep the resulting htpasswd file private
- **HTTPS Recommendation**: Use reverse proxy (nginx/Apache) with SSL/TLS
- **Network Security**: Limit access to trusted IP ranges
- **File Permissions**: htpasswd file stored with 600 permissions

## Troubleshooting

### Common Issues

**Permission Denied**:
```bash
sudo usermod -a -G dialout $USER
# Then logout/login or reboot
```

**Modem Not Detected**:
```bash
ls -la /dev/ttyUSB*  # Check USB devices
sudo systemctl stop ModemManager.service  # Stop conflicting service
```

**Service Won't Start**:
```bash
sudo journalctl -u sms-rest-server -f  # Check logs
sudo systemctl daemon-reload           # Reload after config changes
```

### Debug Mode

Enable detailed logging for troubleshooting:
```bash
python3 sms-rest-server.py --port 18180 --htpasswd /path/to/htpasswd --debug
```

Debug mode provides:
- SMS error details and stack traces
- Reply checking progress with message counts
- Timestamp comparison details for reply filtering
- Modem termination and re-initialization tracking

## Technical Details

### SMS Reply Handling Architecture

The service uses a proven three-phase pattern for reply detection:

1. **Collection Phase**: `get_sms_with_locations()` iterates through complete inbox
2. **Processing Phase**: `check_gps_device_reply()` filters messages by phone + timestamp
3. **Action Phase**: Delete matched message and return result

This ensures **ALL messages are checked** (not just the first one) and prevents processing during iteration.

### Timestamp Handling

- SMS timestamps from modem are in **local time** (not UTC)
- `sent_timestamp` uses `datetime.now()` (local time, no timezone)
- Both timestamps kept as naive datetime for accurate comparison
- API response timestamps use ISO-8601 format: `YYYY-MM-DDTHH:MM:SS`

## Version History

**v1.1.21 (2025-11-26)**
- Added GET /inbox endpoint for retrieving SMS messages from modem
- Query parameters: ?unread, ?delete, ?limit=N
- Short and long parameter forms supported

**v1.1.20 (2025-11-15)**
- Config and credential preservation during reinstallation
- Prompts to preserve or override previous settings
- Merges old config values into new template

**v1.1.19 (2025-11-15)**
- Added Grafana webhook integration (POST /api/v1/alerts)
- Processes Grafana alertmanager webhook JSON arrays
- Message format: [FIRING/RESOLVED] AlertName: content
- Configurable with GRAFANA_WEBHOOK, GRAFANA_DEFAULT_NUMBER

**v1.1.18 (2025-11-15)**
- Fixed htpasswd file ownership during installation
- Automatic ownership to sms-rest-server:sms-rest-server

**v1.1.17 (2025-11-15)**
- Fixed system user home directory for .gammurc config
- Service runs as sms-rest-server user (not root)

**v1.1.16 (2025-11-15)**
- Added --uninstall function to remove service
- Prompts for data directory and system user removal

**v1.1.8 (2025-11-14)**
- CRITICAL: Fixed timezone bug - removed 'Z' suffix from local time timestamps
- Removed dead code (unused SMS_CHECK_INTERVAL variable)

**v1.1.7 (2025-11-14)**
- CRITICAL FIX: SMS reply detection now processes ALL inbox messages
- Standardized logging output with [PREFIX] format

**v1.0.0 (2025-08-25)**
- Initial release with systemd integration

## License

MIT License - See LICENSE file for details.

## Author

Created by [geekinsanemx](https://github.com/geekinsanemx)

## Support

- **Issues**: Report bugs via GitHub Issues
- **Development**: See `CLAUDE.md` for development guidance

---

**Production Note**: This service is designed for production use. Ensure proper security measures (HTTPS, firewall, secure passwords) before deploying in production environments.
