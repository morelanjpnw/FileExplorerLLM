# file_scanner.py
import os
import datetime
import bson  # from pymongo
import sys
import json
import argparse

# Directories for data storage
DATA_DIR = "data"
SCAN_DIR = os.path.join(DATA_DIR, "scans")
CONFIG_FILE = "config.json"

def ensure_directories():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    if not os.path.exists(SCAN_DIR):
        os.makedirs(SCAN_DIR)

def load_config():
    ignore_dirs = []
    include_extensions = None
    if os.path.isfile(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            try:
                config = json.load(f)
                ignore_dirs = config.get("ignore_dirs", [])
                include_extensions = [ext.lower() for ext in config.get("include_extensions", [])]
            except Exception as e:
                print("Error reading config.json:", e)
    return ignore_dirs, include_extensions

def get_file_metadata(path):
    try:
        stats = os.stat(path)
        return {
            "size_bytes": stats.st_size,
            "created": datetime.datetime.fromtimestamp(stats.st_ctime).isoformat(),
            "modified": datetime.datetime.fromtimestamp(stats.st_mtime).isoformat(),
            "accessed": datetime.datetime.fromtimestamp(stats.st_atime).isoformat()
        }
    except Exception as e:
        return {"error": str(e)}

def scan_directory(directory, ignore_dirs, include_extensions, scan_all):
    tree = {}
    target_drive = os.path.splitdrive(directory)[0].lower()
    
    for root, dirs, files in os.walk(directory):
        # Only scan directories on the same drive
        if os.path.splitdrive(root)[0].lower() != target_drive:
            continue
        
        # Apply ignore filter if not scanning all
        if not scan_all:
            dirs[:] = [d for d in dirs if d not in ignore_dirs]
        
        try:
            rel_root = os.path.relpath(root, directory)
        except ValueError:
            continue
        
        # Navigate to the appropriate subtree in the nested dict
        subtree = tree
        if rel_root != ".":
            for part in rel_root.split(os.sep):
                subtree = subtree.setdefault("subdirs", {}).setdefault(part, {})
        
        # Record directory metadata
        subtree["dir_info"] = {"path": root, "metadata": get_file_metadata(root)}
        subtree["files"] = {}
        for filename in files:
            # If allowed file types are defined, filter based on extension (unless overridden)
            if include_extensions and not scan_all:
                ext = os.path.splitext(filename)[1].lower()
                if ext not in include_extensions:
                    continue
            filepath = os.path.join(root, filename)
            subtree["files"][filename] = get_file_metadata(filepath)
    return tree

if __name__ == "__main__":
    ensure_directories()
    
    parser = argparse.ArgumentParser(description="Scan a directory and save metadata as BSON.")
    parser.add_argument("--directory", help="Path to the directory to scan.")
    parser.add_argument("--label", help="Label for this scan (e.g. 'jack_docs').")
    parser.add_argument("--scan-all", action="store_true", help="Scan all files and directories, ignoring config filters.")
    args = parser.parse_args()
    
    if not args.directory:
        args.directory = input("Enter the full path to the directory to scan: ").strip()
    if not os.path.isdir(args.directory):
        print("Invalid directory. Exiting.")
        sys.exit(1)
    if not args.label:
        args.label = input("Enter a label for this scan (e.g. 'jack_docs'): ").strip()
    
    ignore_dirs, include_extensions = load_config()
    print("Scanning... please wait.")
    data = scan_directory(args.directory, ignore_dirs, include_extensions, args.scan_all)
    
    output_file = os.path.join(SCAN_DIR, f"{args.label}_metadata.bson")
    with open(output_file, "wb") as f:
        f.write(bson.BSON.encode(data))
    
    print(f"\n✅ Scan complete! Metadata saved to: {output_file}")
