import ast
import os
from typing import Dict, List, Any

class MetricsCalculator:
    def __init__(self):
        self.metrics = {}
        
    def calculate_file_metrics(self, file_path: str) -> Dict[str, Any]:
        """Calculate actual metrics for a given file."""
        try:
            # Ensure file path is valid
            if not file_path or not os.path.exists(file_path):
                return {
                    'file_path': file_path,
                    'error': f"File not found: {file_path}"
                }
            
            # Read and parse file
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                
            try:
                tree = ast.parse(content)
            except SyntaxError as se:
                return {
                    'file_path': file_path,
                    'error': f"Syntax error in file: {str(se)}"
                }
                
            # Initialize metrics with actual file content
            metrics = {
                'file_path': file_path,
                'file_length': len(content.splitlines()),
                'class_count': 0,
                'method_count': 0,
                'avg_method_length': 0,
                'cyclomatic': 0,
                'cognitive': 0,
                'halstead_vol': 0,
                'comment_ratio': 0,
                'max_depth': 0,
                'max_complexity': 0,
                'avg_complexity': 0,
                'branch_count': 0,
                'code_smells': []
            }
            
            # Calculate class and method metrics
            method_lengths = []
            complexities = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    metrics['class_count'] += 1
                    # Check class length
                    class_length = node.end_lineno - node.lineno
                    if class_length > 200:
                        metrics['code_smells'].append(
                            f"Class {node.name} is too long ({class_length} lines) - Consider splitting into smaller classes"
                        )
                
                elif isinstance(node, ast.FunctionDef):
                    metrics['method_count'] += 1
                    method_length = node.end_lineno - node.lineno
                    method_lengths.append(method_length)
                    
                    # Calculate complexity
                    complexity = self._calculate_complexity(node)
                    complexities.append(complexity)
                    metrics['max_complexity'] = max(metrics['max_complexity'], complexity)
                    
                    # Calculate nesting depth
                    depth = self._calculate_nesting_depth(node)
                    metrics['max_depth'] = max(metrics['max_depth'], depth)
                    
                    # Add code smells for long methods
                    if method_length > 20:
                        metrics['code_smells'].append(
                            f"Function {node.name} is too long ({method_length} lines) - Consider extracting into smaller functions"
                        )
                    if complexity > 10:
                        metrics['code_smells'].append(
                            f"Function {node.name} has high cyclomatic complexity ({complexity}) - Consider simplifying logic"
                        )
                    if depth > 3:
                        metrics['code_smells'].append(
                            f"Function {node.name} has deep nesting (depth: {depth}) - Consider using early returns or guard clauses"
                        )
                
                elif isinstance(node, (ast.If, ast.While, ast.For)):
                    metrics['branch_count'] += 1
            
            # Calculate averages
            if method_lengths:
                metrics['avg_method_length'] = sum(method_lengths) / len(method_lengths)
            if complexities:
                metrics['avg_complexity'] = sum(complexities) / len(complexities)
                metrics['cyclomatic'] = max(complexities)
            
            # Calculate cognitive complexity
            metrics['cognitive'] = self._calculate_cognitive_complexity(tree)
            
            # Calculate comment ratio
            lines = content.splitlines()
            comment_lines = len([line for line in lines if line.strip().startswith('#')])
            total_lines = len(lines)
            metrics['comment_ratio'] = (comment_lines / total_lines * 100) if total_lines > 0 else 0
            
            # Check for long lines
            for i, line in enumerate(lines, 1):
                if len(line.strip()) > 100:
                    metrics['code_smells'].append(
                        f"Line {i} is too long ({len(line)} characters) - Consider breaking into multiple lines"
                    )
            
            # Calculate Halstead volume
            metrics['halstead_vol'] = self._calculate_halstead_volume(content)
            
            return metrics
            
        except Exception as e:
            import traceback
            error_msg = f"Error calculating metrics for {file_path}: {str(e)}\n{traceback.format_exc()}"
            print(error_msg)
            return {
                'file_path': file_path,
                'error': error_msg
            }
    
    def _calculate_complexity(self, node: ast.AST) -> int:
        """Calculate cyclomatic complexity for a node."""
        complexity = 1  # Base complexity
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For)):
                complexity += 1
                # Add complexity for elif branches
                if isinstance(child, ast.If):
                    complexity += len([n for n in child.orelse if isinstance(n, ast.If)])
            elif isinstance(child, ast.BoolOp):
                if isinstance(child.op, (ast.And, ast.Or)):
                    complexity += len(child.values) - 1
            elif isinstance(child, (ast.Break, ast.Continue)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
        
        return complexity
    
    def _calculate_nesting_depth(self, node: ast.AST) -> int:
        """Calculate maximum nesting depth."""
        def get_depth(node, current_depth=0):
            max_depth = current_depth
            for child in ast.iter_child_nodes(node):
                if isinstance(child, (ast.If, ast.While, ast.For, ast.Try)):
                    child_depth = get_depth(child, current_depth + 1)
                    max_depth = max(max_depth, child_depth)
                else:
                    child_depth = get_depth(child, current_depth)
                    max_depth = max(max_depth, child_depth)
            return max_depth
        
        return get_depth(node)
    
    def _calculate_cognitive_complexity(self, node: ast.AST) -> int:
        """Calculate cognitive complexity."""
        complexity = 0
        nesting_level = 0
        
        def process_node(node, level):
            nonlocal complexity
            
            if isinstance(node, (ast.If, ast.While, ast.For)):
                complexity += level + 1
                for child in ast.iter_child_nodes(node):
                    process_node(child, level + 1)
            elif isinstance(node, ast.BoolOp):
                complexity += level + len(node.values) - 1
            elif isinstance(node, ast.Try):
                complexity += level + len(node.handlers)
            else:
                for child in ast.iter_child_nodes(node):
                    process_node(child, level)
        
        process_node(node, nesting_level)
        return complexity
    
    def _calculate_halstead_volume(self, content: str) -> float:
        """Calculate Halstead volume metric."""
        operators = set()
        operands = set()
        
        # Simple parsing for demonstration
        words = content.split()
        for word in words:
            if word in ['if', 'else', 'while', 'for', 'in', 'return', '+', '-', '*', '/', '=', '==', '!=']:
                operators.add(word)
            else:
                operands.add(word)
        
        n1 = len(operators)  # unique operators
        n2 = len(operands)   # unique operands
        N = len(words)       # total length
        
        if n1 + n2 == 0:
            return 0
            
        volume = N * (n1 + n2).bit_length()  # simplified Halstead volume
        return volume 