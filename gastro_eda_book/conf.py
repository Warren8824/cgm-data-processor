import os
import sys
from pathlib import Path

# Add path to your Python code
sys.path.insert(0, os.path.abspath('..'))

def setup(app):
    app.add_css_file('custom.css')