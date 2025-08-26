# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **SMS REST Server** project that provides a comprehensive REST API service for sending SMS messages via GSM modem using the gammu library. It's a production-ready Python Flask application with systemd integration for Linux systems.

## Core Architecture

### Main Components

- **`sms_rest_service.py`** - The main Flask REST API server (1540+ lines) with comprehensive SMS functionality including persistent modem connections, automatic port detection, and enhanced error handling
- **`create_htpasswd.py`** - Simple bcrypt password hashing utility for authentication file creation
- **`test_ctrl_c.py`** - Signal handling test utility for verifying Ctrl+C behavior
- **`requirements.txt`** - Python dependencies (Flask, bcrypt, pyserial, python-gammu)
- **`SMS_REST_README.md`** - Complete user documentation and API reference

### Technology Stack

- **Framework**: Flask (Python 3.8+)
- **SMS Backend**: python-gammu library for GSM modem communication
- **Authentication**: Basic HTTP Auth with bcrypt password hashing
- **Service Management**: systemd integration for Linux systems
- **Communication**: REST API with JSON request/response format

### Key Architectural Patterns

- **Persistent Modem Connection**: Global modem connection (`global_modem`) to avoid re-initialization overhead
- **Intelligent Modem Initialization**: Automatic port detection, ModemManager conflict handling, and configuration management
- **Error Tuple Pattern**: SMS operations return `(success: bool, status: str, details: str)` tuples
- **Case-Insensitive API**: JSON field names converted to lowercase for flexible client integration
- **Signal Handling**: Proper cleanup with SIGINT/SIGTERM handlers for graceful shutdown

## Key Features

- Send SMS via REST API with JSON format
- Automatic GSM modem port detection and configuration
- ModemManager conflict handling (automatic stop/start)
- SMS reply waiting capability (configurable timeout)
- Message length validation and auto-truncation
- Phone number normalization for Mexican +52 country code
- Persistent modem connections to eliminate re-initialization overhead
- Comprehensive error handling and logging
- Health check endpoint for monitoring

## Development Commands

### Installing Dependencies
```bash
pip install -r requirements.txt
```

### Development Mode
```bash
# Basic development with debug logging
python3 sms_rest_service.py --port 18180 --htpasswd /path/to/htpasswd --debug

# With specific modem device
python3 sms_rest_service.py --port 18180 --htpasswd /path/to/htpasswd --device /dev/ttyUSB0 --debug
```

### Production Installation
```bash
# One-command system installation with prerequisites check
sudo python3 sms_rest_service.py --install
```

### Authentication Management
```bash
# Create new htpasswd file (overwrites existing)
python3 create_htpasswd.py admin passw0rd /path/to/htpasswd

# Create htpasswd for system service
python3 create_htpasswd.py admin passw0rd /etc/sms-rest/htpasswd
```

### Testing and Validation
```bash
# Test signal handling (Ctrl+C behavior)
python3 test_ctrl_c.py

# Health check endpoint
curl http://localhost:18180/health

# SMS sending test
curl -X POST http://localhost:18180/ \
     -u admin:passw0rd \
     -H "Content-Type: application/json" \
     -d '{"number": "1234567890", "message": "Test SMS"}'
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

## Configuration

### Default Settings

- **Port**: 18180 (configurable with `--port`)
- **SMS Reply Timeout**: 60 seconds (`SMS_REPLY_TIMEOUT` constant)
- **Message Length Limit**: 160 characters (auto-truncated)

### Command Line Options

- `--port PORT` - Service port (default: 18180)
- `--htpasswd FILE` - Authentication file path (required)
- `--device DEVICE` - Specific modem device (e.g., /dev/ttyUSB0)
- `--debug` - Enable detailed logging
- `--install` - System installation with prerequisites check
- `--help` - Show usage information

## API Endpoints

### POST / (Send SMS)
- **Authentication**: Basic HTTP Auth
- **Content-Type**: application/json
- **Fields** (case-insensitive):
  - `number`: Phone number (10-15 digits)
  - `message`: SMS text (max 160 chars)
  - `reply`: Boolean, wait for reply (optional, default: false)

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
- **Service file**: `/etc/systemd/system/sms-rest.service`
- **Binary location**: `/usr/local/bin/sms-rest-service`
- **Config directory**: `/etc/sms-rest/`
- **Auth file**: `/etc/sms-rest/htpasswd`

### Service Management Commands
```bash
sudo systemctl start sms-rest      # Start service
sudo systemctl stop sms-rest       # Stop service
sudo systemctl enable sms-rest     # Enable auto-start
sudo systemctl status sms-rest     # Check status
sudo journalctl -u sms-rest -f     # View logs
```

## Important Code Patterns

### Persistent Modem Connections
The service maintains a global modem connection (`global_modem`) to avoid re-initialization overhead. Always use `get_modem_connection()` function (lines 832-856) to access the modem, which handles automatic reconnection if needed. Never directly access `global_modem`.

### Error Handling Pattern
SMS operations consistently return tuples: `(success: bool, status: str, details: str)`. Check the success flag first, then handle specific error types:
- `timeout` - SMS sending timeout
- `device_error` - Modem hardware issues  
- `permission_error` - Access permission problems
- `failed` - General SMS sending failure

### Modem Initialization Sequence
The intelligent modem initialization (`init_modem_intelligent()`, lines 286-408) follows this pattern:
1. Check for specific device parameter first
2. Test existing ~/.gammurc configuration
3. Handle ModemManager conflicts by stopping/starting service
4. Auto-detect modem port using AT commands
5. Create/update gammu configuration
6. Initialize and cleanup existing SMS messages

### Request Processing Pattern
API requests follow this validation flow:
1. Basic HTTP authentication (`authenticate_request()`)
2. Content-type validation (application/json)
3. JSON structure validation
4. Case-insensitive field name conversion (`data_lower = {k.lower(): v for k, v in data.items()}`)
5. Required field validation
6. Phone number format validation (10-15 digits)
7. Message length handling (160 char limit with auto-truncation)

### Logging Output Modes
- **Debug mode**: Detailed SMS tracking with full message content and structured output
- **Normal mode**: Concise single-line logging with sender IP tracking

### Signal Handling
Proper cleanup is implemented with signal handlers for SIGINT and SIGTERM (`signal_handler()`, line 1272), ensuring modem connections are terminated gracefully via `cleanup_modem()`.

## Security Considerations

- Uses bcrypt for password hashing (`create_htpasswd.py` utility)
- Basic HTTP authentication required for SMS endpoints
- Default credentials: admin/passw0rd (change for production)
- Health endpoint (`/health`) requires no authentication
- Consider HTTPS for production deployments
- Limit network access to trusted sources
- Service runs as root by default in systemd (required for modem access)

## Development Notes

### Code Organization
- Main service logic in `sms_rest_service.py` (lines 1-1543)
- Flask routes: `/` (POST, SMS sending) and `/health` (GET)
- Global constants: `SERVICE_PORT = 18180`, `SMS_REPLY_TIMEOUT = 60`

### Function Reference
- `get_modem_connection()` - Get persistent modem connection (lines 832-856)
- `send_sms()` - Send SMS with verbose logging (lines 480-603)
- `authenticate_request()` - HTTP Basic Auth validation (lines 1278-1298)
- `init_modem_intelligent()` - Smart modem initialization (lines 286-408)
- `check_prerequisites()` - System validation for installation (lines 858-967)
- `install_service()` - Full system service installation (lines 1036-1258)

### Phone Number Handling
The service includes Mexican +52 country code normalization:
- `normalize_phone_number()` - Strips country codes and formatting (lines 686-702)
- `phone_numbers_match()` - Compares numbers handling +52 variations (lines 704-715)

### Installation System
The `--install` flag provides comprehensive system installation including:
- Prerequisites validation (Python version, packages, systemd, USB devices)
- User confirmation walkthrough
- Service file creation with security settings
- Default authentication setup
- Post-installation guidance