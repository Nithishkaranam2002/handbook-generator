import subprocess
import sys
import os

port = os.environ.get("PORT", "8501")

subprocess.run([
    sys.executable, "-m", "streamlit", "run",
    "frontend/streamlit_app.py",
    "--server.port", port,
    "--server.address", "0.0.0.0",
    "--server.headless", "true"
])
