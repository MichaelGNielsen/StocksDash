
import subprocess

def get_outdated_packages():
    result = subprocess.run(["pip", "list", "--outdated", "--format=freeze"], capture_output=True, text=True)
    lines = result.stdout.strip().split('\n')
    return [line.split('==')[0] for line in lines if line]

def upgrade_packages(packages):
    for package in packages:
        print(f"🔄 Upgrading {package} ...")
        subprocess.run(["pip", "install", "--upgrade", package])

def show_versions():
    print("\n📦 Updated package versions:\n")
    subprocess.run(["pip", "list"])

if __name__ == "__main__":
    outdated = get_outdated_packages()
    if outdated:
        upgrade_packages(outdated)
        show_versions()
    else:
        print("✅ All packages are up to date.")
