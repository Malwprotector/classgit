#!/usr/bin/env python3
"""

- Default path: ~/ClassGit
- Encrypts course files before push (without touching originals)
- Decrypts pulled files automatically into ~/ClassGit/courses
- Never pushes the key
- GitHub repo URL and public key stored locally during setup
"""

import os
import subprocess
from pathlib import Path
import shutil
import tempfile

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
def push_courses(repo_url):
    recipient = get_public_key()
    if not any(COURSES_DIR.iterdir()):
        print("No course files found to push.")
        return

    with tempfile.TemporaryDirectory() as tmpdirname:
        tmpdir = Path(tmpdirname)
        temp_courses = tmpdir / "courses"
        temp_courses.mkdir(parents=True)

        # Encrypt files
        for f in COURSES_DIR.iterdir():
            if f.is_file():
                encrypt_file(f, recipient, temp_courses / (f.name + ".age"))


        # Copy structure to temp repo
        for item in temp_courses.iterdir():
            shutil.move(str(item), tmpdir)
        temp_courses.rmdir()

        # Initialize temp repo and push
        run("git init", cwd=tmpdir)
        run(f"git remote add origin {repo_url}", cwd=tmpdir)
        run("git branch -M main", cwd=tmpdir)
        with open(tmpdir / ".gitignore", "w") as f:
            f.write("config/age_key.txt\n")
        run("git add .gitignore", cwd=tmpdir)
        run("git add .", cwd=tmpdir)
        run('git commit -m "Update courses"', cwd=tmpdir)
        run("git push -u origin main --force", cwd=tmpdir)
    print("Courses encrypted and pushed. Local files remain unencrypted.")

def pull_courses():
    """Pull encrypted files from GitHub and decrypt into COURSES_DIR."""
    temp_pull = tempfile.TemporaryDirectory()
    tmpdir = Path(temp_pull.name)

    # Clone remote into temp folder
    repo_url = REPO_FILE.read_text().strip()
    run(f"git clone {repo_url} {tmpdir}", cwd=LOCAL_DIR)

    # Ensure courses dir exists
    COURSES_DIR.mkdir(exist_ok=True)

    # Decrypt all .age files into COURSES_DIR
    for f in tmpdir.iterdir():
        if f.suffix == ".age":
            decrypt_file(f, AGE_KEY_PATH, COURSES_DIR / f.with_suffix('').name)

    temp_pull.cleanup()
    print(f"Courses pulled and decrypted into {COURSES_DIR}")

def add_device():
    new_path = Path(input("Enter full path to copy your age key for a new device: ").strip())
    new_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(AGE_KEY_PATH, new_path)
    print(f"Key copied to {new_path}")

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
1. Push courses
2. Pull courses
3. Add a new device
4. Show Git status
5. Quit
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
            print("Invalid option, try again.")

# -----------------------------
# Main
# -----------------------------
if __name__ == "__main__":
    menu()
