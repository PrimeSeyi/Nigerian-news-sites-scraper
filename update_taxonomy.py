import os
import sys

# Standardized wrapper script for updating semantic taxonomy classifications
if __name__ == "__main__":
    script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "semantic_classifier.py")
    python_exe = sys.executable
    os.execv(python_exe, [python_exe, script_path] + sys.argv[1:])
