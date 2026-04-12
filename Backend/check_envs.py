import sys
import subprocess
from pathlib import Path

def check_current_env():
    print(f"Testing Environment: {sys.executable}")
    
    # Check NumPy
    try:
        import numpy
        print(f"  - NumPy Version: {numpy.__version__}")
    except ImportError:
        print("  - NumPy: NOT INSTALLED")
    
    # Check Whisper
    try:
        import whisper
        print("  - Whisper: Import SUCCESS! This environment is ready to use.")
    except ImportError as e:
        err_msg = str(e).split('\n')[0]
        print(f"  - Whisper: Import FAILED -> {err_msg}")
        
    # Check ChromaDB (Catching ALL exceptions to reveal hidden SQLite/C++ errors)
    try:
        import chromadb
        print(f"  - ChromaDB Version: {chromadb.__version__}")
    except Exception as e:
        err_msg = str(e).split('\n')[0]
        print(f"  - ChromaDB: Import FAILED -> {err_msg}")

if __name__ == "__main__":
    # If called by subprocess to perform the check
    if len(sys.argv) > 1 and sys.argv[1] == "--check":
        check_current_env()
        sys.exit(0)
        
    print("Searching for Python environments (this might take a few seconds)...")
    backend_dir = Path(__file__).resolve().parent
    
    python_executables = []
    try:
        for path in backend_dir.rglob("python.exe"):
            # Look for python executables inside virtual environments
            if "env" in str(path).lower() or "Scripts" in path.parts:
                python_executables.append(path)
    except Exception:
        pass
        
    # Include the current environment being used to run this script
    python_executables.append(Path(sys.executable))
    
    # Deduplicate paths
    unique_executables = list({str(p.resolve()).lower(): p for p in python_executables}.values())
    
    for py_exe in unique_executables:
        print("-" * 60)
        if py_exe.exists():
            try:
                subprocess.run([str(py_exe), __file__, "--check"])
            except Exception as e:
                print(f"Testing Environment: {py_exe}\n  - Failed to execute: {e}")
                
    print("-" * 60)
    print("Environment scan complete!")