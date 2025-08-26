#!/usr/bin/env python3
"""
SMS REST Service
================
A comprehensive REST API service for sending SMS messages via GSM modem using gammu library.

Features:
- ✅ Send SMS messages via REST API with JSON request/response
- ✅ Basic HTTP authentication with bcrypt password hashing
- ✅ Optional SMS reply waiting (up to 60 seconds, configurable)
- ✅ Message length validation and auto-truncation (160 chars)
- ✅ Automatic modem port detection with USB device scanning
- ✅ Case-insensitive JSON field names (number/Number, message/Message, reply/Reply)
- ✅ Health check endpoint for service monitoring
- ✅ Persistent modem connection (eliminates re-initialization overhead)
- ✅ Enhanced installation system with comprehensive pre-requisites validation
- ✅ Advanced verbose logging with detailed SMS tracking and source IP
- ✅ Automatic SMS cleanup on startup (clears all existing messages from folders 1-4)
- ✅ Phone number normalization for +52 Mexican country code variations
- ✅ Smart ModemManager conflict detection and handling
- ✅ Systemd service integration with proper signal handling
- ✅ Production-ready with security settings and error handling

Installation:
    # Quick system installation (recommended)
    sudo python3 sms_rest_service.py --install

    This will:
    • Check all system prerequisites and dependencies
    • Show installation walkthrough with user confirmation
    • Install service to /usr/local/bin/sms-rest-service
    • Create systemd service with /etc/systemd/system/sms-rest.service
    • Set up configuration directory /etc/sms-rest/
    • Create default authentication (admin/passw0rd)
    • Provide comprehensive post-installation guide

Usage:
    # Basic usage
    python3 sms_rest_service.py --port 18180 --htpasswd /path/to/htpasswd

    # With specific modem device
    python3 sms_rest_service.py --port 18180 --htpasswd /path/to/htpasswd --device /dev/ttyUSB0

    # With enhanced debug mode (verbose output with message content)
    python3 sms_rest_service.py --port 18180 --htpasswd /path/to/htpasswd --debug

Command Line Options:
    --port PORT         Port to run the service on (default: 18180)
    --htpasswd FILE     Path to htpasswd file for authentication
    --device DEVICE     Specific modem device (e.g., /dev/ttyUSB0)
    --debug             Enable debug mode with detailed logging
    --install           Install service system-wide with prerequisites check
    --help              Show help message

API Endpoints:
    POST /
    Content-Type: application/json
    Authorization: Basic <base64(username:password)>

    Body (case-insensitive field names):
    {
        "Number": "1234567890",           // Phone number (10-15 digits)
        "message": "Test message",        // SMS text (auto-truncated at 160 chars)
        "reply": true                     // Wait for reply (optional, default: false)
    }

    GET /health
    Returns: {"status": "healthy", "service": "SMS REST API", "timestamp": "..."}

Verbose Output Examples:
    # Debug mode (detailed format):
    📱 SMS DETAILS:
       DateTime: 2025-08-25 15:30:15
       Sender: admin (192.168.1.100)
       Receiver: 3339564997
       Reply Expected: Yes
       Result: SUCCESS
       Message: 'Test message from HTTP API'

    # Normal mode (concise format):
    📱 2025-08-25 15:30:15 | admin (127.0.0.1) → 3339564997 | SUCCESS (reply expected) | 'Test message'

Global Variables:
    SERVICE_PORT = 18180              // Default service port
    SMS_REPLY_TIMEOUT = 60            // SMS reply wait timeout in seconds

System Service Management:
    sudo systemctl start sms-rest     // Start the service
    sudo systemctl stop sms-rest      // Stop the service
    sudo systemctl enable sms-rest    // Enable auto-start on boot
    sudo systemctl status sms-rest    // Check service status
    sudo journalctl -u sms-rest -f    // View real-time logs

Authentication:
    Default credentials: admin / passw0rd
    Create additional users: python3 create_htpasswd.py username password /etc/sms-rest/htpasswd

Prerequisites:
    • Python 3.8+ with Flask, bcrypt, pyserial, python-gammu packages
    • systemd-compatible Linux system
    • GSM modem connected via USB (/dev/ttyUSB* device)
    • User in 'dialout' group or root privileges
    • Port 18180 available

Hardware Requirements:
    • GSM modem with USB connection
    • SIM card with SMS capabilities
    • Stable USB connection for modem

Created: 2025-08-25
Updated: 2025-08-25 (Enhanced installation, verbose output with IP tracking, message content display)
"""

from flask import Flask, request, jsonify
from werkzeug.security import check_password_hash
import bcrypt
import base64
import gammu
import time
import os
import sys
import getopt
import re
import serial
import subprocess
import signal
import atexit

app = Flask(__name__)

# Global variables
htpasswd_file = None
debug = False
SERVICE_PORT = 18180  # Default service port
SMS_REPLY_TIMEOUT = 60  # SMS reply wait timeout in seconds
modem_device = None  # Specific modem device (e.g., /dev/ttyUSB0)
global_modem = None  # Persistent modem connection

def print_usage():
    """Print usage information"""
    print("""
SMS REST Service

Usage:
    python3 sms_rest_service.py [OPTIONS]

Options:
    --port PORT         Port to run the service on (default: 18180)
    --htpasswd FILE     Path to htpasswd file for authentication
    --device DEVICE     Specific modem device (e.g., /dev/ttyUSB0)
    --debug             Enable debug mode
    --install           Install service to /usr/local/bin and create systemd service
    --help              Show this help message

Example:
    python3 sms_rest_service.py --port 18180 --htpasswd /etc/sms/htpasswd --device /dev/ttyUSB0

API Usage:
    curl -sL -v -X POST http://localhost:18180/ \\
         -u admin:password \\
         -H "Content-Type: application/json" \\
         -d '{"Number": "1234567890", "message": "Test message", "reply": true}'
""")

def detect_modem_port():
    """
    Auto-detect the modem port by scanning available USB serial ports
    Returns: (success: bool, port: str, manufacturer: str)
    """
    print("🔍 Auto-detecting modem port...")

    # Get list of USB serial ports
    usb_ports = []
    for i in range(10):  # Check ttyUSB0 through ttyUSB9
        port = f'/dev/ttyUSB{i}'
        if os.path.exists(port):
            usb_ports.append(port)

    if not usb_ports:
        return False, None, "No USB serial ports found"

    print(f"🔍 Scanning USB ports: {', '.join(usb_ports)}")

    # Test each port
    for port in usb_ports:
        print(f"   Testing {port}...", end=" ")

        try:
            # Try basic AT command
            with serial.Serial(port, 115200, timeout=2) as ser:
                ser.write(b'AT\r\n')
                time.sleep(0.5)
                response = ser.read(ser.in_waiting).decode('utf-8', errors='ignore')

                if 'OK' in response:
                    # Try to get manufacturer
                    ser.write(b'AT+CGMI\r\n')
                    time.sleep(0.5)
                    manu_response = ser.read(ser.in_waiting).decode('utf-8', errors='ignore')

                    # Extract manufacturer name
                    manufacturer = "Unknown"
                    for line in manu_response.split('\n'):
                        line = line.strip()
                        if line and line not in ['AT+CGMI', 'OK', '']:
                            manufacturer = line
                            break

                    print(f"✅ Modem detected! ({manufacturer})")
                    return True, port, manufacturer
                else:
                    print("❌ No response")

        except Exception as e:
            print(f"❌ Error: {e}")
            continue

    return False, None, "No modem found on any USB port"

def update_gammu_config(port):
    """
    Update ~/.gammurc configuration file to use the specified port
    Returns: bool (success)
    """
    gammu_config = f"""[gammu]
port = {port}
model = auto
connection = at
synchronizetime = yes
logfile =
logformat = nothing
use_locking =
gammuloc =
"""

    try:
        # Write to ~/.gammurc
        config_path = os.path.expanduser('~/.gammurc')

        # Backup existing config
        if os.path.exists(config_path):
            backup_path = f"{config_path}.bkp-{time.strftime('%Y%m%d%H%M%S')}"
            import shutil
            shutil.copy2(config_path, backup_path)
            if debug:
                print(f"📋 Backed up existing config to: {backup_path}")

        # Write new config
        with open(config_path, 'w') as f:
            f.write(gammu_config)

        if debug:
            print(f"📝 Updated ~/.gammurc to use port: {port}")
        return True

    except Exception as e:
        print(f"❌ Failed to update gammu config: {e}")
        return False

def test_gammu_config():
    """
    Test if the current gammu configuration works
    Returns: (success: bool, error_message: str)
    """
    try:
        sm = gammu.StateMachine()
        sm.ReadConfig()
        sm.Init()

        # Try a simple command
        info = sm.GetManufacturer()
        sm.Terminate()

        return True, f"✅ Gammu config test successful (Manufacturer: {info})"

    except gammu.ERR_DEVICENOTEXIST as e:
        return False, f"Device not found: {e}"
    except gammu.ERR_DEVICENOPERMISSION as e:
        return False, f"Permission denied: {e}. Try running with sudo or add user to dialout group"
    except gammu.ERR_DEVICEOPENERROR as e:
        return False, f"Device open error: {e}"
    except Exception as e:
        return False, f"Gammu config test failed: {e}"

def init_modem_intelligent():
    """
    Intelligently initialize the GSM modem
    Returns: gammu.StateMachine object or None if failed
    """
    global modem_device
    config_path = os.path.expanduser('~/.gammurc')
    config_exists = os.path.exists(config_path)

    # If specific device is provided, use it directly
    if modem_device:
        print(f"📱 Using specified modem device: {modem_device}")
        if not os.path.exists(modem_device):
            print(f"❌ Specified device does not exist: {modem_device}")
            return None

        # Create/update config with specified device
        print(f"🔧 Creating gammu config for specified device {modem_device}...")
        if not update_gammu_config(modem_device):
            return None

        # Test the configuration
        test_success, test_message = test_gammu_config()
        if not test_success:
            print(f"❌ Config test failed for {modem_device}: {test_message}")
            return None

        # Initialize modem
        try:
            sm = gammu.StateMachine()
            sm.ReadConfig()
            sm.Init()
            print(f"✅ Modem initialized successfully on specified device {modem_device}")
            cleanup_all_sms_messages(sm)
            return sm
        except Exception as e:
            print(f"❌ Failed to initialize modem on {modem_device}: {e}")
            return None

    if config_exists:
        print("📋 Found existing ~/.gammurc config file")

        # Test existing configuration
        test_success, test_message = test_gammu_config()
        if test_success:
            print(f"✅ {test_message}")
            try:
                sm = gammu.StateMachine()
                sm.ReadConfig()
                sm.Init()
                cleanup_all_sms_messages(sm)
                return sm
            except Exception as e:
                print(f"❌ Failed to initialize with existing config: {e}")
                return None
        else:
            print(f"❌ Existing config test failed: {test_message}")

            # Check if it's a ModemManager conflict
            if "permission" in test_message.lower() or "device" in test_message.lower():
                if is_modemmanager_running():
                    print("⚠️  ModemManager is running and may be controlling the modem.")
                    print("   Recommendation: Stop ModemManager service or run with sudo privileges.")
                    if check_modemmanager_exists():
                        print("   To stop: sudo systemctl stop ModemManager.service")
                    return None

            # Suggest config recommendations
            print("💡 Config recommendations:")
            print("   - Check port exists: ls /dev/ttyUSB*")
            print("   - Try: port = /dev/ttyUSB0")
            print("   - Use: connection = at")
            return None
    else:
        print("📋 No ~/.gammurc config found, creating new configuration...")

        # Try to stop ModemManager if it exists and is running
        mm_stopped = False
        if is_modemmanager_running():
            print("⚠️  ModemManager is running, attempting to stop it...")
            if stop_modem_manager():
                mm_stopped = True
            else:
                print("❌ Failed to stop ModemManager. You may need to stop it manually:")
                print("   sudo systemctl stop ModemManager.service")
                return None

        # Auto-detect modem port
        detect_success, port, manufacturer = detect_modem_port()
        if not detect_success:
            print(f"❌ Modem detection failed: {manufacturer}")
            if mm_stopped:
                start_modem_manager()
            return None

        # Create new config with detected port
        print(f"🔧 Creating gammu config for port {port}...")
        if not update_gammu_config(port):
            if mm_stopped:
                start_modem_manager()
            return None

        # Test the new configuration
        test_success, test_message = test_gammu_config()
        if not test_success:
            print(f"❌ New config test failed: {test_message}")
            if mm_stopped:
                start_modem_manager()
            return None

        # Initialize modem
        try:
            sm = gammu.StateMachine()
            sm.ReadConfig()
            sm.Init()
            print(f"✅ Modem initialized successfully on {port} ({manufacturer})")
            cleanup_all_sms_messages(sm)
            return sm
        except Exception as e:
            print(f"❌ Failed to initialize modem: {e}")
            if mm_stopped:
                start_modem_manager()
            return None

# Keep the old function for compatibility
def init_modem():
    """Legacy init_modem function - redirects to intelligent version"""
    return init_modem_intelligent()

def check_modemmanager_exists():
    """Check if ModemManager service exists"""
    try:
        result = subprocess.run(['systemctl', 'list-units', '--all', 'ModemManager.service'],
                              capture_output=True, text=True, timeout=5)
        return 'ModemManager.service' in result.stdout
    except Exception:
        return False

def is_modemmanager_running():
    """Check if ModemManager service is running"""
    try:
        result = subprocess.run(['systemctl', 'is-active', 'ModemManager.service'],
                              capture_output=True, text=True, timeout=5)
        return result.stdout.strip() == 'active'
    except Exception:
        return False

def stop_modem_manager():
    """Stop ModemManager service before initializing modem"""
    if not check_modemmanager_exists():
        if debug:
            print("ModemManager service does not exist, skipping stop")
        return True

    if not is_modemmanager_running():
        if debug:
            print("ModemManager service is not running, skipping stop")
        return True

    try:
        if debug:
            print("Stopping ModemManager service...")
        result = subprocess.run(['sudo', 'systemctl', 'stop', 'ModemManager.service'],
                              capture_output=True, text=True, timeout=10)
        time.sleep(2)  # Give it a moment to stop
        if debug:
            print("ModemManager service stopped successfully")
        return True
    except Exception as e:
        if debug:
            print(f"Failed to stop ModemManager: {e}")
        return False

def start_modem_manager():
    """Start ModemManager service after finishing operations"""
    if not check_modemmanager_exists():
        if debug:
            print("ModemManager service does not exist, skipping start")
        return True

    try:
        if debug:
            print("Starting ModemManager service...")
        result = subprocess.run(['sudo', 'systemctl', 'start', 'ModemManager.service'],
                              capture_output=True, text=True, timeout=10)
        time.sleep(2)  # Give it a moment to start
        if debug:
            print("ModemManager service started successfully")
        return True
    except Exception as e:
        if debug:
            print(f"Failed to start ModemManager: {e}")
        return False

def send_sms(sm, phone_number, message, sender_user=None, source_ip=None, reply_expected=False):
    """
    Send SMS message with detailed verbose output
    Returns: (success: bool, status: str, details: str)
    """
    # Get current timestamp
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')

    try:
        sms_info = {
            'Text': message,
            'SMSC': {'Location': 1},
            'Number': phone_number
        }

        # Send SMS and capture any response
        result = sm.SendSMS(sms_info)

        # Enhanced verbose output
        sender_info = f"{sender_user or 'system'} ({source_ip})" if source_ip else (sender_user or 'system')

        if debug:
            print(f"📱 SMS DETAILS:")
            print(f"   DateTime: {timestamp}")
            print(f"   Sender: {sender_info}")
            print(f"   Receiver: {phone_number}")
            print(f"   Reply Expected: {'Yes' if reply_expected else 'No'}")
            print(f"   Result: SUCCESS")
            print(f"   Message: '{message[:50]}{'...' if len(message) > 50 else ''}'")
        else:
            # Concise output for non-debug mode
            reply_status = " (reply expected)" if reply_expected else ""
            message_preview = f"'{message[:50]}{'...' if len(message) > 50 else ''}'"
            print(f"📱 {timestamp} | {sender_info} → {phone_number} | SUCCESS{reply_status} | {message_preview}")

        return True, "success", "SMS sent successfully"

    except gammu.ERR_TIMEOUT as e:
        error_msg = f"Timeout while sending SMS to {phone_number}: {str(e)}"

        # Enhanced verbose output for errors
        sender_info = f"{sender_user or 'system'} ({source_ip})" if source_ip else (sender_user or 'system')

        if debug:
            print(f"📱 SMS DETAILS:")
            print(f"   DateTime: {timestamp}")
            print(f"   Sender: {sender_info}")
            print(f"   Receiver: {phone_number}")
            print(f"   Reply Expected: {'Yes' if reply_expected else 'No'}")
            print(f"   Result: TIMEOUT ERROR")
            print(f"   Message: '{message[:50]}{'...' if len(message) > 50 else ''}'")
            print(f"   Error: {str(e)}")
        else:
            reply_status = " (reply expected)" if reply_expected else ""
            message_preview = f"'{message[:50]}{'...' if len(message) > 50 else ''}'"
            print(f"📱 {timestamp} | {sender_info} → {phone_number} | TIMEOUT{reply_status} | {message_preview}")

        return False, "timeout", error_msg

    except gammu.ERR_DEVICENOTEXIST as e:
        error_msg = f"Device not found while sending SMS to {phone_number}: {str(e)}"

        # Enhanced verbose output for errors
        sender_info = f"{sender_user or 'system'} ({source_ip})" if source_ip else (sender_user or 'system')

        if debug:
            print(f"📱 SMS DETAILS:")
            print(f"   DateTime: {timestamp}")
            print(f"   Sender: {sender_info}")
            print(f"   Receiver: {phone_number}")
            print(f"   Reply Expected: {'Yes' if reply_expected else 'No'}")
            print(f"   Result: DEVICE ERROR")
            print(f"   Message: '{message[:50]}{'...' if len(message) > 50 else ''}'")
            print(f"   Error: {str(e)}")
        else:
            reply_status = " (reply expected)" if reply_expected else ""
            message_preview = f"'{message[:50]}{'...' if len(message) > 50 else ''}'"
            print(f"📱 {timestamp} | {sender_info} → {phone_number} | DEVICE_ERROR{reply_status} | {message_preview}")

        return False, "device_error", error_msg

    except gammu.ERR_DEVICENOPERMISSION as e:
        error_msg = f"Permission denied while sending SMS to {phone_number}: {str(e)}"

        # Enhanced verbose output for errors
        sender_info = f"{sender_user or 'system'} ({source_ip})" if source_ip else (sender_user or 'system')

        if debug:
            print(f"📱 SMS DETAILS:")
            print(f"   DateTime: {timestamp}")
            print(f"   Sender: {sender_info}")
            print(f"   Receiver: {phone_number}")
            print(f"   Reply Expected: {'Yes' if reply_expected else 'No'}")
            print(f"   Result: PERMISSION ERROR")
            print(f"   Message: '{message[:50]}{'...' if len(message) > 50 else ''}'")
            print(f"   Error: {str(e)}")
        else:
            reply_status = " (reply expected)" if reply_expected else ""
            message_preview = f"'{message[:50]}{'...' if len(message) > 50 else ''}'"
            print(f"📱 {timestamp} | {sender_info} → {phone_number} | PERMISSION_ERROR{reply_status} | {message_preview}")

        return False, "permission_error", error_msg

    except Exception as e:
        error_msg = f"Failed to send SMS to {phone_number}: {str(e)}"

        # Enhanced verbose output for errors
        sender_info = f"{sender_user or 'system'} ({source_ip})" if source_ip else (sender_user or 'system')

        if debug:
            print(f"📱 SMS DETAILS:")
            print(f"   DateTime: {timestamp}")
            print(f"   Sender: {sender_info}")
            print(f"   Receiver: {phone_number}")
            print(f"   Reply Expected: {'Yes' if reply_expected else 'No'}")
            print(f"   Result: GENERAL ERROR")
            print(f"   Message: '{message[:50]}{'...' if len(message) > 50 else ''}'")
            print(f"   Error: {str(e)}")
        else:
            reply_status = " (reply expected)" if reply_expected else ""
            message_preview = f"'{message[:50]}{'...' if len(message) > 50 else ''}'"
            print(f"📱 {timestamp} | {sender_info} → {phone_number} | ERROR{reply_status} | {message_preview}")

        return False, "failed", error_msg

def cleanup_all_sms_messages(sm):
    """
    Delete all SMS messages from all folders in the modem at startup
    Equivalent to: gammu deleteallsms 1; gammu deleteallsms 2; gammu deleteallsms 3; gammu deleteallsms 4
    """
    if debug:
        print("🧹 Cleaning up all existing SMS messages from modem...")

    folders_to_clean = [1, 2, 3, 4]  # Standard SMS folders
    total_deleted = 0

    for folder in folders_to_clean:
        try:
            if debug:
                print(f"🗑️  Cleaning SMS folder {folder}...")

            # Count messages first
            messages_deleted = 0

            # Try to delete all SMS in folder using gammu DeleteAllSMS
            try:
                # Get SMS count first for reporting
                try:
                    sms_list = sm.GetNextSMS(Start=True, Folder=folder)
                    while sms_list:
                        messages_deleted += len(sms_list)
                        try:
                            sms_list = sm.GetNextSMS(Location=sms_list[-1]['Location'], Folder=folder)
                        except gammu.ERR_EMPTY:
                            break
                except gammu.ERR_EMPTY:
                    pass  # No messages in this folder

                if messages_deleted > 0:
                    # Delete all messages in this folder
                    sm.DeleteAllSMS(folder)
                    total_deleted += messages_deleted
                    if debug:
                        print(f"✅ Deleted {messages_deleted} messages from folder {folder}")
                else:
                    if debug:
                        print(f"📭 Folder {folder} is already empty")

            except Exception as e:
                # If DeleteAllSMS fails, try deleting messages individually
                if debug:
                    print(f"⚠️ DeleteAllSMS failed for folder {folder}, trying individual deletion: {e}")

                try:
                    # Get messages and delete one by one
                    while True:
                        try:
                            sms_list = sm.GetNextSMS(Start=True, Folder=folder)
                            for sms in sms_list:
                                sm.DeleteSMS(sms['Location'], folder)
                                messages_deleted += 1
                        except gammu.ERR_EMPTY:
                            break

                    if messages_deleted > 0:
                        total_deleted += messages_deleted
                        if debug:
                            print(f"✅ Individually deleted {messages_deleted} messages from folder {folder}")

                except Exception as e2:
                    if debug:
                        print(f"⚠️ Could not clean folder {folder}: {e2}")

            time.sleep(1)  # Wait 1 second between folder cleanups

        except Exception as e:
            if debug:
                print(f"⚠️ Error processing folder {folder}: {e}")
            continue

    if debug:
        print(f"🧹 SMS cleanup completed: {total_deleted} total messages deleted")
    else:
        if total_deleted > 0:
            print(f"🧹 Cleaned {total_deleted} existing SMS messages from modem")

def normalize_phone_number(phone_number):
    """
    Normalize phone number for comparison
    Removes all non-digits and handles +52 country code
    Returns: normalized 10-digit number (without country code)
    """
    # Remove all non-digit characters
    clean_number = re.sub(r'[^\d]', '', str(phone_number))

    # Handle +52 country code for Mexico
    if clean_number.startswith('52') and len(clean_number) > 10:
        # Remove country code if it looks like +52XXXXXXXXXX (13 digits total)
        if len(clean_number) == 12:  # 52 + 10 digits
            clean_number = clean_number[2:]

    # Return last 10 digits to handle any remaining prefixes
    return clean_number[-10:] if len(clean_number) >= 10 else clean_number

def phone_numbers_match(number1, number2):
    """
    Check if two phone numbers match, handling +52 country code variations
    Returns: True if numbers match, False otherwise
    """
    norm1 = normalize_phone_number(number1)
    norm2 = normalize_phone_number(number2)

    if debug:
        print(f"🔍 Number matching: '{number1}' -> '{norm1}' vs '{number2}' -> '{norm2}'")

    return norm1 == norm2

def get_sms_replies(sm, target_number, timeout_seconds=SMS_REPLY_TIMEOUT):
    """
    Wait for and retrieve SMS replies from a specific number
    Handles +52 country code variations properly
    Returns: list of SMS messages
    """
    replies = []
    start_time = time.time()

    if debug:
        print(f"📱 Waiting for SMS replies from {target_number} for {timeout_seconds} seconds...")

    while (time.time() - start_time) < timeout_seconds:
        try:
            # Get SMS messages
            sms_messages = []
            try:
                sms_messages = sm.GetNextSMS(Start=True, Folder=0)
            except gammu.ERR_EMPTY:
                pass  # No messages
            except Exception as e:
                if debug:
                    print(f"Error reading SMS: {e}")

            # Process messages
            for sms in sms_messages:
                sender_number = str(sms['Number'])

                # Check if this SMS is from our target number using improved matching
                if phone_numbers_match(sender_number, target_number):
                    if debug:
                        print(f"✅ Found matching reply from {sender_number}: '{sms['Text'][:50]}...'")

                    replies.append({
                        'Number': sender_number,
                        'Text': sms['Text'],
                        'DateTime': sms.get('DateTime', 'Unknown'),
                        'Location': sms.get('Location', 0)
                    })

                    # Delete the SMS after reading
                    try:
                        sm.DeleteSMS(sms['Location'], sms['Folder'])
                        if debug:
                            print(f"🗑️ Deleted SMS from location {sms.get('Location', 0)}")
                    except Exception as e:
                        if debug:
                            print(f"⚠️ Could not delete SMS: {e}")
                else:
                    if debug:
                        print(f"❌ SMS from {sender_number} doesn't match target {target_number}")

            if replies:
                break

            time.sleep(1)  # Wait 1 second before checking again

        except Exception as e:
            if debug:
                print(f"Error while waiting for SMS replies: {e}")
            break

    if debug:
        print(f"📨 Reply search completed: found {len(replies)} matching replies")

    return replies

def load_htpasswd_users(htpasswd_path):
    """
    Load users from htpasswd file
    Returns: dict {username: password_hash}
    """
    users = {}
    try:
        with open(htpasswd_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and ':' in line:
                    username, password_hash = line.split(':', 1)
                    users[username] = password_hash
    except Exception as e:
        print(f"Error loading htpasswd file: {e}")
    return users

def verify_password(stored_hash, password):
    """
    Verify password against stored hash (supports bcrypt)
    """
    try:
        if stored_hash.startswith('$2b$') or stored_hash.startswith('$2a$') or stored_hash.startswith('$2y$'):
            # bcrypt hash
            return bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8'))
        else:
            # Fallback to werkzeug for other hash types
            return check_password_hash(stored_hash, password)
    except Exception as e:
        if debug:
            print(f"Password verification error: {e}")
        return False

def initialize_global_modem():
    """Initialize the global modem connection at service startup"""
    global global_modem

    print("🔧 Initializing modem connection...")
    global_modem = init_modem_intelligent()

    if global_modem:
        print("✅ Global modem connection established successfully")
        return True
    else:
        print("❌ Failed to establish global modem connection")
        print("   Service will start but SMS sending will fail until modem is available")
        return False

def get_modem_connection():
    """Get the global modem connection, attempting to reconnect if needed"""
    global global_modem

    if global_modem is None:
        if debug:
            print("🔄 Global modem is None, attempting to initialize...")
        global_modem = init_modem_intelligent()

    # Test if existing connection is still valid
    if global_modem:
        try:
            # Simple test to see if modem is still responsive
            global_modem.GetManufacturer()
            return global_modem
        except Exception as e:
            if debug:
                print(f"🔄 Modem connection lost ({e}), attempting to reconnect...")
            try:
                global_modem.Terminate()
            except:
                pass
            global_modem = init_modem_intelligent()

    return global_modem

def check_prerequisites():
    """Check system prerequisites for SMS REST service installation"""
    print("🔍 Checking system prerequisites...")
    issues = []
    warnings = []

    # 1. Check if running as root
    if os.geteuid() != 0:
        issues.append("Root privileges required. Run with sudo.")

    # 2. Check Python version
    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
        issues.append(f"Python 3.8+ required. Current: {python_version.major}.{python_version.minor}")
    else:
        print(f"   ✅ Python version: {python_version.major}.{python_version.minor}.{python_version.micro}")

    # 3. Check required Python packages
    required_packages = [
        ('flask', 'Flask'),
        ('bcrypt', 'bcrypt'),
        ('serial', 'pyserial'),
        ('gammu', 'python-gammu')
    ]

    missing_packages = []
    for module_name, package_name in required_packages:
        try:
            __import__(module_name)
            print(f"   ✅ {package_name} is installed")
        except ImportError:
            missing_packages.append(package_name)
            issues.append(f"Missing Python package: {package_name}")

    # 4. Check systemd availability
    if not os.path.exists('/etc/systemd/system'):
        issues.append("systemd not available (required for service installation)")
    else:
        print("   ✅ systemd is available")

    # 5. Check if systemctl command exists
    try:
        subprocess.run(['which', 'systemctl'], check=True, capture_output=True)
        print("   ✅ systemctl command is available")
    except subprocess.CalledProcessError:
        issues.append("systemctl command not found")

    # 6. Check for existing installation
    if os.path.exists('/usr/local/bin/sms-rest-service'):
        warnings.append("Previous installation detected at /usr/local/bin/sms-rest-service")

    if os.path.exists('/etc/systemd/system/sms-rest.service'):
        warnings.append("Previous systemd service file detected")

    # 7. Check USB serial device access
    usb_devices = []
    try:
        for device in os.listdir('/dev'):
            if device.startswith('ttyUSB'):
                usb_devices.append(f"/dev/{device}")

        if usb_devices:
            print(f"   ✅ USB serial devices found: {', '.join(usb_devices)}")
        else:
            warnings.append("No USB serial devices found (GSM modem may not be connected)")
    except Exception:
        warnings.append("Cannot check USB devices")

    # 8. Check dialout group membership (for current user)
    try:
        import pwd, grp
        current_user = pwd.getpwuid(os.getuid()).pw_name if os.getuid() != 0 else "root"
        try:
            dialout_group = grp.getgrnam('dialout')
            if os.getuid() == 0:  # Running as root
                print("   ✅ Running as root (has device access)")
            elif current_user in dialout_group.gr_mem:
                print(f"   ✅ User '{current_user}' is in dialout group")
            else:
                warnings.append(f"User '{current_user}' not in dialout group (may need: sudo usermod -a -G dialout {current_user})")
        except KeyError:
            warnings.append("dialout group not found")
    except Exception:
        warnings.append("Cannot check group membership")

    # 9. Check disk space
    try:
        stat = os.statvfs('/usr/local/bin')
        free_space_mb = (stat.f_bavail * stat.f_frsize) / (1024 * 1024)
        if free_space_mb < 10:
            issues.append(f"Insufficient disk space in /usr/local/bin ({free_space_mb:.1f}MB available, 10MB required)")
        else:
            print(f"   ✅ Sufficient disk space: {free_space_mb:.1f}MB available")
    except Exception:
        warnings.append("Cannot check disk space")

    # 10. Check network port availability
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('localhost', 18180))
        sock.close()
        if result == 0:
            warnings.append("Port 18180 is already in use (may conflict with service)")
        else:
            print("   ✅ Port 18180 is available")
    except Exception:
        warnings.append("Cannot check port availability")

    return issues, warnings, missing_packages

def show_installation_walkthrough():
    """Show installation walkthrough and get user confirmation"""
    print("\n" + "="*60)
    print("📋 SMS REST SERVICE INSTALLATION WALKTHROUGH")
    print("="*60)
    print()
    print("This installation will:")
    print("  1. 📁 Copy service script to /usr/local/bin/sms-rest-service")
    print("  2. 📁 Create configuration directory /etc/sms-rest/")
    print("  3. 🔐 Create htpasswd authentication file with admin/passw0rd")
    print("  4. 🔧 Create systemd service file /etc/systemd/system/sms-rest.service")
    print("  5. 📄 Create configuration template file")
    print("  6. 🔄 Reload systemd daemon")
    print()
    print("After installation, you can:")
    print("  • Start service: sudo systemctl start sms-rest")
    print("  • Enable auto-start: sudo systemctl enable sms-rest")
    print("  • Check status: sudo systemctl status sms-rest")
    print("  • View logs: sudo journalctl -u sms-rest -f")
    print()
    print("Service will run on: http://localhost:18180/")
    print("Default credentials: admin / passw0rd")
    print()

    while True:
        response = input("Proceed with installation? [Y/n]: ").lower().strip()
        if response in ['', 'y', 'yes']:
            return True
        elif response in ['n', 'no']:
            return False
        else:
            print("Please enter 'y' for yes or 'n' for no.")

def fix_prerequisites_guide(missing_packages):
    """Show guide to fix missing prerequisites"""
    print("\n" + "="*60)
    print("🔧 PREREQUISITES FIX GUIDE")
    print("="*60)
    print()

    if missing_packages:
        print("📦 Install missing Python packages:")
        print(f"   pip3 install --break-system-packages {' '.join(missing_packages)}")
        print("   # OR using system package manager:")
        for pkg in missing_packages:
            if pkg == 'Flask':
                print("   sudo apt-get install python3-flask")
            elif pkg == 'bcrypt':
                print("   sudo apt-get install python3-bcrypt")
            elif pkg == 'pyserial':
                print("   sudo apt-get install python3-serial")
            elif pkg == 'python-gammu':
                print("   sudo apt-get install python3-gammu")
        print()

    print("🔌 GSM Modem Setup:")
    print("   1. Connect GSM modem via USB")
    print("   2. Check device: ls /dev/ttyUSB*")
    print("   3. Add user to dialout group: sudo usermod -a -G dialout $USER")
    print("   4. Stop ModemManager: sudo systemctl stop ModemManager.service")
    print()

    print("📶 Test GSM Modem:")
    print("   gammu identify  # Should detect modem")
    print("   gammu getnetworkinfo  # Should show network info")
    print()

def install_service():
    """Install the SMS REST service to system with comprehensive validation"""
    import shutil
    import pwd
    import grp

    print("=" * 60)
    print("📦 SMS REST SERVICE INSTALLATION")
    print("=" * 60)
    print()

    # Step 1: Check prerequisites
    issues, warnings, missing_packages = check_prerequisites()

    # Show results
    print()
    if warnings:
        print("⚠️  Warnings:")
        for warning in warnings:
            print(f"   • {warning}")
        print()

    if issues:
        print("❌ Critical Issues Found:")
        for issue in issues:
            print(f"   • {issue}")
        print()

        if missing_packages:
            fix_prerequisites_guide(missing_packages)

        print("Please fix the above issues and run the installation again.")
        sys.exit(1)

    print("✅ All prerequisite checks passed!")
    print()

    # Step 2: Show installation walkthrough
    if not show_installation_walkthrough():
        print("Installation cancelled by user.")
        sys.exit(0)

    print("🚀 Starting installation...")

    # Paths
    script_path = os.path.abspath(__file__)
    target_path = "/usr/local/bin/sms-rest-service"
    service_file = "/etc/systemd/system/sms-rest.service"
    config_dir = "/etc/sms-rest"

    try:
        # 1. Copy script to /usr/local/bin
        print(f"📁 Copying script to {target_path}")
        shutil.copy2(script_path, target_path)
        os.chmod(target_path, 0o755)

        # 2. Create config directory
        print(f"📁 Creating config directory {config_dir}")
        os.makedirs(config_dir, exist_ok=True)
        os.chmod(config_dir, 0o755)

        # 3. Create sample htpasswd file
        htpasswd_path = f"{config_dir}/htpasswd"
        if not os.path.exists(htpasswd_path):
            print(f"🔐 Creating sample htpasswd file at {htpasswd_path}")
            import bcrypt
            username = "admin"
            password = "passw0rd"
            salt = bcrypt.gensalt()
            hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
            with open(htpasswd_path, 'w') as f:
                f.write(f"{username}:{hashed.decode('utf-8')}\n")
            os.chmod(htpasswd_path, 0o600)
            print(f"   Default user: {username}")
            print(f"   Default password: {password}")

        # 4. Create systemd service file
        service_content = f"""[Unit]
Description=SMS REST API Service
After=network.target
Wants=network.target

[Service]
Type=simple
User=root
Group=root
WorkingDirectory=/usr/local/bin
ExecStart=/usr/bin/python3 {target_path} --port 18180 --htpasswd {htpasswd_path}
Restart=always
RestartSec=10
KillMode=mixed
TimeoutStopSec=5

# Environment
Environment=PYTHONUNBUFFERED=1

# Security settings
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
"""

        print(f"🔧 Creating systemd service file at {service_file}")
        with open(service_file, 'w') as f:
            f.write(service_content)
        os.chmod(service_file, 0o644)

        # 5. Create config file template
        config_template = f"{config_dir}/sms-rest.conf"
        if not os.path.exists(config_template):
            config_content = """# SMS REST Service Configuration
#
# Systemd service file: /etc/systemd/system/sms-rest.service
# Edit the service file to customize:
#
# --port PORT          Service port (default: 18180)
# --htpasswd FILE      Authentication file (default: /etc/sms-rest/htpasswd)
# --device DEVICE      Specific modem device (e.g., /dev/ttyUSB0)
# --debug              Enable debug mode (not recommended for production)

# Default configuration:
PORT=18180
HTPASSWD_FILE=/etc/sms-rest/htpasswd
# DEVICE=/dev/ttyUSB0  # Uncomment to specify device
# DEBUG=false          # Uncomment to enable debug mode

# To modify service parameters, edit:
# /etc/systemd/system/sms-rest.service
#
# Then run:
# sudo systemctl daemon-reload
# sudo systemctl restart sms-rest
"""
            print(f"📄 Creating config template at {config_template}")
            with open(config_template, 'w') as f:
                f.write(config_content)
            os.chmod(config_template, 0o644)

        # 6. Reload systemd and enable service
        print("🔄 Reloading systemd daemon...")
        os.system('systemctl daemon-reload')

        print("=" * 60)
        print("✅ INSTALLATION COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print()

        print("🚀 Next Steps:")
        print("   1. sudo systemctl start sms-rest      # Start the service")
        print("   2. sudo systemctl enable sms-rest     # Enable auto-start on boot")
        print("   3. sudo systemctl status sms-rest     # Verify service is running")
        print()

        print("📋 Service Management Commands:")
        print("   sudo systemctl start sms-rest         # Start the service")
        print("   sudo systemctl stop sms-rest          # Stop the service")
        print("   sudo systemctl restart sms-rest       # Restart the service")
        print("   sudo systemctl enable sms-rest        # Enable auto-start")
        print("   sudo systemctl disable sms-rest       # Disable auto-start")
        print("   sudo systemctl status sms-rest        # Check service status")
        print("   sudo journalctl -u sms-rest -f        # View real-time logs")
        print("   sudo journalctl -u sms-rest --since '1 hour ago'  # Recent logs")
        print()

        print("🔧 Configuration Files:")
        print(f"   Service file: {service_file}")
        print(f"   Config dir: {config_dir}")
        print(f"   Auth file: {htpasswd_path}")
        print(f"   Config template: {config_dir}/sms-rest.conf")
        print()

        print("🌐 API Access:")
        print(f"   Endpoint: http://localhost:18180/")
        print(f"   Health check: http://localhost:18180/health")
        print(f"   Authentication: Basic HTTP (base64 encoded)")
        print()

        print("🔐 Default Credentials:")
        print(f"   Username: {username}")
        print(f"   Password: {password}")
        print("   ⚠️  Change default password for production use!")
        print()

        print("🧪 Test the Service:")
        print("   # Health check")
        print("   curl http://localhost:18180/health")
        print()
        print("   # Send test SMS")
        print("   curl -X POST http://localhost:18180/ \\")
        print("        -u admin:passw0rd \\")
        print("        -H 'Content-Type: application/json' \\")
        print("        -d '{\"number\": \"1234567890\", \"message\": \"Test SMS\"}'")
        print()

        print("🔧 Customization:")
        print("   • Edit service parameters in: /etc/systemd/system/sms-rest.service")
        print("   • Add users: python3 /usr/local/bin/create_htpasswd.py user password /etc/sms-rest/htpasswd")
        print("   • After changes: sudo systemctl daemon-reload && sudo systemctl restart sms-rest")
        print()

        if warnings:
            print("⚠️  Post-Installation Notes:")
            for warning in warnings:
                print(f"   • {warning}")
            print()

        print("📖 Documentation: See SMS_REST_README.md for complete API reference")
        print("🐛 Issues: Check 'sudo journalctl -u sms-rest -f' if service fails to start")
        print()
        print("=" * 60)

    except Exception as e:
        print(f"❌ Installation failed: {e}")
        # Cleanup on failure
        for path in [target_path, service_file]:
            if os.path.exists(path):
                try:
                    os.remove(path)
                except:
                    pass
        sys.exit(1)

def cleanup_modem():
    """Clean up modem connection on exit"""
    global global_modem
    if global_modem:
        try:
            print("\n🔌 Cleaning up modem connection...")
            global_modem.Terminate()
            print("✅ Modem connection terminated")
        except:
            pass
        global_modem = None

def signal_handler(signum, frame):
    """Handle Ctrl+C and other signals"""
    print(f"\n🛑 Received signal {signum}, shutting down...")
    cleanup_modem()
    sys.exit(0)

def authenticate_request():
    """
    Authenticate the request using Basic HTTP Auth
    Returns: (success: bool, username: str or None)
    """
    if not htpasswd_file:
        return False, None

    auth = request.authorization
    if not auth:
        return False, None

    users = load_htpasswd_users(htpasswd_file)
    if auth.username not in users:
        return False, None

    stored_hash = users[auth.username]
    if verify_password(stored_hash, auth.password):
        return True, auth.username

    return False, None

@app.route('/', methods=['POST'])
def send_sms_api():
    """
    SMS API endpoint
    """
    # Authenticate request
    authenticated, username = authenticate_request()
    if not authenticated:
        return jsonify({
            'error': 'Authentication required',
            'message': 'Invalid credentials or missing Authorization header'
        }), 401

    # Validate content type
    if not request.is_json:
        return jsonify({
            'error': 'Invalid content type',
            'message': 'Content-Type must be application/json'
        }), 400

    # Get request data
    data = request.get_json()

    # Validate required fields
    if not data:
        return jsonify({
            'error': 'Invalid JSON',
            'message': 'Request body must contain valid JSON'
        }), 400

    # Make field names case-insensitive by converting to lowercase
    data_lower = {k.lower(): v for k, v in data.items()}

    required_fields = ['number', 'message']
    missing_fields = [field for field in required_fields if field not in data_lower]
    if missing_fields:
        return jsonify({
            'error': f'Missing required field(s): {", ".join(missing_fields)}',
            'message': f'Request must include: {", ".join(missing_fields)} (case-insensitive)'
        }), 400

    phone_number = str(data_lower['number'])
    message = str(data_lower['message'])
    wait_for_reply = data_lower.get('reply', False)  # Default: do not wait for reply

    # Validate phone number format
    if not re.match(r'^\d{10,15}$', phone_number):
        return jsonify({
            'error': 'Invalid phone number',
            'message': 'Phone number must contain 10-15 digits only'
        }), 400

    # Handle message length limit
    original_message = message
    message_truncated = False
    if len(message) > 160:
        message = message[:160]
        message_truncated = True

    # Get persistent modem connection
    sm = get_modem_connection()
    if not sm:
        return jsonify({
            'error': 'Modem not available',
            'message': 'Could not establish connection to GSM modem'
        }), 500

    # Get client IP address
    client_ip = request.remote_addr

    # Send SMS
    sms_success, sms_status, sms_details = send_sms(sm, phone_number, message, sender_user=username, source_ip=client_ip, reply_expected=wait_for_reply)

    response_data = {
        'success': sms_success,
        'message': sms_details if sms_success else 'SMS sending failed',
        'modem_response': {
            'status': sms_status,
            'details': sms_details
        },
        'details': {
            'number': phone_number,
            'message_length': len(message),
            'authenticated_user': username
        }
    }

    # If SMS sending failed, return error (don't terminate persistent connection)
    if not sms_success:
        return jsonify(response_data), 500

    # Add truncation warning if message was too long
    if message_truncated:
        response_data['warning'] = 'Message exceeded 160 chars limit, only 160 characters were sent'
        response_data['details']['original_length'] = len(original_message)
        response_data['details']['truncated'] = True

    # Wait for reply if requested
    if wait_for_reply:
        timestamp_wait = time.strftime('%Y-%m-%d %H:%M:%S')
        if debug:
            print(f"⏳ WAITING FOR REPLY:")
            print(f"   DateTime: {timestamp_wait}")
            print(f"   From: {phone_number}")
            print(f"   Timeout: {SMS_REPLY_TIMEOUT} seconds")
        else:
            print(f"⏳ {timestamp_wait} | Waiting for reply from {phone_number} | {SMS_REPLY_TIMEOUT}s timeout")

        replies = get_sms_replies(sm, phone_number, timeout_seconds=SMS_REPLY_TIMEOUT)

        if replies:
            timestamp_received = time.strftime('%Y-%m-%d %H:%M:%S')
            if debug:
                print(f"✅ REPLY RECEIVED:")
                print(f"   DateTime: {timestamp_received}")
                print(f"   From: {phone_number}")
                print(f"   Count: {len(replies)} message(s)")
                for i, reply in enumerate(replies, 1):
                    print(f"   Reply {i}: '{reply.get('Text', '')[:50]}{'...' if len(reply.get('Text', '')) > 50 else ''}'")
            else:
                reply_text = replies[0].get('Text', '') if replies else ''
                print(f"✅ {timestamp_received} | Reply from {phone_number} | {len(replies)} msg(s) | '{reply_text[:30]}{'...' if len(reply_text) > 30 else ''}'")

            response_data['reply'] = {
                'received': True,
                'count': len(replies),
                'messages': replies
            }
        else:
            timestamp_timeout = time.strftime('%Y-%m-%d %H:%M:%S')
            if debug:
                print(f"⏰ REPLY TIMEOUT:")
                print(f"   DateTime: {timestamp_timeout}")
                print(f"   From: {phone_number}")
                print(f"   Result: No reply received within {SMS_REPLY_TIMEOUT} seconds")
            else:
                print(f"⏰ {timestamp_timeout} | No reply from {phone_number} | {SMS_REPLY_TIMEOUT}s timeout")

            response_data['reply'] = {
                'received': False,
                'timeout': SMS_REPLY_TIMEOUT,
                'message': f'No reply received within {SMS_REPLY_TIMEOUT} seconds'
            }

    # Don't terminate modem connection - keep it persistent
    return jsonify(response_data), 200

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'SMS REST API',
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
    }), 200

def main():
    """Main function"""
    global htpasswd_file, debug, SERVICE_PORT, modem_device

    # Default values
    port = SERVICE_PORT

    # Parse command line arguments
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hp:a:D:di",
                                 ["help", "port=", "htpasswd=", "device=", "debug", "install"])
    except getopt.GetoptError as e:
        print(f"Error: {e}")
        print_usage()
        sys.exit(1)

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print_usage()
            sys.exit(0)
        elif opt in ("-p", "--port"):
            try:
                port = int(arg)
                if port < 1 or port > 65535:
                    raise ValueError("Port must be between 1 and 65535")
            except ValueError as e:
                print(f"Error: Invalid port number: {e}")
                sys.exit(1)
        elif opt in ("-a", "--htpasswd"):
            htpasswd_file = arg
            if not os.path.exists(htpasswd_file):
                print(f"Error: htpasswd file not found: {htpasswd_file}")
                sys.exit(1)
        elif opt in ("-D", "--device"):
            modem_device = arg
            if not os.path.exists(modem_device):
                print(f"Error: modem device not found: {modem_device}")
                sys.exit(1)
        elif opt in ("-d", "--debug"):
            debug = True
        elif opt in ("-i", "--install"):
            install_service()
            sys.exit(0)

    # Validate required options
    if not htpasswd_file:
        print("Error: --htpasswd option is required")
        print_usage()
        sys.exit(1)

    # Print startup information
    modem_info = f"Device: {modem_device}" if modem_device else "Device: Auto-detect"
    print(f"""
SMS REST Service Starting...
=============================
Port: {port}
Auth file: {htpasswd_file}
{modem_info}
Debug: {debug}
=============================
""")

    # Set up signal handlers for clean shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    atexit.register(cleanup_modem)

    # Initialize global modem connection
    # Skip initialization in Flask's parent reloader process
    if debug and os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
        print("🔄 Flask reloader parent process, modem will be initialized after restart")
    else:
        initialize_global_modem()

    # Start Flask app
    try:
        app.run(host='0.0.0.0', port=port, debug=debug, use_reloader=debug)
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")
        cleanup_modem()
        sys.exit(0)
    except Exception as e:
        print(f"Error starting server: {e}")
        cleanup_modem()
        sys.exit(1)

if __name__ == '__main__':
    main()
