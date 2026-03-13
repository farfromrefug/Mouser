#!/usr/bin/env python3
"""
Simple test script to verify Linux support without requiring a full UI.
This tests the core functionality on Linux systems.
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all modules can be imported."""
    print("=" * 60)
    print("Testing module imports...")
    print("=" * 60)
    
    try:
        from core import config
        print("✓ config module imported")
        print(f"  Config dir: {config.CONFIG_DIR}")
    except Exception as e:
        print(f"✗ config import failed: {e}")
        return False
    
    try:
        from core import key_simulator
        print("✓ key_simulator module imported")
        print(f"  Available actions: {len(key_simulator.ACTIONS)}")
    except Exception as e:
        print(f"✗ key_simulator import failed: {e}")
        return False
    
    try:
        from core import app_detector
        print("✓ app_detector module imported")
    except Exception as e:
        print(f"✗ app_detector import failed: {e}")
        return False
    
    try:
        from core import mouse_hook
        print("✓ mouse_hook module imported")
    except Exception as e:
        print(f"✗ mouse_hook import failed: {e}")
        return False
    
    try:
        from core import hid_gesture
        print("✓ hid_gesture module imported")
    except Exception as e:
        print(f"✗ hid_gesture import failed: {e}")
        return False
    
    try:
        from core import engine
        print("✓ engine module imported")
    except Exception as e:
        print(f"✗ engine import failed: {e}")
        return False
    
    return True

def test_platform_detection():
    """Test platform detection."""
    print("\n" + "=" * 60)
    print("Testing platform detection...")
    print("=" * 60)
    
    print(f"Platform: {sys.platform}")
    
    if sys.platform.startswith("linux"):
        print("✓ Linux detected")
        
        # Check display server
        display = os.environ.get("DISPLAY")
        wayland = os.environ.get("WAYLAND_DISPLAY")
        
        if display:
            print(f"  X11 display: {display}")
        if wayland:
            print(f"  Wayland display: {wayland}")
        
        if not display and not wayland:
            print("  ⚠ No display server detected (headless?)")
    else:
        print(f"⚠ Not running on Linux (platform: {sys.platform})")
    
    return True

def test_mouse_hook():
    """Test MouseHook instantiation."""
    print("\n" + "=" * 60)
    print("Testing MouseHook...")
    print("=" * 60)
    
    try:
        from core.mouse_hook import MouseHook
        hook = MouseHook()
        print("✓ MouseHook instantiated")
        print(f"  Backend available: {hasattr(hook, '_backend')}")
        return True
    except Exception as e:
        print(f"✗ MouseHook instantiation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_key_simulator():
    """Test key simulator actions."""
    print("\n" + "=" * 60)
    print("Testing key simulator...")
    print("=" * 60)
    
    try:
        from core import key_simulator
        
        # List all available actions
        print(f"Available actions ({len(key_simulator.ACTIONS)}):")
        categories = {}
        for action_id, action in key_simulator.ACTIONS.items():
            category = action.get('category', 'Other')
            if category not in categories:
                categories[category] = []
            categories[category].append(action_id)
        
        for category, actions in sorted(categories.items()):
            print(f"  {category}:")
            for action_id in actions:
                action = key_simulator.ACTIONS[action_id]
                print(f"    - {action_id}: {action['label']}")
        
        print("✓ Key simulator actions available")
        return True
    except Exception as e:
        print(f"✗ Key simulator test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_app_detector():
    """Test app detector."""
    print("\n" + "=" * 60)
    print("Testing app detector...")
    print("=" * 60)
    
    try:
        from core.app_detector import get_foreground_exe
        
        exe = get_foreground_exe()
        if exe:
            print(f"✓ Current foreground app detected: {exe}")
        else:
            print("⚠ No foreground app detected (may be normal in headless env)")
        
        return True
    except Exception as e:
        print(f"✗ App detector test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_config():
    """Test config loading/saving."""
    print("\n" + "=" * 60)
    print("Testing config...")
    print("=" * 60)
    
    try:
        from core import config
        
        print("✓ Config module loaded")
        print(f"  Config directory: {config.CONFIG_DIR}")
        print(f"  Config file: {config.CONFIG_FILE}")
        
        # Check if config directory exists or can be created
        if not os.path.exists(config.CONFIG_DIR):
            print(f"  ⚠ Config directory doesn't exist yet (will be created on first run)")
        else:
            print(f"  ✓ Config directory exists")
        
        return True
    except Exception as e:
        print(f"✗ Config test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("Mouser Linux Support Test Suite")
    print("=" * 60)
    print()
    
    results = []
    
    results.append(("Imports", test_imports()))
    results.append(("Platform Detection", test_platform_detection()))
    results.append(("MouseHook", test_mouse_hook()))
    results.append(("Key Simulator", test_key_simulator()))
    results.append(("App Detector", test_app_detector()))
    results.append(("Config", test_config()))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print()
    print(f"Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓ All tests passed! Linux support is working.")
        return 0
    else:
        print(f"\n⚠ {total - passed} test(s) failed. Some features may not work.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
