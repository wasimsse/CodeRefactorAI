import ast
import re
from typing import Dict, Any, List
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
                    if file.endswith('.py'):  # Only analyze Python files for now
                        file_path = os.path.join(root, file)
                        try:
                            file_metrics = self.analyze_file(file_path)
                            
                            # Aggregate metrics
                            project_metrics['complexity']['score'] += file_metrics['complexity'].get('score', 0)
                            project_metrics['complexity']['issues'].extend(file_metrics['complexity'].get('issues', []))
                            
                            project_metrics['maintainability']['score'] += file_metrics['maintainability'].get('score', 0)
                            project_metrics['maintainability']['issues'].extend(file_metrics['maintainability'].get('issues', []))
                            
                            project_metrics['code_smells'].extend(file_metrics.get('code_smells', []))
                            
                            if 'performance' in file_metrics:
                                project_metrics['performance']['score'] += file_metrics['performance'].get('score', 0)
                                project_metrics['performance']['issues'].extend(file_metrics['performance'].get('issues', []))
                            
                            # Aggregate raw metrics
                            for key in project_metrics['raw_metrics'].keys():
                                project_metrics['raw_metrics'][key] += file_metrics.get('raw_metrics', {}).get(key, 0)
                            
                            project_metrics['files_analyzed'] += 1
                        except Exception as e:
                            print(f"Error analyzing file {file_path}: {str(e)}")
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
                'complexity': {'score': 50, 'issues': [f"Error analyzing project complexity: {str(e)}"]},
                'maintainability': {'score': 50, 'issues': [f"Error analyzing project maintainability: {str(e)}"]},
                'code_smells': [f"Error detecting project code smells: {str(e)}"],
                'performance': {'score': 50, 'issues': [f"Error analyzing project performance: {str(e)}"]},
                'raw_metrics': {
                    'loc': 0, 'lloc': 0, 'sloc': 0,
                    'comments': 0, 'multi': 0, 'blank': 0
                },
                'files_analyzed': 0,
                'total_files': 0
            }
            
    def analyze_file(self, file_path: str) -> Dict[str, Any]:
        """Analyze a file and return metrics."""
        try:
            # Get file extension
            ext = os.path.splitext(file_path)[1].lower()
            
            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # For Python files, use Python-specific analysis
            if ext == '.py':
                tree = ast.parse(content)
                
                # Get basic metrics
                basic_metrics = self._get_basic_metrics(content)
                
                # Get Python-specific analysis
                python_analysis = self._analyze_python(content)
                
                # Calculate cyclomatic complexity
                complexity_visitor = ComplexityVisitor.from_code(content)
                total_complexity = sum(item.complexity for item in complexity_visitor.functions)
                
                # Calculate maintainability index
                mi_score = radon_metrics.mi_visit(content, multi=True)
                maintainability_score = min(100, max(0, mi_score))
                
                # Calculate raw metrics
                raw_metrics = analyze(content)
                
                return {
                    'file_path': file_path,
                    'complexity': {
                        'score': max(0, min(100, 100 - (total_complexity * 5))),
                        'issues': python_analysis.get('code_smells', [])
                    },
                    'maintainability': {
                        'score': maintainability_score,
                        'issues': []
                    },
                    'code_smells': python_analysis.get('code_smells', []),
                    'performance': {
                        'score': 75,
                        'issues': []
                    },
                    'raw_metrics': {
                        'loc': raw_metrics.loc,
                        'lloc': raw_metrics.lloc,
                        'sloc': raw_metrics.sloc,
                        'comments': raw_metrics.comments,
                        'multi': raw_metrics.multi,
                        'blank': raw_metrics.blank,
                        'classes': python_analysis.get('class_count', 0),
                        'functions': python_analysis.get('function_count', 0),
                        'average_method_length': basic_metrics['average_line_length'],
                        'max_complexity': total_complexity,
                        'comment_ratio': (raw_metrics.comments + raw_metrics.multi) / raw_metrics.loc if raw_metrics.loc > 0 else 0
                    },
                    'halstead_metrics': python_analysis.get('halstead_metrics', self._get_default_halstead_metrics())
                }
            else:
                # Use generic analysis for other file types
                return self._analyze_generic(content)
                
        except Exception as e:
            print(f"Error analyzing file: {str(e)}")
            return {
                'file_path': file_path,
                'complexity': {'score': 50, 'issues': [f"Error analyzing complexity: {str(e)}"]},
                'maintainability': {'score': 50, 'issues': [f"Error analyzing maintainability: {str(e)}"]},
                'code_smells': [f"Error detecting code smells: {str(e)}"],
                'performance': {'score': 50, 'issues': [f"Error analyzing performance: {str(e)}"]},
                'raw_metrics': {
                    'loc': 0, 'lloc': 0, 'sloc': 0,
                    'comments': 0, 'multi': 0, 'blank': 0,
                    'classes': 0, 'functions': 0,
                    'average_method_length': 0,
                    'max_complexity': 0,
                    'comment_ratio': 0
                },
                'halstead_metrics': self._get_default_halstead_metrics()
            }

    def _get_basic_metrics(self, content: str) -> Dict[str, Any]:
        """Get basic code metrics."""
        lines = content.split('\n')
        non_empty_lines = [line for line in lines if line.strip()]
        
        return {
            'total_lines': len(lines),
            'non_empty_lines': len(non_empty_lines),
            'average_line_length': sum(len(line) for line in non_empty_lines) / len(non_empty_lines) if non_empty_lines else 0,
            'max_line_length': max(len(line) for line in lines) if lines else 0
        }

    def _analyze_python(self, content: str) -> Dict[str, Any]:
        """Analyze Python code."""
        try:
            tree = ast.parse(content)
            
            # Count functions and classes
            functions = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
            classes = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
            
            # Analyze imports
            imports = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imports.extend(alias.name for alias in node.names)
                elif isinstance(node, ast.ImportFrom):
                    imports.append(f"{node.module}")
            
            # Calculate cyclomatic complexity
            complexity_visitor = ComplexityVisitor.from_code(content)
            complexity = sum(item.complexity for item in complexity_visitor.functions)
            
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
                    code_smells.append(f"Function '{func.name}' is too long ({len(func.body)} lines)")
            
            # Check class complexity
            for cls in classes:
                methods = [node for node in ast.walk(cls) if isinstance(node, ast.FunctionDef)]
                if len(methods) > 10:
                    code_smells.append(f"Class '{cls.name}' has too many methods ({len(methods)})")
            
            # Check nesting depth
            for func in functions:
                nesting = self._calculate_nesting_level(func)
                if nesting > 3:
                    code_smells.append(f"Function '{func.name}' has deep nesting (level {nesting})")
            
            return {
                "language": "python",
                "function_count": len(functions),
                "class_count": len(classes),
                "imports": imports,
                "complexity": complexity,
                "maintainability": {
                    "score": maintainability_score,
                    "issues": []
                },
                "code_smells": code_smells,
                "raw_metrics": {
                    "loc": raw_metrics.loc,
                    "lloc": raw_metrics.lloc,
                    "sloc": raw_metrics.sloc,
                    "comments": raw_metrics.comments,
                    "multi": raw_metrics.multi,
                    "blank": raw_metrics.blank
                },
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
                    "bugs": halstead.bugs
                }
            }
            
        except Exception as e:
            return {
                "language": "python",
                "error": str(e),
                "complexity": {"score": 50, "issues": ["Error analyzing code"]},
                "maintainability": {"score": 50, "issues": ["Error analyzing code"]},
                "code_smells": ["Error analyzing code"],
                "performance": {"score": 50, "issues": ["Error analyzing code"]}
            }
            
    def _analyze_javascript(self, content: str) -> Dict[str, Any]:
        """Analyze JavaScript/TypeScript code."""
        try:
            # Parse JavaScript code
            tree = esprima.parseScript(content)
            
            # Count functions and classes
            functions = len([node for node in self._walk_js_ast(tree) if node.type == 'FunctionDeclaration'])
            classes = len([node for node in self._walk_js_ast(tree) if node.type == 'ClassDeclaration'])
            
            # Count imports
            imports = len([node for node in self._walk_js_ast(tree) if node.type == 'ImportDeclaration'])
            
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
        """Analyze Java code using javalang."""
        try:
            tree = javalang.parse.parse(content)
            metrics = {
                'classes': len(list(tree.filter(javalang.tree.ClassDeclaration))),
                'interfaces': len(list(tree.filter(javalang.tree.InterfaceDeclaration))),
                'methods': len(list(tree.filter(javalang.tree.MethodDeclaration))),
                'imports': len(list(tree.filter(javalang.tree.Import))),
                'complexity': self._calculate_java_complexity(tree),
                'smells': self._detect_java_smells(tree)
            }
            return metrics
        except Exception as e:
            self.logger.log_error(f"Error analyzing Java code: {str(e)}")
            return self._get_default_metrics()

    def _calculate_java_complexity(self, tree) -> int:
        """Calculate cyclomatic complexity for Java code."""
        complexity = 1  # Base complexity
        
        # Count control structures
        control_structures = [
            (javalang.tree.IfStatement, 1),
            (javalang.tree.ForStatement, 1),
            (javalang.tree.WhileStatement, 1),
            (javalang.tree.DoStatement, 1),
            (javalang.tree.CatchClause, 1),
            (javalang.tree.SwitchStatement, 1),
            (javalang.tree.ConditionalExpression, 1)
        ]
        
        for node_type, weight in control_structures:
            complexity += len(list(tree.filter(node_type))) * weight
        
        return complexity

    def _detect_java_smells(self, tree) -> List[str]:
        """Detect code smells in Java code."""
        smells = []
        
        # Check for long methods
        for method in tree.filter(javalang.tree.MethodDeclaration):
            if len(list(method.body)) > 20:  # More than 20 statements
                smells.append(f"Long method detected: {method.name}")
        
        # Check for large classes
        for class_decl in tree.filter(javalang.tree.ClassDeclaration):
            if len(list(class_decl.methods)) > 10:  # More than 10 methods
                smells.append(f"Large class detected: {class_decl.name}")
        
        # Check for deep nesting
        for node in tree.filter(javalang.tree.IfStatement):
            nesting_level = self._calculate_nesting_level(node)
            if nesting_level > 4:  # More than 4 levels of nesting
                smells.append(f"Deep nesting detected in {node.position.line}")
        
        return smells

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
            
    def _analyze_code_quality(self, content: str) -> Dict[str, Any]:
        """Analyze general code quality metrics."""
        try:
            # Calculate metrics
            lines = content.splitlines()
            non_empty_lines = [line for line in lines if line.strip()]
            comment_lines = [line for line in lines if line.strip().startswith(('#', '//', '/*', '*', '*/'))]
            
            return {
                "non_empty_lines": len(non_empty_lines),
                "comment_lines": len(comment_lines),
                "comment_ratio": len(comment_lines) / len(non_empty_lines) if non_empty_lines else 0,
                "avg_line_length": sum(len(line) for line in non_empty_lines) / len(non_empty_lines) if non_empty_lines else 0,
                "max_line_length": max((len(line) for line in non_empty_lines), default=0)
            }
            
        except Exception as e:
            return {
                "error": str(e)
            }
            
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
                    if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor,
                                      ast.Try, ast.With, ast.AsyncWith)):
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
                                if isinstance(node.iter.args[0].func, ast.Name):
                                    if node.iter.args[0].func.id == 'len':
                                        issues.append(f"Consider using enumerate() instead of range(len()) at line {node.lineno}")
                                        
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
            
    def _detect_csharp_smells(self, content: str) -> List[str]:
        """Detect code smells in C# code."""
        smells = []
        parser = csharp_parser.CSharpParser()
        
        # Check for long methods
        for method in parser.get_method_signatures(content):
            if len(method) > 50:  # More than 50 lines
                smells.append(f"Long method detected: {method}")
        
        # Check for large classes
        metrics = parser.analyze_file(content)
        if metrics['classes'] > 10:
            smells.append("Large class detected")
            
        # Check for deep nesting
        if metrics['complexity'] > 10:
            smells.append("High cyclomatic complexity detected")
            
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
            issues.append("Consider sealing virtual methods for better performance")
            
        # Check for unnecessary boxing/unboxing
        if 'object' in content and 'var' not in content:
            issues.append("Consider using var to avoid unnecessary boxing/unboxing")
            
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
            issues.append("Consider using inline functions for performance-critical code")
            
        # Check for unnecessary object copying
        if 'const&' not in content:
            issues.append("Consider using const references to avoid unnecessary copying")
            
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
            if node.type in ['IfStatement', 'WhileStatement', 'ForStatement', 'SwitchStatement']:
                complexity += 1
                
        return complexity

    def _calculate_scores(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate final scores and format results for visualization."""
        
        # Calculate complexity score (0-100, lower is better)
        complexity_score = min(100, max(0, 100 - (metrics.get('complexity', 0) * 5)))
        
        # Calculate maintainability score (0-100, higher is better)
        maintainability_score = min(100, max(0, metrics.get('maintainability', {}).get('score', 70)))
        
        # Calculate performance score (0-100)
        performance_score = 85  # Default good performance score
        
        # Generate meaningful issues
        complexity_issues = []
        if complexity_score < 60:
            complexity_issues.append("High cyclomatic complexity detected. Consider breaking down complex functions.")
        if metrics.get('max_line_length', 0) > 100:
            complexity_issues.append("Some lines are too long. Consider breaking them into smaller chunks.")
        
        code_smells = []
        if metrics.get('function_count', 0) > 20:
            code_smells.append("Too many functions in one file. Consider splitting into multiple files.")
        if metrics.get('average_line_length', 0) > 50:
            code_smells.append("Average line length is high. Consider improving code readability.")
        
        performance_issues = []
        if metrics.get('imports', []) and len(metrics.get('imports', [])) > 15:
            performance_issues.append("Large number of imports may impact performance.")
        
        return {
            'complexity': {
                'score': complexity_score,
                'issues': complexity_issues
            },
            'maintainability': {
                'score': maintainability_score,
                'issues': [
                    "Consider adding more documentation" if maintainability_score < 80 else None,
                    "Complex code structures detected" if maintainability_score < 60 else None
                ]
            },
            'code_smells': code_smells,
            'performance': {
                'score': performance_score,
                'issues': performance_issues
            }
        }

    def _analyze_generic(self, content: str) -> Dict[str, Any]:
        """Generic analysis for unsupported languages."""
        return {
            'complexity': {'score': 50, 'issues': ["Language not fully supported yet"]},
            'maintainability': {'score': 50, 'issues': ["Language not fully supported yet"]},
            'code_smells': ["Language not fully supported yet"],
            'performance': {'score': 50, 'issues': ["Language not fully supported yet"]},
            'raw_metrics': self._get_basic_metrics(content),
            'halstead_metrics': self._calculate_halstead_metrics(content)
        }

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
                issues.append("High cyclomatic complexity detected. Consider breaking down complex functions.")
            if len(content.split('\n')) > 300:
                issues.append("File is too long. Consider splitting it into multiple files.")
            
            return {
                'score': score,
                'issues': issues
            }
        except:
            return {'score': 50, 'issues': ["Error calculating complexity metrics"]}

    def _calculate_maintainability_metrics(self, content: str) -> Dict[str, Any]:
        """Calculate code maintainability metrics."""
        try:
            # Calculate maintainability index using radon
            mi_score = radon_metrics.mi_visit(content, multi=True)
            
            # Convert to 0-100 scale
            score = max(0, min(100, mi_score))
            
            issues = []
            if score < 65:
                issues.append("Low maintainability index. Consider improving code structure and documentation.")
            if len([line for line in content.split('\n') if line.strip().startswith('#')]) < len(content.split('\n')) * 0.1:
                issues.append("Low comment ratio. Consider adding more documentation.")
            
            return {
                'score': score,
                'issues': issues
            }
        except:
            return {'score': 50, 'issues': ["Error calculating maintainability metrics"]}

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
                    smells.append(f"Function is too long ({len(current_function)} lines)")
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
            issues.append("Using 'import *' can slow down imports and create namespace issues")
            score -= 20
        
        if 'while True:' in content:
            issues.append("Infinite loop detected. Ensure proper exit conditions")
            score -= 15
        
        if '.copy()' not in content and any(op in content for op in ['list(', 'dict(']):
            issues.append("Consider using .copy() for mutable objects to prevent unintended modifications")
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
                        if not line or line.startswith(('#', '//', '/*', '*', '*/')):
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
            n1 = len(operators) or 1  # Number of unique operators (prevent division by zero)
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