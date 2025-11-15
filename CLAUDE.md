# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **SMS REST Server** project (v1.1.7) that provides a comprehensive REST API service for sending SMS messages via GSM modem using the gammu library. It's a production-ready Python Flask application with systemd integration for Linux systems.

## Core Architecture

### Main Components

- **`sms-rest-server.py`** - The main Flask REST API server with comprehensive SMS functionality
- **Auth helper** (`sms-rest-server.py --create-htpasswd/--update-htpasswd`) - manage bcrypt-hashed authentication files
- **`test_ctrl_c.py`** - Signal handling test utility
- **`requirements.txt`** - Python dependencies file
- **`SMS_REST_README.md`** - Complete user documentation and API reference
- **`CLAUDE.md`** - This file (project guidance for Claude Code)

### Technology Stack

- **Framework**: Flask (Python 3.8+)
- **SMS Backend**: python-gammu library for GSM modem communication
- **Authentication**: Basic HTTP Auth with bcrypt password hashing
- **Service Management**: systemd integration for Linux systems
- **Communication**: REST API with JSON request/response format

## Key Features

- Send SMS via REST API with standardized JSON response format
- Automatic GSM modem port detection with smart config validation
- ModemManager conflict handling (automatic stop/start)
- SMS reply waiting with complete inbox scanning (prevents missing replies)
- Message length validation and auto-truncation (160 chars)
- Phone number normalization for Mexican +52 country code
- Persistent modem connections (eliminates re-initialization overhead)
- Automatic SMS inbox cleanup on startup (prevents old message confusion)
- Standardized logging output with [PREFIX] format for easy parsing
- Comprehensive error handling with machine-readable error codes
- Health check endpoint for monitoring
- Config file support (/etc/default/sms-rest-server)

## Common Development Tasks

### Running the Service

```bash
# Development mode with debug
python3 sms-rest-server.py --port 18180 --htpasswd /path/to/htpasswd --debug

# Production mode with specific device
python3 sms-rest-server.py --port 18180 --htpasswd /path/to/htpasswd --device /dev/ttyUSB0

# Using config file
python3 sms-rest-server.py --config /etc/default/sms-rest-server
```

### Installing as System Service

```bash
# Install with prerequisites check and systemd integration
sudo python3 sms-rest-server.py --install
```

### Creating Authentication Files

```bash
# Create new htpasswd file (prompts for password twice)
python3 sms-rest-server.py --create-htpasswd /path/to/htpasswd admin

# Add additional users
python3 sms-rest-server.py --update-htpasswd /path/to/htpasswd username
```

### Testing Signal Handling

```bash
# Test Ctrl+C and signal handling
python3 test_ctrl_c.py
```

## Dependencies

Install required packages:
```bash
pip install -r requirements.txt
```

Required packages:
- Flask >= 2.3.0
- Werkzeug >= 2.3.0
- bcrypt >= 4.0.0
- pyserial >= 3.5
- python-gammu >= 3.2

System packages (Debian/Ubuntu):
```bash
sudo apt-get install python3-gammu python3-flask python3-bcrypt python3-serial
```

## Configuration

### Default Settings

- **Port**: 18180 (configurable with `--port` or config file)
- **SMS Reply Timeout**: 60 seconds (configurable with `timeout` field in request, max 600s)
- **SMS Check Interval**: 5 seconds (during reply waiting)
- **Message Length Limit**: 160 characters (auto-truncated)

### Command Line Options

- `--port PORT` - Service port (default: 18180)
- `--htpasswd FILE` - Authentication file path (required unless in config)
- `--device DEVICE` - Specific modem device (e.g., /dev/ttyUSB0)
- `--config FILE` - Load configuration from file
- `--debug` - Enable detailed logging
- `--install` - System installation with prerequisites check
- `--create-htpasswd FILE USER [PASS]` - Create/update htpasswd entries (prompts if PASS omitted)
- `--update-htpasswd FILE USER [PASS]` - Alias for the same behavior
- `--help` - Show usage information

### Configuration File

Default: `/etc/default/sms-rest-server`

Format: `KEY=VALUE` (shell-style)

Supported keys: `PORT`, `HTPASSWD_FILE`, `DEVICE`, `DEBUG`

Priority: CLI arguments > --config file > /etc/default/sms-rest-server > defaults

## API Endpoints

### POST / (Send SMS)
- **Authentication**: Basic HTTP Auth
- **Content-Type**: application/json
- **Fields** (case-insensitive):
  - `number`: Phone number (10 digits, optional +52 prefix)
  - `message`: SMS text (max 160 chars, auto-truncated)
  - `reply`: Boolean, wait for reply (optional, default: false)
  - `timeout`: Reply timeout in seconds (optional, default: 60, max: 600)

**Response Format (v1.1.7):**
- Standardized JSON with industry-standard fields
- `status`: 'sent', 'delivered', 'timeout', 'failed'
- `message_id`: UUID v4 for message tracking
- `timestamp`: ISO-8601 UTC timestamp
- `reply`: Object with `text`, `received_at`, `elapsed_seconds` (if reply requested)
- `meta`: Metadata like truncation info (if applicable)
- `error_code`: Machine-readable error code (if failed)
- `error_message`: Human-readable error description (if failed)

### GET /health (Health Check)
- Returns service status and timestamp
- No authentication required

## Hardware Requirements

- GSM modem with USB connection
- SIM card with SMS capabilities
- Linux system with systemd support
- User in 'dialout' group or root privileges
- Available USB serial port (/dev/ttyUSB*)

## System Integration

### Systemd Service
- **Installation directory**: `/usr/local/SMS-REST-Server/`
- **Service script**: `/usr/local/SMS-REST-Server/sms-rest-server.py`
- **Service file**: `/etc/systemd/system/sms-rest-server.service`
- **Config file**: `/etc/default/sms-rest-server`
- **Data directory**: `/var/lib/sms-rest-server/`
- **Auth file**: `/var/lib/sms-rest-server/htpasswd`

### Service Management Commands
```bash
sudo systemctl start sms-rest-server      # Start service
sudo systemctl stop sms-rest-server       # Stop service
sudo systemctl enable sms-rest-server     # Enable auto-start
sudo systemctl status sms-rest-server     # Check status
sudo journalctl -u sms-rest-server -f     # View logs
```

## Important Code Patterns

### Persistent Modem Connections
The service maintains a global modem connection (`global_modem`) to avoid re-initialization overhead. Always use `get_modem_connection()` to access the modem, which handles automatic reconnection if needed.

### SMS Reply Handling (CRITICAL)
**Pattern from program_gps_device.py - DO NOT MODIFY**

Three-phase architecture (NEVER process during iteration):
1. **Collection**: `get_sms_with_locations()` - Iterates through COMPLETE inbox
2. **Processing**: `check_gps_device_reply()` - Filters by phone + timestamp
3. **Action**: Delete matched message and return

**Key implementation details:**
- Uses `GetSMSStatus()` to get total message count
- Loops with `GetNextSMS()` until all messages retrieved
- Stores messages in array FIRST, processes AFTER
- Timestamp filtering: both `sent_timestamp` and SMS datetime use local time (NO timezone conversion)
- Check interval: 5 seconds (same as program_gps_device.py)

### Error Handling
SMS operations return tuples: `(success: bool, status: str, details: str)`. Always check the success flag and handle different error types (timeout, device_error, permission_error, failed).

API responses use machine-readable error codes:
- `AUTHENTICATION_REQUIRED`, `INVALID_CONTENT_TYPE`, `INVALID_JSON`
- `MISSING_REQUIRED_FIELDS`, `INVALID_PHONE_NUMBER`
- `MODEM_NOT_AVAILABLE`, `MODEM_TIMEOUT`, `MODEM_DEVICE_ERROR`
- `SEND_FAILED`

### Logging Format
Standardized output with prefixes:
- `[MODEM]` - Modem initialization/connection
- `[CLEAN]` - SMS inbox cleanup
- `[SMS]` - SMS send operations
- `[REPLY]` - Reply waiting/received

Example: `[SMS] 2025-11-14 01:40:00 | admin (127.0.0.1) → 1234567890 | SUCCESS (reply expected) | 'Test'`

### Signal Handling
Proper cleanup is implemented with signal handlers for SIGINT and SIGTERM, ensuring modem connections are terminated gracefully.

## Security Considerations

- Uses bcrypt for password hashing
- Basic HTTP authentication required
- No default credentials are shipped—operators must create htpasswd entries before running the service
- Consider HTTPS for production deployments
- Limit network access to trusted sources
