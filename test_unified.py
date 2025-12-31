#!/usr/bin/env python3
# coding: utf-8

"""
Test script for unified web + telegram bot deployment
"""

import os
import sys
import time
import requests
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))


def test_web_server(host="localhost", port=8000, timeout=30):
    """Test if web server is accessible"""
    url = f"http://{host}:{port}"

    print(f"Testing web server at {url}...")

    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            # Test root endpoint
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"✓ Root endpoint accessible: {response.status_code}")

                # Test API docs
                docs_url = f"{url}/docs"
                docs_response = requests.get(docs_url, timeout=5)
                if docs_response.status_code == 200:
                    print(f"✓ API docs accessible: {docs_url}")

                # Test health check (if exists)
                try:
                    health_url = f"{url}/api/info"
                    test_payload = {"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}
                    # Just check if endpoint exists, don't expect it to succeed
                    health_response = requests.post(health_url, json=test_payload, timeout=5)
                    print(f"✓ API endpoint responding: {health_url} (status: {health_response.status_code})")
                except Exception as e:
                    print(f"⚠ API endpoint test error (might be normal): {e}")

                return True

        except requests.exceptions.ConnectionError:
            print(f"⏳ Waiting for server to start... ({int(time.time() - start_time)}s)")
            time.sleep(2)
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return False

    print(f"❌ Server did not start within {timeout} seconds")
    return False


def check_configuration():
    """Check if necessary configuration is present"""
    print("\n=== Checking Configuration ===")

    required_vars = ["APP_ID", "APP_HASH", "BOT_TOKEN"]
    optional_vars = ["ENABLE_WEB", "WEB_PORT", "WEB_HOST"]

    all_ok = True
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"✓ {var}: {'*' * 10} (set)")
        else:
            print(f"❌ {var}: Not set (required for TG bot)")
            all_ok = False

    print("\nOptional configuration:")
    for var in optional_vars:
        value = os.getenv(var)
        default = {"ENABLE_WEB": "true", "WEB_PORT": "8000", "WEB_HOST": "0.0.0.0"}.get(var, "")
        print(f"  {var}: {value or f'(default: {default})'}")

    return all_ok


def check_dependencies():
    """Check if required packages are installed"""
    print("\n=== Checking Dependencies ===")

    packages = {
        "fastapi": "FastAPI",
        "uvicorn": "Uvicorn",
        "pyrogram": "Pyrogram",
        "yt_dlp": "yt-dlp",
    }

    all_ok = True
    for module, name in packages.items():
        try:
            __import__(module)
            print(f"✓ {name} installed")
        except ImportError:
            print(f"❌ {name} not installed")
            all_ok = False

    return all_ok


def check_files():
    """Check if necessary files exist"""
    print("\n=== Checking Files ===")

    files = [
        "src/main.py",
        "src/web/app.py",
        "src/web/downloader.py",
        "index.html",
    ]

    all_ok = True
    for file in files:
        path = Path(file)
        if path.exists():
            print(f"✓ {file}")
        else:
            print(f"⚠ {file} (not found)")
            if file != "index.html":  # index.html is optional
                all_ok = False

    return all_ok


def main():
    """Run all checks"""
    print("=" * 60)
    print("Unified Deployment Test Suite")
    print("=" * 60)

    # Load .env if it exists
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✓ Loaded .env file")
    except ImportError:
        print("⚠ python-dotenv not installed, skipping .env loading")
    except Exception as e:
        print(f"⚠ Could not load .env: {e}")

    # Run checks
    deps_ok = check_dependencies()
    files_ok = check_files()
    config_ok = check_configuration()

    print("\n" + "=" * 60)
    print("Summary:")
    print(f"  Dependencies: {'✓ OK' if deps_ok else '❌ Missing packages'}")
    print(f"  Files: {'✓ OK' if files_ok else '❌ Missing files'}")
    print(f"  Configuration: {'✓ OK' if config_ok else '⚠ Missing TG bot config'}")
    print("=" * 60)

    # Offer to test web server
    enable_web = os.getenv("ENABLE_WEB", "true").lower() in ("true", "1", "yes")
    if enable_web:
        print("\n💡 Tip: To test the web server, run:")
        print("   python src/main.py")
        print("   Then in another terminal, run:")
        print("   python test_unified.py --test-web")

    if "--test-web" in sys.argv:
        port = int(os.getenv("WEB_PORT", "8000"))
        host = os.getenv("WEB_HOST", "localhost")
        if host == "0.0.0.0":
            host = "localhost"

        print(f"\n=== Testing Web Server ===")
        if test_web_server(host, port):
            print("\n✓ Web server test passed!")
            return 0
        else:
            print("\n❌ Web server test failed!")
            return 1

    return 0 if (deps_ok and files_ok) else 1


if __name__ == "__main__":
    sys.exit(main())
