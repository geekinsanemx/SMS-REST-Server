#!/usr/bin/env python3
"""
Create htpasswd file with bcrypt hashing for SMS REST service

Usage:
    python3 create_htpasswd.py username password output_file
    
Example:
    python3 create_htpasswd.py admin passw0rd /etc/sms/htpasswd
"""

import bcrypt
import sys

def create_htpasswd_entry(username, password):
    """Create bcrypt hash for password"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return f"{username}:{hashed.decode('utf-8')}"

def main():
    if len(sys.argv) != 4:
        print(__doc__)
        sys.exit(1)
    
    username = sys.argv[1]
    password = sys.argv[2]
    output_file = sys.argv[3]
    
    entry = create_htpasswd_entry(username, password)
    
    try:
        with open(output_file, 'w') as f:
            f.write(entry + '\n')
        print(f"htpasswd file created: {output_file}")
        print(f"Username: {username}")
        print("Password: [hidden]")
    except Exception as e:
        print(f"Error creating htpasswd file: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()