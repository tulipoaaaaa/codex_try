import subprocess

# List of packages to upgrade (package, safe_version)
UPGRADES = [
    ("Pillow", "10.3.0"),
    ("setuptools", "69.5.1"),
    ("cryptography", "42.0.5"),
    ("scrapy", "2.11.1"),
    ("scikit-learn", "1.4.2"),
    ("black", "24.4.2"),
    # Add more as needed
]

def upgrade_package(pkg, version):
    print(f"Upgrading {pkg} to {version} ...")
    subprocess.run(["pip", "install", f"{pkg}>={version}"], check=True)

def main():
    for pkg, version in UPGRADES:
        upgrade_package(pkg, version)
    # Freeze the new requirements
    with open("CorpusBuilderApp/requirements.txt", "w") as f:
        subprocess.run(["pip", "freeze"], stdout=f, check=True)
    print("All packages upgraded and requirements.txt updated.")

if __name__ == "__main__":
    main()