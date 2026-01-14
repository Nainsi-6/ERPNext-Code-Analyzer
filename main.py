"""
Enhanced Main Entry Point
- Keeps all existing analysis functionality
- Adds RAG system commands
- Unified CLI for both analysis and Q&A
"""

import os
import sys
import argparse
from dotenv import load_dotenv
from colorama import Fore, Style

from extractor import CodeExtractor
from relationships import RelationshipDetector
from output import OutputFormatter
from errors import ErrorDetector
from rag import CodeRAGSystem

from google.generativeai import configure, GenerativeModel


def setup_gemini(api_key: str):
    """Configure Gemini API."""
    if not api_key:
        print(f"{Fore.RED}ERROR: GOOGLE_API_KEY not found in .env")
        sys.exit(1)
    configure(api_key=api_key)
    print(f"{Fore.GREEN}✓ Gemini API configured")


def find_python_files(directory: str) -> list:
    """Recursively find all Python files in directory."""
    python_files = []
    for root, dirs, files in os.walk(directory):
        dirs[:] = [d for d in dirs if d not in 
                  ['venv', '__pycache__', '.git', 'node_modules', '.pytest_cache']]
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    return sorted(python_files)


def analyze_file(file_path: str, save_json: bool = False):
    """Analyze a single Python file."""
    print(f"{Fore.CYAN}Analyzing: {file_path}\n")

    print(f"{Fore.YELLOW}[1/3] Extracting code structure...")
    extractor = CodeExtractor()
    entities = extractor.extract_from_file(file_path)

    print(f"{Fore.YELLOW}[2/3] Detecting call relationships...")
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        code = f.read()

    detector = RelationshipDetector()
    relationships = detector.detect_relationships(code)

    print(f"{Fore.YELLOW}[2.5/3] Detecting potential issues...")
    error_detector = ErrorDetector()
    issues = error_detector.analyze(code)

    print(f"{Fore.YELLOW}[3/3] Generating analysis...\n")
    OutputFormatter.print_summary(file_path, entities, relationships)
    OutputFormatter.print_entities(entities)
    OutputFormatter.print_relationships(relationships)

    if issues["errors"] or issues["warnings"]:
        print(f"\n{Fore.RED}>>> DETECTED ISSUES")
        for err in issues["errors"]:
            print(f"{Fore.RED}  ❌ {err['type']} (line {err.get('line', 'N/A')}): {err['message']}")
        for warn in issues["warnings"]:
            print(f"{Fore.YELLOW}  ⚠️ {warn['type']} (line {warn.get('line', 'N/A')}): {warn['message']}")
    else:
        print(f"{Fore.GREEN}✓ No structural issues detected")

    print(f"{Fore.YELLOW}Getting AI insights from Gemini...")
    model = GenerativeModel('gemini-2.5-flash')
    prompt = f"""You are a senior ERPNext backend engineer. Analyze this code:

Classes: {len(entities.get('classes', []))}
Functions: {len(entities.get('functions', []))}
Call relationships: {relationships.get('stats', {}).get('total_calls', 0)}

Code sample:
{code[:2000]}...

Provide: 1) Main purpose 2) Key logic 3) Issues 4) Improvements"""
    
    response = model.generate_content(prompt)
    OutputFormatter.print_gemini_analysis(response.text if response else "No analysis")

    if save_json:
        analysis_data = {
            "file": file_path,
            "entities": entities,
            "relationships": relationships,
            "issues": issues
        }
        OutputFormatter.save_json(analysis_data, "analysis_output.json")

    print(f"{Fore.GREEN}\n✓ Analysis complete!\n")


def analyze_folder(folder_path: str, save_json: bool = False):
    """Analyze entire folder."""
    if not os.path.isdir(folder_path):
        print(f"{Fore.RED}ERROR: {folder_path} is not a directory")
        sys.exit(1)

    print(f"{Fore.CYAN}Analyzing folder: {folder_path}\n")

    python_files = find_python_files(folder_path)

    if not python_files:
        print(f"{Fore.RED}No Python files found in {folder_path}")
        sys.exit(1)

    print(f"{Fore.GREEN}Found {len(python_files)} Python files\n")

    all_entities = {'classes': [], 'functions': [], 'imports': []}
    all_relationships = {'calls': [], 'stats': {'total_calls': 0}}
    all_issues = []
    file_details = {}

    extractor = CodeExtractor()
    detector = RelationshipDetector()

    print(f"{Fore.YELLOW}[1/3] Analyzing files...")
    for idx, file_path in enumerate(python_files, 1):
        try:
            relative_path = os.path.relpath(file_path, folder_path)
            print(f"  [{idx}/{len(python_files)}] {relative_path}")

            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                code = f.read()

            entities = extractor.extract_from_file(file_path)
            relationships = detector.detect_relationships(code)
            error_detector = ErrorDetector()
            file_issues = error_detector.analyze(code)

            all_issues.append({"file": relative_path, **file_issues})

            for entity in entities['classes']:
                entity['file'] = relative_path
                all_entities['classes'].append(entity)

            for entity in entities['functions']:
                entity['file'] = relative_path
                all_entities['functions'].append(entity)

            file_details[relative_path] = {
                'classes': len(entities['classes']),
                'functions': len(entities['functions'])
            }

        except Exception as e:
            print(f"{Fore.RED}    Error in {relative_path}: {str(e)}")

    print(f"\n{Fore.YELLOW}[3/3] Generating analysis...\n")
    OutputFormatter.print_folder_summary(folder_path, file_details, all_entities, all_relationships)
    OutputFormatter.print_entities(all_entities)

    print(f"{Fore.GREEN}\n✓ Folder analysis complete!\n")

    if save_json:
        analysis_data = {
            "folder": folder_path,
            "files_analyzed": len(python_files),
            "file_details": file_details,
            "entities": all_entities,
            "issues": all_issues
        }
        OutputFormatter.save_json(analysis_data, "folder_analysis_output.json")


def init_rag(path: str, collection_name: str = "erpnext_code"):
    """Initialize RAG database from file or folder."""
    rag = CodeRAGSystem()
    rag.create_collection(collection_name)

    print(f"{Fore.YELLOW}Building RAG database...\n")

    if os.path.isfile(path):
        print(f"{Fore.CYAN}Adding file: {path}")
        chunks = rag.add_file_to_rag(path)
        print(f"{Fore.GREEN}✓ Added {chunks} chunks\n")
    elif os.path.isdir(path):
        print(f"{Fore.CYAN}Adding folder: {path}\n")
        results = rag.add_folder_to_rag(path)
        print(f"\n{Fore.GREEN}✓ RAG Database Built!")
        print(f"  Files: {results['total_files']}")
        print(f"  Total chunks: {results['total_chunks']}\n")
    else:
        print(f"{Fore.RED}Path not found: {path}")
        sys.exit(1)

    stats = rag.get_db_stats()
    # print(f"{Fore.CYAN}Database: {stats['db_path']}\n")
    print(f"{Fore.CYAN}Collection: {stats['collection']}")
    print(f"{Fore.CYAN}Total chunks: {stats['total_chunks']}\n")


def rag_ask(
    question: str,
    collection_name: str = "erpnext_code",
    file: str = None,
    folder: str = None
):
    """Ask a question to the RAG system."""
    rag = CodeRAGSystem()

    rag.create_collection(collection_name)

    print(f"{Fore.CYAN}Question: {question}\n")
    print(f"{Fore.YELLOW}Searching codebase and generating answer...\n")

    answer = rag.ask(
        question,
        file=file,
        folder=folder
    )

    print(f"{Fore.GREEN}>>> ANSWER")
    print(f"{Fore.LIGHTGREEN_EX}{answer}{Style.RESET_ALL}\n")

    rag.save_query_results(question, answer)
    print(f"{Fore.CYAN}✓ Query saved to rag_queries.json\n")

    
    # print(f"{Fore.GREEN}>>> ANSWER")
    # print(f"{Fore.LIGHTGREEN_EX}{answer}{Style.RESET_ALL}\n")

    # rag.save_query_results(question, answer)
    # print(f"{Fore.CYAN}✓ Query saved to rag_queries.json\n")


def rag_search(keyword: str, collection_name: str = "erpnext_code"):
    """Search for keyword in RAG database."""
    rag = CodeRAGSystem()
    
    try:
        rag.create_collection(collection_name)
    except:
        print(f"{Fore.YELLOW}Creating new collection...")
        rag.create_collection(collection_name)

    print(f"{Fore.CYAN}Searching for: {keyword}\n")

    results = rag.search_code(keyword)

    if not results:
        print(f"{Fore.YELLOW}No results found\n")
        return

    print(f"{Fore.GREEN}Found {len(results)} matches:\n")
    
    for i, result in enumerate(results, 1):
        print(f"{Fore.CYAN}[{i}] {result['file']} (Lines {result['start_line']}-{result['end_line']})")
        print(f"{Fore.YELLOW}Similarity: {result['similarity']:.2%}\n")
        print(f"{Fore.WHITE}{result['code'][:300]}...\n")


def main():
    """Main entry point."""
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")
    setup_gemini(api_key)

    parser = argparse.ArgumentParser(
        description="ERPNext Code Analyzer + RAG System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze single file
  python main.py analyze sales_invoice.py
  
  # Analyze folder
  python main.py analyze ./erpnext --json
  
  # Build RAG database
  python main.py rag-init ./erpnext
  python main.py rag-init sales_invoice.py
  
  # Ask question to RAG
  python main.py rag-ask "What functions validate sales data?"
  
  # Search codebase
  python main.py rag-search "frappe.throw"
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze code')
    analyze_parser.add_argument('path', help='Path to Python file or folder')
    analyze_parser.add_argument('--json', action='store_true', help='Save to JSON')

    # RAG commands
    rag_init_parser = subparsers.add_parser('rag-init', help='Build RAG database')
    rag_init_parser.add_argument('path', help='Path to Python file or folder')
    rag_init_parser.add_argument('--collection', default='erpnext_code', help='Collection name')

    rag_ask_parser = subparsers.add_parser('rag-ask', help='Ask question to RAG')
    rag_ask_parser.add_argument('question', help='Question about the codebase')
    rag_ask_parser.add_argument('--collection', default='erpnext_code', help='Collection name')

    rag_search_parser = subparsers.add_parser('rag-search', help='Search codebase')
    rag_search_parser.add_argument('keyword', help='Keyword to search')
    rag_search_parser.add_argument('--collection', default='erpnext_code', help='Collection name')

    # rag_ask_parser = subparsers.add_parser('rag-ask', help='Ask question to RAG')
    # rag_ask_parser.add_argument('question', help='Question about the codebase')
    rag_ask_parser.add_argument('--file', help='Limit search to a specific file')
    rag_ask_parser.add_argument('--folder', help='Limit search to a folder')
    # rag_ask_parser.add_argument('--collection', default='erpnext_code', help='Collection name')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == 'analyze':
        if os.path.isdir(args.path):
            analyze_folder(args.path, args.json)
        elif os.path.isfile(args.path):
            analyze_file(args.path, args.json)
        else:
            print(f"{Fore.RED}Path not found: {args.path}")
            sys.exit(1)

    elif args.command == 'rag-init':
        init_rag(args.path, args.collection)

    elif args.command == 'rag-ask':
        rag_ask(
            args.question,
            collection_name=args.collection,
            file=args.file,
            folder=args.folder
        )

    elif args.command == 'rag-search':
        rag_search(args.keyword, args.collection)


if __name__ == "__main__":
    main()
