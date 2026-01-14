"""
Module 3: Format and display analysis results
- Creates beautiful terminal output
- Generates analysis summaries
"""

from colorama import Fore, Back, Style, init
from typing import Dict, List, Any
import json

init(autoreset=True)


class OutputFormatter:
    """Format and display code analysis results."""

    @staticmethod
    def print_header(title: str):
        """Print a formatted header."""
        print(f"\n{Style.BRIGHT}{Fore.CYAN}{'='*60}")
        print(f"{title.center(60)}")
        print(f"{'='*60}{Style.RESET_ALL}\n")

    @staticmethod
    def print_section(title: str):
        """Print a section header."""
        print(f"{Style.BRIGHT}{Fore.YELLOW}>>> {title}{Style.RESET_ALL}")

    @staticmethod
    def print_entities(entities: Dict[str, Any]):
        """Display extracted entities."""
        OutputFormatter.print_section("EXTRACTED ENTITIES")

        if entities.get("classes"):
            print(f"\n{Fore.GREEN}Classes ({len(entities['classes'])}):")
            for cls in entities["classes"]:
                print(f"  {Fore.CYAN}class {cls['name']}{Fore.WHITE} (line {cls['line']})")
                if cls.get("bases"):
                    print(f"    {Fore.MAGENTA}inherits: {', '.join(cls['bases'])}")
                if cls.get("methods"):
                    print(f"    {Fore.BLUE}methods: {len(cls['methods'])} → {', '.join(cls['methods'][:3])}")

        if entities.get("functions"):
            print(f"\n{Fore.GREEN}Functions ({len(entities['functions'])}):")
            for func in entities["functions"][:10]:
                args_str = ", ".join(func["args"])
                print(f"  {Fore.CYAN}def {func['name']}({args_str}){Fore.WHITE} (line {func['line']})")
            if len(entities["functions"]) > 10:
                print(f"  ... and {len(entities['functions']) - 10} more functions")

        if entities.get("imports"):
            print(f"\n{Fore.GREEN}Imports ({len(entities['imports'])}):")
            for imp in entities["imports"][:8]:
                if imp["type"] == "import":
                    print(f"  {Fore.YELLOW}import {imp['module']}")
                else:
                    print(f"  {Fore.YELLOW}from {imp['module']} import {imp['name']}")
            if len(entities["imports"]) > 8:
                print(f"  ... and {len(entities['imports']) - 8} more imports")

    @staticmethod
    def print_relationships(relationships: Dict[str, Any]):
        """Display call relationships."""
        OutputFormatter.print_section("CALL RELATIONSHIPS")

        rels = relationships.get("relationships", [])
        stats = relationships.get("stats", {})

        print(f"\n{Fore.CYAN}Total function calls detected: {stats.get('total_calls', 0)}")
        print(f"{Fore.CYAN}Unique callers: {stats.get('unique_callers', 0)}")
        print(f"{Fore.CYAN}Unique callees: {stats.get('unique_callees', 0)}")

        if stats.get("most_called"):
            print(f"\n{Fore.GREEN}Most Called Functions:")
            for func, count in stats["most_called"]:
                bar = "█" * min(count // 5, 20)
                print(f"  {Fore.YELLOW}{func:30} {Fore.CYAN}{count:3} calls {bar}")

        if stats.get("most_calls_from"):
            print(f"\n{Fore.GREEN}Functions That Call Most Others:")
            for func, count in stats["most_calls_from"]:
                bar = "█" * min(count // 5, 20)
                print(f"  {Fore.YELLOW}{func:30} {Fore.CYAN}{count:3} calls {bar}")

    @staticmethod
    def print_gemini_analysis(analysis: str):
        """Display AI-generated analysis."""
        OutputFormatter.print_section("AI ANALYSIS (Gemini)")
        print(f"\n{Fore.LIGHTGREEN_EX}{analysis}{Style.RESET_ALL}\n")

    @staticmethod
    def save_json(data: Dict, filename: str):
        """Save analysis to JSON file."""
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"{Fore.GREEN}✓ Saved to {filename}")

    @staticmethod
    def print_summary(file_path: str, entities: Dict, relationships: Dict):
        """Print overall summary."""
        OutputFormatter.print_header("CODE ANALYSIS SUMMARY")
        print(f"{Fore.BLUE}File: {file_path}")
        print(f"{Fore.BLUE}Classes: {len(entities.get('classes', []))}")
        print(f"{Fore.BLUE}Functions: {len(entities.get('functions', []))}")
        print(f"{Fore.BLUE}Imports: {len(entities.get('imports', []))}")
        print(f"{Fore.BLUE}Call Relationships: {relationships.get('stats', {}).get('total_calls', 0)}")

    @staticmethod
    def print_folder_summary(folder_path: str, file_details: Dict, entities: Dict, relationships: Dict):
        """Print folder analysis summary."""
        OutputFormatter.print_header("FOLDER ANALYSIS SUMMARY")
        print(f"{Fore.BLUE}Folder: {folder_path}")
        print(f"{Fore.BLUE}Files analyzed: {len(file_details)}")
        print(f"{Fore.BLUE}Total Classes: {len(entities.get('classes', []))}")
        print(f"{Fore.BLUE}Total Functions: {len(entities.get('functions', []))}")
        print(f"{Fore.BLUE}Total Imports: {len(entities.get('imports', []))}")
        print(f"{Fore.BLUE}Cross-file Call Relationships: {relationships.get('stats', {}).get('total_calls', 0)}")
        
        print(f"\n{Fore.CYAN}Top files by function count:")
        sorted_files = sorted(file_details.items(), key=lambda x: x[1]['functions'], reverse=True)
        for filename, stats in sorted_files[:10]:
            print(f"  {Fore.YELLOW}{filename:40} {Fore.GREEN}({stats['functions']} functions, {stats['classes']} classes)")

