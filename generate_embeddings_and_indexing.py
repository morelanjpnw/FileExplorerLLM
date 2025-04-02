# generate_embeddings_and_indexing.py
import os
import bson  # from pymongo
import json
import faiss
import numpy as np
import pickle
from sentence_transformers import SentenceTransformer
import argparse
import glob

DATA_DIR = "data"
SCAN_DIR = os.path.join(DATA_DIR, "scans")
INDEX_DIR = os.path.join(DATA_DIR, "indexes")

def ensure_directories():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    if not os.path.exists(SCAN_DIR):
        os.makedirs(SCAN_DIR)
    if not os.path.exists(INDEX_DIR):
        os.makedirs(INDEX_DIR)

def load_metadata(file_path):
    with open(file_path, "rb") as f:
        data = bson.BSON(f.read()).decode()
    return data

def flatten_metadata(metadata, parent_path=""):
    documents = []
    if "dir_info" in metadata:
        path_val = metadata["dir_info"].get("path", parent_path)
        doc_text = f"Directory: {path_val}"
        documents.append((path_val, doc_text))
    files = metadata.get("files", {})
    for filename, data in files.items():
        full_path = os.path.join(parent_path, filename) if parent_path else filename
        text = f"File: {full_path}\nMetadata: {json.dumps(data)}"
        documents.append((full_path, text))
    subdirs = metadata.get("subdirs", {})
    for subdir, submeta in subdirs.items():
        sub_path = os.path.join(parent_path, subdir) if parent_path else subdir
        documents.extend(flatten_metadata(submeta, sub_path))
    return documents

def list_available_scan_labels():
    # Look for files ending with _metadata.bson in the SCAN_DIR
    pattern = os.path.join(SCAN_DIR, "*_metadata.bson")
    files = glob.glob(pattern)
    labels = []
    for file in files:
        base = os.path.basename(file)
        if base.endswith("_metadata.bson"):
            label = base[:-len("_metadata.bson")]
            labels.append(label)
    return labels

if __name__ == "__main__":
    ensure_directories()
    
    parser = argparse.ArgumentParser(description="Generate embeddings and FAISS index for one or more scans.")
    parser.add_argument("--scans", nargs="+", help="List of scan labels to process (e.g. jack_docs d_docs).")
    parser.add_argument("--output-label", help="Label for the combined output index and mapping.")
    args = parser.parse_args()
    
    if not args.scans:
        available_labels = list_available_scan_labels()
        if available_labels:
            print("Available scan labels:")
            for label in available_labels:
                print(f" - {label}")
        else:
            print("No scan files found in the scans directory.")
        scans_input = input("Enter the scan labels to process (separated by spaces): ").strip()
        args.scans = scans_input.split()
    if not args.output_label:
        args.output_label = input("Enter a label for the combined output index and mapping: ").strip()
    
    all_documents = []
    for label in args.scans:
        file_path = os.path.join(SCAN_DIR, f"{label}_metadata.bson")
        if not os.path.isfile(file_path):
            print(f"Scan file not found: {file_path}")
            continue
        metadata = load_metadata(file_path)
        docs = flatten_metadata(metadata)
        all_documents.extend(docs)
    
    if not all_documents:
        print("No documents found from specified scans. Exiting.")
        exit(1)
    
    texts = [doc[1] for doc in all_documents]
    file_names = [doc[0] for doc in all_documents]
    
    model = SentenceTransformer('all-MiniLM-L6-v2')
    embeddings = model.encode(texts, convert_to_numpy=True)
    
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)
    
    index_file = os.path.join(INDEX_DIR, f"{args.output_label}_index.index")
    mapping_file = os.path.join(INDEX_DIR, f"{args.output_label}_mapping.pkl")
    faiss.write_index(index, index_file)
    with open(mapping_file, "wb") as f:
        pickle.dump({"file_names": file_names, "texts": texts}, f)
    
    print(f"✅ FAISS index saved to: {index_file}")
    print(f"✅ Mapping saved to: {mapping_file}")
