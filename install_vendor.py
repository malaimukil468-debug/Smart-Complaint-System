import urllib.request
import json
import zipfile
import io
import os
import tarfile

packages = ["Flask", "Werkzeug", "Jinja2", "itsdangerous", "click", "colorama", "blinker"]
vendor_dir = "vendor"
os.makedirs(vendor_dir, exist_ok=True)

def download_wheel(pkg):
    try:
        url = f"https://pypi.org/pypi/{pkg}/json"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode('utf-8'))
        
        version = data["info"]["version"]
        urls = data["releases"][version]
        
        wheel_url = next((u["url"] for u in urls if u["filename"].endswith(".whl")), None)
        if not wheel_url:
            print(f"No wheel for {pkg}")
            return
            
        print(f"Downloading {pkg} from {wheel_url}...")
        req = urllib.request.Request(wheel_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as resp:
            with zipfile.ZipFile(io.BytesIO(resp.read()), 'r') as z:
                z.extractall(vendor_dir)
        print(f"Successfully installed {pkg}")
    except Exception as e:
        print(f"Failed to install {pkg}: {e}")

for pkg in packages:
    download_wheel(pkg)

# Special handling for MarkupSafe, download tar.gz and extract src/markupsafe
pkg = "MarkupSafe"
try:
    url = f"https://pypi.org/pypi/{pkg}/json"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode('utf-8'))
    
    version = data["info"]["version"]
    urls = data["releases"][version]
    tar_url = next((u["url"] for u in urls if u["filename"].endswith(".tar.gz")), None)
    
    if tar_url:
        print(f"Downloading {pkg} tar.gz from {tar_url}...")
        req = urllib.request.Request(tar_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as resp:
            with tarfile.open(fileobj=io.BytesIO(resp.read()), mode="r:gz") as tar:
                for member in tar.getmembers():
                    if member.name.startswith(f"MarkupSafe-{version}/src/markupsafe"):
                        # strip the prefix
                        member.name = member.name.replace(f"MarkupSafe-{version}/src/", "")
                        tar.extract(member, path=vendor_dir)
        print(f"Successfully installed {pkg}")
except Exception as e:
    print(f"Failed to install {pkg}: {e}")

print("All dependencies downloaded to vendor/")
