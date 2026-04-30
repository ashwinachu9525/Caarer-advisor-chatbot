import subprocess
import sys
import os
import platform

# Terminal colors for better UI
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_status(msg, status="info"):
    if status == "success":
        print(f"{Colors.OKGREEN}[✔] {msg}{Colors.ENDC}")
    elif status == "error":
        print(f"{Colors.FAIL}[✖] {msg}{Colors.ENDC}")
    elif status == "warning":
        print(f"{Colors.WARNING}[!] {msg}{Colors.ENDC}")
    else:
        print(f"{Colors.OKCYAN}[i] {msg}{Colors.ENDC}")

def check_python_version():
    """Ensure Python version is at least 3.8"""
    print_status(f"System: {platform.system()} {platform.release()}", "info")
    print_status(f"Python version: {sys.version.split()[0]}", "info")
    
    if sys.version_info < (3, 8):
        print_status("Python 3.8 or higher is required. Please upgrade Python.", "error")
        sys.exit(1)

def upgrade_pip():
    """Upgrade pip to the latest version before installing packages."""
    print_status("Upgrading pip to the latest version...", "info")
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip', '--quiet'])
        print_status("Pip successfully upgraded.", "success")
    except subprocess.CalledProcessError:
        print_status("Failed to upgrade pip. Continuing anyway...", "warning")

def install_requirements(requirements_file='requirements.txt'):
    """Install packages from the requirements file safely."""
    if not os.path.exists(requirements_file):
        print_status(f"'{requirements_file}' not found in the current directory.", "error")
        sys.exit(1)

    with open(requirements_file, 'r') as f:
        # Filter out comments and empty lines
        packages = [line.strip() for line in f.readlines() if line.strip() and not line.startswith('#')]

    print(f"\n{Colors.BOLD}{Colors.HEADER}=== Starting Installation of {len(packages)} Packages ==={Colors.ENDC}\n")

    successful = 0
    failed = []

    for package in packages:
        print(f"Installing {package}...")
        try:
            # First attempt: Install exactly what is in the file
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package, '--quiet'])
            print_status(f"{package} installed successfully.", "success")
            successful += 1
        except subprocess.CalledProcessError:
            print_status(f"Failed to install {package}. Attempting fallback to latest unpinned version...", "warning")
            
            # Second attempt: Strip version pinning (e.g., package>=1.0.0 -> package)
            base_package = package.split('=')[0].split('>')[0].split('<')[0]
            try:
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--upgrade', base_package, '--quiet'])
                print_status(f"Latest version of {base_package} installed successfully.", "success")
                successful += 1
            except subprocess.CalledProcessError as e:
                print_status(f"Critical failure installing {base_package}. Error: {e}", "error")
                failed.append(package)

    # --- Post-Installation Summary ---
    print(f"\n{Colors.BOLD}{Colors.HEADER}=== Installation Summary ==={Colors.ENDC}")
    print_status(f"Successfully installed: {successful}/{len(packages)} packages", "success" if successful == len(packages) else "warning")
    
    if failed:
        print_status("The following packages failed to install:", "error")
        for f in failed:
            print(f"  - {f}")
            
    # Quick sanity check for core libraries
    print(f"\n{Colors.BOLD}Verifying Core Imports...{Colors.ENDC}")
    try:
        import numpy
        import langchain
        import flask
        print_status(f"Numpy ({numpy.__version__}), LangChain ({langchain.__version__}), and Flask ({flask.__version__}) are verified and ready.", "success")
    except ImportError as e:
        print_status(f"Verification failed: {e}", "error")

if __name__ == '__main__':
    try:
        check_python_version()
        upgrade_pip()
        install_requirements()
        print(f"\n{Colors.BOLD}{Colors.OKGREEN}Setup Complete! You can now run `python app.py`{Colors.ENDC}\n")
    except KeyboardInterrupt:
        print(f"\n{Colors.FAIL}Installation aborted by user.{Colors.ENDC}")
        sys.exit(1)