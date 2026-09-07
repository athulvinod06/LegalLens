"""
LegalLens — One-Command Root Launcher
Runs both the FastAPI backend and the React frontend simultaneously from the project root.
Usage:
    python run.py
"""

import os
import sys
import time
import subprocess
import webbrowser
import signal

def main():
    root_dir = os.path.dirname(os.path.abspath(__file__))
    frontend_dir = os.path.join(root_dir, "frontend")
    
    # Ensure local Node.js is on PATH if installed in user directory
    user_node = r"C:\Users\Athul\AppData\Local\Programs\nodejs"
    env = os.environ.copy()
    if os.path.exists(user_node) and user_node not in env.get("PATH", ""):
        env["PATH"] = user_node + os.pathsep + env.get("PATH", "")

    python_exe = sys.executable

    print("=" * 60)
    print("           LegalLens — Starting Application")
    print("=" * 60)
    print()

    # 1. Start FastAPI Backend
    print("[1/2] Launching FastAPI Backend on http://127.0.0.1:8000 ...")
    backend_cmd = [
        python_exe,
        "-m",
        "uvicorn",
        "backend.app.main:app",
        "--host",
        "127.0.0.1",
        "--port",
        "8000",
        "--reload",
    ]
    backend_proc = subprocess.Popen(
        backend_cmd,
        cwd=root_dir,
        env=env,
    )

    # 2. Start Frontend Server
    print("[2/2] Launching React Frontend on http://127.0.0.1:3000 ...")
    frontend_cmd = ["npm.cmd" if os.name == "nt" else "npm", "run", "preview", "--", "--port", "3000", "--host", "127.0.0.1"]
    frontend_proc = subprocess.Popen(
        frontend_cmd,
        cwd=frontend_dir,
        env=env,
    )

    time.sleep(2.5)

    print()
    print("=" * 60)
    print("  LegalLens is now running!")
    print("  - Frontend UI:  http://127.0.0.1:3000")
    print("  - Backend API:  http://127.0.0.1:8000")
    print("  - Swagger Docs: http://127.0.0.1:8000/docs")
    print("  Press Ctrl+C to stop both servers.")
    print("=" * 60)
    print()

    try:
        webbrowser.open("http://127.0.0.1:3000")
    except Exception:
        pass

    def cleanup(signum=None, frame=None):
        print("\nStopping LegalLens servers...")
        try:
            backend_proc.terminate()
        except Exception:
            pass
        try:
            frontend_proc.terminate()
        except Exception:
            pass
        sys.exit(0)

    signal.signal(signal.SIGINT, cleanup)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, cleanup)

    try:
        while True:
            time.sleep(1)
            # If any process terminated prematurely, exit
            if backend_proc.poll() is not None or frontend_proc.poll() is not None:
                break
    except KeyboardInterrupt:
        pass
    finally:
        cleanup()

if __name__ == "__main__":
    main()
