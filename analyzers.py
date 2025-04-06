import re
import ast
from typing import Dict, List, Any
import javalang
import esprima

class PythonAnalyzer:
    def analyze(self, content: str) -> Dict[str, Any]:
        """Analyze Python code and return comprehensive metrics."""
        metrics = {
            'raw_metrics': {
                'loc': 0,
                'sloc': 0,
                'comments': 0,
                'classes': 0,
                'methods': 0,
                'functions': 0,
                'imports': 0,
                'packages': 0
            },
            'complexity': {
                'score': 0,
                'issues': []
            },
            'maintainability': {
                'score': 0,
                'issues': []
            },
            'code_smells': [],
            'refactoring_opportunities': [],
            'dependencies': [],
            'issues': []
        }

        try:
            tree = ast.parse(content)
            lines = content.splitlines()
            
            # Basic metrics
            metrics['raw_metrics']['loc'] = len(lines)
            metrics['raw_metrics']['sloc'] = len([l for l in lines if l.strip()])
            
            # Count comments
            metrics['raw_metrics']['comments'] = len([l for l in lines if l.strip().startswith('#')])
            
            # Analyze imports
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    metrics['raw_metrics']['imports'] += len(node.names)
                    metrics['dependencies'].extend(n.name for n in node.names)
                elif isinstance(node, ast.ImportFrom):
                    metrics['raw_metrics']['imports'] += len(node.names)
                    metrics['dependencies'].append(f"{node.module}")
            
            # Count classes and methods
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    metrics['raw_metrics']['classes'] += 1
                    
                    # Check class size
                    class_body = len(node.body)
                    if class_body > 300:
                        metrics['code_smells'].append(f"Large class '{node.name}' ({class_body} lines)")
                        metrics['refactoring_opportunities'].append(f"Consider splitting class '{node.name}' into smaller classes")
                
                elif isinstance(node, ast.FunctionDef):
                    if isinstance(node.parent, ast.ClassDef):
                        metrics['raw_metrics']['methods'] += 1
                    else:
                        metrics['raw_metrics']['functions'] += 1
                    
                    # Check function complexity
                    func_complexity = self._calculate_function_complexity(node)
                    if func_complexity > 10:
                        metrics['code_smells'].append(f"Complex function '{node.name}' (complexity: {func_complexity})")
                        metrics['refactoring_opportunities'].append(f"Consider breaking down function '{node.name}' into smaller functions")
            
            # Calculate overall complexity
            metrics['complexity']['score'] = self._calculate_complexity(tree)
            
            # Calculate maintainability
            metrics['maintainability']['score'] = self._calculate_maintainability(metrics['raw_metrics'])
            
            return metrics
        except Exception as e:
            metrics['issues'].append(f"Error analyzing Python code: {str(e)}")
            return metrics

    def _calculate_function_complexity(self, node: ast.AST) -> int:
        """Calculate cyclomatic complexity of a function."""
        complexity = 1
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        return complexity

    def _calculate_complexity(self, tree: ast.AST) -> float:
        """Calculate overall code complexity score."""
        total_complexity = 0
        num_functions = 0
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                total_complexity += self._calculate_function_complexity(node)
                num_functions += 1
        
        avg_complexity = total_complexity / max(num_functions, 1)
        return max(0, min(100, 100 - (avg_complexity * 5)))

    def _calculate_maintainability(self, metrics: Dict) -> float:
        """Calculate maintainability index."""
        score = 100
        
        # Reduce score based on various metrics
        if metrics['loc'] > 1000:
            score -= 20
        if metrics['comments'] / max(metrics['loc'], 1) < 0.1:
            score -= 20
        if metrics['classes'] > 10:
            score -= 10
        if metrics['methods'] + metrics['functions'] > 20:
            score -= 10
        
        return max(0, min(100, score))

class JavaAnalyzer:
    def analyze(self, content: str) -> Dict[str, Any]:
        """Analyze Java code and return comprehensive metrics."""
        metrics = {
            'raw_metrics': {
                'loc': 0,
                'sloc': 0,
                'comments': 0,
                'classes': 0,
                'methods': 0,
                'functions': 0,
                'imports': 0,
                'packages': 0
            },
            'complexity': {
                'score': 0,
                'issues': []
            },
            'maintainability': {
                'score': 0,
                'issues': []
            },
            'code_smells': [],
            'refactoring_opportunities': [],
            'dependencies': [],
            'issues': []
        }

        try:
            tree = javalang.parse.parse(content)
            lines = content.splitlines()
            
            # Basic metrics
            metrics['raw_metrics']['loc'] = len(lines)
            metrics['raw_metrics']['sloc'] = len([l for l in lines if l.strip()])
            
            # Count comments
            single_comments = len([l for l in lines if l.strip().startswith('//')])
            multi_comments = len(re.findall(r'/\*.*?\*/', content, re.DOTALL))
            metrics['raw_metrics']['comments'] = single_comments + multi_comments
            
            # Analyze imports and packages
            imports = list(tree.filter(javalang.tree.Import))
            metrics['raw_metrics']['imports'] = len(imports)
            metrics['dependencies'].extend(imp.path for imp in imports)
            
            packages = list(tree.filter(javalang.tree.PackageDeclaration))
            metrics['raw_metrics']['packages'] = len(packages)
            
            # Count classes and methods
            classes = list(tree.filter(javalang.tree.ClassDeclaration))
            metrics['raw_metrics']['classes'] = len(classes)
            
            methods = list(tree.filter(javalang.tree.MethodDeclaration))
            metrics['raw_metrics']['methods'] = len(methods)
            
            # Analyze class complexity
            for class_decl in classes:
                class_methods = len(class_decl.methods)
                if class_methods > 20:
                    metrics['code_smells'].append(f"Large class '{class_decl.name}' ({class_methods} methods)")
                    metrics['refactoring_opportunities'].append(f"Consider splitting class '{class_decl.name}' into smaller classes")
            
            # Analyze method complexity
            for method in methods:
                method_complexity = self._calculate_method_complexity(method)
                if method_complexity > 10:
                    metrics['code_smells'].append(f"Complex method '{method.name}' (complexity: {method_complexity})")
                    metrics['refactoring_opportunities'].append(f"Consider breaking down method '{method.name}' into smaller methods")
            
            # Calculate overall complexity
            metrics['complexity']['score'] = self._calculate_complexity(tree)
            
            # Calculate maintainability
            metrics['maintainability']['score'] = self._calculate_maintainability(metrics['raw_metrics'])
            
            return metrics
        except Exception as e:
            metrics['issues'].append(f"Error analyzing Java code: {str(e)}")
            return metrics

    def _calculate_method_complexity(self, method) -> int:
        """Calculate cyclomatic complexity of a method."""
        complexity = 1
        
        # Count control flow statements
        for path, node in method.filter(javalang.tree.IfStatement):
            complexity += 1
        for path, node in method.filter(javalang.tree.WhileStatement):
            complexity += 1
        for path, node in method.filter(javalang.tree.ForStatement):
            complexity += 1
        for path, node in method.filter(javalang.tree.SwitchStatement):
            complexity += len(node.cases)
        
        return complexity

    def _calculate_complexity(self, tree) -> float:
        """Calculate overall code complexity score."""
        total_complexity = 0
        methods = list(tree.filter(javalang.tree.MethodDeclaration))
        
        for method in methods:
            total_complexity += self._calculate_method_complexity(method)
        
        avg_complexity = total_complexity / max(len(methods), 1)
        return max(0, min(100, 100 - (avg_complexity * 5)))

    def _calculate_maintainability(self, metrics: Dict) -> float:
        """Calculate maintainability index."""
        score = 100
        
        # Reduce score based on various metrics
        if metrics['loc'] > 1000:
            score -= 20
        if metrics['comments'] / max(metrics['loc'], 1) < 0.1:
            score -= 20
        if metrics['classes'] > 10:
            score -= 10
        if metrics['methods'] > 20:
            score -= 10
        
        return max(0, min(100, score))

class JavaScriptAnalyzer:
    def analyze(self, content: str) -> Dict[str, Any]:
        """Analyze JavaScript code and return comprehensive metrics."""
        metrics = {
            'raw_metrics': {
                'loc': 0,
                'sloc': 0,
                'comments': 0,
                'classes': 0,
                'methods': 0,
                'functions': 0,
                'imports': 0,
                'packages': 0
            },
            'complexity': {
                'score': 0,
                'issues': []
            },
            'maintainability': {
                'score': 0,
                'issues': []
            },
            'code_smells': [],
            'refactoring_opportunities': [],
            'dependencies': [],
            'issues': []
        }

        try:
            tree = esprima.parseScript(content, {'comment': True, 'loc': True})
            lines = content.splitlines()
            
            # Basic metrics
            metrics['raw_metrics']['loc'] = len(lines)
            metrics['raw_metrics']['sloc'] = len([l for l in lines if l.strip()])
            
            # Count comments
            metrics['raw_metrics']['comments'] = len(tree.comments)
            
            # Analyze imports
            import_count = len(re.findall(r'(import|require)\s*\(.*?\)', content))
            metrics['raw_metrics']['imports'] = import_count
            
            # Count functions and classes
            for node in self._walk_ast(tree.body):
                if node.type == 'FunctionDeclaration':
                    metrics['raw_metrics']['functions'] += 1
                    
                    # Check function complexity
                    func_complexity = self._calculate_function_complexity(node)
                    if func_complexity > 10:
                        metrics['code_smells'].append(f"Complex function (complexity: {func_complexity})")
                        metrics['refactoring_opportunities'].append("Consider breaking down complex function into smaller functions")
                
                elif node.type == 'ClassDeclaration':
                    metrics['raw_metrics']['classes'] += 1
                    
                    # Check class size
                    class_methods = len([m for m in node.body.body if m.type == 'MethodDefinition'])
                    if class_methods > 10:
                        metrics['code_smells'].append(f"Large class with {class_methods} methods")
                        metrics['refactoring_opportunities'].append("Consider splitting large class into smaller classes")
            
            # Calculate overall complexity
            metrics['complexity']['score'] = self._calculate_complexity(tree)
            
            # Calculate maintainability
            metrics['maintainability']['score'] = self._calculate_maintainability(metrics['raw_metrics'])
            
            return metrics
        except Exception as e:
            metrics['issues'].append(f"Error analyzing JavaScript code: {str(e)}")
            return metrics

    def _walk_ast(self, nodes):
        """Walk through AST nodes."""
        for node in nodes:
            yield node
            if hasattr(node, 'body'):
                if isinstance(node.body, list):
                    yield from self._walk_ast(node.body)
                else:
                    yield from self._walk_ast([node.body])

    def _calculate_function_complexity(self, node) -> int:
        """Calculate cyclomatic complexity of a function."""
        complexity = 1
        
        for child in self._walk_ast([node]):
            if child.type in ['IfStatement', 'WhileStatement', 'ForStatement', 'SwitchCase']:
                complexity += 1
            elif child.type == 'LogicalExpression':
                complexity += 1
        
        return complexity

    def _calculate_complexity(self, tree) -> float:
        """Calculate overall code complexity score."""
        total_complexity = 0
        num_functions = 0
        
        for node in self._walk_ast(tree.body):
            if node.type == 'FunctionDeclaration':
                total_complexity += self._calculate_function_complexity(node)
                num_functions += 1
        
        avg_complexity = total_complexity / max(num_functions, 1)
        return max(0, min(100, 100 - (avg_complexity * 5)))

    def _calculate_maintainability(self, metrics: Dict) -> float:
        """Calculate maintainability index."""
        score = 100
        
        # Reduce score based on various metrics
        if metrics['loc'] > 1000:
            score -= 20
        if metrics['comments'] / max(metrics['loc'], 1) < 0.1:
            score -= 20
        if metrics['classes'] > 10:
            score -= 10
        if metrics['functions'] > 20:
            score -= 10
        
        return max(0, min(100, score)) 