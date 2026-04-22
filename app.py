import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

port = int(os.environ.get("PORT", 7860))

from frontend.app import demo

demo.launch(
    server_name="0.0.0.0",
    server_port=port,
    share=False,
    show_error=True
)
