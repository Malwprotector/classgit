#!/usr/bin/env python3
"""

- Default path: ~/ClassGit
- Encrypts course files before push (without touching originals)
- Decrypts pulled files automatically into ~/ClassGit/courses
- Never pushes the key
- GitHub repo URL and public key stored locally during setup
- Incremental pushes: only new or modified files are encrypted and pushed
- Generates a README.md during push with system info
"""

import os
import subprocess
from pathlib import Path
import shutil
import tempfile

# -----
# logo intro
# -----
print(r"""
░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
░░░░░░░▒░░░░░░░░░░░░░░░▓░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
░░░░░░░░░░░░░░░░░░░░░░█▓▓█▓▓█▓▓▓█░░░░░░░░░░░░░░░░░░░░░░
░░░░░░░░░░░░░░░░░░░░░▓▓▓▓░░░░░▓▓█▓█░░░░░░░░░░░░░░░░░░░░
░░░░░░▒░░░░░░░░░░░░░█▓▓░░░░░░░░░██▓░░░░░░░░░░░░░░░░░░░░
░░░░░░░░░░░░░░░░░░░░█▓▓░░░░░░░░░▓█▓▒░░░░░░░░░░░░░░░░░░░
░░░░░░░░░░░░░░░░░░░░▓▓▓░░░░░░░░░▓█▓▒░░░░░░▓██░░░░░░░░░░
░░░░░░░░░░░░░░░▒░██▓▓██▓█▓▓████▓███▓█▓░░░░▓▓█░░░░░░░░░░
░░░░░░░░░░░░░░░░░██▓▓▓▓██▓█░▓███▓▓▓▓░░░░█▓░░░░░░░░▒░░░░
░░░░░░░░░░░░░░░░░█▓▓█▓▓▓██░░░▓██▓█▓░██▓▓░░░░░░░░░░░░░░░
░░░░░░░░░░░░░░░░░█████▒██▓▓░▓██▓█▓█▓░█▓▓▓░░▓▓░░░░░░░░░░
░░░░░░░░░░░░░███▓░░▓█▓█▓█▓░░░██▓▓▓███▓░░░░░░░░░░░░░░░░░
░░░░░░░░░░░░▓░░░░░█▓▓░░█▓▓▓▓████▓▓▓▓██▓▓░░█░░░░░░░░░░░░
░░░░░░░░░░░█░░▓░░░▒█░░█▓░▓█▓█▓▓▓░█▓░░░▓█░░░▓░░░░░░░░░░░
░░░░░░░░░░█▒░░░░░░▓▓░░▓░░▓░█▓░▓█░░█░░░█▓█░░░▓░░░░░░░░░░
░░░░░░░░░█▓█▓█▓▓█░░░░░█░█░░▓▓░░█░░░░░░▒█▓▓▓█▓▓░░░░░░░░░
░░░░░░░░░░█▓█▓███▓▓██▓░░▓░░██░░░░▓██▓▓▓▓▓▓█▓▓░░░░░░░░░░
░░░░░░░░░░░░░░░░▒█▓█▓▓▓█▓██▓▓██▓██▓█▓▓█░░░░░░░░░░░░░░░░
░░░░░░░░░░░░░░░░░░░░░░███░░░░░▓▓█░░░░░░░░░░░░░░░░░░░░░░
░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
░░░░░▓██▓█░██░░░░█▓▓▒░░▓██▓▓░▓█▓█▓░▓███▓░█▓░█▓█▓██░░░░░
░░░░░█▓░▓█░▓▓░░░░▓██▓░░▓▒░░░░█▓░░░░▓▓░░░░█▓░░░▓█░░░░░░░
░░░░░▓█░░░░▓▓░░░██░▓▓░░▓██▒░░▓▓██░░▓▓░▓▓░██░░░▓█░░░░░░░
░░░░░█▓░▓▓░▓▓░░░▓▓▓▓▓░░░░░▓█░░░░█▓░█▓░▓█░▓█░░░▓█░░░░░░░
░░░░░▓▓▓▓█░▓█▓▓░▓█░░▓▓░▓█▓▓▓░▓▓▓█▓░▓▓▓██░▓█░░░▓█░░░░░░░
░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
""")

# -----------------------------
# Configuration
# -----------------------------
LOCAL_DIR = Path.home() / "ClassGit"
CONFIG_DIR = LOCAL_DIR / "config"
COURSES_DIR = LOCAL_DIR / "courses"
AGE_KEY_PATH = CONFIG_DIR / "age_key.txt"
REPO_FILE = CONFIG_DIR / "repo_url.txt"
PUBLIC_KEY_FILE = CONFIG_DIR / "public_key.txt"

# -----------------------------
# Utility Functions
# -----------------------------
def run(cmd, cwd=None):
    result = subprocess.run(cmd, shell=True, cwd=cwd)
    if result.returncode != 0:
        print(f"Error running: {cmd}")
        exit(1)

def encrypt_file(file_path, recipient, output_path):
    subprocess.run([
        "age",
        "-r", recipient,
        "-o", str(output_path),
        str(file_path)
    ], check=True)

def decrypt_file(file_path, key_path, output_path):
    subprocess.run([
        "age",
        "-d",
        "-i", str(key_path),
        "-o", str(output_path),
        str(file_path)
    ], check=True)

# -----------------------------
# Setup Functions
# -----------------------------
def configure_repo():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    COURSES_DIR.mkdir(exist_ok=True)

    if not AGE_KEY_PATH.exists():
        run(f"age-keygen -o {AGE_KEY_PATH}")
        print(f"Encryption key created at {AGE_KEY_PATH}")

    if REPO_FILE.exists():
        repo_url = REPO_FILE.read_text().strip()
    else:
        repo_url = input("Enter your GitHub repository HTTPS URL: ").strip()
        REPO_FILE.write_text(repo_url)

    if not PUBLIC_KEY_FILE.exists():
        key = input("Enter the Age public key to encrypt courses (this will be saved): ").strip()
        PUBLIC_KEY_FILE.write_text(key)

    if not (LOCAL_DIR / ".git").exists():
        run("git init", cwd=LOCAL_DIR)
        run(f"git remote add origin {repo_url}", cwd=LOCAL_DIR)
        run("git branch -M main", cwd=LOCAL_DIR)
        with open(LOCAL_DIR / ".gitignore", "w") as f:
            f.write("config/age_key.txt\n")
        run("git add .gitignore", cwd=LOCAL_DIR)
        run('git commit -m "Initial commit with gitignore"', cwd=LOCAL_DIR)

    return repo_url

def get_public_key():
    return PUBLIC_KEY_FILE.read_text().strip()

# -----------------------------
# Core Functions
# -----------------------------
def generate_readme(tmpdir):
    """Create or update README.md with system info."""
    readme_path = tmpdir / "README.md"
    content = f"""# ClassGit

ClassGit is a system for secure synchronization of your course files using Git and age encryption.

**Default local folder:** `{LOCAL_DIR}`
**Encrypted files:** Stored on GitHub only, local files remain unencrypted.
**Key location:** `{AGE_KEY_PATH}` (never pushed)
**Public key:** stored locally for encryption
**Do not remove** the `{LOCAL_DIR}/.git` folder.


## Usage

1. **Push courses:** Encrypts all files in `{COURSES_DIR}` and pushes them to the remote repo.
2. **Pull courses:** Downloads encrypted files from GitHub and decrypts them automatically into `{COURSES_DIR}`.
3. **Add a new device:** Copy your age key to another device to access the encrypted files.
4. **Git status:** Check the repository status locally.

## License & Disclaimer

ClassGit is provided **as-is**. The author is not responsible for any data loss, misuse, or damage caused while using the system.
"""
    readme_path.write_text(content)

def push_courses(repo_url):
    recipient = get_public_key()
    if not any(COURSES_DIR.iterdir()):
        print("No course files found to push.")
        return

    encrypted_dir = LOCAL_DIR / "encrypted"
    encrypted_dir.mkdir(exist_ok=True)

    print("🔒 Synchronizing encrypted directory...")

    # --- Encrypt or update changed files ---
    for root, dirs, files in os.walk(COURSES_DIR):
        rel_path = Path(root).relative_to(COURSES_DIR)
        for d in dirs:
            (encrypted_dir / rel_path / d).mkdir(parents=True, exist_ok=True)
        for f in files:
            src = Path(root) / f
            dst = encrypted_dir / rel_path / (f + ".age")
            if not dst.exists() or src.stat().st_mtime > dst.stat().st_mtime:
                print(f"🔒 Encrypting {src} → {dst}")
                encrypt_file(src, recipient, dst)

    # --- Remove orphan encrypted files ---
    for root, dirs, files in os.walk(encrypted_dir):
        for f in files:
            if not f.endswith(".age"):
                continue
            enc_path = Path(root) / f
            try:
                rel = enc_path.relative_to(encrypted_dir)
            except Exception:
                continue
            orig = COURSES_DIR / rel.with_suffix('')  # remove .age
            if not orig.exists():
                print(f"🗑️ Removing orphan encrypted file: {enc_path}")
                try:
                    enc_path.unlink()
                except Exception as e:
                    print(f"❌ Failed to remove {enc_path}: {e}")

    # --- Remove empty directories in encrypted_dir ---
    for root, dirs, files in os.walk(encrypted_dir, topdown=False):
        rootp = Path(root)
        if rootp == encrypted_dir:
            continue
        if not any(rootp.iterdir()):
            try:
                print(f"🗑️ Removing empty directory: {rootp}")
                rootp.rmdir()
            except Exception as e:
                print(f"❌ Failed to remove dir {rootp}: {e}")

    # --- Generate README.md ---
    generate_readme(LOCAL_DIR)

    # --- Update .gitignore ---
    gitignore_path = LOCAL_DIR / ".gitignore"
    with open(gitignore_path, "w") as f:
        f.write("# Local sensitive / plaintext\n")
        f.write("config/\n")
        f.write("courses/\n")
        f.write("\n# Keep encrypted files (in encrypted/ or repo root) and README\n")
        f.write("!.gitignore\n")
        f.write("!README.md\n")

    # --- Git snapshot (single commit) ---
    print("🧹 Creating single-commit snapshot to avoid large history...")

    subprocess.run(["git", "checkout", "--orphan", "temp-branch"], cwd=LOCAL_DIR, check=True)
    subprocess.run(["git", "add", "-A"], cwd=LOCAL_DIR, check=True)
    subprocess.run(["git", "commit", "-m", "Snapshot: update courses and README"], cwd=LOCAL_DIR, check=True)
    subprocess.run(["git", "branch", "-D", "main"], cwd=LOCAL_DIR, check=True)
    subprocess.run(["git", "branch", "-m", "main"], cwd=LOCAL_DIR, check=True)
    subprocess.run(["git", "reflog", "expire", "--expire=now", "--all"], cwd=LOCAL_DIR, check=True)
    subprocess.run(["git", "gc", "--prune=now", "--aggressive"], cwd=LOCAL_DIR, check=True)

    # --- Push forced to remote ---
    subprocess.run(["git", "push", "--force", "origin", "main"], cwd=LOCAL_DIR, check=True)
    print("✅ Courses encrypted and pushed (history reset).")



def pull_courses():
    print("⬇️ Pulling latest encrypted files from remote...")

    # --- fetch and force align with origin/main if divergence ---
    fetch = subprocess.run(["git", "fetch", "origin"], cwd=LOCAL_DIR)
    if fetch.returncode != 0:
        print("❌ Failed to fetch from remote.")
        return

    # check divergence
    status = subprocess.run(["git", "status", "--porcelain=2", "--branch"],
                            cwd=LOCAL_DIR, capture_output=True, text=True)
    if "branch.ab" in status.stdout and "+" in status.stdout:
        print("⚠️ Local branch diverged from remote. Resetting to origin/main...")
        reset = subprocess.run(["git", "reset", "--hard", "origin/main"], cwd=LOCAL_DIR)
        if reset.returncode != 0:
            print("❌ Failed to reset to remote branch.")
            return
    else:
        # normal fast-forward pull
        pull = subprocess.run(["git", "pull", "--ff-only"], cwd=LOCAL_DIR)
        if pull.returncode != 0:
            print("⚠️ Pull failed, forcing reset to remote state...")
            subprocess.run(["git", "reset", "--hard", "origin/main"], cwd=LOCAL_DIR)

    encrypted_dir = LOCAL_DIR / "encrypted"
    decrypted_dir = Path.home() / "ClassGit" / "courses"
    decrypted_dir.mkdir(parents=True, exist_ok=True)

    if not encrypted_dir.exists():
        print("❌ No encrypted/ directory found after sync. Check remote repo contents.")
        return

    # Iterate through all .age files and decrypt them
    for root, _, files in os.walk(encrypted_dir):
        for file in files:
            if file.endswith(".age"):
                src = Path(root) / file
                relative = src.relative_to(encrypted_dir)
                dst = decrypted_dir / relative.with_suffix("")

                dst.parent.mkdir(parents=True, exist_ok=True)
                cmd = [
                    "age", "-d",
                    "-i", str(AGE_KEY_PATH),
                    "-o", str(dst),
                    str(src)
                ]
                print(f"🔓 Decrypting {src} → {dst}")
                try:
                    subprocess.run(cmd, check=True)
                except subprocess.CalledProcessError:
                    print(f"❌ Failed to decrypt {src}")



def add_device():
    new_path = Path(input("Enter full path to copy your age key for a new device: ").strip())
    new_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(AGE_KEY_PATH, new_path)
    print(f"🔑 Key copied to {new_path}")

def status():
    run("git status", cwd=LOCAL_DIR)

# -----------------------------
# Menu
# -----------------------------
def menu():
    repo_url = configure_repo()
    while True:
        print("""
ClassGit Menu
1. ⬆️ Push courses
2. ⬇️ Pull courses
3. 💻 Add a new device
4. 📋 Show Git status
5. 🚪 Quit
""")
        choice = input("Select an option: ").strip()
        if choice == "1":
            push_courses(repo_url)
        elif choice == "2":
            pull_courses()
        elif choice == "3":
            add_device()
        elif choice == "4":
            status()
        elif choice == "5":
            exit()
        else:
            print("❓ Invalid option, try again.")

# -----------------------------
# Main
# -----------------------------
if __name__ == "__main__":
    menu()
