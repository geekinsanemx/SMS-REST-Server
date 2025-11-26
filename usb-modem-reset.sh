#!/bin/bash
# usb-modem-reset.sh
# Resets USB modem devices via sysfs authorization
# Usage: ./usb-modem-reset.sh /dev/ttyUSB0
#        ./usb-modem-reset.sh /dev/ttyUSB*

set -e

if [ $# -eq 0 ]; then
    echo "Usage: $0 <device> [device...]"
    echo "Examples:"
    echo "  $0 /dev/ttyUSB0"
    echo "  $0 /dev/ttyUSB*"
    exit 1
fi

# Function to find USB bus device from tty device
find_usb_device() {
    local tty_dev="$1"
    local tty_name=$(basename "$tty_dev")

    if [ ! -e "$tty_dev" ]; then
        echo "❌ Device $tty_dev does not exist"
        return 1
    fi

    # Get the device path
    local dev_path=$(udevadm info --query=path --name="$tty_dev" 2>/dev/null)
    if [ -z "$dev_path" ]; then
        echo "❌ Could not get udev info for $tty_dev"
        return 1
    fi

    # Extract USB device ID (e.g., 4-1 from /devices/.../usb4/4-1/4-1:1.0/...)
    local usb_id=$(echo "$dev_path" | grep -oP 'usb\d+/\K[^/]+(?=/)')
    if [ -z "$usb_id" ]; then
        echo "❌ Could not extract USB device ID from $dev_path"
        return 1
    fi

    echo "$usb_id"
}

# Function to reset USB device
reset_usb_device() {
    local usb_id="$1"
    local usb_path="/sys/bus/usb/devices/$usb_id"

    if [ ! -d "$usb_path" ]; then
        echo "❌ USB device path not found: $usb_path"
        return 1
    fi

    echo "🔄 Resetting USB device: $usb_id"

    # Deauthorize
    echo 0 | sudo tee "$usb_path/authorized" > /dev/null
    if [ $? -ne 0 ]; then
        echo "❌ Failed to deauthorize $usb_id"
        return 1
    fi
    echo "   ⏸️  Deauthorized"

    # Wait
    sleep 2

    # Reauthorize
    echo 1 | sudo tee "$usb_path/authorized" > /dev/null
    if [ $? -ne 0 ]; then
        echo "❌ Failed to reauthorize $usb_id"
        return 1
    fi
    echo "   ▶️  Reauthorized"

    return 0
}

# Main logic
echo "========================================="
echo "USB Modem Reset Utility"
echo "========================================="
echo ""

# Collect unique USB devices to reset
declare -A usb_devices

for dev in "$@"; do
    echo "📱 Processing: $dev"
    usb_id=$(find_usb_device "$dev")
    if [ $? -eq 0 ] && [ -n "$usb_id" ]; then
        echo "   → USB device: $usb_id"
        usb_devices["$usb_id"]=1
    fi
    echo ""
done

if [ ${#usb_devices[@]} -eq 0 ]; then
    echo "❌ No valid USB devices found to reset"
    exit 1
fi

echo "========================================="
echo "Resetting ${#usb_devices[@]} USB device(s)..."
echo "========================================="
echo ""

# Reset each unique USB device
for usb_id in "${!usb_devices[@]}"; do
    reset_usb_device "$usb_id"
    echo ""
done

echo "⏳ Waiting for devices to re-enumerate..."
sleep 3

echo "========================================="
echo "✅ Reset complete!"
echo "========================================="
echo ""

echo "📋 Current USB serial devices:"
ls -1 /dev/ttyUSB* 2>/dev/null || echo "   (none found yet, may need a few more seconds)"
echo ""

echo "📊 Recent kernel messages:"
dmesg | tail -10 | grep -i usb || echo "   (no recent USB messages)"
echo ""

echo "💡 Test modem with:"
echo "   gammu --config \"\" --device /dev/ttyUSB0 --connection at identify"
