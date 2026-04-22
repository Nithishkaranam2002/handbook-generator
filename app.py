import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

os.environ["GRADIO_SERVER_NAME"] = "0.0.0.0"
os.environ["GRADIO_SERVER_PORT"] = str(os.environ.get("PORT", "7860"))

from frontend.app import demo

demo.launch(
    server_name="0.0.0.0",
    server_port=int(os.environ.get("PORT", 7860)),
    share=False,
    show_error=True
)
