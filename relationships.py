"""
Module 2: Detect call relationships between functions
- Finds who calls whom
- Detects dependencies
"""

import ast
from typing import Dict, List, Set, Tuple


class RelationshipDetector:
    """Detect function calls and relationships in code."""

    def __init__(self):
        self.relationships = []
        self.function_calls = {}
        self.current_function = None

    def detect_relationships(self, code: str) -> Dict[str, List[Dict]]:
        """Analyze code and find all call relationships."""
        self.relationships = []
        self.function_calls = {}

        try:
            tree = ast.parse(code)
            self._analyze_calls(tree)
        except SyntaxError:
            return {"relationships": [], "stats": {}}

        return {
            "relationships": self.relationships,
            "stats": self._calculate_stats()
        }

    def _analyze_calls(self, tree: ast.AST):
        """Walk tree and find all function calls."""
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self.current_function = node.name
                self.function_calls[node.name] = []
                self._find_calls_in_node(node)

    def _find_calls_in_node(self, node: ast.AST):
        """Find all calls within a node."""
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Name):
                    called = child.func.id
                    self.relationships.append({
                        "caller": self.current_function,
                        "callee": called,
                        "line": child.lineno,
                        "type": "function_call"
                    })
                    if self.current_function:
                        self.function_calls[self.current_function].append(called)
                elif isinstance(child.func, ast.Attribute):
                    method = child.func.attr
                    self.relationships.append({
                        "caller": self.current_function,
                        "callee": method,
                        "line": child.lineno,
                        "type": "method_call"
                    })

    def _calculate_stats(self) -> Dict:
        """Calculate relationship statistics."""
        if not self.relationships:
            return {"total_calls": 0, "unique_callers": 0, "unique_callees": 0}

        unique_callers = set(r["caller"] for r in self.relationships)
        unique_callees = set(r["callee"] for r in self.relationships)

        return {
            "total_calls": len(self.relationships),
            "unique_callers": len(unique_callers),
            "unique_callees": len(unique_callees),
            "most_called": self._get_most_called(5),
            "most_calls_from": self._get_most_calls_from(5)
        }

    def _get_most_called(self, limit: int) -> List[Tuple[str, int]]:
        """Find functions called most frequently."""
        call_counts = {}
        for r in self.relationships:
            call_counts[r["callee"]] = call_counts.get(r["callee"], 0) + 1
        return sorted(call_counts.items(), key=lambda x: x[1], reverse=True)[:limit]

    def _get_most_calls_from(self, limit: int) -> List[Tuple[str, int]]:
        """Find functions that call most others."""
        call_counts = {}
        for r in self.relationships:
            call_counts[r["caller"]] = call_counts.get(r["caller"], 0) + 1
        return sorted(call_counts.items(), key=lambda x: x[1], reverse=True)[:limit]
