import os
import subprocess
import urllib.request

# ─── CONFIG ───────────────────────────────────────────────
CONDA_DIR        = "/tmp/miniconda3"
REQUIREMENTS_DIR = "/kaggle/working/requirements"
GITHUB_RAW       = "https://raw.githubusercontent.com/tgthuan02/project-requirements/main"
PROJECTS         = ["paddle-ocr-vl-1.5", "deepseek-ocr-v1", "deepseek-ocr-v2"]

# ══════════════════════════════════════════════════════════
# 1. CONDA
# ══════════════════════════════════════════════════════════
if os.path.isfile(f"{CONDA_DIR}/bin/conda"):
    print("Conda already installed")
else:
    print("Installing Miniconda...")
    urllib.request.urlretrieve(
        "https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh",
        "/tmp/miniconda.sh"
    )
    subprocess.run(["bash", "/tmp/miniconda.sh", "-b", "-p", CONDA_DIR], check=True)
    os.remove("/tmp/miniconda.sh")
    print("Miniconda installed")

os.environ["PATH"] = f"{CONDA_DIR}/bin:{os.environ['PATH']}"
ver = subprocess.run(["conda", "--version"], capture_output=True, text=True).stdout.strip()
print(f"{ver} ready")

subprocess.run(["conda", "install", "python=3.11", "requests", "urllib3", "-y", "-q"], check=False)
python_path = f"{CONDA_DIR}/bin/python"
py_ver = subprocess.run([python_path, "--version"], capture_output=True, text=True).stdout.strip()
print(f"Python version: {py_ver}")


# ══════════════════════════════════════════════════════════
# 2. CONDA TOS
# ══════════════════════════════════════════════════════════
for channel in ["pkgs/main", "pkgs/r"]:
    subprocess.run([
        "conda", "tos", "accept",
        "--override-channels", "--channel",
        f"https://repo.anaconda.com/{channel}", "-y"
    ], capture_output=True)

# ══════════════════════════════════════════════════════════
# 3. PULL REQUIREMENTS FROM GITHUB
# ══════════════════════════════════════════════════════════
os.makedirs(REQUIREMENTS_DIR, exist_ok=True)
print("\nPulling requirements from GitHub...")

pulled = []
for project in PROJECTS:
    url  = f"{GITHUB_RAW}/{project}.txt"
    dest = f"{REQUIREMENTS_DIR}/{project}.txt"
    try:
        urllib.request.urlretrieve(url, dest)
        print(f"   {project}.txt")
        pulled.append(project)
    except Exception as e:
        print(f"   {project}.txt — not found ({e})")

if not pulled:
    raise RuntimeError("No requirement files pulled. Check GITHUB_RAW URL.")

# ══════════════════════════════════════════════════════════
# 4. SELECT PROJECT
# ══════════════════════════════════════════════════════════
available = [
    f.replace(".txt", "")
    for f in os.listdir(REQUIREMENTS_DIR)
    if f.endswith(".txt")
]

while True:
    print("\n" + "═" * 40)
    print("Available projects:")
    for i, p in enumerate(available, 1):
        with open(f"{REQUIREMENTS_DIR}/{p}.txt") as f:
            libs = [l.strip() for l in f if l.strip() and not l.startswith("#")]
        preview = ", ".join(libs[:3]) + ("..." if len(libs) > 3 else "")
        print(f"   {i}. {p:<20} ({preview})")
    print("   0. Exit")
    print("═" * 40)

    choice = input("\nSelect project (enter number): ").strip()

    if choice == "0":
        print("Setup complete!")
        print("\nLoading Conda environment and launching terminal...")

        # Write a custom bashrc for the new shell
        rc_file = "/tmp/conda_bashrc"
        with open(rc_file, "w") as f:
            f.write("source ~/.bashrc 2>/dev/null\n")
            f.write(f"source {CONDA_DIR}/etc/profile.d/conda.sh\n")
            f.write("conda activate base\n")
            f.write('export PYTHONWARNINGS="ignore"\n')
            f.write('echo -e "\\nConda environment activated! Type \\"exit\\" to quit."\n')

        # Launch bash with the custom rcfile
        new_env = os.environ.copy()
        new_env["PATH"] = f"{CONDA_DIR}/bin:{new_env.get('PATH', '')}"
        os.execle("/bin/bash", "bash", "--rcfile", rc_file, new_env)

    try:
        selected = available[int(choice) - 1]
        req_file = f"{REQUIREMENTS_DIR}/{selected}.txt"

        print(f"\nInstalling requirements for '{selected}'...")

        # Standard install
        subprocess.run(["pip", "install", "-r", req_file], check=True)

        # Post-install hooks (lines starting with "# post-install:")
        with open(req_file) as f:
            hooks = [
                l.replace("# post-install:", "").strip()
                for l in f
                if l.strip().startswith("# post-install:")
            ]

        for hook in hooks:
            print(f"\nPost-install: {hook}")
            subprocess.run(["pip", "install"] + hook.split(), check=True)

        print(f"\n'{selected}' environment ready!")

    except (IndexError, ValueError):
        print("Invalid selection")
