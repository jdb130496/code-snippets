#!/bin/bash

# Complete Audio System Diagnosis Script for Fedora
# This will help identify why there's no audio output

echo "=== COMPLETE AUDIO SYSTEM DIAGNOSIS ==="
echo "Date: $(date)"
echo "System: $(uname -a)"
echo "Distribution: $(cat /etc/fedora-release 2>/dev/null || echo "Unknown")"
echo ""

# 1. Check if audio hardware is detected
echo "1. AUDIO HARDWARE DETECTION:"
echo "----------------------------------------"
echo "Sound cards detected by kernel:"
cat /proc/asound/cards 2>/dev/null || echo "  No sound cards found in /proc/asound/cards"
echo ""

echo "Hardware audio devices (lspci):"
lspci | grep -i audio || echo "  No audio devices found via lspci"
echo ""

echo "Hardware audio devices (lsusb - USB audio):"
lsusb | grep -i audio || echo "  No USB audio devices found"
echo ""

# 2. Check ALSA status
echo "2. ALSA STATUS:"
echo "----------------------------------------"
if command -v aplay >/dev/null 2>&1; then
    echo "ALSA playback devices:"
    aplay -l 2>/dev/null || echo "  No ALSA playback devices found"
    echo ""

    echo "ALSA capture devices:"
    arecord -l 2>/dev/null || echo "  No ALSA capture devices found"
    echo ""
else
    echo "  ALSA tools not available"
fi

# 3. Check PulseAudio/PipeWire status
echo "3. AUDIO SERVER STATUS:"
echo "----------------------------------------"

# Check what's running
echo "Audio-related processes:"
ps aux | grep -E "(pulseaudio|pipewire|jack)" | grep -v grep || echo "  No audio servers running"
echo ""

# PulseAudio specific checks
if command -v pulseaudio >/dev/null 2>&1; then
    echo "PulseAudio status:"
    if pulseaudio --check; then
        echo "  ✓ PulseAudio daemon is running"
    else
        echo "  ✗ PulseAudio daemon is NOT running"
    fi

    if command -v pactl >/dev/null 2>&1; then
        echo ""
        echo "PulseAudio sinks (output devices):"
        pactl list short sinks 2>/dev/null || echo "  Cannot get PulseAudio sinks"
        echo ""

        echo "PulseAudio sources (input devices):"
        pactl list short sources 2>/dev/null || echo "  Cannot get PulseAudio sources"
        echo ""

        echo "Default sink:"
        pactl get-default-sink 2>/dev/null || echo "  Cannot get default sink"
        echo ""
    fi
else
    echo "  PulseAudio not installed"
fi

# PipeWire checks
if command -v pipewire >/dev/null 2>&1; then
    echo "PipeWire status:"
    systemctl --user is-active pipewire 2>/dev/null || echo "  PipeWire service status unknown"

    if command -v pw-cli >/dev/null 2>&1; then
        echo ""
        echo "PipeWire devices:"
        pw-cli list-objects 2>/dev/null | grep -A5 -B5 "audio" | head -20 || echo "  Cannot list PipeWire devices"
    fi
fi

echo ""

# 4. Check system services
echo "4. AUDIO SERVICES STATUS:"
echo "----------------------------------------"
echo "Systemd user audio services:"
systemctl --user list-units --state=active | grep -E "(pulse|pipewire|wireplumber)" || echo "  No active audio services found"
echo ""

echo "System-wide audio services:"
systemctl list-units --state=active | grep -E "(pulse|pipewire|alsa)" || echo "  No system audio services found"
echo ""

# 5. Check audio group membership
echo "5. USER PERMISSIONS:"
echo "----------------------------------------"
echo "Current user: $USER"
echo "Audio-related group memberships:"
groups $USER | grep -E "(audio|pulse|pulse-access)" || echo "  User not in audio-related groups"
echo ""

echo "Audio group members:"
getent group audio 2>/dev/null || echo "  No audio group found"
echo ""

# 6. Check kernel modules
echo "6. KERNEL MODULES:"
echo "----------------------------------------"
echo "Loaded sound-related modules:"
lsmod | grep -E "(snd|audio)" || echo "  No sound modules loaded"
echo ""

# 7. Check mixer/volume levels
echo "7. VOLUME LEVELS:"
echo "----------------------------------------"
if command -v amixer >/dev/null 2>&1; then
    echo "ALSA mixer controls:"
    amixer scontents 2>/dev/null | grep -A3 -B1 -E "(Master|PCM|Speaker|Headphone)" || echo "  Cannot get mixer controls"
else
    echo "  amixer not available"
fi
echo ""

if command -v pactl >/dev/null 2>&1; then
    echo "PulseAudio volumes:"
    pactl list sinks 2>/dev/null | grep -E "(Name:|Volume:|Mute:)" || echo "  Cannot get PulseAudio volumes"
fi

echo ""

# 8. Environment variables
echo "8. AUDIO ENVIRONMENT:"
echo "----------------------------------------"
echo "Relevant environment variables:"
echo "  XDG_RUNTIME_DIR: $XDG_RUNTIME_DIR"
echo "  PULSE_SERVER: $PULSE_SERVER"
echo "  XDG_SESSION_TYPE: $XDG_SESSION_TYPE"
echo "  DISPLAY: $DISPLAY"
echo "  WAYLAND_DISPLAY: $WAYLAND_DISPLAY"
echo ""

# 9. Check for conflicts or issues
echo "9. POTENTIAL ISSUES:"
echo "----------------------------------------"

# Check if multiple audio systems are fighting
pulse_running=$(pgrep pulseaudio | wc -l)
pipewire_running=$(pgrep pipewire | wc -l)

if [ $pulse_running -gt 0 ] && [ $pipewire_running -gt 0 ]; then
    echo "  ⚠️  WARNING: Both PulseAudio ($pulse_running) and PipeWire ($pipewire_running) processes detected"
fi

# Check permissions on audio devices
if [ -e /dev/snd ]; then
    echo "  Audio device permissions:"
    ls -la /dev/snd/ | head -5
else
    echo "  ✗ /dev/snd directory not found"
fi

echo ""

# 10. Basic test
echo "10. BASIC AUDIO TEST:"
echo "----------------------------------------"
echo "Attempting to play test tone via ALSA:"
if timeout 2 speaker-test -t sine -f 1000 -l 1 >/dev/null 2>&1; then
    echo "  ✓ ALSA test tone succeeded"
else
    echo "  ✗ ALSA test tone failed"
fi

echo ""
echo "=== DIAGNOSIS COMPLETE ==="
echo ""
echo "NEXT STEPS based on common issues:"
echo "1. If no hardware detected: Check if drivers are installed"
echo "2. If hardware detected but no sound: Check volume levels and muting"
echo "3. If PulseAudio not running: Try 'pulseaudio --start'"
echo "4. If user not in audio group: 'sudo usermod -a -G audio $USER' (then reboot)"
echo "5. If modules not loaded: Check if sound drivers are blacklisted"
echo "6. If PipeWire conflict: Choose one audio system and disable the other"
