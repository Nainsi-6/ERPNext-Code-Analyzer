"""
Module: Error Detection Rules
- Static analysis only
- No code execution
"""

import ast


class ErrorDetector:
    def __init__(self):
        self.errors = []
        self.warnings = []

    def analyze(self, code: str):
        tree = ast.parse(code)

        self._check_bare_except(tree)
        self._check_broad_exception(tree)
        self._check_large_functions(tree)
        self._check_large_classes(tree)
        self._check_erpnext_validations(tree)

        return {
            "errors": self.errors,
            "warnings": self.warnings
        }

    # ---------------------------
    # Rule 1: bare except
    # ---------------------------
    def _check_bare_except(self, tree):
        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler) and node.type is None:
                self.errors.append({
                    "type": "BareExcept",
                    "message": "Bare except detected (should catch specific exceptions)",
                    "line": node.lineno
                })

    # ---------------------------
    # Rule 2: except Exception without logging
    # ---------------------------
    def _check_broad_exception(self, tree):
        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler):
                if isinstance(node.type, ast.Name) and node.type.id == "Exception":
                    if not any(
                        isinstance(n, ast.Call) and getattr(n.func, "id", "") in ["print", "log", "logger"]
                        for n in ast.walk(node)
                    ):
                        self.warnings.append({
                            "type": "BroadException",
                            "message": "Catching Exception without logging",
                            "line": node.lineno
                        })

    # ---------------------------
    # Rule 3: very large functions
    # ---------------------------
    def _check_large_functions(self, tree, limit=80):
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                length = (node.end_lineno or node.lineno) - node.lineno
                if length > limit:
                    self.warnings.append({
                        "type": "LargeFunction",
                        "message": f"Function '{node.name}' is too long ({length} lines)",
                        "line": node.lineno
                    })

    # ---------------------------
    # Rule 4: very large classes
    # ---------------------------
    def _check_large_classes(self, tree, limit=30):
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]
                if len(methods) > limit:
                    self.warnings.append({
                        "type": "LargeClass",
                        "message": f"Class '{node.name}' has too many methods ({len(methods)})",
                        "line": node.lineno
                    })

    # ---------------------------
    # Rule 5: ERPNext validation smell
    # ---------------------------
    def _check_erpnext_validations(self, tree):
        has_validate = False
        has_throw = False

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "validate":
                has_validate = True
                for n in ast.walk(node):
                    if isinstance(n, ast.Call) and getattr(n.func, "id", "") == "throw":
                        has_throw = True

        if has_validate and not has_throw:
            self.warnings.append({
                "type": "ERPNextValidation",
                "message": "`validate()` found but no frappe.throw() used",
                "line": None
            })
