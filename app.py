import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from frontend.app import demo

if __name__ == "__main__":
    demo.launch()