import ast
import re
from typing import Dict, Any, List, Optional
from pathlib import Path
import magic
import pygments
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter
import radon.complexity as radon_complexity
import radon.metrics as radon_metrics
from radon.visitors import ComplexityVisitor
import javalang
import cpp_parser
import esprima
import csharp_parser
import os
from radon.complexity import cc_visit
from radon.metrics import h_visit
from radon.raw import analyze
import math
import tokenize
from io import StringIO
from datetime import datetime


class CodeAnalyzer:
    def __init__(self, config):
        """Initialize CodeAnalyzer with configuration."""
        self.config = config
        self.mime = magic.Magic(mime=True)
        self.supported_languages = {
            'python': self._analyze_python,
            'java': self._analyze_generic,
            'cpp': self._analyze_generic,
            'javascript': self._analyze_generic,
            'csharp': self._analyze_generic
        }

    def analyze_project(self, project_path: str) -> Dict[str, Any]:
        """Analyze an entire project directory and return aggregated metrics."""
        try:
            project_metrics = {
                'complexity': {'score': 0, 'issues': []},
                'maintainability': {'score': 0, 'issues': []},
                'code_smells': [],
                'performance': {'score': 0, 'issues': []},
                'raw_metrics': {
                    'loc': 0, 'lloc': 0, 'sloc': 0,
                    'comments': 0, 'multi': 0, 'blank': 0
                },
                'files_analyzed': 0,
                'total_files': 0
            }

            # Walk through the project directory
            for root, _, files in os.walk(project_path):
                for file in files:
                    if file.endswith(
                            '.py'):  # Only analyze Python files for now
                        file_path = os.path.join(root, file)
                        try:
                            file_metrics = self.analyze_file(file_path)

                            # Aggregate metrics
                            project_metrics['complexity']['score'] += file_metrics['complexity'].get(
                                'score', 0)
                            project_metrics['complexity']['issues'].extend(
                                file_metrics['complexity'].get('issues', []))

                            project_metrics['maintainability']['score'] += file_metrics['maintainability'].get(
                                'score', 0)
                            project_metrics['maintainability']['issues'].extend(
                                file_metrics['maintainability'].get('issues', []))

                            project_metrics['code_smells'].extend(
                                file_metrics.get('code_smells', []))

                            if 'performance' in file_metrics:
                                project_metrics['performance']['score'] += file_metrics['performance'].get(
                                    'score', 0)
                                project_metrics['performance']['issues'].extend(
                                    file_metrics['performance'].get('issues', []))

                            # Aggregate raw metrics
                            for key in project_metrics['raw_metrics'].keys():
                                project_metrics['raw_metrics'][key] += file_metrics.get(
                                    'raw_metrics', {}).get(key, 0)

                            project_metrics['files_analyzed'] += 1
                        except Exception as e:
                            print(
                                f"Error analyzing file {file_path}: {
                                    str(e)}")
                            continue

                    project_metrics['total_files'] += 1

            # Calculate average scores
            if project_metrics['files_analyzed'] > 0:
                project_metrics['complexity']['score'] /= project_metrics['files_analyzed']
                project_metrics['maintainability']['score'] /= project_metrics['files_analyzed']
                project_metrics['performance']['score'] /= project_metrics['files_analyzed']

            return project_metrics

        except Exception as e:
            print(f"Error analyzing project: {str(e)}")
            return {
                'complexity': {
                    'score': 50,
                    'issues': [
                        f"Error analyzing project complexity: {
                            str(e)}"]},
                'maintainability': {
                    'score': 50,
                    'issues': [
                        f"Error analyzing project maintainability: {
                            str(e)}"]},
                'code_smells': [
                    f"Error detecting project code smells: {
                        str(e)}"],
                'performance': {
                    'score': 50,
                    'issues': [
                        f"Error analyzing project performance: {
                            str(e)}"]},
                'raw_metrics': {
                    'loc': 0,
                    'lloc': 0,
                    'sloc': 0,
                    'comments': 0,
                    'multi': 0,
                    'blank': 0},
                'files_analyzed': 0,
                'total_files': 0}

    def analyze_file(self, file_path: str, content: Optional[str] = None) -> Dict:
        """Analyze a single file and return metrics."""
        try:
            metrics = {
                'file_path': file_path,
                'raw_metrics': {
                    'loc': 0,
                    'sloc': 0,
                    'comments': 0,
                    'multi': 0,
                    'blank': 0,
                    'classes': 0,
                    'methods': 0,
                    'functions': 0,
                    'imports': 0
                },
                'complexity': {'score': 0, 'issues': []},
                'maintainability': {'score': 0, 'issues': []},
                'code_smells': [],
                'refactoring_opportunities': [],
                'cognitive_complexity': 0,
                'code_coverage': 0,
                'function_count': 0,
                'class_count': 0,
                'design_issues': [],
                'performance_issues': [],
                'security_issues': [],
                'function_metrics': {},
                'dependencies': {'direct': 0, 'indirect': 0, 'depth': 0, 'circular_deps': []},
                'technical_debt': {'score': 0, 'hours_to_fix': 0, 'issues': []},
                'language_specific': {}
            }

            # Read file content if not provided
            if content is None:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

            # Get file extension
            ext = os.path.splitext(file_path)[1].lower()

            # Process based on file type
            if ext == '.py':
                metrics.update(self._analyze_python(content))
            elif ext in ['.js', '.jsx', '.ts', '.tsx']:
                metrics.update(self._analyze_javascript(content))
            elif ext == '.java':
                metrics.update(self._analyze_java(content))
            elif ext in ['.cpp', '.hpp', '.cc', '.h']:
                metrics.update(self._analyze_cpp(content))
            else:
                metrics.update(self._analyze_generic(content))

            # Store the content for display
            metrics['content'] = content
            
            return metrics

        except Exception as e:
            print(f"Error analyzing file {file_path}: {str(e)}")
            return {
                'error': str(e),
                'file_path': file_path
            }

    def _calculate_function_complexity(self, node: ast.AST) -> int:
        """Calculate cyclomatic complexity of a function."""
        complexity = 1  # Base complexity
        for child in ast.walk(node):
            if isinstance(
                child,
                (ast.If,
                 ast.While,
                 ast.For,
                 ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        return complexity

    def _calculate_maintainability_score(self, metrics: Dict) -> float:
        """Calculate maintainability score based on various metrics."""
        score = 100

        # Penalize for large files
        if metrics['loc'] > 1000:
            score -= 20
        elif metrics['loc'] > 500:
            score -= 10

        # Penalize for low comment ratio
        comment_ratio = (metrics['comments'] +
                         metrics['multi']) / max(metrics['loc'], 1)
        if comment_ratio < 0.1:
            score -= 20
        elif comment_ratio < 0.2:
            score -= 10

        # Penalize for too many classes or methods
        if metrics['classes'] > 10:
            score -= 10
        if metrics['methods'] + metrics['functions'] > 20:
            score -= 10
        elif metrics['methods'] + metrics['functions'] > 10:
            score -= 5

        # Penalize for large average method length
        if metrics['average_method_length'] > 50:
            score -= 20
        elif metrics['average_method_length'] > 30:
            score -= 10

        return max(0, min(100, score))

    def _calculate_basic_metrics(self, content: str) -> Dict[str, Any]:
        """Calculate basic metrics when detailed parsing fails."""
        lines = content.splitlines()
        non_empty_lines = [l for l in lines if l.strip()]

        # Count basic metrics
        total_lines = len(lines)
        source_lines = len(non_empty_lines)
        blank_lines = total_lines - source_lines

        # Count comments
        single_comments = 0
        multi_comments = 0
        javadoc_comments = 0
        in_multi_comment = False
        in_javadoc = False

        # Track packages and imports
        declared_packages = []
        imported_packages = set()
        import_count = 0

        # Track methods and functions
        class_count = 0
        method_count = 0
        function_count = 0  # For anonymous methods and lambda expressions
        method_lines = []  # Track method lengths
        current_method_lines = 0
        in_method = False
        brace_count = 0

        i = 0
        while i < len(lines):
            line = lines[i].strip()

            # Skip empty lines
            if not line:
                i += 1
                continue

            # Handle Javadoc comments
            if line.startswith('/**'):
                in_javadoc = True
                javadoc_comments += 1
                while i < len(lines) and '*/' not in lines[i]:
                    javadoc_comments += 1
                    i += 1
                if i < len(lines):  # Count the closing line
                    javadoc_comments += 1
                in_javadoc = False

            # Handle regular multi-line comments
            elif line.startswith('/*'):
                in_multi_comment = True
                multi_comments += 1
                while i < len(lines) and '*/' not in lines[i]:
                    multi_comments += 1
                    i += 1
                if i < len(lines):  # Count the closing line
                    multi_comments += 1
                in_multi_comment = False

            # Handle single-line comments
            elif line.startswith('//'):
                single_comments += 1

            # Track packages and imports
            elif line.startswith('package '):
                package_name = line[8:].rstrip(';').strip()
                if package_name:
                    declared_packages.append(package_name)

            elif line.startswith('import '):
                import_count += 1
                # Extract base package name from import
                import_path = line[7:].rstrip(';').strip()
                if import_path:
                    package_parts = import_path.split('.')
                    base_package = package_parts[0]
                    if len(package_parts) > 1:
                        imported_packages.add(base_package)

            # Count classes
            elif 'class ' in line and '{' in line:
                class_count += 1

            # Count methods and track their lengths
            elif any(modifier + ' ' in line for modifier in ['public', 'private', 'protected']) and '(' in line and ')' in line:
                if '{' in line:  # Method declaration with opening brace
                    in_method = True
                    brace_count = 1
                    current_method_lines = 1
                    if not any(
                        c in line for c in [
                            'class',
                            'interface',
                            'enum']):  # Ensure it's not a class/interface declaration
                        method_count += 1
                # Method declaration without opening brace
                elif not any(c in line for c in ['class', 'interface', 'enum']):
                    method_count += 1

            # Track method bodies
            elif in_method:
                current_method_lines += 1
                brace_count += line.count('{') - line.count('}')
                if brace_count == 0:
                    in_method = False
                    method_lines.append(current_method_lines)
                    current_method_lines = 0

            # Count anonymous functions and lambda expressions
            elif ('->' in line or 'new ' in line) and '{' in line:
                function_count += 1

            i += 1

        # Calculate average method length
        avg_method_length = sum(method_lines) / \
            len(method_lines) if method_lines else 0

        return {
            'file_path': 'unknown',
            'raw_metrics': {
                'loc': total_lines,
                'sloc': source_lines,
                'comments': single_comments,
                'javadoc': javadoc_comments,
                'multi': multi_comments,
                'blank': blank_lines,
                'classes': class_count,
                'methods': method_count,
                'functions': function_count,
                'imports': import_count,
                'packages': len(declared_packages),
                'average_method_length': avg_method_length,
                'comment_ratio': (single_comments + multi_comments + javadoc_comments) / max(total_lines, 1)
            },
            'declared_packages': declared_packages,
            'imported_packages': sorted(list(imported_packages)),
            'complexity': {
                'score': 75,  # Default moderate score when detailed analysis fails
                'issues': ["Detailed complexity analysis not available"]
            },
            'maintainability': {
                'score': 75,  # Default moderate score when detailed analysis fails
                'issues': ["Detailed maintainability analysis not available"]
            },
            'code_smells': [],
            'refactoring_opportunities': []
        }

    def _analyze_python(self, content: str) -> Dict[str, Any]:
        """Analyze Python code."""
        try:
            tree = ast.parse(content)

            # Count functions and classes
            functions = [
                node for node in ast.walk(tree) if isinstance(
                    node, ast.FunctionDef)]
            classes = [
                node for node in ast.walk(tree) if isinstance(
                    node, ast.ClassDef)]

            # Analyze imports
            imports = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imports.extend(alias.name for alias in node.names)
                elif isinstance(node, ast.ImportFrom):
                    imports.append(f"{node.module}")

            # Calculate cyclomatic complexity
            complexity_visitor = ComplexityVisitor.from_code(content)
            complexity = sum(
                item.complexity for item in complexity_visitor.functions)

            # Calculate Halstead metrics
            halstead = h_visit(content)

            # Calculate raw metrics
            raw_metrics = analyze(content)

            # Calculate maintainability index
            mi_score = radon_metrics.mi_visit(content, multi=True)
            maintainability_score = min(100, max(0, mi_score))

            # Detect code smells
            code_smells = []

            # Check function length
            for func in functions:
                if len(func.body) > 15:  # More than 15 lines
                    code_smells.append(
                        f"Function '{func.name}' is too long ({len(func.body)} lines)")

            # Check class complexity
            for cls in classes:
                methods = [
                    node for node in ast.walk(cls) if isinstance(
                        node, ast.FunctionDef)]
                if len(methods) > 10:
                    code_smells.append(
                        f"Class '{
                            cls.name}' has too many methods ({
                            len(methods)})")

            # Check nesting depth
            for func in functions:
                nesting = self._calculate_nesting_level(func)
                if nesting > 3:
                    code_smells.append(
                        f"Function '{
                            func.name}' has deep nesting (level {nesting})")

            return {
                "language": "python",
                "function_count": len(functions),
                "class_count": len(classes),
                "imports": imports,
                "complexity": {"score": complexity, "issues": []},
                "maintainability": {
                    "score": maintainability_score,
                    "issues": []},
                "code_smells": code_smells,
                "cognitive_complexity": complexity,
                "code_coverage": 0,
                "raw_metrics": {
                    "loc": raw_metrics.loc,
                    "lloc": raw_metrics.lloc,
                    "sloc": raw_metrics.sloc,
                    "comments": raw_metrics.comments,
                    "multi": raw_metrics.multi,
                    "blank": raw_metrics.blank,
                    "classes": len(classes),
                    "functions": len(functions),
                    "average_method_length": self._get_basic_metrics(content)['average_line_length'],
                    "max_complexity": complexity,
                    "comment_ratio": (
                        raw_metrics.comments +
                        raw_metrics.multi) /
                    raw_metrics.loc if raw_metrics.loc > 0 else 0},
                "halstead_metrics": {
                    "h1": halstead.h1,
                    "h2": halstead.h2,
                    "N1": halstead.N1,
                    "N2": halstead.N2,
                    "vocabulary": halstead.vocabulary,
                    "length": halstead.length,
                    "volume": halstead.volume,
                    "difficulty": halstead.difficulty,
                    "effort": halstead.effort,
                    "time": halstead.time,
                    "bugs": halstead.bugs}}

        except Exception as e:
            return {
                "language": "python",
                "error": str(e),
                "complexity": {
                    "score": 50,
                    "issues": ["Error analyzing code"]},
                "maintainability": {
                    "score": 50,
                    "issues": ["Error analyzing code"]},
                "code_smells": ["Error analyzing code"],
                "performance": {
                    "score": 50,
                    "issues": ["Error analyzing code"]}}

    def _analyze_javascript(self, content: str) -> Dict[str, Any]:
        """Analyze JavaScript/TypeScript code."""
        try:
            # Parse JavaScript code
            tree = esprima.parseScript(content)

            # Count functions and classes
            functions = len([node for node in self._walk_js_ast(
                tree) if node.type == 'FunctionDeclaration'])
            classes = len([node for node in self._walk_js_ast(
                tree) if node.type == 'ClassDeclaration'])

            # Count imports
            imports = len([node for node in self._walk_js_ast(
                tree) if node.type == 'ImportDeclaration'])

            # Basic complexity calculation
            complexity = self._calculate_js_complexity(tree)

            return {
                "language": "javascript",
                "function_count": functions,
                "class_count": classes,
                "imports": imports,
                "complexity": complexity,
                'maintainability': 100 - min(complexity * 10, 100),
                'code_smells': self._detect_javascript_smells(content),
                'performance': self._analyze_javascript_performance(content)
            }

        except Exception as e:
            return {
                "language": "javascript",
                "error": str(e)
            }

    def _analyze_java(self, content: str) -> Dict:
        """Analyze Java code and return metrics."""
        try:
            tree = javalang.parse.parse(content)
            
            # Count classes, methods, and imports
            classes = list(tree.filter(javalang.tree.ClassDeclaration))
            methods = list(tree.filter(javalang.tree.MethodDeclaration))
            imports = list(tree.filter(javalang.tree.Import))
            
            # Calculate complexity
            complexity_score = self._calculate_java_complexity(tree)
            
            # Calculate maintainability score (inverse of complexity)
            maintainability_score = max(0, min(100, 100 - (complexity_score * 2)))
            
            # Count lines with improved accuracy
            lines = content.splitlines()
            loc = len(lines)  # Total lines
            
            # Count actual source lines (excluding comments and blank lines)
            sloc = 0
            in_multi_comment = False
            single_comments = 0
            multi_comments = 0
            blank_lines = 0
            
            for line in lines:
                stripped = line.strip()
                if not stripped:  # Blank line
                    blank_lines += 1
                    continue
                    
                if stripped.startswith('/*') or stripped.startswith('/**'):
                    in_multi_comment = True
                    multi_comments += 1
                    continue
                    
                if in_multi_comment:
                    multi_comments += 1
                    if '*/' in stripped:
                        in_multi_comment = False
                    continue
                    
                if stripped.startswith('//'):
                    single_comments += 1
                    continue
                    
                if stripped.startswith('*'):  # Part of Javadoc
                    multi_comments += 1
                    continue
                    
                if not in_multi_comment:
                    sloc += 1
            
            # Calculate comment ratio
            total_comments = single_comments + multi_comments
            comment_ratio = total_comments / loc if loc > 0 else 0
            
            # Count packages (unique import paths)
            packages = set()
            import_paths = []
            for imp in imports:
                if hasattr(imp, 'path'):
                    import_path = imp.path
                    import_paths.append(import_path)
                    if '.' in import_path:
                        packages.add(import_path.split('.')[0])
            
            return {
                'language': 'java',
                'complexity': {'score': complexity_score, 'issues': []},
                'maintainability': {'score': maintainability_score, 'issues': []},
                'cognitive_complexity': complexity_score,
                'code_coverage': 0,
                'raw_metrics': {
                    'loc': loc,  # Total lines of code
                    'sloc': sloc,  # Source lines of code (excluding comments and blanks)
                    'comments': total_comments,  # Total comments (single + multi)
                    'single_comments': single_comments,
                    'multi_comments': multi_comments,
                    'blank': blank_lines,
                    'classes': len(classes),
                    'methods': len(methods),
                    'functions': len(methods),  # In Java, methods are functions
                    'comment_ratio': comment_ratio,
                    'packages': len(packages)  # Number of unique imported packages
                },
                'imports': import_paths,
                'packages': list(packages),
                'code_smells': self._detect_java_smells(tree),
                'design_issues': [],
                'performance_issues': [],
                'security_issues': []
            }
        except Exception as e:
            print(f"Error parsing Java code: {str(e)}")
            # Fallback to basic analysis when parsing fails
            basic_metrics = self._basic_java_analysis(content)
            return {
                'language': 'java',
                'complexity': {'score': basic_metrics['complexity'], 'issues': []},
                'maintainability': {'score': 70, 'issues': []},  # Default reasonable score
                'cognitive_complexity': basic_metrics['complexity'],
                'code_coverage': 0,
                'raw_metrics': {
                    'loc': len(content.splitlines()),
                    'sloc': len([l for l in content.splitlines() if l.strip()]),
                    'comments': basic_metrics['comments'],
                    'single_comments': basic_metrics['single_comments'],
                    'multi_comments': basic_metrics['multi_comments'],
                    'blank': basic_metrics['blank_lines'],
                    'classes': basic_metrics['classes'],
                    'methods': basic_metrics['methods'],
                    'functions': basic_metrics['methods'],
                    'comment_ratio': basic_metrics['comment_ratio'],
                    'packages': basic_metrics['imports']
                },
                'imports': basic_metrics['import_paths'],
                'packages': basic_metrics['packages'],
                'code_smells': basic_metrics['smells'],
                'design_issues': [],
                'performance_issues': [],
                'security_issues': []
            }

    def _basic_java_analysis(self, content: str) -> Dict:
        """Perform basic Java code analysis when full parsing fails."""
        lines = content.splitlines()
        
        # Initialize metrics
        metrics = {
            'classes': 0,
            'methods': 0,
            'imports': 0,
            'complexity': 0,
            'comments': 0,
            'single_comments': 0,
            'multi_comments': 0,
            'blank_lines': 0,
            'import_paths': [],
            'packages': set(),
            'smells': []
        }

        # Process each line
        in_multi_comment = False
        for line in lines:
            stripped = line.strip()
            
            # Skip blank lines
            if not stripped:
                metrics['blank_lines'] += 1
                continue
            
            # Handle comments
            if stripped.startswith('/*') or stripped.startswith('/**'):
                in_multi_comment = True
                metrics['multi_comments'] += 1
                continue
                
            if in_multi_comment:
                metrics['multi_comments'] += 1
                if stripped.endswith('*/'):
                    in_multi_comment = False
                continue
                
            if stripped.startswith('//'):
                metrics['single_comments'] += 1
                continue
                
            if stripped.startswith('*'):  # Part of Javadoc
                metrics['multi_comments'] += 1
                continue

            # Count classes using regex
            if re.search(r'\b(public|private|protected)?\s+class\s+\w+', stripped):
                metrics['classes'] += 1

            # Count methods using regex
            if re.search(r'\b(public|private|protected)?\s+\w+\s+\w+\s*\([^)]*\)', stripped):
                metrics['methods'] += 1

            # Process imports
            if stripped.startswith('import '):
                metrics['imports'] += 1
                import_match = re.search(r'import\s+([\w\.]+);', stripped)
                if import_match:
                    import_path = import_match.group(1)
                    metrics['import_paths'].append(import_path)
                    # Extract package name (first part of import path)
                    package = import_path.split('.')[0]
                    metrics['packages'].add(package)

        # Calculate total comments
        metrics['comments'] = metrics['single_comments'] + metrics['multi_comments']
        
        # Calculate comment ratio
        total_lines = len(lines)
        metrics['comment_ratio'] = metrics['comments'] / total_lines if total_lines > 0 else 0

        # Basic complexity calculation
        control_structures = [
            r'\bif\b',
            r'\bwhile\b',
            r'\bfor\b',
            r'\bswitch\b',
            r'\bcatch\b',
            r'\bcase\b'
        ]
        
        metrics['complexity'] = 1  # Base complexity
        for pattern in control_structures:
            metrics['complexity'] += len(re.findall(pattern, content))

        # Convert packages set to list for return
        metrics['packages'] = list(metrics['packages'])

        return metrics

    def _calculate_java_complexity(self, tree) -> int:
        """Calculate cyclomatic complexity for Java code with improved accuracy."""
        complexity = 1  # Base complexity

        # Define control structures with their weights
        control_structures = [
            (javalang.tree.IfStatement, 1),
            (javalang.tree.ForStatement, 1),
            (javalang.tree.WhileStatement, 1),
            (javalang.tree.DoStatement, 1),
            (javalang.tree.CatchClause, 1),
            (javalang.tree.SwitchStatement, 1),
            # Add weight for binary operations
            (javalang.tree.BinaryOperation, 0.5)
        ]

        try:
            # Count control structures
            for node_type, weight in control_structures:
                nodes = list(tree.filter(node_type))
                complexity += len(nodes) * weight

            # Add complexity for nested structures
            for path, node in tree.filter(javalang.tree.BlockStatement):
                nesting_level = self._calculate_nesting_level(node)
                complexity += nesting_level * 0.5

            # Add complexity for method parameters
            for path, node in tree.filter(javalang.tree.MethodDeclaration):
                complexity += len(node.parameters) * 0.2

        except Exception as e:
            # If detailed analysis fails, return a conservative estimate
            return max(complexity, 5)

        return int(complexity)  # Return as integer to avoid floating point complexity

    def _detect_java_smells(self, tree) -> List[str]:
        """Detect code smells in Java code with improved detection."""
        smells = []

        try:
            # Check for long methods
            for path, method in tree.filter(javalang.tree.MethodDeclaration):
                if method.body and len(list(method.body)) > 20:
                    smells.append(f"Long method detected: {method.name}")

            # Check for large classes
            for path, class_decl in tree.filter(javalang.tree.ClassDeclaration):
                if len(list(class_decl.methods)) > 10:
                    smells.append(f"Large class detected: {class_decl.name}")

            # Check for deep nesting
            return smells
        except Exception as e:
            print(f"Error detecting Java smells: {str(e)}")
            return smells

    def _count_operators(self, node) -> int:
        """Count the number of operators in a binary operation."""
        count = 1  # Count the current operator

        if isinstance(node.left, javalang.tree.BinaryOperation):
            count += self._count_operators(node.left)
        if isinstance(node.right, javalang.tree.BinaryOperation):
            count += self._count_operators(node.right)

        return count

    def _calculate_nesting_level(self, node, level=0) -> int:
        """Calculate nesting level of a node."""
        max_level = level
        for child in node.children:
            if isinstance(child, (javalang.tree.IfStatement,
                                  javalang.tree.ForStatement,
                                  javalang.tree.WhileStatement,
                                  javalang.tree.DoStatement)):
                child_level = self._calculate_nesting_level(child, level + 1)
                max_level = max(max_level, child_level)
        return max_level

    def _analyze_cpp(self, content: str) -> Dict[str, Any]:
        """Analyze C++ code."""
        try:
            parser = cpp_parser.CppParser()
            metrics = parser.analyze_file(content)

            # Add additional metrics
            metrics.update({
                "language": "cpp",
                "dependencies": parser.get_dependencies(content),
                "class_hierarchy": parser.get_class_hierarchy(content),
                "function_signatures": parser.get_function_signatures(content)
            })

            return metrics

        except Exception as e:
            return {
                "language": "cpp",
                "error": str(e)
            }

    def _analyze_code_quality(self, content: str) -> Dict:
        """Analyze code quality metrics."""
        try:
            lines = content.splitlines()
            non_empty_lines = [l for l in lines if l.strip()]
            comment_lines = [l for l in lines if l.strip().startswith('#')]
            
            metrics = {
                'non_empty_lines': len(non_empty_lines),
                'comment_lines': len(comment_lines),
                'comment_ratio': len(comment_lines) / len(non_empty_lines) if non_empty_lines else 0,
                'avg_line_length': sum(len(l) for l in non_empty_lines) / len(non_empty_lines) if non_empty_lines else 0,
                'max_line_length': max((len(l) for l in non_empty_lines), default=0)
            }
            return metrics
        except Exception as e:
            print(f"Error analyzing code quality: {str(e)}")
            return {}

    def _calculate_complexity(self, content: Any) -> int:
        """Calculate code complexity."""
        try:
            if isinstance(content, str):
                # Count control structures
                control_structures = [
                    r'if\s*\([^)]*\)',
                    r'else\s*{',
                    r'for\s*\([^)]*\)',
                    r'while\s*\([^)]*\)',
                    r'switch\s*\([^)]*\)',
                    r'catch\s*\([^)]*\)',
                    r'&&',
                    r'\|\|',
                    r'\?',
                    r':'
                ]

                complexity = 1  # Base complexity
                for pattern in control_structures:
                    complexity += len(re.findall(pattern, content))

                return complexity

            elif isinstance(content, ast.AST):
                # Python AST-based complexity calculation
                complexity = 1

                for node in ast.walk(content):
                    if isinstance(
                        node,
                        (ast.If,
                         ast.While,
                         ast.For,
                         ast.AsyncFor,
                         ast.Try,
                         ast.With,
                         ast.AsyncWith)):
                        complexity += 1
                    elif isinstance(node, ast.BoolOp):
                        complexity += len(node.values) - 1

                return complexity

            return 1

        except Exception:
            return 1

    def get_syntax_highlighted_code(self, content: str, language: str) -> str:
        """Get syntax highlighted HTML for code."""
        try:
            lexer = get_lexer_by_name(language)
            formatter = HtmlFormatter(style='monokai')
            return pygments.highlight(content, lexer, formatter)
        except Exception:
            return content

    def _analyze_python_performance(self, tree: ast.AST) -> Dict:
        """Analyze Python code for performance issues."""
        issues = []

        # Loop optimization detection
        for node in ast.walk(tree):
            if isinstance(node, ast.For):
                if isinstance(node.iter, ast.Call):
                    if isinstance(node.iter.func, ast.Name):
                        if node.iter.func.id == 'range':
                            # Check for range(len()) pattern
                            if isinstance(node.iter.args[0], ast.Call):
                                if isinstance(
                                        node.iter.args[0].func, ast.Name):
                                    if node.iter.args[0].func.id == 'len':
                                        issues.append(
                                            f"Consider using enumerate() instead of range(len()) at line {
                                                node.lineno}")

        return {
            'score': 100 - len(issues) * 10,
            'issues': issues
        }

    def _format_maintainability_issues(self, mi: float) -> List[str]:
        """Format maintainability issues for display."""
        issues = []
        if mi < 65:
            issues.append("Low maintainability score - consider refactoring")
        return issues

    def _detect_python_smells(self, tree: ast.AST) -> List[str]:
        """Detect code smells in Python code."""
        smells = []

        # Long method detection
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if len(node.body) > 20:  # More than 20 lines
                    smells.append(f"Long method detected: {node.name}")

        # Deep nesting detection
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.For, ast.While)):
                nesting_level = self._calculate_nesting_level(node)
                if nesting_level > 4:  # More than 4 levels deep
                    smells.append(f"Deep nesting detected at line {node.lineno}")

        return smells

    def _calculate_nesting_level(self, node: ast.AST, level: int = 0) -> int:
        """Calculate nesting level of a node."""
        max_level = level
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.If, ast.For, ast.While)):
                child_level = self._calculate_nesting_level(child, level + 1)
                max_level = max(max_level, child_level)
        return max_level

    def _analyze_csharp(self, content: str) -> Dict:
        """Analyze C# code."""
        try:
            parser = csharp_parser.CSharpParser()
            metrics = parser.analyze_file(content)

            # Add additional metrics
            metrics.update({
                "language": "csharp",
                "dependencies": parser.get_dependencies(content),
                "class_hierarchy": parser.get_class_hierarchy(content),
                "method_signatures": parser.get_method_signatures(content),
                "property_signatures": parser.get_property_signatures(content)
            })

            return metrics

        except Exception as e:
            return {
                "language": "csharp",
                "error": str(e)
            }

    def _detect_csharp_smells(self, tree: Any) -> List[str]:
        """Detect code smells in C# code."""
        smells = []
        for method in tree.Members.OfType<MethodDeclarationSyntax>():
            if method.Span.Length > 50:
                smells.append(f"Long method detected: {method.Identifier.Text}")
            if method.ParameterList.Parameters.Count > 5:
                smells.append(f"Too many parameters in method: {method.Identifier.Text}")
        return smells

    def _calculate_csharp_complexity(self, content: str) -> int:
        """Calculate cyclomatic complexity for C# code."""
        parser = csharp_parser.CSharpParser()
        return parser.analyze_file(content)['complexity']

    def _calculate_csharp_maintainability(self, content: str) -> Dict:
        """Calculate maintainability metrics for C# code."""
        parser = csharp_parser.CSharpParser()
        metrics = parser.analyze_file(content)

        # Calculate maintainability score based on various factors
        score = 100

        # Penalize for high complexity
        if metrics['complexity'] > 10:
            score -= 10 * (metrics['complexity'] - 10)

        # Penalize for too many dependencies
        if len(metrics['dependencies']) > 10:
            score -= 5 * (len(metrics['dependencies']) - 10)

        # Penalize for deep class hierarchy
        if len(metrics['class_hierarchy']) > 3:
            score -= 5 * (len(metrics['class_hierarchy']) - 3)

        return {
            'score': max(0, score),
            'issues': self._format_maintainability_issues(score)
        }

    def _analyze_csharp_performance(self, content: str) -> Dict:
        """Analyze C# code for performance issues."""
        issues = []
        parser = csharp_parser.CSharpParser()

        # Check for virtual methods in performance-critical code
        if 'virtual' in content and 'sealed' not in content:
            issues.append(
                "Consider sealing virtual methods for better performance")

        # Check for unnecessary boxing/unboxing
        if 'object' in content and 'var' not in content:
            issues.append(
                "Consider using var to avoid unnecessary boxing/unboxing")

        return {
            'score': 100 - len(issues) * 10,
            'issues': issues
        }

    def _detect_cpp_smells(self, content: str) -> List[str]:
        """Detect code smells in C++ code."""
        smells = []
        parser = cpp_parser.CppParser()

        # Check for long functions
        for func in parser.get_function_signatures(content):
            if len(func) > 50:  # More than 50 lines
                smells.append(f"Long function detected: {func}")

        # Check for deep nesting
        if parser.analyze_file(content)['complexity'] > 10:
            smells.append("High cyclomatic complexity detected")

        return smells

    def _calculate_cpp_complexity(self, content: str) -> int:
        """Calculate cyclomatic complexity for C++ code."""
        parser = cpp_parser.CppParser()
        return parser.analyze_file(content)['complexity']

    def _calculate_cpp_maintainability(self, content: str) -> Dict:
        """Calculate maintainability metrics for C++ code."""
        parser = cpp_parser.CppParser()
        metrics = parser.analyze_file(content)

        # Calculate maintainability score based on various factors
        score = 100

        # Penalize for high complexity
        if metrics['complexity'] > 10:
            score -= 10 * (metrics['complexity'] - 10)

        # Penalize for too many dependencies
        if len(metrics['dependencies']) > 10:
            score -= 5 * (len(metrics['dependencies']) - 10)

        # Penalize for deep class hierarchy
        if len(metrics['class_hierarchy']) > 3:
            score -= 5 * (len(metrics['class_hierarchy']) - 3)

        return {
            'score': max(0, score),
            'issues': self._format_maintainability_issues(score)
        }

    def _analyze_cpp_performance(self, content: str) -> Dict:
        """Analyze C++ code for performance issues."""
        issues = []
        parser = cpp_parser.CppParser()

        # Check for virtual functions in performance-critical code
        if 'virtual' in content and 'inline' not in content:
            issues.append(
                "Consider using inline functions for performance-critical code")

        # Check for unnecessary object copying
        if 'const&' not in content:
            issues.append(
                "Consider using const references to avoid unnecessary copying")

        return {
            'score': 100 - len(issues) * 10,
            'issues': issues
        }

    def _detect_javascript_smells(self, content: str):
        # Implementation of detect_javascript_smells method
        pass

    def _calculate_javascript_complexity(self, content: str):
        # Implementation of calculate_javascript_complexity method
        pass

    def _calculate_javascript_maintainability(self, content: str):
        # Implementation of calculate_javascript_maintainability method
        pass

    def _analyze_javascript_performance(self, content: str):
        # Implementation of analyze_javascript_performance method
        pass

    def _walk_js_ast(self, node):
        """Walk JavaScript AST."""
        yield node
        for key, value in node.__dict__.items():
            if isinstance(value, list):
                for item in value:
                    if hasattr(item, '__dict__'):
                        yield from self._walk_js_ast(item)
            elif hasattr(value, '__dict__'):
                yield from self._walk_js_ast(value)

    def _calculate_js_complexity(self, tree) -> int:
        """Calculate complexity for JavaScript code."""
        complexity = 0

        # Count control flow statements
        for node in self._walk_js_ast(tree):
            if node.type in [
                'IfStatement',
                'WhileStatement',
                'ForStatement',
                    'SwitchStatement']:
                complexity += 1

        return complexity

    def _calculate_scores(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate final scores and format results for visualization."""

        # Calculate complexity score (0-100, lower is better)
        complexity_score = min(
            100, max(0, 100 - (metrics.get('complexity', 0) * 5)))

        # Calculate maintainability score (0-100, higher is better)
        maintainability_score = min(
            100, max(
                0, metrics.get(
                    'maintainability', {}).get(
                    'score', 70)))

        # Calculate performance score (0-100)
        performance_score = 85  # Default good performance score

        # Generate meaningful issues
        complexity_issues = []
        if complexity_score < 60:
            complexity_issues.append(
                "High cyclomatic complexity detected. Consider breaking down complex functions.")
        if metrics.get('max_line_length', 0) > 100:
            complexity_issues.append(
                "Some lines are too long. Consider breaking them into smaller chunks.")

        code_smells = []
        if metrics.get('function_count', 0) > 20:
            code_smells.append(
                "Too many functions in one file. Consider splitting into multiple files.")
        if metrics.get('average_line_length', 0) > 50:
            code_smells.append(
                "Average line length is high. Consider improving code readability.")

        performance_issues = []
        if metrics.get('imports', []) and len(metrics.get('imports', [])) > 15:
            performance_issues.append(
                "Large number of imports may impact performance.")

        return {
            'complexity': {
                'score': complexity_score,
                'issues': complexity_issues},
            'maintainability': {
                'score': maintainability_score,
                'issues': [
                    "Consider adding more documentation" if maintainability_score < 80 else None,
                    "Complex code structures detected" if maintainability_score < 60 else None]},
            'code_smells': code_smells,
            'performance': {
                'score': performance_score,
                'issues': performance_issues}}

    def _analyze_generic(self, content: str) -> Dict[str, Any]:
        """Generic analysis for unsupported languages."""
        return {
            'complexity': {
                'score': 50,
                'issues': ["Language not fully supported yet"]},
            'maintainability': {
                'score': 50,
                'issues': ["Language not fully supported yet"]},
            'code_smells': ["Language not fully supported yet"],
            'performance': {
                'score': 50,
                'issues': ["Language not fully supported yet"]},
            'raw_metrics': self._get_basic_metrics(content),
            'halstead_metrics': self._calculate_halstead_metrics(content)}

    def _calculate_complexity_metrics(self, content: str) -> Dict[str, Any]:
        """Calculate code complexity metrics."""
        try:
            # Calculate cyclomatic complexity using radon
            complexity = cc_visit(content)
            total_complexity = sum(item.complexity for item in complexity)

            # Generate complexity score (0-100, lower complexity is better)
            score = max(0, min(100, 100 - (total_complexity * 5)))

            issues = []
            if total_complexity > 10:
                issues.append(
                    "High cyclomatic complexity detected. Consider breaking down complex functions.")
            if len(content.split('\n')) > 300:
                issues.append(
                    "File is too long. Consider splitting it into multiple files.")

            return {
                'score': score,
                'issues': issues
            }
        except BaseException:
            return {'score': 50, 'issues': [
                "Error calculating complexity metrics"]}

    def _calculate_maintainability_metrics(
            self, content: str) -> Dict[str, Any]:
        """Calculate code maintainability metrics."""
        try:
            # Calculate maintainability index using radon
            mi_score = radon_metrics.mi_visit(content, multi=True)

            # Convert to 0-100 scale
            score = max(0, min(100, mi_score))

            issues = []
            if score < 65:
                issues.append(
                    "Low maintainability index. Consider improving code structure and documentation.")
            if len([line for line in content.split('\n') if line.strip(
            ).startswith('#')]) < len(content.split('\n')) * 0.1:
                issues.append(
                    "Low comment ratio. Consider adding more documentation.")

            return {
                'score': score,
                'issues': issues
            }
        except BaseException:
            return {'score': 50, 'issues': [
                "Error calculating maintainability metrics"]}

    def _detect_code_smells(self, content: str) -> List[str]:
        """Detect code smells."""
        smells = []
        lines = content.split('\n')

        # Check line length
        for i, line in enumerate(lines, 1):
            if len(line.strip()) > 100:
                smells.append(f"Line {i} is too long ({len(line)} characters)")

        # Check function length
        current_function = []
        for line in lines:
            if line.strip().startswith('def '):
                if len(current_function) > 20:
                    smells.append(
                        f"Function is too long ({
                            len(current_function)} lines)")
                current_function = []
            current_function.append(line)

        # Check nesting depth
        max_depth = 0
        current_depth = 0
        for line in lines:
            indent = len(line) - len(line.lstrip())
            depth = indent // 4
            max_depth = max(max_depth, depth)
        if max_depth > 4:
            smells.append(f"Deep nesting detected (depth: {max_depth})")

        return smells

    def _analyze_performance(self, content: str) -> Dict[str, Any]:
        """Analyze code for performance issues."""
        issues = []
        score = 100

        # Check for common performance issues
        if 'import *' in content:
            issues.append(
                "Using 'import *' can slow down imports and create namespace issues")
            score -= 20

        if 'while True:' in content:
            issues.append(
                "Infinite loop detected. Ensure proper exit conditions")
            score -= 15

        if '.copy()' not in content and any(
                op in content for op in ['list(', 'dict(']):
            issues.append(
                "Consider using .copy() for mutable objects to prevent unintended modifications")
            score -= 10

        return {
            'score': max(0, score),
            'issues': issues
        }

    def _calculate_halstead_metrics(self, code: str) -> dict:
        """Calculate Halstead metrics for the given code."""
        try:
            # Initialize metrics
            operators = set()
            operands = set()
            total_operators = 0
            total_operands = 0

            # Basic operators in most programming languages
            basic_operators = {
                '+', '-', '*', '/', '%', '=', '==', '!=', '<', '>', '<=', '>=',
                '&&', '||', '!', '++', '--', '+=', '-=', '*=', '/=', '%=',
                'and', 'or', 'not', 'in', 'is', 'lambda', 'if', 'else', 'elif',
                'for', 'while', 'return', 'yield', 'break', 'continue', 'pass'
            }

            # Handle empty or invalid code
            if not code or not code.strip():
                return self._get_default_halstead_metrics()

            try:
                # Try to parse as valid Python code first
                tree = ast.parse(code)

                # Walk the AST to collect operators and operands
                for node in ast.walk(tree):
                    if isinstance(node, ast.Name):
                        operands.add(node.id)
                        total_operands += 1
                    elif isinstance(node, ast.Num):
                        operands.add(str(node.n))
                        total_operands += 1
                    elif isinstance(node, ast.Str):
                        operands.add(node.s)
                        total_operands += 1
                    elif isinstance(node, ast.operator):
                        operators.add(node.__class__.__name__)
                        total_operators += 1
                    elif isinstance(node, ast.BoolOp):
                        operators.add(node.op.__class__.__name__)
                        total_operators += 1
                    elif isinstance(node, ast.Compare):
                        for op in node.ops:
                            operators.add(op.__class__.__name__)
                            total_operators += 1

            except SyntaxError:
                # Fallback to basic tokenization for non-Python code
                try:
                    code_lines = code.splitlines()
                    for line in code_lines:
                        line = line.strip()
                        if not line or line.startswith(
                                ('#', '//', '/*', '*', '*/')):
                            continue

                        # Split line into tokens
                        tokens = line.split()
                        for token in tokens:
                            if token in basic_operators:
                                operators.add(token)
                                total_operators += 1
                            else:
                                operands.add(token)
                                total_operands += 1
                except Exception as e:
                    print(f"Error in basic tokenization: {str(e)}")
                    return self._get_default_halstead_metrics()

            # Calculate Halstead metrics
            # Number of unique operators (prevent division by zero)
            n1 = len(operators) or 1
            n2 = len(operands) or 1   # Number of unique operands
            N1 = total_operators or 1  # Total operators
            N2 = total_operands or 1   # Total operands

            vocabulary = n1 + n2
            length = N1 + N2
            volume = length * math.log2(vocabulary)
            difficulty = (n1 / 2) * (N2 / n2)
            effort = difficulty * volume
            time = effort / 18  # Estimated time in seconds
            bugs = volume / 3000  # Estimated number of bugs

            return {
                'vocabulary': round(vocabulary, 2),
                'length': round(length, 2),
                'volume': round(volume, 2),
                'difficulty': round(difficulty, 2),
                'effort': round(effort, 2),
                'time': round(time, 2),
                'bugs': round(bugs, 3)
            }

        except Exception as e:
            print(f"Error calculating Halstead metrics: {str(e)}")
            return self._get_default_halstead_metrics()

    def _get_default_halstead_metrics(self) -> dict:
        """Return default Halstead metrics."""
        return {
            'vocabulary': 0,
            'length': 0,
            'volume': 0,
            'difficulty': 0,
            'effort': 0,
            'time': 0,
            'bugs': 0
        }

    def _get_basic_metrics(self, content, language=None):
        """Get basic code metrics regardless of language."""
        try:
            lines = content.splitlines()
            total_lines = len(lines)
            blank_lines = len([line for line in lines if not line.strip()])
            comment_lines = 0
            code_lines = 0
            
            # Language specific comment detection
            single_line_comment = '//'  # Default for C-style languages
            multi_line_start = '/*'
            multi_line_end = '*/'
            
            if language == 'python':
                single_line_comment = '#'
                multi_line_start = '"""'
                multi_line_end = '"""'
            elif language == 'ruby':
                single_line_comment = '#'
                multi_line_start = '=begin'
                multi_line_end = '=end'
            
            in_multi_line_comment = False
            
            for line in lines:
                stripped_line = line.strip()
                
                # Skip empty lines
                if not stripped_line:
                    continue
                
                # Handle multi-line comments
                if multi_line_start in stripped_line:
                    in_multi_line_comment = True
                    comment_lines += 1
                    continue
                
                if in_multi_line_comment:
                    comment_lines += 1
                    if multi_line_end in stripped_line:
                        in_multi_line_comment = False
                    continue
                
                # Handle single-line comments
                if stripped_line.startswith(single_line_comment):
                    comment_lines += 1
                else:
                    code_lines += 1
            
            return {
                'total_lines': total_lines,
                'code_lines': code_lines,
                'comment_lines': comment_lines,
                'blank_lines': blank_lines,
                'comment_ratio': comment_lines / total_lines if total_lines > 0 else 0
            }
        except Exception as e:
            print(f"Error in _get_basic_metrics: {str(e)}")
            return {
                'total_lines': 0,
                'code_lines': 0,
                'comment_lines': 0,
                'blank_lines': 0,
                'comment_ratio': 0
            }


def analyze_file(file_path: str, content: str = None) -> dict:
    """
    Analyze a single file and return its metrics.

    Args:
        file_path: Path to the file to analyze
        content: Optional file content if already loaded

    Returns:
        dict: Dictionary containing all metrics and analysis results
    """
    analyzer = CodeAnalyzer({})  # Initialize with empty config
    return analyzer.analyze_file(file_path, content)


__all__ = ['CodeAnalyzer', 'analyze_file']
