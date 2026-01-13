"""
Module 1: Extract code structure using Python AST
- Finds all classes, functions, imports
- Returns entities with metadata
"""

import ast
import os
from pathlib import Path
from typing import Dict, List, Any
from errors import ErrorDetector


class CodeExtractor:
    """Extract code entities (classes, functions, imports) from Python files."""

    def __init__(self):
        self.entities = {
            "classes": [],
            "functions": [],
            "imports": [],
            "decorators": []
        }
        self.current_file = ""

    def extract_from_file(self, file_path: str) -> Dict[str, Any]:
        """Parse a single Python file and extract all entities."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                code = f.read()
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            return self.entities

        self.current_file = file_path
        self.entities = {
            "classes": [],
            "functions": [],
            "imports": [],
            "decorators": [],
            "file_path": file_path,
            "total_lines": len(code.split('\n'))
        }

        try:
            tree = ast.parse(code)
            self._walk_tree(tree)
        except SyntaxError as e:
            print(f"Syntax error in {file_path}: {e}")

        return self.entities

    def _walk_tree(self, tree: ast.AST):
        """Walk AST and extract entities."""
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                self._extract_class(node)
            elif isinstance(node, ast.FunctionDef):
                self._extract_function(node)
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                self._extract_import(node)

    def _extract_class(self, node: ast.ClassDef):
        """Extract class information."""
        methods = [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
        bases = [ast.unparse(base) for base in node.bases]
        
        self.entities["classes"].append({
            "name": node.name,
            "line": node.lineno,
            "methods": methods,
            "method_count": len(methods),
            "bases": bases if bases else ["object"],
            "docstring": ast.get_docstring(node) or ""
        })

    def _extract_function(self, node: ast.FunctionDef):
        """Extract function information."""
        decorators = [ast.unparse(d) for d in node.decorator_list]
        args = [arg.arg for arg in node.args.args]
        
        self.entities["functions"].append({
            "name": node.name,
            "line": node.lineno,
            "args": args,
            "arg_count": len(args),
            "decorators": decorators,
            "docstring": ast.get_docstring(node) or ""
        })

    def _extract_import(self, node: ast.AST):
        """Extract import information."""
        if isinstance(node, ast.Import):
            for alias in node.names:
                self.entities["imports"].append({
                    "type": "import",
                    "module": alias.name,
                    "alias": alias.asname,
                    "line": node.lineno
                })
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                self.entities["imports"].append({
                    "type": "from",
                    "module": node.module or "",
                    "name": alias.name,
                    "alias": alias.asname,
                    "line": node.lineno
                })

    def extract_from_directory(self, dir_path: str) -> Dict[str, Any]:
        """Extract from all Python files in directory."""
        all_entities = {
            "classes": [],
            "functions": [],
            "imports": [],
            "files": []
        }

        for py_file in Path(dir_path).rglob("*.py"):
            if "__pycache__" not in str(py_file):
                entities = self.extract_from_file(str(py_file))
                all_entities["files"].append(entities)
                all_entities["classes"].extend(entities.get("classes", []))
                all_entities["functions"].extend(entities.get("functions", []))
                all_entities["imports"].extend(entities.get("imports", []))

        return all_entities
