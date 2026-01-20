import zipfile
import os
import shutil

base_dist = r"app/chat/dist"
target_dir = r"app/chat/static/vendor"

files = [
    ("bootstrap (1).zip", "bootstrap"),
    ("fontawesome-free-6.4.0-web.zip", "fontawesome")
]

for zip_name, extract_name in files:
    zip_path = os.path.join(base_dist, zip_name)
    extract_to = os.path.join(target_dir, extract_name)
    
    if not os.path.exists(zip_path):
        print(f"File not found: {zip_path}")
        continue
        
    print(f"Extracting {zip_path} to {extract_to}...")
    
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(target_dir) # Extract to vendor first
        
        # Check what was extracted. Usually zips have a top folder.
        # We might need to rename it.
        # Let's see the extracted root name
        extracted_roots = zip_ref.namelist()[0].split('/')[0]
        full_extracted_path = os.path.join(target_dir, extracted_roots)
        
        # Rename if needed (if the zip content folder name is different from what we want)
        # But for now, let's just extract and I'll inspect.
        print(f"Extracted to {target_dir}")

