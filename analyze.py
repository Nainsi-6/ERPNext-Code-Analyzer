"""
Module 4: Main Entry Point
- Orchestrates the analysis
- Integrates with Gemini API
- Handles CLI arguments
"""

import os
import sys
import argparse
from dotenv import load_dotenv
from colorama import Fore, Style
from pathlib import Path

from extractor import CodeExtractor
from relationships import RelationshipDetector
from output import OutputFormatter
from errors import ErrorDetector

from google.generativeai import configure, GenerativeModel


def setup_gemini(api_key: str):
    """Configure Gemini API."""
    if not api_key:
        print(f"{Fore.RED}ERROR: GOOGLE_API_KEY not found in .env")
        sys.exit(1)
    configure(api_key=api_key)
    print(f"{Fore.GREEN}✓ Gemini API configured")


def find_python_files(directory: str) -> list:
    """Recursively find all Python files in directory"""
    python_files = []
    for root, dirs, files in os.walk(directory):
        # Skip virtual environments and cache
        dirs[:] = [d for d in dirs if d not in ['venv', '__pycache__', '.git', 'node_modules', '.pytest_cache']]
        
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    
    return sorted(python_files)


def analyze_file(file_path: str, save_json: bool = False):
    """Analyze a single Python file."""
    print(f"{Fore.CYAN}Analyzing: {file_path}\n")

    # Step 1: Extract entities
    print(f"{Fore.YELLOW}[1/3] Extracting code structure...")
    extractor = CodeExtractor()
    entities = extractor.extract_from_file(file_path)

    # Step 2: Detect relationships
    print(f"{Fore.YELLOW}[2/3] Detecting call relationships...")
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        code = f.read()
    
    detector = RelationshipDetector()
    relationships = detector.detect_relationships(code)

# Step 2.5: Detect potential issues
    print(f"{Fore.YELLOW}[2.5/3] Detecting potential issues...")
    error_detector = ErrorDetector()
    issues = error_detector.analyze(code)

    # Step 3: Display extraction results
    print(f"{Fore.YELLOW}[3/3] Generating analysis...\n")
    OutputFormatter.print_summary(file_path, entities, relationships)
    OutputFormatter.print_entities(entities)
    OutputFormatter.print_relationships(relationships)

    # Step 4: Get AI analysis from Gemini

        # Display detected issues
    if issues["errors"] or issues["warnings"]:
        print(f"\n{Fore.RED}>>> DETECTED ISSUES")

        for err in issues["errors"]:
            print(
                f"{Fore.RED}  ❌ {err['type']} "
                f"(line {err.get('line', 'N/A')}): {err['message']}"
            )

        for warn in issues["warnings"]:
            print(
                f"{Fore.YELLOW}  ⚠️ {warn['type']} "
                f"(line {warn.get('line', 'N/A')}): {warn['message']}"
            )
    else:
        print(f"{Fore.GREEN}✓ No structural issues detected")


    print(f"{Fore.YELLOW}Getting AI insights from Gemini...")
    
    ai_analysis = get_gemini_analysis(code, entities, relationships)
    OutputFormatter.print_gemini_analysis(ai_analysis)

    # Step 5: Save to JSON if requested
    if save_json:
        analysis_data = {
            "file": file_path,
            "entities": entities,
            "relationships": relationships,
            "ai_analysis": ai_analysis,
            "issues": issues,

        }
        OutputFormatter.save_json(analysis_data, "analysis_output.json")

   

    print(f"{Fore.GREEN}\n✓ Analysis complete!\n")


def analyze_folder(folder_path: str, save_json: bool = False):
    """Analyze entire folder - find all .py files and aggregate results"""
    all_issues = []
    if not os.path.isdir(folder_path):
        print(f"{Fore.RED}ERROR: {folder_path} is not a directory")
        sys.exit(1)
    
    print(f"{Fore.CYAN}Analyzing folder: {folder_path}\n")
    
    # Find all Python files
    python_files = find_python_files(folder_path)
    
    if not python_files:
        print(f"{Fore.RED}No Python files found in {folder_path}")
        sys.exit(1)
    
    print(f"{Fore.GREEN}Found {len(python_files)} Python files\n")
    
    # Aggregate results
    all_entities = {
        'classes': [],
        'functions': [],
        'imports': []
    }
    all_relationships = {
        'calls': [],
        'stats': {
            'total_calls': 0,
            'unique_callers': 0,
            'unique_callees': 0,
            'most_called': []
        }
    }
    file_details = {}
    
    # Analyze each file
    extractor = CodeExtractor()
    detector = RelationshipDetector()
    
    print(f"{Fore.YELLOW}[1/3] Extracting code structure from all files...")
    print(f"{Fore.YELLOW}[1/3] Analyzing files...")
    for idx, file_path in enumerate(python_files, 1):
        try:
            relative_path = os.path.relpath(file_path, folder_path)
            print(f"  [{idx}/{len(python_files)}] {relative_path}")

        # 🔹 Read file
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                code = f.read()

        # 🔹 Extract entities
            entities = extractor.extract_from_file(file_path)

        # 🔹 Detect relationships
            relationships = detector.detect_relationships(code)

        # 🔹 Detect issues
            error_detector = ErrorDetector()
            file_issues = error_detector.analyze(code)

            all_issues.append({
                "file": relative_path,
                "errors": file_issues["errors"],
                "warnings": file_issues["warnings"],
            })

        # 🔹 Aggregate entities
            for entity in entities['classes']:
                entity['file'] = relative_path
                all_entities['classes'].append(entity)

            for entity in entities['functions']:
                entity['file'] = relative_path
                all_entities['functions'].append(entity)

            for entity in entities['imports']:
                entity['file'] = relative_path
                all_entities['imports'].append(entity)

        # 🔹 Aggregate relationships
            for call in relationships.get('calls', []):
                call['file'] = relative_path
                all_relationships['calls'].append(call)

            all_relationships['stats']['total_calls'] += relationships.get(
                'stats', {}
            ).get('total_calls', 0)

        # 🔹 File summary
            file_details[relative_path] = {
                'classes': len(entities['classes']),
                'functions': len(entities['functions']),
                'imports': len(entities['imports'])
            }

        except Exception as e:
            print(f"{Fore.RED}    Error in {relative_path}: {str(e)}")

    # Calculate unique callers/callees
    callers = set(call['caller'] for call in all_relationships['calls'])
    callees = set(call['callee'] for call in all_relationships['calls'])
    all_relationships['stats']['unique_callers'] = len(callers)
    all_relationships['stats']['unique_callees'] = len(callees)
    
    # Get most called functions
    call_counts = {}
    for call in all_relationships['calls']:
        callee = call['callee']
        call_counts[callee] = call_counts.get(callee, 0) + 1
    
    all_relationships['stats']['most_called'] = sorted(
        call_counts.items(), key=lambda x: x[1], reverse=True
    )[:5]
    
    print(f"\n{Fore.YELLOW}[3/3] Generating analysis...\n")
    
    # Display results
    OutputFormatter.print_folder_summary(folder_path, file_details, all_entities, all_relationships)
    OutputFormatter.print_entities(all_entities)
    OutputFormatter.print_relationships(all_relationships)
    
    # Get AI analysis
     # Display detected issues
    print(f"\n{Fore.YELLOW}>>> DETECTED ISSUES")

    has_any_issue = False

    for item in all_issues:
        file = item["file"]
        errors = item["errors"]
        warnings = item["warnings"]

        if not errors and not warnings:
            continue

        has_any_issue = True
        print(f"\n{Fore.CYAN}File: {file}")

        for err in errors:
            print(
                f"{Fore.RED}  ❌ {err['type']} "
                f"(line {err.get('line', 'N/A')}): {err['message']}"
            )

        for warn in warnings:
            print(
                f"{Fore.YELLOW}  ⚠️ {warn['type']} "
                f"(line {warn.get('line', 'N/A')}): {warn['message']}"
            )

    if not has_any_issue:
        print(f"{Fore.GREEN}✓ No structural issues detected")

    print(f"{Fore.YELLOW}Getting AI insights from Gemini...")
    code_sample = "\n".join([
        f"# File: {fp}\n" + open(fp, 'r', encoding='utf-8', errors='ignore').read()[:500]
        for fp in python_files[:3]
    ])
    
    ai_analysis = get_gemini_analysis(code_sample, all_entities, all_relationships)
    OutputFormatter.print_gemini_analysis(ai_analysis)
    
    # Save to JSON if requested
    if save_json:
        analysis_data = {
            "folder": folder_path,
            "files_analyzed": len(python_files),
            "file_details": file_details,
            "entities": all_entities,
            "relationships": all_relationships,
            "ai_analysis": ai_analysis,
            "issues": all_issues
        }
        OutputFormatter.save_json(analysis_data, "folder_analysis_output.json")
    
    print(f"{Fore.GREEN}\n✓ Folder analysis complete!\n")


def get_gemini_analysis(code: str, entities: dict, relationships: dict) -> str:
    """Get AI-powered analysis from Gemini."""
    try:
        model = GenerativeModel('gemini-2.5-flash')
        
        prompt = f"""
You are a senior ERPNext backend engineer analyzing Python code.

Analyze this code and provide insights:

=== CODE STRUCTURE ===
Classes: {len(entities.get('classes', []))}
Functions: {len(entities.get('functions', []))}
Imports: {len(entities.get('imports', []))}
Call Relationships: {relationships.get('stats', {}).get('total_calls', 0)}

=== KEY CLASSES ===
{format_entities(entities.get('classes', []))}

=== KEY FUNCTIONS ===
{format_entities(entities.get('functions', []))}

=== SOURCE CODE ===
{code[:3000]}...

Please provide:
1. Main purpose of this code
2. Key business logic and responsibilities
3. Important hooks or validations
4. Dependencies and integrations
5. Potential issues or improvements

Be concise and practical.
"""
        response = model.generate_content(prompt)
        return response.text if response else "Analysis could not be generated."
    except Exception as e:
        return f"Error getting Gemini analysis: {str(e)}"


def format_entities(entities: list, limit: int = 5) -> str:
    """Format entities for prompt."""
    if not entities:
        return "None"
    
    text = ""
    for entity in entities[:limit]:
        if "methods" in entity:  # Class
            text += f"- {entity['name']} (line {entity['line']})\n"
        else:  # Function
            text += f"- {entity['name']}({', '.join(entity.get('args', []))}) (line {entity['line']})\n"
    
    if len(entities) > limit:
        text += f"- ... and {len(entities) - limit} more\n"
    
    return text


def main():
    """Main entry point."""
    # Load environment
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")
    setup_gemini(api_key)

    # Parse arguments
    parser = argparse.ArgumentParser(
        description="AI-Powered Python Code Analyzer (with Gemini)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python analyze.py sales_invoice.py
  python analyze.py sales_invoice.py --json
  python analyze.py ./erpnext
  python analyze.py ./accounts --json
        """
    )
    
    parser.add_argument("path", help="Path to Python file or folder")
    parser.add_argument("--json", action="store_true", help="Save analysis to JSON")

    args = parser.parse_args()

    # Detect if file or folder
    if os.path.isdir(args.path):
        analyze_folder(args.path, args.json)
    elif os.path.isfile(args.path):
        analyze_file(args.path, args.json)
    else:
        print(f"{Fore.RED}Path not found: {args.path}")
        sys.exit(1)


if __name__ == "__main__":
    main()
