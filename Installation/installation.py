import os
import sys
import subprocess
import platform
from pathlib import Path
import venv


REPO_URL = "https://github.com/thebrickmaster626-bit/Kario-Assistant"
PROJECT_NAME = "Kario-Assistant"


def run(cmd, cwd=None):
    print(f"\n>> {' '.join(cmd)}\n")
    subprocess.run(cmd, cwd=cwd, check=True)


def install_pyaudio_deps():
    system = platform.system()

    print("\n=== Installing PyAudio dependencies ===\n")

    try:
        if system == "Darwin":
            # macOS
            print("macOS detected")

            # check brew exists
            if subprocess.call(["which", "brew"], stdout=subprocess.DEVNULL) != 0:
                print("Homebrew not found. Please install it first: https://brew.sh")
                return

            run(["brew", "install", "portaudio"])

        elif system == "Linux":
            print("Linux detected")

            # try apt first
            if subprocess.call(["which", "apt-get"], stdout=subprocess.DEVNULL) == 0:
                run(["sudo", "apt-get", "update"])
                run(["sudo", "apt-get", "install", "-y", "portaudio19-dev"])
            else:
                print("apt-get not found. Install portaudio manually.")

        elif system == "Windows":
            print("Windows detected")
            print("Using pip wheels (may require prebuilt binaries)")

        # Always attempt pip install
        run([sys.executable, "-m", "pip", "install", "pyaudio"])

        print("PyAudio setup complete.")

    except Exception as e:
        print(f"PyAudio install failed: {e}")
        print("You may need to install PortAudio manually.")


def main():
    print("=== Kario Installer ===\n")

    dest = input("Enter full folder path where you want the project cloned: ").strip()
    dest_path = Path(dest)

    if not dest_path.exists():
        print("Invalid path.")
        sys.exit(1)

    os.chdir(dest_path)

    repo_path = dest_path / PROJECT_NAME

    # Clone repo
    if not repo_path.exists():
        run(["git", "clone", REPO_URL])
    else:
        print("Repo already exists, skipping clone.")

    os.chdir(repo_path)

    # Create venv
    venv_path = repo_path / ".venv"

    if not venv_path.exists():
        print("Creating virtual environment...")
        venv.EnvBuilder(with_pip=True).create(venv_path)

    # Python inside venv
    if platform.system() == "Windows":
        python_bin = venv_path / "Scripts" / "python.exe"
    else:
        python_bin = venv_path / "bin" / "python"

    # Install requirements
    run([str(python_bin), "-m", "pip", "install", "-r", "Installation/requirements.txt"])

    # PyAudio special install
    install_pyaudio_deps()

    # Ollama models
    print("\n=== Installing Ollama models ===\n")
    run(["ollama", "pull", "phi4-mini"])
    run(["ollama", "pull", "ministral-3:3b"])

    print("\n=== Setup complete ===")
    print("Start Ollama with: ollama serve")
    print(f"Run assistant with: {python_bin} main.py")


if __name__ == "__main__":
    main()