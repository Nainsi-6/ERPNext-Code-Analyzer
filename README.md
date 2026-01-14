# ERPNext Code Analyzer 🔍

##Code Intelligence + RAG Q&A tool for ERPNext using embeddings + LLM

A practical AI-powered tool for understanding, exploring, and questioning large Python codebases, built specifically with ERPNext in mind.

Instead of relying on keyword search, this tool indexes the codebase using embeddings, understands structure and relationships, and lets you ask natural-language questions using a Retrieval-Augmented Generation (RAG) approach grounded strictly in real source code.

##  What This Tool Does:

## 1. Static Code Analysis

Analyze a single Python file or an entire folder

Extracts:
Classes
Functions
Imports

Detects:
Function-to-function call relationships
Large functions and large classes
Common ERPNext validation and design issues
Useful when you want a quick structural understanding without using the LLM

## 2. RAG-based Code Questioning (Core Feature)

This tool uses a Retrieval-Augmented Generation (RAG) pipeline powered by embeddings + an LLM to answer questions directly from real code.

###🔹 Full Codebase Questions

Ask questions across the entire ERPNext repository:
``` bash
python main.py rag-ask "Where are validation errors raised?"
``` 

Example use cases:

Understanding global flows
Finding validations spread across multiple modules
Learning how ERPNext works end-to-end

###🔹 Folder-based Questions

Limit questions to a specific functional area (accounts, stock, selling, etc.):

``` bash
python main.py rag-ask "How are taxes calculated?" --folder erpnext/erpnext/accounts
```

Example use cases:
Exploring business logic inside a module
Debugging issues scoped to one domain
Understanding module-level responsibilities

###🔹 File-based Questions

Ask questions about one exact file only:

``` bash
python main.py rag-ask "Which methods calculate totals?" --file erpnext/erpnext/accounts/doctype/sales_invoice/sales_invoice.py
```

Example use cases:
Deep-diving into a single DocType
Reviewing unfamiliar files
Interview preparation on specific code

## 3. How the LLM Is Used:

Python code is chunked and converted into embeddings
Embeddings are stored in ChromaDB

On each question:

Relevant code chunks are retrieved using vector similarity
Only those chunks are sent to the LLM (Google Gemini)
The answer is generated strictly from retrieved code, not from assumptions

This ensures:

No hallucinated answers
Fully code-grounded responses
Traceable logic back to real files

## 4. AI-Assisted Understanding (Developer-Focused)

Using the retrieved code context, the LLM helps to:

Explain business logic
Summarize what a module or file actually does
Highlight design and validation concerns
Answer questions in a clear, backend-developer tone

## 🧠 Why This Is Useful

ERPNext is large and difficult to navigate.

This tool helps you:

Onboard faster into ERPNext internals
Understand hidden flows (taxes, validations, lifecycle hooks)
Debug unfamiliar modules confidently
Prepare for backend / ERPNext interviews
Demonstrate real-world RAG with embeddings on a production-scale codebase

## 🏗️ Project Structure

``` bash
my-erpnext-analyzer/
│
├── main.py                 # Unified CLI entry point
├── rag.py                  # RAG system (embeddings + retrieval + Gemini)
├── extractor.py            # AST-based structure extractor
├── relationships.py        # Function call relationship detector
├── errors.py               # Code smell & validation detector
├── output.py               # Terminal + JSON formatter
├── requirements.txt        # Python dependencies
├── README.md
│
├── chroma_db/              # Vector database (auto-generated)
└── erpnext/                # ERPNext source code
```
## 🛠️ Tech Stack

``` bash
Python 3.10+
AST (Abstract Syntax Tree) – static code parsing
ChromaDB – vector database for storing embeddings
Google Gemini API – embedding generation and answer synthesis
Colorama – readable CLI output
Argparse – command-line interface
```

## ⚙️ Setup
### Create virtual environment
``` bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
```

### Install dependencies
``` bash
pip install -r requirements.txt
```


Create a .env file:

``` bash
GOOGLE_API_KEY=your_gemini_api_key_here
```

###📦 Build the RAG Database (Required Once)

Indexes ERPNext by generating embeddings for code chunks and storing them in ChromaDB.

### Index entire ERPNext folder
``` bash
python main.py rag-init ./erpnext
```
This step:
Splits Python files into chunks
Generates embeddings for each chunk
Stores them in chroma_db
Needs to be run once per codebase

## ❓ Ask Questions Using RAG
Global (entire codebase)
``` bash
python main.py rag-ask "Where are validation errors raised?"
```

### Folder-scoped question
``` bash
python main.py rag-ask "How are taxes calculated?" --folder erpnext/erpnext/accounts
```

### File-scoped question
``` bash
python main.py rag-ask "How are taxes calculated?" --file erpnext/erpnext/accounts/doctype/sales_invoice/sales_invoice.py
```
Each answer is generated using retrieved embeddings, ensuring responses are grounded in real code.

### 🔍 Keyword Search (Vector-based)
``` bash
python main.py rag-search "tax"
```
Returns:
Matching files
Line ranges
Similarity score
Relevant code snippets

## 🧪 Static Analysis (Without RAG)

### Analyze a single file
``` bash
python main.py analyze erpnext/erpnext/accounts/doctype/sales_invoice/sales_invoice.py
```
### Analyze a folder
``` bash
python main.py analyze erpnext/erpnext/accounts
```

### Optional JSON output:
``` bash
python main.py analyze erpnext/erpnext/accounts --json
```

## 🧩 Example Output (RAG)
``` bash
Question: How are taxes calculated?
```
Answer:
``` bash
Taxes are calculated through calculate_taxes_and_totals, which iterates
over tax rows and items, applying charge types such as "Actual",
"On Net Total", and "On Previous Row Amount".
```

❤️ Made by Nainsi Gupta
