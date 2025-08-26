# SMS REST Service

A REST API service for sending SMS messages via GSM modem using gammu library.

## Features

- ✅ Send SMS messages via REST API
- ✅ Basic HTTP authentication with bcrypt hashing
- ✅ Optional SMS reply waiting (up to 60 seconds)
- ✅ Message length validation and truncation (160 chars)
- ✅ Automatic modem port detection
- ✅ JSON request/response format
- ✅ Health check endpoint

## Installation

### Quick System Installation (Recommended)

Install as a system service with one command:
```bash
sudo python3 sms_rest_service.py --install
```

This will:
- Install service to `/usr/local/bin/sms-rest-service`
- Create systemd service file `/etc/systemd/system/sms-rest.service`
- Create config directory `/etc/sms-rest/`
- Generate default authentication file with user `admin` and password `passw0rd`
- Set up the service to run on port 18180

After installation, start the service:
```bash
sudo systemctl start sms-rest
sudo systemctl enable sms-rest  # Enable auto-start on boot
```

### Manual Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create htpasswd file:
```bash
python3 create_htpasswd.py admin passw0rd /tmp/htpasswd
```

3. Make scripts executable:
```bash
chmod +x sms_rest_service.py
chmod +x create_htpasswd.py
```

## Usage

### Start the service:
```bash
# Auto-detect modem device
python3 sms_rest_service.py --port 18180 --htpasswd /tmp/htpasswd --debug

# Use specific modem device
python3 sms_rest_service.py --port 18180 --htpasswd /tmp/htpasswd --device /dev/ttyUSB0 --debug
```

### API Endpoints

#### Send SMS

**Default behavior (no reply waiting):**
```bash
curl -sL -v -X POST http://localhost:18180/ \
     -u admin:passw0rd \
     -H "Content-Type: application/json" \
     -d '{"Number": "1234567890", "message": "Test message from HTTP API"}'
```

**With reply waiting:**
```bash
curl -sL -v -X POST http://localhost:18180/ \
     -u admin:passw0rd \
     -H "Content-Type: application/json" \
     -d '{"Number": "1234567890", "message": "Test message from HTTP API", "reply": true}'
```

**Case-insensitive examples:**
```bash
# All lowercase
curl -X POST http://localhost:18180/ -u admin:passw0rd \
     -H "Content-Type: application/json" \
     -d '{"number": "1234567890", "message": "test message", "reply": false}'

# Mixed case
curl -X POST http://localhost:18180/ -u admin:passw0rd \
     -H "Content-Type: application/json" \
     -d '{"NUMBER": "1234567890", "Message": "Test message", "Reply": true}'
```

**Request Parameters (case-insensitive):**
- `Number` or `number`: Phone number (10-15 digits)
- `Message` or `message`: SMS text (max 160 chars, auto-truncated)  
- `Reply` or `reply`: Boolean, wait for reply (optional, default: false - only waits when explicitly set to true)

**Response Examples:**

Success without reply:
```json
{
  "success": true,
  "message": "SMS sent successfully",
  "modem_response": {
    "status": "success",
    "details": "SMS sent successfully"
  },
  "details": {
    "number": "1234567890",
    "message_length": 25,
    "authenticated_user": "admin"
  }
}
```

Success with reply:
```json
{
  "success": true,
  "message": "SMS sent successfully",
  "modem_response": {
    "status": "success",
    "details": "SMS sent successfully"
  },
  "details": {
    "number": "1234567890",
    "message_length": 25,
    "authenticated_user": "admin"
  },
  "reply": {
    "received": true,
    "count": 1,
    "messages": [
      {
        "Number": "+521234567890",
        "Text": "Reply message",
        "DateTime": "2025-08-25 09:30:15",
        "Location": 1
      }
    ]
  }
}
```

Message too long (auto-truncated):
```json
{
  "success": true,
  "message": "SMS sent successfully",
  "modem_response": {
    "status": "success",
    "details": "SMS sent successfully"
  },
  "warning": "Message exceeded 160 chars limit, only 160 characters were sent",
  "details": {
    "number": "1234567890",
    "message_length": 160,
    "original_length": 200,
    "truncated": true,
    "authenticated_user": "admin"
  }
}
```

SMS sending failed (timeout):
```json
{
  "success": false,
  "message": "SMS sending failed",
  "modem_response": {
    "status": "timeout",
    "details": "Timeout while sending SMS to 1234567890: Operation timed out"
  },
  "details": {
    "number": "1234567890",
    "message_length": 25,
    "authenticated_user": "admin"
  }
}
```

SMS sending failed (device error):
```json
{
  "success": false,
  "message": "SMS sending failed",
  "modem_response": {
    "status": "device_error",
    "details": "Device not found while sending SMS to 1234567890: Device not available"
  },
  "details": {
    "number": "1234567890",
    "message_length": 25,
    "authenticated_user": "admin"
  }
}
```

#### Health Check
```bash
curl http://localhost:18180/health
```

Response:
```json
{
  "status": "healthy",
  "service": "SMS REST API",
  "timestamp": "2025-08-25 09:30:00"
}
```

## Command Line Options

```
Options:
    --port PORT         Port to run the service on (default: 18180)
    --htpasswd FILE     Path to htpasswd file for authentication
    --device DEVICE     Specific modem device (e.g., /dev/ttyUSB0)
    --debug             Enable debug mode
    --install           Install service to /usr/local/bin and create systemd service
    --help              Show help message
```

## System Service Management

After installation with `--install`, use these commands:

```bash
# Service control
sudo systemctl start sms-rest      # Start the service
sudo systemctl stop sms-rest       # Stop the service  
sudo systemctl restart sms-rest    # Restart the service
sudo systemctl status sms-rest     # Check service status

# Auto-start control
sudo systemctl enable sms-rest     # Enable auto-start on boot
sudo systemctl disable sms-rest    # Disable auto-start

# Logs and monitoring
sudo journalctl -u sms-rest -f     # View real-time logs
sudo journalctl -u sms-rest --since "1 hour ago"  # Recent logs
```

## Configuration Files

After system installation:
- **Service file**: `/etc/systemd/system/sms-rest.service`
- **Config directory**: `/etc/sms-rest/`
- **Auth file**: `/etc/sms-rest/htpasswd`
- **Config template**: `/etc/sms-rest/sms-rest.conf`

## Authentication

The service uses Basic HTTP authentication with bcrypt password hashing.

### Creating Users

Use the included `create_htpasswd.py` script:

```bash
# Create new htpasswd file
python3 create_htpasswd.py admin passw0rd /etc/sms/htpasswd

# Add another user (append to existing file)
python3 create_htpasswd.py user2 mypassword /etc/sms/htpasswd
```

### Manual htpasswd Entry

You can also create entries manually using Python:

```python
import bcrypt
username = "admin"
password = "passw0rd"
salt = bcrypt.gensalt()
hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
print(f"{username}:{hashed.decode('utf-8')}")
```

## Error Responses

| Status | Error | Description |
|--------|-------|-------------|
| 401 | Authentication required | Missing or invalid credentials |
| 400 | Invalid content type | Content-Type must be application/json |
| 400 | Missing required field | Number or message missing |
| 400 | Invalid phone number | Phone number format invalid |
| 500 | Modem initialization failed | GSM modem not available |
| 500 | SMS sending failed | Failed to send SMS |

## Hardware Requirements

- GSM modem connected via USB (auto-detected)
- SIM card with SMS capabilities
- Linux system with gammu support

## Modem Setup

The service automatically:
1. Stops ModemManager service
2. Detects modem port (/dev/ttyUSB*)
3. Configures gammu (~/.gammurc)
4. Initializes modem connection
5. Restarts ModemManager after operation

## Security Notes

- Uses bcrypt hashing for passwords
- Requires Basic HTTP authentication
- Consider using HTTPS in production
- Limit network access to trusted sources

## Troubleshooting

### Common Issues

1. **Permission denied**: Add user to dialout group
```bash
sudo usermod -a -G dialout $USER
```

2. **Modem not detected**: Check USB connection
```bash
ls -la /dev/ttyUSB*
```

3. **ModemManager conflicts**: Service automatically manages this

### Debug Mode

Enable debug mode for detailed logging:
```bash
python3 sms_rest_service.py --port 18180 --htpasswd /tmp/htpasswd --device /dev/ttyUSB0 --debug
```

## Service Customization

To customize the installed service, edit the systemd service file:

```bash
sudo systemctl stop sms-rest
sudo nano /etc/systemd/system/sms-rest.service
sudo systemctl daemon-reload
sudo systemctl start sms-rest
```

Common customizations:
- Change port: `--port 8080`
- Specify device: `--device /dev/ttyUSB0`  
- Enable debug mode: `--debug` (not recommended for production)

## License

Created by Claude Code Assistant for TrackGPS project.