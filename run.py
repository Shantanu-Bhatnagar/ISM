"""
OmniStore ISM Application Launcher
Starts the Uvicorn web server and opens the interactive dashboard in your browser.
"""

import sys
import webbrowser
import threading
import time
import uvicorn

def open_browser():
    time.sleep(1.2)
    url = "http://127.0.0.1:8000"
    print(f"\n[+] Opening OmniStore ISM Dashboard in browser: {url}")
    webbrowser.open(url)

def main():
    print("=" * 70)
    print("   OMNISTORE ISM - ENTERPRISE INFORMATION STORAGE MANAGEMENT")
    print("   Simulating RAID, Deduplication, Tiering, SAN, DR & Security")
    print("=" * 70)
    print("\n[*] Initializing storage controllers and fabric...")
    print("[*] Server starting on http://127.0.0.1:8000")
    print("[*] Press Ctrl+C to terminate.")

    # Launch browser automatically in background thread
    threading.Thread(target=open_browser, daemon=True).start()

    # Start FastAPI with Uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=False, log_level="info")

if __name__ == "__main__":
    main()
