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
- ✅ Operator service numbers support (2222, 7373) - no country code normalization
- ✅ Health check endpoint for service monitoring
- ✅ Persistent modem connection (eliminates re-initialization overhead)
- ✅ Enhanced installation system with comprehensive pre-requisites validation
- ✅ Advanced verbose logging with detailed SMS tracking and source IP
- ✅ Automatic SMS cleanup on startup (clears all existing messages from folders 1-4)
- ✅ E.164 international phone number format with configurable LOCAL_COUNTRY_CODE
- ✅ Smart ModemManager conflict detection and handling
- ✅ Systemd service integration with proper signal handling
- ✅ Production-ready with security settings and error handling

Installation:
    # Quick system installation (recommended)
    sudo python3 sms-rest-server.py --install

    This will:
    • Check all system prerequisites and dependencies
    • Show installation walkthrough with user confirmation
    • Install service to /usr/local/SMS-REST-Server/
    • Create systemd service with /etc/systemd/system/sms-rest-server.service
    • Set up data directory /var/lib/sms-rest-server/
    • Prompt you to create initial htpasswd credentials securely
    • Provide comprehensive post-installation guide

Usage:
    # Basic usage
    python3 sms-rest-server.py --port 18180 --htpasswd /path/to/htpasswd

    # With specific modem device
    python3 sms-rest-server.py --port 18180 --htpasswd /path/to/htpasswd --device /dev/ttyUSB0

    # With enhanced debug mode (verbose output with message content)
    python3 sms-rest-server.py --port 18180 --htpasswd /path/to/htpasswd --debug

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
        "Number": "1234567890",           // Phone number (see formats below)
        "message": "Test message",        // SMS text (auto-truncated at 160 chars)
        "reply": true,                    // Wait for reply (optional, default: false)
        "timeout": 120                    // Reply timeout in seconds (optional, default: 60, max: 600)
    }

    Supported phone number formats:
    - 10 digits (local): "1234567890" → auto-adds +52 (LOCAL_COUNTRY_CODE)
    - E.164 international: "+12125551234", "+521234567890"
    - Operator services: "2222", "7373" (no country code)
    - REJECTED: "521234567890" (11+ digits without + is ambiguous)

    GET /health
    Returns: {"status": "healthy", "service": "SMS REST API", "timestamp": "..."}

Verbose Output Examples:
    # Debug mode (detailed format):
    📱 SMS DETAILS:
       DateTime: 2025-08-25 15:30:15
       Sender: admin (192.168.1.100)
       Receiver: 1234567890
       Reply Expected: Yes
       Result: SUCCESS
       Message: 'Test message from HTTP API'

    # Normal mode (concise format):
    📱 2025-08-25 15:30:15 | admin (127.0.0.1) → 1234567890 | SUCCESS (reply expected) | 'Test message'

Global Variables:
    SERVICE_PORT = 18180              // Default service port
    SMS_REPLY_TIMEOUT = 60            // Default SMS reply wait timeout in seconds (overridable via 'timeout' field)

System Service Management:
    sudo systemctl start sms-rest-server      // Start the service
    sudo systemctl stop sms-rest-server       // Stop the service
    sudo systemctl enable sms-rest-server     // Enable auto-start on boot
    sudo systemctl status sms-rest-server     // Check service status
    sudo journalctl -u sms-rest-server -f     // View real-time logs

Authentication:
    Create credentials with: python3 sms-rest-server.py --create-htpasswd /var/lib/sms-rest-server/htpasswd admin
    (You will be prompted for the password; repeat for additional users.)

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
Updated: 2025-11-14 (E.164 international format support)
Author: geekinsanemx (https://github.com/geekinsanemx)
Version: 1.1.18
Changelog:
  - 1.1.18 (2025-11-15): Fixed htpasswd file ownership during installation
                        - Set htpasswd file ownership to sms-rest-server:sms-rest-server after creation
                        - Fixes "Permission denied" error when service tries to read htpasswd
  - 1.1.17 (2025-11-15): Fixed system user home directory for .gammurc config
                        - Changed user creation to use --home-dir /var/lib/sms-rest-server --create-home
                        - Ensures ~/.gammurc resolves to /var/lib/sms-rest-server/.gammurc
                        - Fixed "No such file or directory" error when service starts
  - 1.1.16 (2025-11-15): Added --uninstall function to remove service
                        - Created uninstall_service() function to reverse installation
                        - Stops and disables systemd service
                        - Removes service file, config file, and installation directory
                        - Prompts user for data directory and system user removal
                        - Added --uninstall option to CLI and help text
  - 1.1.15 (2025-11-15): Fixed installation password display bug and added dedicated system user
                        - Fixed undefined 'password' variable bug in installation output (line 1780)
                        - Created dedicated 'sms-rest-server' system user for service
                        - Service now runs as sms-rest-server user (not root) for security
                        - Added user to dialout group for serial port access
                        - Set proper ownership of /var/lib/sms-rest-server/ directory
                        - Updated systemd service: User=sms-rest-server, Group=dialout
                        - Fixed password display to only show when newly created
  - 1.1.14 (2025-11-15): Added requirements.txt and auto-install for Python dependencies
                        - Created requirements.txt with all Python package dependencies
                        - Updated --install to offer automatic pip package installation
                        - Updated fix_prerequisites_guide() to suggest requirements.txt usage
                        - Installation now prompts to install missing packages automatically
  - 1.1.13 (2025-11-15): Fixed recharge reply matching for 7373
                        - Recharge replies from PASA TIEMPO (sent to 7373) now matched by device number in text
                        - Extracts device number from message and checks if present in reply
                        - Special case handling: to_number='7373' + device_number in reply text
                        - Matches modem version behavior for recharge confirmations
  - 1.1.12 (2025-11-15): Fixed balance check reply matching
                        - Balance replies from Telcel (sent to 333) now matched by 'saldo' in text
                        - Special case handling: to_number='333' + reply contains 'saldo'
                        - Matches modem version behavior for balance checks
  - 1.1.11 (2025-11-15): Enhanced logging with message ID column
                        - Added message_id column to all SMS send logs
                        - Added REPLY RECEIVED logging when reply is matched to message
                        - Added REPLY TIMEOUT logging when message times out waiting
                        - Added STORE EXPIRED logging when messages are removed from store
                        - Format: [PREFIX] timestamp | message_id | parties | ACTION | details
                        - Improved grep/filtering by message ID for operational tracking
  - 1.1.10 (2025-11-14): E.164 international phone number format support
                        - Added LOCAL_COUNTRY_CODE constant (+52 for Mexico, configurable)
                        - Internal format changed to E.164 (+{country_code}{number})
                        - Accepted formats: 10 digits (auto +52), +{country}{number}, operator services
                        - Rejected: 11+ digits without + (ambiguous country code)
                        - Updated validate_and_normalize_phone() for E.164 validation
                        - Updated normalize_phone_number() to return E.164 format
                        - Updated check_sms_reply() for direct E.164 comparison
                        - Reply matching now works with modem's natural E.164 format
                        - Backward compatible: API still accepts same formats
  - 1.1.9 (2025-11-14): Added operator service numbers support
                        - Added OPERATOR_SERVICE_NUMBERS constant (2222, 7373)
                        - Operator numbers bypass country code normalization
                        - Updated phone validation to accept operator service numbers
                        - Updated normalize_phone_number to preserve operator numbers
                        - Operator numbers work with reply waiting (though most don't reply)
  - 1.1.8 (2025-11-14): Bug fixes and documentation cleanup
                        - CRITICAL: Fixed timezone bug - removed 'Z' suffix from local time timestamps
                        - Removed dead code (unused SMS_CHECK_INTERVAL variable)
                        - Fixed all documentation inconsistencies (file names, service names, paths)
                        - Updated all references: sms_rest_service.py → sms-rest-server.py
                        - Updated service name: sms-rest.service → sms-rest-server.service
                        - Updated paths: /etc/sms-rest/ → /var/lib/sms-rest-server/
                        - Updated authentication instructions to use --create-htpasswd flag
  - 1.1.7 (2025-11-14): CRITICAL FIX: SMS reply detection now processes ALL inbox messages + timezone fix
                        - Replaced single GetNextSMS() with full inbox iteration pattern
                        - Added get_sms_with_locations() helper - iterates through complete inbox
                        - Added check_sms_reply() helper - filters by phone + timestamp
                        - Separate collection from processing pattern (NEVER process during iteration)
                        - Reply waiting now works correctly (was only checking first message)
                        - Uses 5-second check interval for reply detection
                        - CRITICAL: Fixed timezone mismatch - use local time for both sent_timestamp and SMS datetime
                        - Modem returns SMS DateTime in local time, not UTC (was incorrectly marking as UTC)
  - 1.1.6 (2025-11-13): Fixed SMS reply handling and improved modem initialization
                        - Added timestamp-based reply filtering (prevents old stored messages)
                        - Record sent_timestamp before sending SMS
                        - get_sms_replies() now filters messages by timestamp (only accept after send)
                        - Smart gammurc validation (reuse existing config if valid, no scan)
                        - Added read_port_from_gammurc() and test_existing_gammu_config()
                        - Replaced Python SMS cleanup with gammu CLI (more reliable)
                        - clear_inbox_with_gammu_cli() uses subprocess.run(['gammu', 'deleteallsms'])
                        - Fixed modem init flow: Init → Terminate → Clean inbox → Re-init
                        - Removed cleanup_all_sms_messages() (replaced by CLI version)
  - 1.1.5 (2025-11-13): Fixed phone number validation regex bug
                        - Changed from r'^\+?52?\d{10}$' to r'^(\+?52)?\d{10}$'
                        - Previous regex incorrectly required "5" at start
                        - Now correctly accepts: "1234567890", "+521234567890", "521234567890"
  - 1.1.4 (2025-11-13): Removed personal phone number from documentation examples
  - 1.1.3 (2025-11-13): Accept phone numbers with optional +52 Mexican country code prefix
                        - Updated validation regex to accept: "1234567890", "+521234567890", "521234567890"
                        - API responses show original format as received in 'to' field
                        - Modem receives normalized 10-digit number
                        - Updated error message and API documentation
  - 1.1.2 (2025-11-13): Fixed Author attribution line (removed Claude attribution per workflow rules)
  - 1.1.1 (2025-11-13): Service now exits with error if modem initialization fails at startup
                        - Added fatal error check in main() to prevent running without modem
                        - Added helpful troubleshooting messages on modem init failure
                        - Prevents broken service state (systemd will handle restarts)
  - 1.1.0 (2025-11-13): Standardized REST API response format (industry standard for SMS/messaging APIs)
                        - Consistent response structure for all endpoints (success/error)
                        - Added unique message_id (UUID v4) for message tracking
                        - ISO-8601 timestamps (UTC) for all responses
                        - Machine-readable error codes (AUTHENTICATION_REQUIRED, INVALID_PHONE_NUMBER, etc.)
                        - Flat response structure optimized for Lambda/serverless
                        - Always include 'message' field showing sent/intended text
                        - Standardized status values: 'sent', 'delivered', 'timeout', 'failed'
                        - Simplified reply structure with ISO-8601 timestamps
                        - Added meta field for warnings (truncation, etc.)
  - 1.0.3 (2025-11-13): Removed 'count' field, added 'elapsed_time' to show actual time spent
                        waiting for reply, included 'timeout' value in response
  - 1.0.2 (2025-11-13): Added 'timeout' field in JSON payload for custom reply wait time,
                        changed reply check interval from 1s to 5s for efficiency
  - 1.0.1 (2025-11-13): Added config file support (/etc/default/sms-rest-server), --config option,
                        integrated --create-htpasswd functionality, updated installation paths to
                        /usr/local/SMS-REST-Server/, removed /etc/sms-rest/ dependency
  - 1.0.0 (2025-08-25): Initial release with installation system
"""

VERSION = "1.1.18"

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
import uuid
import threading
from queue import Queue, Empty
from datetime import datetime, timezone, timedelta
import getpass

app = Flask(__name__)

htpasswd_file = None
debug = False
config_file = None

# ---- Configurable defaults (override via config file or editing here) ----
SERVICE_PORT = 18180
SMS_REPLY_TIMEOUT = 60
REPLY_POLL_INTERVAL = 5
TIMEOUT_SWEEP_INTERVAL = 5
QUEUE_WAIT_SECONDS = 1
MESSAGE_RETENTION_SECONDS = 24 * 60 * 60

modem_device = None
global_modem = None

message_store = {}
message_lock = threading.RLock()
send_queue = Queue()
worker_thread = None
worker_stop_event = threading.Event()
LOCAL_TIMEZONE = datetime.now().astimezone().tzinfo

OPERATOR_SERVICE_NUMBERS = ['2222', '7373', '333']

LOCAL_COUNTRY_CODE = '+52'
ERROR_CODES = {
    'AUTHENTICATION_REQUIRED': 'Authentication required',
    'INVALID_CONTENT_TYPE': 'Content-Type must be application/json',
    'INVALID_JSON': 'Request body must contain valid JSON',
    'MISSING_REQUIRED_FIELDS': 'Missing required fields',
    'INVALID_PHONE_NUMBER': 'Phone number must be 10 digits (optional +52 prefix)',
    'INVALID_TIMEOUT_VALUE': 'Timeout must be between 1 and 600 seconds',
    'INVALID_TIMEOUT_FORMAT': 'Timeout must be a valid integer',
    'MODEM_NOT_AVAILABLE': 'Could not establish connection to GSM modem',
    'MODEM_TIMEOUT': 'Timeout while sending SMS',
    'MODEM_DEVICE_ERROR': 'Device not found',
    'MODEM_PERMISSION_ERROR': 'Permission denied',
    'SEND_FAILED': 'Failed to send SMS',
    'NOT_FOUND': 'Message not found'
}

SMS_ERROR_CODE_MAP = {
    'timeout': 'MODEM_TIMEOUT',
    'device_error': 'MODEM_DEVICE_ERROR',
    'permission_error': 'MODEM_PERMISSION_ERROR',
    'failed': 'SEND_FAILED'
}

def format_timestamp(dt=None):
    if dt is None:
        target = datetime.now(timezone.utc)
    else:
        target = ensure_utc(dt)
    return target.strftime('%Y-%m-%dT%H:%M:%SZ')


def build_api_response(status, message_id=None, to=None, from_user=None, message_text=None,
                       error_code=None, error_message=None, reply_data=None, meta=None,
                       http_status=200, timestamp_override=None):
    if timestamp_override is not None:
        if isinstance(timestamp_override, str):
            timestamp = timestamp_override
        else:
            timestamp = format_timestamp(timestamp_override)
    else:
        timestamp = format_timestamp()

    response = {
        'status': status,
        'message_id': message_id,
        'timestamp': timestamp,
        'to': to,
        'from': from_user,
        'message': message_text,
        'reply': reply_data if reply_data is not None else None
    }

    if error_code or error_message:
        response['error_code'] = error_code
        response['error_message'] = error_message

    if meta:
        response['meta'] = meta

    return jsonify(response), http_status


def ensure_utc(dt):
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=LOCAL_TIMEZONE).astimezone(timezone.utc)
    return dt.astimezone(timezone.utc)


def create_message_record(message_id, *, original_number, normalized_number, message_text,
                          username, requires_reply, timeout_seconds, meta, client_ip):
    now = datetime.now(timezone.utc)
    record = {
        'message_id': message_id,
        'original_number': original_number,
        'to_number': normalized_number,
        'message': message_text,
        'from_user': username,
        'status': 'queued',
        'created_at': now,
        'sent_at': None,
        'requires_reply': requires_reply,
        'timeout_seconds': timeout_seconds if requires_reply else None,
        'reply_text': None,
        'reply_at': None,
        'elapsed_seconds': None,
        'error_code': None,
        'error_message': None,
        'meta': meta,
        'client_ip': client_ip
    }

    with message_lock:
        message_store[message_id] = record

    return record


def update_message_record(message_id, **updates):
    with message_lock:
        record = message_store.get(message_id)
        if not record:
            return None
        for key, value in updates.items():
            record[key] = value
        return record.copy()


def get_message_record(message_id):
    with message_lock:
        record = message_store.get(message_id)
        return record.copy() if record else None


def determine_record_timestamp(record):
    if record.get('status') in ['sent', 'failed', 'replied', 'timeout'] and record.get('sent_at'):
        return record['sent_at']
    return record.get('created_at')


def build_reply_payload(record):
    if record.get('reply_text') and record.get('reply_at'):
        return {
            'text': record['reply_text'],
            'received_at': format_timestamp(record['reply_at']),
            'elapsed_seconds': record.get('elapsed_seconds')
        }
    return None


def apply_reply_to_message(sender_number, reply_text, sms_datetime):
    if not sender_number:
        return None

    sms_dt = ensure_utc(sms_datetime) or datetime.now(timezone.utc)
    best_id = None
    best_record = None

    with message_lock:
        for message_id, record in message_store.items():
            if not record.get('requires_reply') or record.get('status') != 'sent':
                continue

            to_number = record.get('to_number')
            message_text = record.get('message', '')

            is_balance_reply = (to_number == '333' and 'saldo' in reply_text.lower())

            is_recharge_reply = False
            if to_number == '7373':
                match = re.search(r'\d+', message_text)
                if match:
                    device_number = match.group(0)
                    is_recharge_reply = device_number in reply_text

            if not is_balance_reply and not is_recharge_reply and not phone_numbers_match(to_number, sender_number):
                continue

            sent_at = record.get('sent_at')
            if not sent_at:
                continue

            timeout_window = record.get('timeout_seconds') or SMS_REPLY_TIMEOUT
            deadline = sent_at + timedelta(seconds=timeout_window)

            if sms_dt <= sent_at or sms_dt > deadline:
                continue

            if best_record is None or sent_at > best_record.get('sent_at'):
                best_id = message_id
                best_record = record

        if not best_record:
            return None

        elapsed = None
        if best_record.get('sent_at'):
            elapsed = max(int((sms_dt - best_record['sent_at']).total_seconds()), 0)

        best_record.update({
            'status': 'replied',
            'reply_text': reply_text,
            'reply_at': sms_dt,
            'elapsed_seconds': elapsed,
            'error_code': None,
            'error_message': None
        })

        msg_id_display = best_id if best_id else "no-msg-id"
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        reply_preview = f"'{reply_text[:50]}{'...' if len(reply_text) > 50 else ''}'"
        from_user = best_record.get('from_user', 'unknown')
        print(f"[REPLY] {timestamp} | {msg_id_display} | {sender_number} → {from_user} | RECEIVED | {reply_preview} (elapsed: {elapsed}s)")

        return best_id


def handle_timeouts():
    now = datetime.now(timezone.utc)
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    with message_lock:
        for message_id, record in message_store.items():
            if not record.get('requires_reply') or record.get('status') != 'sent':
                continue
            sent_at = record.get('sent_at')
            if not sent_at:
                continue

            timeout_window = record.get('timeout_seconds') or SMS_REPLY_TIMEOUT
            deadline = sent_at + timedelta(seconds=timeout_window)
            if now > deadline:
                record['status'] = 'timeout'
                elapsed = int((now - sent_at).total_seconds())
                record['elapsed_seconds'] = max(elapsed, timeout_window)
                record['reply_text'] = None
                record['reply_at'] = None

                msg_id_display = message_id if message_id else "no-msg-id"
                from_user = record.get('from_user', 'unknown')
                to_number = record.get('to_number', 'unknown')
                print(f"[REPLY] {timestamp} | {msg_id_display} | {from_user} → {to_number} | TIMEOUT | waited {timeout_window}s")


def poll_incoming_replies(sm):
    cleanup_expired_messages()
    try:
        messages = get_sms_with_locations(sm)
    except Exception as exc:
        if debug:
            print(f"[REPLY] Poll error: {exc}")
        return False

    for sms in messages:
        sender = str(sms.get('Number', '')).strip()
        sms_dt = ensure_utc(sms.get('DateTime')) or datetime.now(timezone.utc)
        reply_text = sms.get('Text', '')
        location = sms.get('Location')
        folder = sms.get('Folder', 0)

        matched_id = apply_reply_to_message(sender, reply_text, sms_dt)
        if matched_id:
            if debug:
                print(f"[REPLY] Matched incoming SMS from {sender} to message {matched_id}")
            try:
                if location is not None:
                    sm.DeleteSMS(Folder=folder, Location=location)
            except Exception as exc:
                if debug:
                    print(f"[REPLY] Failed to delete SMS at location {location}: {exc}")

    return True


def cleanup_expired_messages():
    if MESSAGE_RETENTION_SECONDS <= 0:
        return

    cutoff = datetime.now(timezone.utc) - timedelta(seconds=MESSAGE_RETENTION_SECONDS)
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    removed = []
    with message_lock:
        for message_id, record in list(message_store.items()):
            created_at = record.get('created_at')
            if created_at and created_at < cutoff:
                age_hours = int((datetime.now(timezone.utc) - created_at).total_seconds() / 3600)
                status = record.get('status', 'unknown')
                msg_id_display = message_id if message_id else "no-msg-id"
                print(f"[STORE] {timestamp} | {msg_id_display} | EXPIRED | age: {age_hours}h, status: {status}")
                removed.append(message_id)
                del message_store[message_id]


def process_send_job(sm, job):
    message_id = job['message_id']
    now = datetime.now(timezone.utc)

    sms_success, sms_status, sms_details = send_sms(
        sm,
        job['to_number'],
        job['message'],
        sender_user=job.get('from_user'),
        source_ip=job.get('client_ip'),
        reply_expected=job.get('requires_reply', False),
        message_id=message_id
    )

    if sms_success:
        update_message_record(
            message_id,
            status='sent',
            sent_at=now,
            error_code=None,
            error_message=None
        )
        return True, None
    else:
        error_code = SMS_ERROR_CODE_MAP.get(sms_status, 'SEND_FAILED')
        update_message_record(
            message_id,
            status='failed',
            sent_at=now,
            error_code=error_code,
            error_message=sms_details
        )
        return False, sms_status


def gsm_worker_loop():
    sm = None
    last_reply_poll = 0
    last_timeout_check = 0

    while not worker_stop_event.is_set() or not send_queue.empty():
        job = None
        try:
            job = send_queue.get(timeout=QUEUE_WAIT_SECONDS)
        except Empty:
            job = None

        if job:
            if sm is None:
                sm = get_modem_connection()
            if not sm:
                update_message_record(
                    job['message_id'],
                    status='failed',
                    sent_at=datetime.now(timezone.utc),
                    error_code='MODEM_NOT_AVAILABLE',
                    error_message=ERROR_CODES['MODEM_NOT_AVAILABLE']
                )
                send_queue.task_done()
            else:
                try:
                    success, failure_status = process_send_job(sm, job)
                    if not success and failure_status in ('device_error', 'permission_error'):
                        sm = None
                except Exception as exc:
                    update_message_record(
                        job['message_id'],
                        status='failed',
                        sent_at=datetime.now(timezone.utc),
                        error_code='SEND_FAILED',
                        error_message=str(exc)
                    )
                    if debug:
                        print(f"[WORKER] Send job error: {exc}")
                    sm = None
                finally:
                    send_queue.task_done()

        now = time.time()
        if now - last_reply_poll >= REPLY_POLL_INTERVAL:
            if sm is None:
                sm = get_modem_connection()
            if sm:
                poll_success = poll_incoming_replies(sm)
                if not poll_success:
                    sm = None
            last_reply_poll = now

        if now - last_timeout_check >= TIMEOUT_SWEEP_INTERVAL:
            handle_timeouts()
            last_timeout_check = now

    if debug:
        print("[WORKER] GSM worker stopped")


def start_gsm_worker():
    global worker_thread
    if worker_thread and worker_thread.is_alive():
        return
    worker_stop_event.clear()
    worker_thread = threading.Thread(target=gsm_worker_loop, name='gsm-worker', daemon=True)
    worker_thread.start()
    if debug:
        print("[WORKER] GSM worker started")


def stop_gsm_worker():
    global worker_thread
    worker_stop_event.set()
    if worker_thread and worker_thread.is_alive():
        worker_thread.join(timeout=5)
    worker_thread = None

def read_port_from_gammurc():
    config_path = os.path.expanduser('~/.gammurc')

    if not os.path.exists(config_path):
        return None

    try:
        with open(config_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line.startswith('port') and '=' in line:
                    port = line.split('=')[1].strip()
                    return port
    except Exception:
        return None

    return None

def test_existing_gammu_config():
    try:
        sm = gammu.StateMachine()
        sm.ReadConfig()
        sm.Init()

        try:
            manufacturer = sm.GetManufacturer()
            sm.Terminate()
            return True, manufacturer
        except:
            sm.Terminate()
            return True, "Unknown"

    except Exception:
        return False, None

def clear_inbox_with_gammu(sm):
    try:
        folders = sm.GetSMSFolders()
    except Exception as exc:
        print(f"❌ Unable to read SMS folders: {exc}")
        return False

    cleaned = 0
    for folder in folders:
        folder_id = folder.get('Folder', 0)
        folder_name = folder.get('Name', f"Folder {folder_id}")
        if debug:
            print(f"🗑️ Cleaning SMS folder {folder_id} ({folder_name})...")
        start = True
        last_batch = None
        while True:
            try:
                if start:
                    last_batch = sm.GetNextSMS(Start=True, Folder=folder_id)
                    start = False
                else:
                    last_batch = sm.GetNextSMS(Location=last_batch[0]['Location'], Folder=folder_id)
            except gammu.ERR_EMPTY:
                break
            except Exception as exc:
                print(f"❌ Error reading folder {folder_id} ({folder_name}): {exc}")
                break

            for message in last_batch:
                location = message.get('Location')
                try:
                    sm.DeleteSMS(Folder=folder_id, Location=location)
                    cleaned += 1
                except Exception as exc:
                    print(f"❌ Failed to delete SMS at folder {folder_id}, location {location}: {exc}")

    if cleaned > 0:
        print(f"[CLEAN] SMS inbox cleaned ({cleaned} messages deleted)")
    else:
        print("[CLEAN] SMS inbox already empty")
    return True

def print_usage():
    print(f"""
SMS REST Service v{VERSION}

Usage:
    sms-rest-server.py [OPTIONS]

Options:
    --port PORT              Port to run the service on (default: 18180)
    --htpasswd FILE          Path to htpasswd file for authentication
    --device DEVICE          Specific modem device (e.g., /dev/ttyUSB0)
    --config FILE            Load configuration from file
    --debug                  Enable debug mode
    --install                Install service system-wide
    --uninstall              Uninstall service (removes systemd service, prompts for data/user removal)
    --create-htpasswd FILE USER [PASS]  Create/update htpasswd entry (prompts for PASS if omitted)
    --update-htpasswd FILE USER [PASS]  Alias for --create-htpasswd
    --help                   Show this help message

Config File:
    Default: /etc/default/sms-rest-server (if exists)
    Format: KEY=VALUE (shell-style)
    Supported keys: PORT, HTPASSWD_FILE, DEVICE, DEBUG,
                    SMS_REPLY_TIMEOUT, REPLY_POLL_INTERVAL,
                    TIMEOUT_SWEEP_INTERVAL, QUEUE_WAIT_SECONDS,
                    MESSAGE_RETENTION_SECONDS
    Priority: CLI args > --config file > /etc/default/sms-rest-server > defaults

Examples:
    # Run with config file
    sms-rest-server.py --config /etc/default/sms-rest-server

    # Run with CLI arguments (override config)
    sms-rest-server.py --port 18180 --htpasswd /var/lib/sms-rest-server/htpasswd

    # Create htpasswd file (interactive password prompt)
    sms-rest-server.py --create-htpasswd /var/lib/sms-rest-server/htpasswd admin

    # Update existing user (alias works the same way)
    sms-rest-server.py --update-htpasswd /var/lib/sms-rest-server/htpasswd admin

    # Install as system service
    sudo sms-rest-server.py --install

    # Uninstall system service
    sudo sms-rest-server.py --uninstall

API Usage:
    # Send SMS without waiting for reply
    curl -X POST http://localhost:18180/ \\
         -u <user>:<password> \\
         -H "Content-Type: application/json" \\
         -d '{{"Number": "1234567890", "message": "Test message"}}'

    # Send SMS and wait for reply (with custom timeout)
    curl -X POST http://localhost:18180/ \\
         -u <user>:<password> \\
         -H "Content-Type: application/json" \\
         -d '{{"Number": "1234567890", "message": "Test", "reply": true, "timeout": 120}}'
""")

def create_htpasswd_entry(username, password):
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return f"{username}:{hashed.decode('utf-8')}"

def create_htpasswd_file(username, password, output_file):
    try:
        entry = create_htpasswd_entry(username, password)

        output_dir = os.path.dirname(output_file)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, mode=0o755, exist_ok=True)

        lines = []
        replaced = False
        if os.path.exists(output_file):
            with open(output_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    existing_user = line.split(':', 1)[0]
                    if existing_user == username:
                        lines.append(entry)
                        replaced = True
                    else:
                        lines.append(line)
        if not replaced:
            lines.append(entry)

        with open(output_file, 'w') as f:
            for line in lines:
                f.write(line + '\n')

        os.chmod(output_file, 0o600)

        if '/var/lib/sms-rest-server' in output_file:
            try:
                import pwd
                sms_user = pwd.getpwnam('sms-rest-server')
                os.chown(output_file, sms_user.pw_uid, sms_user.pw_gid)
                if replaced:
                    print(f"✅ Updated htpasswd entry for '{username}' in {output_file} (ownership: sms-rest-server)")
                else:
                    print(f"✅ Added '{username}' to htpasswd file: {output_file} (ownership: sms-rest-server)")
            except (KeyError, Exception) as e:
                if replaced:
                    print(f"✅ Updated htpasswd entry for '{username}' in {output_file}")
                else:
                    print(f"✅ Added '{username}' to htpasswd file: {output_file}")
                print(f"   ⚠️  Could not set ownership to sms-rest-server: {e}")
        else:
            if replaced:
                print(f"✅ Updated htpasswd entry for '{username}' in {output_file}")
            else:
                print(f"✅ Added '{username}' to htpasswd file: {output_file}")

        return True
    except Exception as e:
        print(f"❌ Error creating htpasswd file: {e}")
        return False


def prompt_for_password(username="user"):
    while True:
        pwd = getpass.getpass(f"Enter password for '{username}': ")
        if not pwd:
            print("Password cannot be empty. Please try again.")
            continue
        confirm = getpass.getpass("Confirm password: ")
        if pwd != confirm:
            print("Passwords do not match. Please try again.")
            continue
        return pwd

def parse_config_file(config_path):
    config = {}

    if not os.path.exists(config_path):
        return config

    try:
        with open(config_path, 'r') as f:
            for line in f:
                line = line.strip()

                if not line or line.startswith('#'):
                    continue

                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()

                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]

                    config[key] = value

        if debug:
            print(f"📄 Loaded config from: {config_path}")
            for key, value in config.items():
                print(f"   {key}={value}")

        return config
    except Exception as e:
        print(f"⚠️  Error reading config file {config_path}: {e}")
        return {}

def load_config():
    global config_file

    if config_file and os.path.exists(config_file):
        return parse_config_file(config_file)

    default_config = '/etc/default/sms-rest-server'
    if os.path.exists(default_config):
        return parse_config_file(default_config)

    return {}


def get_int_config(config, key, current_value, min_value=None, max_value=None):
    if key not in config:
        return current_value

    raw_value = config[key]
    try:
        value = int(raw_value)
        if min_value is not None and value < min_value:
            raise ValueError
        if max_value is not None and value > max_value:
            raise ValueError
        return value
    except ValueError:
        print(f"Warning: Invalid value for {key} in config ({raw_value}), keeping {current_value}")
        return current_value

def detect_modem_port():
    print("🔍 Auto-detecting modem port...")

    usb_ports = []
    for i in range(10):
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
        config_path = os.path.expanduser('~/.gammurc')

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
    try:
        sm = gammu.StateMachine()
        sm.ReadConfig()
        sm.Init()

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
    global modem_device

    if modem_device:
        if not os.path.exists(modem_device):
            print(f"[MODEM] Specified device does not exist: {modem_device}")
            return None

        existing_port = read_port_from_gammurc()
        if existing_port == modem_device:
            config_valid, manufacturer = test_existing_gammu_config()

            if config_valid:
                sm = gammu.StateMachine()
                sm.ReadConfig()
                sm.Init()
                manufacturer_info = f" ({manufacturer})" if manufacturer else ""
                print(f"[MODEM] Using existing config: {modem_device}{manufacturer_info}")
                return sm

        if not update_gammu_config(modem_device):
            return None

        test_success, test_message = test_gammu_config()
        if not test_success:
            print(f"[MODEM] Config test failed for {modem_device}: {test_message}")
            return None

        # Initialize modem
        try:
            sm = gammu.StateMachine()
            sm.ReadConfig()
            sm.Init()
            print(f"[MODEM] Initialized on {modem_device}")
            return sm
        except Exception as e:
            print(f"[MODEM] Failed to initialize on {modem_device}: {e}")
            return None

    existing_port = read_port_from_gammurc()

    if existing_port:
        config_valid, manufacturer = test_existing_gammu_config()

        if config_valid:
            sm = gammu.StateMachine()
            sm.ReadConfig()
            sm.Init()
            manufacturer_info = f" ({manufacturer})" if manufacturer else ""
            print(f"[MODEM] Using existing config: {existing_port}{manufacturer_info}")
            return sm

    mm_stopped = False
    if is_modemmanager_running():
        if stop_modem_manager():
            mm_stopped = True
        else:
            print("[MODEM] Failed to stop ModemManager")
            return None

    detect_success, port, manufacturer = detect_modem_port()
    if not detect_success:
        print(f"[MODEM] Detection failed: {manufacturer}")
        if mm_stopped:
            start_modem_manager()
        return None

    if not update_gammu_config(port):
        if mm_stopped:
            start_modem_manager()
        return None

    test_success, test_message = test_gammu_config()
    if not test_success:
        print(f"[MODEM] Config test failed: {test_message}")
        if mm_stopped:
            start_modem_manager()
        return None

    try:
        sm = gammu.StateMachine()
        sm.ReadConfig()
        sm.Init()
        print(f"[MODEM] Initialized on {port} ({manufacturer})")
        return sm
    except Exception as e:
        print(f"[MODEM] Failed to initialize: {e}")
        if mm_stopped:
            start_modem_manager()
        return None

def init_modem():
    return init_modem_intelligent()

def check_modemmanager_exists():
    try:
        result = subprocess.run(['systemctl', 'list-units', '--all', 'ModemManager.service'],
                              capture_output=True, text=True, timeout=5)
        return 'ModemManager.service' in result.stdout
    except Exception:
        return False

def is_modemmanager_running():
    try:
        result = subprocess.run(['systemctl', 'is-active', 'ModemManager.service'],
                              capture_output=True, text=True, timeout=5)
        return result.stdout.strip() == 'active'
    except Exception:
        return False

def stop_modem_manager():
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
        time.sleep(2)
        if debug:
            print("ModemManager service stopped successfully")
        return True
    except Exception as e:
        if debug:
            print(f"Failed to stop ModemManager: {e}")
        return False

def start_modem_manager():
    if not check_modemmanager_exists():
        if debug:
            print("ModemManager service does not exist, skipping start")
        return True

    try:
        if debug:
            print("Starting ModemManager service...")
        result = subprocess.run(['sudo', 'systemctl', 'start', 'ModemManager.service'],
                              capture_output=True, text=True, timeout=10)
        time.sleep(2)
        if debug:
            print("ModemManager service started successfully")
        return True
    except Exception as e:
        if debug:
            print(f"Failed to start ModemManager: {e}")
        return False

def send_sms(sm, phone_number, message, sender_user=None, source_ip=None, reply_expected=False, message_id=None):
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    msg_id_display = message_id if message_id else "no-msg-id"

    try:
        sms_info = {
            'Text': message,
            'SMSC': {'Location': 1},
            'Number': phone_number
        }

        result = sm.SendSMS(sms_info)

        sender_info = f"{sender_user or 'system'} ({source_ip})" if source_ip else (sender_user or 'system')

        reply_status = " (reply expected)" if reply_expected else ""
        message_preview = f"'{message[:50]}{'...' if len(message) > 50 else ''}'"
        print(f"[SMS] {timestamp} | {msg_id_display} | {sender_info} → {phone_number} | SUCCESS{reply_status} | {message_preview}")

        return True, "success", "SMS sent successfully"

    except gammu.ERR_TIMEOUT as e:
        error_msg = f"Timeout while sending SMS to {phone_number}: {str(e)}"

        sender_info = f"{sender_user or 'system'} ({source_ip})" if source_ip else (sender_user or 'system')

        reply_status = " (reply expected)" if reply_expected else ""
        message_preview = f"'{message[:50]}{'...' if len(message) > 50 else ''}'"
        print(f"[SMS] {timestamp} | {msg_id_display} | {sender_info} → {phone_number} | TIMEOUT{reply_status} | {message_preview}")

        return False, "timeout", error_msg

    except gammu.ERR_DEVICENOTEXIST as e:
        error_msg = f"Device not found while sending SMS to {phone_number}: {str(e)}"

        sender_info = f"{sender_user or 'system'} ({source_ip})" if source_ip else (sender_user or 'system')

        reply_status = " (reply expected)" if reply_expected else ""
        message_preview = f"'{message[:50]}{'...' if len(message) > 50 else ''}'"
        print(f"[SMS] {timestamp} | {msg_id_display} | {sender_info} → {phone_number} | DEVICE_ERROR{reply_status} | {message_preview}")

        return False, "device_error", error_msg

    except gammu.ERR_DEVICENOPERMISSION as e:
        error_msg = f"Permission denied while sending SMS to {phone_number}: {str(e)}"

        sender_info = f"{sender_user or 'system'} ({source_ip})" if source_ip else (sender_user or 'system')

        reply_status = " (reply expected)" if reply_expected else ""
        message_preview = f"'{message[:50]}{'...' if len(message) > 50 else ''}'"
        print(f"[SMS] {timestamp} | {msg_id_display} | {sender_info} → {phone_number} | PERMISSION_ERROR{reply_status} | {message_preview}")

        return False, "permission_error", error_msg

    except Exception as e:
        error_msg = f"Failed to send SMS to {phone_number}: {str(e)}"

        sender_info = f"{sender_user or 'system'} ({source_ip})" if source_ip else (sender_user or 'system')

        reply_status = " (reply expected)" if reply_expected else ""
        message_preview = f"'{message[:50]}{'...' if len(message) > 50 else ''}'"
        print(f"[SMS] {timestamp} | {msg_id_display} | {sender_info} → {phone_number} | ERROR{reply_status} | {message_preview}")

        return False, "failed", error_msg

def validate_and_normalize_phone(phone_number):
    if str(phone_number) in OPERATOR_SERVICE_NUMBERS:
        return True, str(phone_number), None

    clean = str(phone_number).replace(' ', '').replace('-', '')

    if clean.startswith('+'):
        if re.match(r'^\+\d{1,3}\d{4,14}$', clean):
            return True, clean, None
        else:
            return False, None, 'Invalid E.164 format (use +{country_code}{number})'

    if re.match(r'^\d{10}$', clean):
        return True, f"{LOCAL_COUNTRY_CODE}{clean}", None

    if re.match(r'^\d{11,}$', clean):
        return False, None, 'Ambiguous format (use +{country_code}{number} for international numbers)'

    return False, None, 'Invalid phone number format (use 10 digits or +{country_code}{number})'

def normalize_phone_number(phone_number):
    valid, normalized, error = validate_and_normalize_phone(phone_number)

    if valid:
        return normalized
    else:
        return str(phone_number)

def phone_numbers_match(number1, number2):
    norm1 = normalize_phone_number(number1)
    norm2 = normalize_phone_number(number2)

    if debug:
        print(f"🔍 Number matching: '{number1}' -> '{norm1}' vs '{number2}' -> '{norm2}'")

    return norm1 == norm2

def get_sms_with_locations(sm):
    response = []
    try:
        status = sm.GetSMSStatus()
        remain = status["SIMUsed"] + status["PhoneUsed"] + status["TemplatesUsed"]
        start = True
        while remain > 0:
            if start:
                sms = sm.GetNextSMS(Start=True, Folder=0)
                start = False
            else:
                sms = sm.GetNextSMS(Location=sms[0]["Location"], Folder=0)
            remain = remain - len(sms)
            for m in sms:
                response.append({
                    "Number": m['Number'],
                    "DateTime": m.get('DateTime'),
                    "State": m.get('State'),
                    "Text": m['Text'],
                    "Location": m['Location']
                })
    except gammu.ERR_EMPTY:
        pass
    return response

def load_htpasswd_users(htpasswd_path):
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
    try:
        if stored_hash.startswith('$2b$') or stored_hash.startswith('$2a$') or stored_hash.startswith('$2y$'):
            return bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8'))
        else:
            return check_password_hash(stored_hash, password)
    except Exception as e:
        if debug:
            print(f"Password verification error: {e}")
        return False

def initialize_global_modem():
    global global_modem

    print("[MODEM] Initializing connection...")
    global_modem = init_modem_intelligent()

    if not global_modem:
        print("[MODEM] Failed to establish connection")
        return False

    print("[CLEAN] Clearing SMS inbox...")
    if not clear_inbox_with_gammu(global_modem):
        print("[CLEAN] Inbox cleanup failed, continuing...")

    print("[MODEM] Connection established")
    return True

def get_modem_connection():
    global global_modem

    if global_modem is None:
        if debug:
            print("🔄 Global modem is None, attempting to initialize...")
        global_modem = init_modem_intelligent()

    if global_modem:
        try:
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
    print("🔍 Checking system prerequisites...")
    issues = []
    warnings = []

    if os.geteuid() != 0:
        issues.append("Root privileges required. Run with sudo.")

    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
        issues.append(f"Python 3.8+ required. Current: {python_version.major}.{python_version.minor}")
    else:
        print(f"   ✅ Python version: {python_version.major}.{python_version.minor}.{python_version.micro}")

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

    if not os.path.exists('/etc/systemd/system'):
        issues.append("systemd not available (required for service installation)")
    else:
        print("   ✅ systemd is available")

    try:
        subprocess.run(['which', 'systemctl'], check=True, capture_output=True)
        print("   ✅ systemctl command is available")
    except subprocess.CalledProcessError:
        issues.append("systemctl command not found")

    if os.path.exists('/usr/local/bin/sms-rest-service'):
        warnings.append("Previous installation detected at /usr/local/bin/sms-rest-service")

    if os.path.exists('/etc/systemd/system/sms-rest-server.service'):
        warnings.append("Previous systemd service file detected")

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
            if os.getuid() == 0:
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
    print("\n" + "="*60)
    print("📋 SMS REST SERVER INSTALLATION WALKTHROUGH")
    print("="*60)
    print()
    print("This installation will:")
    print("  1. 📁 Create /usr/local/SMS-REST-Server/ directory")
    print("  2. 📁 Copy sms-rest-server.py and requirements.txt")
    print("  3. 👤 Create system user 'sms-rest-server' (added to dialout group)")
    print("  4. 📁 Create /var/lib/sms-rest-server/ data directory")
    print("  5. 🔐 Prompt you to create an initial htpasswd user (admin)")
    print("  6. 📄 Create /etc/default/sms-rest-server config file")
    print("  7. 🔧 Create /etc/systemd/system/sms-rest-server.service")
    print("  8. 🔄 Reload systemd daemon")
    print()
    print("⚠️  Note: Service will run as 'sms-rest-server' user (not root)")
    print()
    print("After installation, you can:")
    print("  • Start service: sudo systemctl start sms-rest-server")
    print("  • Enable auto-start: sudo systemctl enable sms-rest-server")
    print("  • Check status: sudo systemctl status sms-rest-server")
    print("  • View logs: sudo journalctl -u sms-rest-server -f")
    print()
    print("Service will run on: http://localhost:18180/")
    print()

    while True:
        response = input("Proceed with installation? [Y/n]: ").lower().strip()
        if response in ['', 'y', 'yes']:
            return True
        elif response in ['n', 'no']:
            return False
        else:
            print("Please enter 'y' for yes or 'n' for no.")

def fix_prerequisites_guide(missing_packages, script_dir):
    print("\n" + "="*60)
    print("🔧 PREREQUISITES FIX GUIDE")
    print("="*60)
    print()

    if missing_packages:
        requirements_file = os.path.join(script_dir, 'requirements.txt')

        print("📦 Install missing Python packages:")
        print()
        print("   Option 1 - Install from requirements.txt (recommended):")
        if os.path.exists(requirements_file):
            print(f"   pip3 install --break-system-packages -r {requirements_file}")
        else:
            print("   requirements.txt not found, use Option 2 or 3")
        print()
        print("   Option 2 - Install individually:")
        print(f"   pip3 install --break-system-packages {' '.join(missing_packages)}")
        print()
        print("   Option 3 - Using system package manager:")
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
    import shutil
    import pwd
    import grp

    print("=" * 60)
    print(f"📦 SMS REST SERVICE INSTALLATION v{VERSION}")
    print("=" * 60)
    print()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    issues, warnings, missing_packages = check_prerequisites()

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
            print("\nWould you like to install missing Python packages now? (y/n): ", end='', flush=True)
            response = input().strip().lower()
            if response in ['y', 'yes']:
                requirements_file = os.path.join(script_dir, 'requirements.txt')
                if os.path.exists(requirements_file):
                    print(f"\nInstalling packages from {requirements_file}...")
                    result = os.system(f'pip3 install --break-system-packages -r "{requirements_file}"')
                    if result == 0:
                        print("\n✅ Python packages installed successfully!")
                        print("Please run the installation again: sudo ./sms-rest-server.py --install")
                        sys.exit(0)
                    else:
                        print("\n❌ Failed to install Python packages")
                        fix_prerequisites_guide(missing_packages, script_dir)
                        sys.exit(1)
                else:
                    print("\n❌ requirements.txt not found")
                    fix_prerequisites_guide(missing_packages, script_dir)
                    sys.exit(1)
            else:
                fix_prerequisites_guide(missing_packages, script_dir)
                print("\nPlease fix the above issues and run the installation again.")
                sys.exit(1)
        else:
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
    script_dir = os.path.dirname(script_path)
    install_dir = "/usr/local/SMS-REST-Server"
    target_script = f"{install_dir}/sms-rest-server.py"
    target_requirements = f"{install_dir}/requirements.txt"
    service_file = "/etc/systemd/system/sms-rest-server.service"
    config_file = "/etc/default/sms-rest-server"
    data_dir = "/var/lib/sms-rest-server"
    htpasswd_path = f"{data_dir}/htpasswd"

    try:
        # 1. Create installation directory
        print(f"📁 Creating installation directory {install_dir}")
        os.makedirs(install_dir, exist_ok=True)
        os.chmod(install_dir, 0o755)

        # 2. Copy script to installation directory
        print(f"📁 Copying sms-rest-server.py to {target_script}")
        shutil.copy2(script_path, target_script)
        os.chmod(target_script, 0o755)

        # 3. Copy requirements.txt to installation directory
        requirements_source = os.path.join(script_dir, 'requirements.txt')
        if os.path.exists(requirements_source):
            print(f"📁 Copying requirements.txt to {target_requirements}")
            shutil.copy2(requirements_source, target_requirements)
            os.chmod(target_requirements, 0o644)
        else:
            print(f"⚠️  requirements.txt not found in {script_dir}, skipping")

        # 4. Create system user
        print(f"👤 Creating system user 'sms-rest-server'...")
        try:
            pwd.getpwnam('sms-rest-server')
            print(f"   ℹ️  User 'sms-rest-server' already exists, skipping user creation")
        except KeyError:
            result = os.system('useradd --system --home-dir /var/lib/sms-rest-server --create-home --shell /bin/false sms-rest-server')
            if result != 0:
                raise Exception("Failed to create system user 'sms-rest-server'")
            print(f"   ✅ Created system user 'sms-rest-server' (home: /var/lib/sms-rest-server)")

        try:
            grp.getgrnam('dialout')
            result = os.system('usermod -a -G dialout sms-rest-server')
            if result != 0:
                raise Exception("Failed to add user to dialout group")
            print(f"   ✅ Added 'sms-rest-server' to dialout group")
        except KeyError:
            print(f"   ⚠️  dialout group not found, skipping group assignment")

        # 5. Create data directory
        print(f"📁 Creating data directory {data_dir}")
        os.makedirs(data_dir, exist_ok=True)
        os.chmod(data_dir, 0o755)

        try:
            sms_user = pwd.getpwnam('sms-rest-server')
            os.chown(data_dir, sms_user.pw_uid, sms_user.pw_gid)
            print(f"   ✅ Set ownership to sms-rest-server:sms-rest-server")
        except Exception as e:
            print(f"   ⚠️  Could not set ownership: {e}")

        # 6. Create htpasswd file
        username = "admin"
        htpasswd_created = False
        admin_pwd = None
        if not os.path.exists(htpasswd_path):
            print(f"🔐 Creating htpasswd file at {htpasswd_path}")
            admin_pwd = prompt_for_password(username)
            create_htpasswd_file(username, admin_pwd, htpasswd_path)
            htpasswd_created = True

            try:
                sms_user = pwd.getpwnam('sms-rest-server')
                os.chown(htpasswd_path, sms_user.pw_uid, sms_user.pw_gid)
                print(f"   ✅ Set htpasswd ownership to sms-rest-server:sms-rest-server")
            except Exception as e:
                print(f"   ⚠️  Could not set htpasswd ownership: {e}")
        else:
            print(f"⚠️  htpasswd file already exists at {htpasswd_path}, skipping")

            try:
                sms_user = pwd.getpwnam('sms-rest-server')
                os.chown(htpasswd_path, sms_user.pw_uid, sms_user.pw_gid)
                print(f"   ✅ Validated htpasswd ownership (sms-rest-server:sms-rest-server)")
            except Exception as e:
                print(f"   ⚠️  Could not validate htpasswd ownership: {e}")

        # 7. Create config file
        if not os.path.exists(config_file):
            config_content = f"""# SMS REST Server Configuration
# This file is sourced by systemd service as environment variables
# Format: KEY=VALUE (shell-style)

# Service port
PORT=18180

# Authentication file
HTPASSWD_FILE={htpasswd_path}

# Modem device (uncomment to specify)
# DEVICE=/dev/ttyUSB0

# Debug mode (uncomment to enable)
# DEBUG=true

# Default reply timeout (seconds)
# SMS_REPLY_TIMEOUT=60

# Worker polling intervals (seconds)
# REPLY_POLL_INTERVAL=5
# TIMEOUT_SWEEP_INTERVAL=5
# QUEUE_WAIT_SECONDS=1

# Message retention window (seconds)
# MESSAGE_RETENTION_SECONDS=86400

# Configuration priority:
# 1. Command-line arguments (highest)
# 2. This file (/etc/default/sms-rest-server)
# 3. Code defaults (lowest)
#
# After modifying this file, restart the service:
# sudo systemctl restart sms-rest-server
"""
            print(f"📄 Creating config file at {config_file}")
            with open(config_file, 'w') as f:
                f.write(config_content)
            os.chmod(config_file, 0o644)
        else:
            print(f"⚠️  Config file already exists at {config_file}, skipping")

        # 8. Create systemd service file
        service_content = f"""[Unit]
Description=SMS REST API Server
After=network.target
Wants=network.target

[Service]
Type=simple
User=sms-rest-server
Group=dialout
SupplementaryGroups=dialout
WorkingDirectory={install_dir}

# Load configuration from /etc/default/sms-rest-server
EnvironmentFile=-{config_file}

# Start the service (config file values used if not overridden)
ExecStart=/usr/bin/python3 {target_script} --config {config_file}

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

        # 9. Reload systemd daemon
        print("🔄 Reloading systemd daemon...")
        os.system('systemctl daemon-reload')

        print("=" * 60)
        print("✅ INSTALLATION COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print()

        print("🚀 Next Steps:")
        print("   1. sudo systemctl start sms-rest-server      # Start the service")
        print("   2. sudo systemctl enable sms-rest-server     # Enable auto-start on boot")
        print("   3. sudo systemctl status sms-rest-server     # Verify service is running")
        print()

        print("📋 Service Management Commands:")
        print("   sudo systemctl start sms-rest-server         # Start the service")
        print("   sudo systemctl stop sms-rest-server          # Stop the service")
        print("   sudo systemctl restart sms-rest-server       # Restart the service")
        print("   sudo systemctl enable sms-rest-server        # Enable auto-start")
        print("   sudo systemctl disable sms-rest-server       # Disable auto-start")
        print("   sudo systemctl status sms-rest-server        # Check service status")
        print("   sudo journalctl -u sms-rest-server -f        # View real-time logs")
        print("   sudo journalctl -u sms-rest-server --since '1 hour ago'  # Recent logs")
        print()

        print("📁 Installation Paths:")
        print(f"   Installation dir: {install_dir}")
        print(f"   Service script: {target_script}")
        print(f"   Requirements: {target_requirements}")
        print(f"   Service file: {service_file}")
        print(f"   Config file: {config_file}")
        print(f"   Data directory: {data_dir}")
        print(f"   Auth file: {htpasswd_path}")
        print()

        print("🌐 API Access:")
        print(f"   Endpoint: http://localhost:18180/")
        print(f"   Health check: http://localhost:18180/health")
        print(f"   Authentication: Basic HTTP (base64 encoded)")
        print()

        print("🔐 Default Credentials:")
        print(f"   Username: {username}")
        if htpasswd_created and admin_pwd:
            print(f"   Password: {admin_pwd}")
            print("   ⚠️  Save this password - it cannot be retrieved later!")
        else:
            print("   Password: (existing htpasswd file, password not shown)")
            print(f"   ℹ️  To create additional users: {target_script} --create-htpasswd {htpasswd_path} <username>")
        print()

        print("🧪 Test the Service:")
        print("   # Health check")
        print("   curl http://localhost:18180/health")
        print()
        print("   # Send test SMS")
        print("   curl -X POST http://localhost:18180/ \\")
        print("        -u <user>:<password> \\")
        print("        -H 'Content-Type: application/json' \\")
        print("        -d '{\"number\": \"1234567890\", \"message\": \"Test SMS\"}'")
        print()

        print("🔧 Configuration:")
        print(f"   • Edit config file: {config_file}")
        print(f"   • Create additional users: {target_script} --create-htpasswd {htpasswd_path} user")
        print("   • After config changes: sudo systemctl restart sms-rest-server")
        print()

        if warnings:
            print("⚠️  Post-Installation Notes:")
            for warning in warnings:
                print(f"   • {warning}")
            print()

        print("📖 For complete documentation, see SMS_REST_README.md")
        print("🐛 Troubleshooting: sudo journalctl -u sms-rest-server -f")
        print()
        print("=" * 60)

    except Exception as e:
        print(f"❌ Installation failed: {e}")
        # Cleanup on failure
        for path in [target_script, service_file]:
            if os.path.exists(path):
                try:
                    os.remove(path)
                except:
                    pass
        if os.path.exists(install_dir) and not os.listdir(install_dir):
            try:
                os.rmdir(install_dir)
            except:
                pass
        sys.exit(1)

def uninstall_service():
    import shutil
    import pwd
    import grp

    print("=" * 60)
    print(f"🗑️  SMS REST SERVICE UNINSTALLATION v{VERSION}")
    print("=" * 60)
    print()

    if os.geteuid() != 0:
        print("❌ Root privileges required. Run with sudo.")
        sys.exit(1)

    install_dir = "/usr/local/SMS-REST-Server"
    service_file = "/etc/systemd/system/sms-rest-server.service"
    config_file = "/etc/default/sms-rest-server"
    data_dir = "/var/lib/sms-rest-server"

    service_exists = os.path.exists(service_file)
    install_exists = os.path.exists(install_dir)
    config_exists = os.path.exists(config_file)
    data_exists = os.path.exists(data_dir)

    if not service_exists and not install_exists and not config_exists:
        print("⚠️  No installation found. Nothing to uninstall.")
        print()
        print("Checked locations:")
        print(f"   • Service file: {service_file}")
        print(f"   • Installation dir: {install_dir}")
        print(f"   • Config file: {config_file}")
        sys.exit(0)

    print("This will remove:")
    if service_exists:
        print(f"   • Systemd service: {service_file}")
    if install_exists:
        print(f"   • Installation directory: {install_dir}")
    if config_exists:
        print(f"   • Config file: {config_file}")
    print()

    if data_exists:
        print("⚠️  Optional (will prompt):")
        print(f"   • Data directory: {data_dir} (contains htpasswd)")
        print("   • System user: sms-rest-server")
        print()

    while True:
        response = input("Proceed with uninstallation? [y/N]: ").lower().strip()
        if response in ['y', 'yes']:
            break
        elif response in ['', 'n', 'no']:
            print("Uninstallation cancelled.")
            sys.exit(0)
        else:
            print("Please enter 'y' for yes or 'n' for no.")

    print()
    print("🚀 Starting uninstallation...")

    try:
        if service_exists:
            print("🛑 Stopping service (if running)...")
            result = os.system('systemctl stop sms-rest-server 2>/dev/null')
            if result == 0:
                print("   ✅ Service stopped")
            else:
                print("   ℹ️  Service was not running")

            print("🔓 Disabling service (if enabled)...")
            result = os.system('systemctl disable sms-rest-server 2>/dev/null')
            if result == 0:
                print("   ✅ Service disabled")
            else:
                print("   ℹ️  Service was not enabled")

            print(f"🗑️  Removing service file: {service_file}")
            os.remove(service_file)
            print("   ✅ Service file removed")

            print("🔄 Reloading systemd daemon...")
            os.system('systemctl daemon-reload')
            print("   ✅ Systemd daemon reloaded")

        if config_exists:
            print(f"🗑️  Removing config file: {config_file}")
            os.remove(config_file)
            print("   ✅ Config file removed")

        if install_exists:
            print(f"🗑️  Removing installation directory: {install_dir}")
            shutil.rmtree(install_dir)
            print("   ✅ Installation directory removed")

        if data_exists:
            print()
            while True:
                response = input(f"Remove data directory {data_dir} (contains htpasswd)? [y/N]: ").lower().strip()
                if response in ['y', 'yes']:
                    print(f"🗑️  Removing data directory: {data_dir}")
                    shutil.rmtree(data_dir)
                    print("   ✅ Data directory removed")
                    break
                elif response in ['', 'n', 'no']:
                    print(f"   ℹ️  Keeping data directory: {data_dir}")
                    break
                else:
                    print("Please enter 'y' for yes or 'n' for no.")

        try:
            pwd.getpwnam('sms-rest-server')
            print()
            while True:
                response = input("Remove system user 'sms-rest-server'? [y/N]: ").lower().strip()
                if response in ['y', 'yes']:
                    print("🗑️  Removing system user 'sms-rest-server'...")
                    result = os.system('userdel sms-rest-server 2>/dev/null')
                    if result == 0:
                        print("   ✅ System user removed")
                    else:
                        print("   ⚠️  Failed to remove system user")
                    break
                elif response in ['', 'n', 'no']:
                    print("   ℹ️  Keeping system user 'sms-rest-server'")
                    break
                else:
                    print("Please enter 'y' for yes or 'n' for no.")
        except KeyError:
            pass

        print()
        print("=" * 60)
        print("✅ UNINSTALLATION COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print()

        print("📋 Summary:")
        print("   ✅ Systemd service removed and disabled")
        print("   ✅ Installation files removed")
        print()

        if data_exists and os.path.exists(data_dir):
            print("📁 Remaining Files:")
            print(f"   • Data directory: {data_dir}")
            print("     (manually remove if no longer needed)")
            print()

        try:
            pwd.getpwnam('sms-rest-server')
            print("👤 Remaining System User:")
            print("   • User: sms-rest-server")
            print("     (manually remove with: sudo userdel sms-rest-server)")
            print()
        except KeyError:
            pass

        print("=" * 60)

    except Exception as e:
        print(f"❌ Uninstallation failed: {e}")
        sys.exit(1)

def cleanup_modem():
    global global_modem
    stop_gsm_worker()
    if global_modem:
        try:
            print("\n🔌 Cleaning up modem connection...")
            global_modem.Terminate()
            print("✅ Modem connection terminated")
        except:
            pass
        global_modem = None

def signal_handler(signum, frame):
    print(f"\n🛑 Received signal {signum}, shutting down...")
    cleanup_modem()
    sys.exit(0)

def authenticate_request():
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
    authenticated, username = authenticate_request()
    if not authenticated:
        return build_api_response(
            status='failed',
            from_user=username,
            error_code='AUTHENTICATION_REQUIRED',
            error_message='Invalid credentials or missing Authorization header',
            http_status=401
        )

    if not request.is_json:
        return build_api_response(
            status='failed',
            from_user=username,
            error_code='INVALID_CONTENT_TYPE',
            error_message=ERROR_CODES['INVALID_CONTENT_TYPE'],
            http_status=400
        )

    data = request.get_json()

    if not data:
        return build_api_response(
            status='failed',
            from_user=username,
            error_code='INVALID_JSON',
            error_message=ERROR_CODES['INVALID_JSON'],
            http_status=400
        )

    data_lower = {k.lower(): v for k, v in data.items()}

    phone_number = str(data_lower.get('number', '')) if 'number' in data_lower else None
    message = str(data_lower.get('message', '')) if 'message' in data_lower else None
    wait_for_reply = data_lower.get('reply', False)
    reply_timeout = data_lower.get('timeout', SMS_REPLY_TIMEOUT)

    required_fields = ['number', 'message']
    missing_fields = [field for field in required_fields if field not in data_lower]
    if missing_fields:
        return build_api_response(
            status='failed',
            to=phone_number,
            from_user=username,
            message_text=message,
            error_code='MISSING_REQUIRED_FIELDS',
            error_message=f'Missing required field(s): {", ".join(missing_fields)}',
            http_status=400
        )

    if wait_for_reply and reply_timeout:
        try:
            reply_timeout = int(reply_timeout)
            if reply_timeout < 1 or reply_timeout > 600:
                return build_api_response(
                    status='failed',
                    to=phone_number,
                    from_user=username,
                    message_text=message,
                    error_code='INVALID_TIMEOUT_VALUE',
                    error_message=ERROR_CODES['INVALID_TIMEOUT_VALUE'],
                    http_status=400
                )
        except (ValueError, TypeError):
            return build_api_response(
                status='failed',
                to=phone_number,
                from_user=username,
                message_text=message,
                error_code='INVALID_TIMEOUT_FORMAT',
                error_message=ERROR_CODES['INVALID_TIMEOUT_FORMAT'],
                http_status=400
            )

    valid, normalized_number, error_msg = validate_and_normalize_phone(phone_number)

    if not valid:
        return build_api_response(
            status='failed',
            to=phone_number,
            from_user=username,
            message_text=message,
            error_code='INVALID_PHONE_NUMBER',
            error_message=error_msg,
            http_status=400
        )

    original_phone_number = phone_number
    phone_number = normalized_number

    original_message = message
    message_truncated = False
    meta = None

    if len(message) > 160:
        message = message[:160]
        message_truncated = True
        meta = {
            'truncated': True,
            'original_length': len(original_message),
            'sent_length': 160
        }

    client_ip = request.remote_addr
    msg_id = str(uuid.uuid4())

    record = create_message_record(
        msg_id,
        original_number=original_phone_number,
        normalized_number=phone_number,
        message_text=message,
        username=username,
        requires_reply=bool(wait_for_reply),
        timeout_seconds=reply_timeout if wait_for_reply else None,
        meta=meta,
        client_ip=client_ip
    )

    job_payload = {
        'message_id': msg_id,
        'to_number': phone_number,
        'message': message,
        'from_user': username,
        'requires_reply': bool(wait_for_reply),
        'timeout_seconds': reply_timeout if wait_for_reply else None,
        'client_ip': client_ip
    }

    send_queue.put(job_payload)

    return build_api_response(
        status='queued',
        message_id=msg_id,
        to=original_phone_number,
        from_user=username,
        message_text=message,
        meta=meta,
        http_status=200,
        timestamp_override=record.get('created_at')
    )

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'service': 'SMS REST API',
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
    }), 200


@app.route('/status', methods=['GET'])
def get_message_status():
    authenticated, username = authenticate_request()
    if not authenticated:
        return build_api_response(
            status='failed',
            from_user=username,
            error_code='AUTHENTICATION_REQUIRED',
            error_message='Invalid credentials or missing Authorization header',
            http_status=401
        )

    message_id = request.args.get('message_id')
    if not message_id and request.is_json:
        payload = request.get_json(silent=True) or {}
        message_id = payload.get('message_id')

    if not message_id:
        return build_api_response(
            status='failed',
            from_user=username,
            error_code='MISSING_REQUIRED_FIELDS',
            error_message='message_id is required',
            http_status=400
        )

    record = get_message_record(str(message_id))
    if not record or record.get('from_user') != username:
        return build_api_response(
            status='failed',
            from_user=username,
            error_code='NOT_FOUND',
            error_message='Message not found',
            http_status=404
        )

    timestamp_source = determine_record_timestamp(record)
    reply_payload = build_reply_payload(record)

    return build_api_response(
        status=record.get('status'),
        message_id=record.get('message_id'),
        to=record.get('original_number'),
        from_user=record.get('from_user'),
        message_text=record.get('message'),
        reply_data=reply_payload,
        meta=record.get('meta'),
        error_code=record.get('error_code'),
        error_message=record.get('error_message'),
        timestamp_override=timestamp_source
    )

def main():
    global htpasswd_file, debug, SERVICE_PORT, modem_device, config_file
    global SMS_REPLY_TIMEOUT, REPLY_POLL_INTERVAL, TIMEOUT_SWEEP_INTERVAL, QUEUE_WAIT_SECONDS
    global MESSAGE_RETENTION_SECONDS

    port = None
    port_from_cli = False

    try:
        opts, args = getopt.getopt(
            sys.argv[1:],
            "hp:a:D:c:di",
            [
                "help", "port=", "htpasswd=", "device=", "config=", "debug",
                "install", "uninstall", "create-htpasswd", "update-htpasswd"
            ]
        )
    except getopt.GetoptError as e:
        print(f"Error: {e}")
        print_usage()
        sys.exit(1)

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print_usage()
            sys.exit(0)
        elif opt == "--install":
            install_service()
            sys.exit(0)
        elif opt == "--uninstall":
            uninstall_service()
            sys.exit(0)
        elif opt in ("--create-htpasswd", "--update-htpasswd"):
            # Expects at least 2 additional arguments: output_file username [password]
            if len(args) < 2:
                print("Error: --create-htpasswd requires: output_file username [password]")
                print("\nExample:")
                print("  sms-rest-server.py --create-htpasswd /var/lib/sms-rest-server/htpasswd admin")
                sys.exit(1)
            output_file, username = args[0], args[1]
            password = args[2] if len(args) >= 3 else prompt_for_password(username)
            success = create_htpasswd_file(username, password, output_file)
            sys.exit(0 if success else 1)
        elif opt in ("-c", "--config"):
            config_file = arg
            if not os.path.exists(config_file):
                print(f"Error: config file not found: {config_file}")
                sys.exit(1)

    config = load_config()

    SMS_REPLY_TIMEOUT = get_int_config(config, 'SMS_REPLY_TIMEOUT', SMS_REPLY_TIMEOUT, 1, 600)
    REPLY_POLL_INTERVAL = get_int_config(config, 'REPLY_POLL_INTERVAL', REPLY_POLL_INTERVAL, 1)
    TIMEOUT_SWEEP_INTERVAL = get_int_config(config, 'TIMEOUT_SWEEP_INTERVAL', TIMEOUT_SWEEP_INTERVAL, 1)
    QUEUE_WAIT_SECONDS = get_int_config(config, 'QUEUE_WAIT_SECONDS', QUEUE_WAIT_SECONDS, 1)
    MESSAGE_RETENTION_SECONDS = get_int_config(config, 'MESSAGE_RETENTION_SECONDS', MESSAGE_RETENTION_SECONDS, 0)

    for opt, arg in opts:
        if opt in ("-p", "--port"):
            try:
                port = int(arg)
                port_from_cli = True
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

    if not port_from_cli and 'PORT' in config:
        try:
            port = int(config['PORT'])
        except ValueError:
            print(f"Warning: Invalid PORT value in config file: {config['PORT']}")

    if not htpasswd_file and 'HTPASSWD_FILE' in config:
        htpasswd_file = config['HTPASSWD_FILE']

    if not modem_device and 'DEVICE' in config:
        modem_device = config['DEVICE']

    if not debug and 'DEBUG' in config:
        debug = config['DEBUG'].lower() in ['true', '1', 'yes']

    if port is None:
        port = SERVICE_PORT

    if not htpasswd_file:
        print("Error: --htpasswd option is required (or set HTPASSWD_FILE in config)")
        print("\nYou can:")
        print("  1. Specify via CLI: --htpasswd /path/to/htpasswd")
        print("  2. Set in config file: HTPASSWD_FILE=/path/to/htpasswd")
        print("  3. Use default config: /etc/default/sms-rest-server")
        print_usage()
        sys.exit(1)

    modem_info = f"Device: {modem_device}" if modem_device else "Device: Auto-detect"
    config_source = "Default" if not config_file and not os.path.exists('/etc/default/sms-rest-server') else \
                    config_file if config_file else "/etc/default/sms-rest-server"

    print(f"""
SMS REST Server v{VERSION} Starting...
=============================
Port: {port}
Auth file: {htpasswd_file}
{modem_info}
Config: {config_source}
Debug: {debug}
=============================
""")

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    atexit.register(cleanup_modem)

    if debug and os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
        print("🔄 Flask reloader parent process, modem will be initialized after restart")
    else:
        modem_initialized = initialize_global_modem()
        if not modem_initialized:
            print("\n❌ FATAL: Failed to initialize modem. Service cannot start without modem.")
            print("   Please check:")
            print("   - GSM modem is connected via USB")
            print("   - Port permissions (add user to dialout group)")
            print("   - ModemManager is not interfering (sudo systemctl stop ModemManager)")
            print("   - Device path is correct (use --device option if needed)")
            sys.exit(1)
        start_gsm_worker()

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
