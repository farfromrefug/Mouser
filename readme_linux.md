# Linux Setup Guide for Mouser

This guide explains how to set up and use Mouser on Linux systems.

## System Requirements

- **Linux Distribution:** Ubuntu 20.04+, Fedora 35+, Debian 11+, or equivalent
- **Python:** 3.10 or higher
- **Display Server:** X11 or Wayland
- **Desktop Environment:** GNOME, KDE, XFCE, or others

## Installation

### 1. Install System Dependencies

#### Ubuntu/Debian:
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
sudo apt install libhidapi-libusb0 libxcb1 libxcb-xkb1
sudo apt install qt6-base-dev  # For PySide6
```

#### Fedora:
```bash
sudo dnf install python3 python3-pip
sudo dnf install hidapi libxcb
sudo dnf install qt6-qtbase-devel  # For PySide6
```

#### Arch Linux:
```bash
sudo pacman -S python python-pip hidapi libxcb qt6-base
```

### 2. Clone and Set Up

```bash
# Clone the repository
git clone https://github.com/TomBadash/MouseControl.git
cd MouseControl

# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
```

### 3. Configure Permissions (Optional but Recommended)

For better HID device access, add your user to the `input` group:

```bash
sudo usermod -a -G input $USER
```

**Important:** You must log out and log back in (or reboot) for group changes to take effect.

### 4. Run Mouser

```bash
source .venv/bin/activate  # If not already activated
python main_qml.py
```

## Platform-Specific Features

### X11 Backend

The X11 backend provides the best experience with full event interception:

- **Pros:**
  - Native mouse button remapping
  - Full horizontal scroll support
  - Direct event blocking

- **Cons:**
  - Requires python-xlib library
  - Only works on X11 (not Wayland)

**Check if you're using X11:**
```bash
echo $DISPLAY
# If this prints something like ":0" or ":1", you're on X11
```

### Wayland Backend

On Wayland, Mouser uses pynput as a fallback:

- **Pros:**
  - Cross-compatible (works on X11 too)
  - No special permissions needed
  - Works with most desktop environments

- **Cons:**
  - Limited event blocking capabilities
  - Events may still reach applications
  - Horizontal scroll detection may be limited

**Check if you're using Wayland:**
```bash
echo $WAYLAND_DISPLAY
# If this prints something like "wayland-0", you're on Wayland
```

## Supported Features on Linux

| Feature | X11 | Wayland |
|---------|-----|---------|
| Basic button remapping | ✅ | ✅ |
| Middle button | ✅ | ✅ |
| Back/Forward buttons | ✅ | ✅ |
| Horizontal scroll | ✅ | ⚠️ Limited |
| Gesture button (HID++) | ✅ | ✅ |
| Event blocking | ✅ | ⚠️ Limited |
| App detection | ✅ | ⚠️ Limited |
| DPI control | ✅ | ✅ |
| Per-app profiles | ✅ | ⚠️ Limited |

## Key Bindings

Linux uses different key combinations compared to Windows/macOS:

| Action | Linux Shortcut |
|--------|----------------|
| Switch Windows | Alt + Tab |
| Show Desktop | Super + D |
| Activities Overview | Super |
| Browser Back | Alt + Left |
| Browser Forward | Alt + Right |
| Copy | Ctrl + C |
| Paste | Ctrl + V |
| Cut | Ctrl + X |
| Undo | Ctrl + Z |

## Troubleshooting

### Mouse not detected

1. **Check USB permissions:**
   ```bash
   ls -l /dev/hidraw*
   ```
   
2. **Verify hidapi installation:**
   ```bash
   python3 -c "import hid; print(hid.enumerate())"
   ```

3. **Try running with elevated permissions (not recommended for regular use):**
   ```bash
   sudo python main_qml.py
   ```

### App detection not working

On Wayland, app detection is limited. Try:

1. **Switch to X11 session** (log out, select X11 at login screen)
2. **Install required libraries:**
   ```bash
   pip install python-xlib
   ```

### Gesture button not working

1. **Check if HID device is accessible:**
   ```bash
   ls -l /dev/hidraw*
   sudo chmod 666 /dev/hidraw*  # Temporary fix
   ```

2. **Make permissions permanent** by creating a udev rule:
   ```bash
   sudo tee /etc/udev/rules.d/99-logitech-hid.rules <<EOF
   KERNEL=="hidraw*", ATTRS{idVendor}=="046d", MODE="0666"
   EOF
   
   sudo udevadm control --reload-rules
   sudo udevadm trigger
   ```

3. **Reconnect your mouse** (turn off and on, or re-pair Bluetooth)

### Qt/PySide6 issues

If you encounter Qt-related errors:

```bash
# Install additional Qt dependencies
sudo apt install libqt6gui6 libqt6qml6 libqt6quick6
# or on Fedora:
sudo dnf install qt6-qtdeclarative
```

### Button mappings not working

1. **Check if Logitech software is running:**
   ```bash
   ps aux | grep -i logitech
   # Kill any Logitech processes
   ```

2. **Verify pynput installation:**
   ```bash
   pip install --upgrade pynput
   ```

3. **Test keyboard simulation:**
   ```bash
   python3 -c "from pynput.keyboard import Key, Controller; kb = Controller(); kb.press(Key.space); kb.release(Key.space)"
   ```

## Desktop Environment Specific Notes

### GNOME (Ubuntu, Fedora)

- Works well on both X11 and Wayland
- On Wayland: App detection uses D-Bus (GNOME Shell interface)
- May need to grant accessibility permissions in Settings → Privacy

### KDE Plasma

- Best experience on X11
- Wayland support improving in Plasma 6+
- Full mouse button remapping available

### XFCE

- Excellent compatibility (X11 only)
- All features fully supported

## Performance Tips

1. **Reduce polling interval** if CPU usage is high (edit `app_detector.py`)
2. **Disable unused features** in the UI
3. **Use X11 backend** when possible for better performance

## Autostart on Login

### systemd User Service

Create `~/.config/systemd/user/mouser.service`:

```ini
[Unit]
Description=Mouser Mouse Button Remapper
After=graphical-session.target

[Service]
Type=simple
ExecStart=/path/to/MouseControl/.venv/bin/python /path/to/MouseControl/main_qml.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
```

Enable and start:
```bash
systemctl --user enable mouser.service
systemctl --user start mouser.service
```

### Desktop Entry (XDG Autostart)

Create `~/.config/autostart/mouser.desktop`:

```ini
[Desktop Entry]
Type=Application
Name=Mouser
Comment=MX Master 3S Button Remapper
Exec=/path/to/MouseControl/.venv/bin/python /path/to/MouseControl/main_qml.py
Icon=/path/to/MouseControl/images/logo.png
Terminal=false
Categories=Utility;
X-GNOME-Autostart-enabled=true
```

## Known Issues

1. **Wayland event blocking**: Events are intercepted but may still reach applications. This is a Wayland security limitation.

2. **App detection on Wayland**: Limited to GNOME Shell and KDE KWin. Other compositors may not support app detection.

3. **Horizontal scroll**: Detection varies by desktop environment and toolkit (GTK vs Qt applications).

4. **Permission requirements**: Some features may require adding user to `input` group or creating udev rules.

## Contributing

Found a Linux-specific bug or have a suggestion? Please report it on [GitHub Issues](https://github.com/TomBadash/MouseControl/issues) with:

- Linux distribution and version
- Desktop environment and display server (X11/Wayland)
- Python version
- Error messages or logs

## See Also

- [Main README](README.md) - General information and Windows/macOS setup
- [macOS Setup Guide](readme_mac_osx.md) - macOS-specific instructions
