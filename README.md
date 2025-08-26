# SMS REST Server

A comprehensive REST API service for sending SMS messages via GSM modem using the gammu library. This is a production-ready Python Flask application with systemd integration for Linux systems.

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![Flask](https://img.shields.io/badge/flask-2.3+-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

## Features

- ✅ **REST API**: Send SMS messages via HTTP POST with JSON format
- ✅ **Authentication**: Secure Basic HTTP authentication with bcrypt hashing
- ✅ **SMS Reply Waiting**: Optional SMS reply monitoring (configurable timeout)
- ✅ **Message Validation**: Automatic length validation and truncation (160 chars)
- ✅ **Auto-Detection**: Intelligent GSM modem port detection
- ✅ **Persistent Connections**: Eliminates modem re-initialization overhead
- ✅ **Health Monitoring**: Built-in health check endpoint
- ✅ **System Integration**: Complete systemd service installation
- ✅ **Production Ready**: Comprehensive error handling and logging

## Quick Start

### Installation

1. **One-Command Installation** (Recommended):
```bash
sudo python3 sms_rest_service.py --install
```

2. **Manual Installation**:
```bash
git clone https://github.com/username/SMS-REST-Server.git
cd SMS-REST-Server
pip install -r requirements.txt
python3 create_htpasswd.py admin passw0rd /tmp/htpasswd
python3 sms_rest_service.py --port 18180 --htpasswd /tmp/htpasswd --debug
```

### Usage

**Send SMS (Basic)**:
```bash
curl -X POST http://localhost:18180/ \
     -u admin:passw0rd \
     -H "Content-Type: application/json" \
     -d '{"number": "1234567890", "message": "Hello from SMS REST API"}'
```

**Send SMS with Reply Waiting**:
```bash
curl -X POST http://localhost:18180/ \
     -u admin:passw0rd \
     -H "Content-Type: application/json" \
     -d '{"number": "1234567890", "message": "Please reply", "reply": true}'
```

**Health Check**:
```bash
curl http://localhost:18180/health
```

## API Reference

### Endpoints

| Method | Endpoint | Auth Required | Description |
|--------|----------|---------------|-------------|
| POST | `/` | ✅ Yes | Send SMS message |
| GET | `/health` | ❌ No | Service health check |

### Request Format

```json
{
  "number": "1234567890",      // Required: Phone number (10-15 digits)
  "message": "Your message",   // Required: SMS text (max 160 chars)
  "reply": false              // Optional: Wait for reply (default: false)
}
```

**Note**: Field names are case-insensitive (`Number`, `MESSAGE`, `Reply` all work).

### Response Examples

**Success**:
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

**With Reply**:
```json
{
  "success": true,
  "message": "SMS sent successfully",
  "reply": {
    "received": true,
    "count": 1,
    "messages": [
      {
        "Number": "+521234567890",
        "Text": "Thank you!",
        "DateTime": "2025-08-26 09:30:15"
      }
    ]
  }
}
```

## Hardware Requirements

- **GSM Modem**: USB-connected GSM modem with SMS capability
- **SIM Card**: Active SIM card with SMS service
- **Operating System**: Linux with systemd support
- **Python**: Version 3.8 or higher
- **Permissions**: User in 'dialout' group or root privileges

## System Service Management

After installation with `--install`:

```bash
# Service Control
sudo systemctl start sms-rest      # Start service
sudo systemctl stop sms-rest       # Stop service
sudo systemctl restart sms-rest    # Restart service
sudo systemctl status sms-rest     # Check status

# Auto-start Control
sudo systemctl enable sms-rest     # Enable auto-start on boot
sudo systemctl disable sms-rest    # Disable auto-start

# Monitoring
sudo journalctl -u sms-rest -f     # Real-time logs
```

## Configuration

### Command Line Options

```bash
python3 sms_rest_service.py [OPTIONS]

Options:
  --port PORT         Service port (default: 18180)
  --htpasswd FILE     Authentication file path (required)
  --device DEVICE     Specific modem device (e.g., /dev/ttyUSB0)
  --debug             Enable detailed logging
  --install           Install as system service
  --help              Show help message
```

### Authentication Management

Create users with the included utility:

```bash
# Create new htpasswd file
python3 create_htpasswd.py admin passw0rd /path/to/htpasswd

# For system service
python3 create_htpasswd.py admin passw0rd /etc/sms-rest/htpasswd
```

## File Structure

```
SMS-REST-Server/
├── sms_rest_service.py     # Main Flask application (1540+ lines)
├── create_htpasswd.py      # Password hashing utility
├── requirements.txt        # Python dependencies
├── SMS_REST_README.md      # Detailed documentation
├── CLAUDE.md              # Development guidance
└── README.md              # This file
```

## Dependencies

- **Flask** >= 2.3.0 - Web framework
- **Werkzeug** >= 2.3.0 - WSGI utility library  
- **bcrypt** >= 4.0.0 - Password hashing
- **pyserial** >= 3.5 - Serial communication
- **python-gammu** >= 3.2 - SMS modem interface

Install with: `pip install -r requirements.txt`

## Architecture Highlights

- **Persistent Modem Connection**: Global connection management eliminates initialization overhead
- **Intelligent Auto-Detection**: Automatic USB port scanning and modem configuration
- **ModemManager Handling**: Smart conflict resolution with system ModemManager service
- **Case-Insensitive API**: Flexible JSON field name handling for client compatibility
- **Mexican +52 Support**: Built-in phone number normalization for Mexican carriers
- **Production Logging**: Dual output modes (debug/production) with IP tracking

## Security

- **Authentication**: Basic HTTP Auth with bcrypt password hashing
- **Default Credentials**: admin/passw0rd (⚠️ Change for production!)
- **HTTPS Recommendation**: Use reverse proxy with SSL/TLS
- **Network Security**: Limit access to trusted IP ranges
- **File Permissions**: Secure htpasswd file storage (600 permissions)

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
sudo journalctl -u sms-rest -f  # Check logs
sudo systemctl daemon-reload    # Reload after config changes
```

### Debug Mode

Enable detailed logging for troubleshooting:
```bash
python3 sms_rest_service.py --port 18180 --htpasswd /path/to/htpasswd --debug
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

- **Documentation**: See `SMS_REST_README.md` for complete API reference
- **Issues**: Report bugs and feature requests via GitHub Issues
- **Development**: See `CLAUDE.md` for development guidance

## Acknowledgments

- Built with [python-gammu](https://github.com/gammu/python-gammu) for SMS functionality

---

**Production Note**: This service is designed for production use. Ensure proper security measures (HTTPS, firewall, secure passwords) before deploying in production environments.
