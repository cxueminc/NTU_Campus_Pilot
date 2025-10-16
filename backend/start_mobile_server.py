#!/usr/bin/env python3
"""
Start the backend server for mobile development
This script starts the server on all interfaces so mobile devices can connect
"""

import uvicorn
import os
import socket

def get_local_ip():
    """Get the local IP address of this computer"""
    try:
        # Connect to a remote address to determine local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        return "localhost"

def start_server():
    """Start the FastAPI server for mobile development"""
    local_ip = get_local_ip()
    
    print("🚀 Starting NTU Navigation Backend for Mobile Development")
    print("=" * 60)
    print(f"🖥️  Local IP Address: {local_ip}")
    print(f"🌐 Server will be accessible at:")
    print(f"   • Web/Local: http://127.0.0.1:8000")
    print(f"   • Mobile/Network: http://{local_ip}:8000")
    print("=" * 60)
    print("📱 Update your frontend API_BASE to:")
    print(f'   const API_BASE = "http://{local_ip}:8000";')
    print("=" * 60)
    print("🔥 Starting server... Press Ctrl+C to stop")
    print()
    
    # Start server on all interfaces
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",  # Listen on all interfaces
        port=8000,
        reload=True,
        reload_dirs=["app"],
        log_level="info"
    )

if __name__ == "__main__":
    start_server()