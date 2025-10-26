import subprocess
import sys
from pathlib import Path

def run_tests():
    """Execute pytest on test_rules.py and log the output."""
    print("Running tests from test_rules.py...")
    print("-" * 60)
    
    # Get project root (parent of tests directory)
    project_root = Path(__file__).parent.parent
    
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/test_rules.py", "-v"],
        capture_output=True,
        text=True,
        cwd=project_root  # Run from project root
    )
    
    print(result.stdout)
    if result.stderr:
        print(result.stderr)
    
    print("-" * 60)
    print(f"Exit code: {result.returncode}")
    
    return result.returncode

if __name__ == "__main__":
    exit_code = run_tests()

    sys.exit(exit_code)