import re
from typing import Dict, List, Tuple

class CppParser:
    def __init__(self):
        self.class_pattern = re.compile(r'class\s+(\w+)\s*{')
        self.function_pattern = re.compile(r'(\w+)\s+(\w+)\s*\([^)]*\)\s*{')
        self.include_pattern = re.compile(r'#include\s+[<"]([^>"]+)[>"]')
        self.namespace_pattern = re.compile(r'namespace\s+(\w+)\s*{')
        self.template_pattern = re.compile(r'template\s*<[^>]+>')

    def analyze_file(self, content: str) -> Dict:
        """Analyze C++ code and return metrics."""
        metrics = {
            'classes': self._count_classes(content),
            'functions': self._count_functions(content),
            'includes': self._count_includes(content),
            'namespaces': self._count_namespaces(content),
            'templates': self._count_templates(content),
            'complexity': self._calculate_complexity(content)
        }
        return metrics

    def _count_classes(self, content: str) -> int:
        """Count the number of class definitions."""
        return len(self.class_pattern.findall(content))

    def _count_functions(self, content: str) -> int:
        """Count the number of function definitions."""
        return len(self.function_pattern.findall(content))

    def _count_includes(self, content: str) -> int:
        """Count the number of include statements."""
        return len(self.include_pattern.findall(content))

    def _count_namespaces(self, content: str) -> int:
        """Count the number of namespace definitions."""
        return len(self.namespace_pattern.findall(content))

    def _count_templates(self, content: str) -> int:
        """Count the number of template definitions."""
        return len(self.template_pattern.findall(content))

    def _calculate_complexity(self, content: str) -> int:
        """Calculate cyclomatic complexity of the code."""
        complexity = 1  # Base complexity
        
        # Count control structures
        control_structures = [
            r'if\s*\([^)]*\)',
            r'else\s*if\s*\([^)]*\)',
            r'else',
            r'for\s*\([^)]*\)',
            r'while\s*\([^)]*\)',
            r'do\s*{',
            r'catch\s*\([^)]*\)',
            r'&&',
            r'\|\|',
            r'\?',
            r':',
            r'case\s+[^:]+:',
            r'default:'
        ]
        
        for pattern in control_structures:
            complexity += len(re.findall(pattern, content))
        
        return complexity

    def get_dependencies(self, content: str) -> List[str]:
        """Extract dependencies from include statements."""
        return self.include_pattern.findall(content)

    def get_class_hierarchy(self, content: str) -> List[Tuple[str, str]]:
        """Extract class inheritance relationships."""
        inheritance_pattern = re.compile(r'class\s+(\w+)\s*:\s*(?:public|private|protected)\s+(\w+)')
        return inheritance_pattern.findall(content)

    def get_function_signatures(self, content: str) -> List[str]:
        """Extract function signatures."""
        return self.function_pattern.findall(content) 