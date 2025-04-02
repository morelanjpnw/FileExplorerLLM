# chatbot.py
import os
import argparse
import glob
import faiss
import pickle
import numpy as np
import requests
from sentence_transformers import SentenceTransformer

DATA_DIR = "data"
INDEX_DIR = os.path.join(DATA_DIR, "indexes")

def list_available_indexes():
    pattern = os.path.join(INDEX_DIR, "*_index.index")
    index_files = glob.glob(pattern)
    labels = []
    for index_file in index_files:
        base = os.path.basename(index_file)
        if base.endswith("_index.index"):
            label = base[:-len("_index.index")]
            mapping_file = os.path.join(INDEX_DIR, f"{label}_mapping.pkl")
            if os.path.isfile(mapping_file):
                labels.append((label, index_file, mapping_file))
    return labels

def query_ollama(prompt):
    url = "http://localhost:11434/api/generate"  # Ollama API endpoint
    payload = {
        "model": "llama3.2",  # Update this if needed
        "prompt": prompt,
        "stream": False
    }
    response = requests.post(url, json=payload)
    try:
        return response.json().get("response", "")
    except Exception as e:
        print("Error parsing JSON:", e)
        print("Response text:", response.text)
        return ""

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Chatbot to query file metadata FAISS index.")
    parser.add_argument("--index-file", help="FAISS index file to load (e.g. combined_index.index)")
    parser.add_argument("--mapping-file", help="Mapping file to load (e.g. combined_mapping.pkl)")
    args = parser.parse_args()
    
    if not args.index_file or not args.mapping_file:
        available = list_available_indexes()
        if not available:
            print("No available index/mapping pairs found in data/indexes.")
            exit(1)
        print("Available index/mapping pairs:")
        for idx, (label, index_path, mapping_path) in enumerate(available, start=1):
            print(f"  {idx}. Label: {label}")
        choice = input("Enter the number or label of the scan to load: ").strip()
        selected = None
        # Try to interpret as a number.
        try:
            choice_num = int(choice)
            if 1 <= choice_num <= len(available):
                selected = available[choice_num - 1]
            else:
                print("Invalid number selection. Exiting.")
                exit(1)
        except ValueError:
            # Otherwise, check if the input matches a label.
            for item in available:
                if item[0] == choice:
                    selected = item
                    break
            if not selected:
                print("Invalid label selection. Exiting.")
                exit(1)
        label, index_path, mapping_path = selected
        args.index_file = os.path.basename(index_path)
        args.mapping_file = os.path.basename(mapping_path)
    
    index_path = os.path.join(INDEX_DIR, args.index_file)
    mapping_path = os.path.join(INDEX_DIR, args.mapping_file)
    
    if not os.path.isfile(index_path):
        print(f"Index file not found: {index_path}")
        exit(1)
    if not os.path.isfile(mapping_path):
        print(f"Mapping file not found: {mapping_path}")
        exit(1)
    
    with open(mapping_path, "rb") as f:
        mapping = pickle.load(f)
    file_names = mapping["file_names"]
    texts = mapping["texts"]
    
    index = faiss.read_index(index_path)
    
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    def retrieve_relevant_documents(query, k=5):
        query_embedding = model.encode([query], convert_to_numpy=True)
        distances, indices = index.search(query_embedding, k)
        results = []
        for idx in indices[0]:
            if idx < len(texts):
                results.append(texts[idx])
        return results

    # Initialize conversation history; each exchange consists of a user and bot message.
    conversation_history = []

    print("Chatbot initialized. Type 'exit' to quit.")
    while True:
        user_input = input("You: ")
        if user_input.lower() == "exit":
            break

        # Append the new user message to conversation history.
        conversation_history.append(f"You: {user_input}")
        
        # Retrieve relevant documents from FAISS.
        relevant_docs = retrieve_relevant_documents(user_input, k=5)
        context = "\n\n".join(relevant_docs)
        
        # Include only the last 10 exchanges (i.e. 20 lines) in the prompt.
        history_to_include = "\n".join(conversation_history[-20:])
        
        prompt = (
            f"Conversation History:\n{history_to_include}\n\n"
            f"Context:\n{context}\n\n"
            f"User: {user_input}\nBot:"
        )
        
        response = query_ollama(prompt)
        
        # Append the bot response to conversation history.
        conversation_history.append(f"Bot: {response}")
        
        print("Bot:", response)
