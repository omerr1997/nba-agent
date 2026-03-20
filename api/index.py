import sys
import os

# Make sure the project root is on the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app  # noqa: E402  — FastAPI app instance
