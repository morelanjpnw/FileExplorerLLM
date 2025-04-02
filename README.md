# FileExplorerLLM

**FileExplorerLLM** is an intelligent local file system explorer powered by large language models (LLMs). It scans your local directories for file metadata (and, in the future, file content), indexes the data using embeddings and FAISS, and enables natural language queries via an interactive chatbot.

> **Note:** The current implementation uses [Ollama](https://ollama.com) to run LLMs locally (e.g. Llama 3), but the project is designed to remain flexible and model-agnostic.

---

## Features

- 🔍 **Recursive File Scanning** – Captures directory structure and metadata (created, modified, size, etc.).
- 🧠 **LLM-Powered Chat** – Ask natural language questions about your files (e.g. "Which files relate to blast furnace interiors?").
- ⚡ **Embeddings + FAISS** – Creates a fast searchable index using vector embeddings from file info.
- 🧱 **Multi-Scan Support** – Label and reuse scans; combine multiple scans into one searchable dataset.
- ⚙️ **Configurable Filters** – Skip noisy folders (like `node_modules`) or file types based on `config.json`.

---

## Prerequisites

- **Python 3.7+**
- **[Ollama](https://ollama.com)** – For local LLM access (e.g., `llama3` or another supported model).

---

## Installation

### 1. Clone the Repository

\`\`\`bash
git clone https://github.com/your-username/FileExplorerLLM.git
cd FileExplorerLLM
\`\`\`

### 2. Create and Activate a Virtual Environment

\`\`\`bash
python -m venv .venv
\`\`\`

- **On Windows (PowerShell):**
  \`\`\`bash
  .\.venv\Scripts\Activate.ps1
  \`\`\`

- **On macOS/Linux:**
  \`\`\`bash
  source .venv/bin/activate
  \`\`\`

### 3. Install Dependencies

\`\`\`bash
pip install pymongo sentence-transformers faiss-cpu requests
\`\`\`

---

## Usage

### 1. Scan a Directory

\`\`\`bash
python file_scanner.py --directory "C:\Users\You\Documents" --label my_docs
\`\`\`

- Output is saved to \`data/scans/my_docs_metadata.bson\`
- Use \`--scan-all\` to ignore config filters and include all files

### 2. Generate Embeddings & Index

\`\`\`bash
python generate_embeddings_and_indexing.py --scans my_docs another_scan --output-label combined_docs
\`\`\`

- Saves index/mapping to \`data/indexes/combined_docs_index.index\` and \`.pkl\`
- If \`--scans\` is omitted, the script lists available scans for you to choose from

### 3. Run the Chatbot

\`\`\`bash
python chatbot.py --index-file combined_docs_index.index --mapping-file combined_docs_mapping.pkl
\`\`\`

- If arguments are omitted, you'll be shown available indexes to choose from
- Make sure Ollama is running (e.g. \`ollama run llama3\`)

---

## Configuration

The \`config.json\` file lets you define folders and file types to exclude/include. Example:

\`\`\`json
{
  "ignore_dirs": ["node_modules", "Library", "bin", "obj"],
  "include_extensions": [
    ".txt", ".pdf", ".docx", ".pptx", ".xlsx",
    ".jpg", ".png", ".tif", ".gif", ".mp4", ".py", ".js"
  ]
}
\`\`\`

---

## Future Plans

- 📝 Extract and index content from documents (e.g., \`.txt\`, \`.pdf\`, \`.docx\`)
- 🧠 Use image models to tag \`.jpg\` / \`.png\` files for semantic search
- 🔄 Background indexing + real-time file watchers
- 🔐 Optional encrypted data storage

---

## License

MIT License — see [LICENSE](LICENSE) for full terms.

---

## Acknowledgements

- [Ollama](https://ollama.com) for local LLM model runtime
- [Sentence Transformers](https://www.sbert.net/) for fast embeddings
- [FAISS](https://github.com/facebookresearch/faiss) for vector indexing
