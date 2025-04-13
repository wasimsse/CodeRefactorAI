import re
from typing import Dict, List, Tuple

class CSharpParser:
    def __init__(self):
        self.class_pattern = re.compile(r'class\s+(\w+)\s*{')
        self.interface_pattern = re.compile(r'interface\s+(\w+)\s*{')
        self.struct_pattern = re.compile(r'struct\s+(\w+)\s*{')
        self.enum_pattern = re.compile(r'enum\s+(\w+)\s*{')
        self.method_pattern = re.compile(r'(\w+)\s+(\w+)\s*\([^)]*\)\s*{')
        self.property_pattern = re.compile(r'(\w+)\s+(\w+)\s*{\s*get;\s*set;\s*}')
        self.using_pattern = re.compile(r'using\s+([^;]+);')
        self.namespace_pattern = re.compile(r'namespace\s+(\w+(?:\.\w+)*)\s*{')
        self.attribute_pattern = re.compile(r'\[([^\]]+)\]')

    def analyze_file(self, content: str) -> Dict:
        """Analyze C# code and return metrics."""
        metrics = {
            'classes': self._count_classes(content),
            'interfaces': self._count_interfaces(content),
            'structs': self._count_structs(content),
            'enums': self._count_enums(content),
            'methods': self._count_methods(content),
            'properties': self._count_properties(content),
            'using_statements': self._count_using_statements(content),
            'namespaces': self._count_namespaces(content),
            'attributes': self._count_attributes(content),
            'complexity': self._calculate_complexity(content)
        }
        return metrics

    def _count_classes(self, content: str) -> int:
        """Count the number of class definitions."""
        return len(self.class_pattern.findall(content))

    def _count_interfaces(self, content: str) -> int:
        """Count the number of interface definitions."""
        return len(self.interface_pattern.findall(content))

    def _count_structs(self, content: str) -> int:
        """Count the number of struct definitions."""
        return len(self.struct_pattern.findall(content))

    def _count_enums(self, content: str) -> int:
        """Count the number of enum definitions."""
        return len(self.enum_pattern.findall(content))

    def _count_methods(self, content: str) -> int:
        """Count the number of method definitions."""
        return len(self.method_pattern.findall(content))

    def _count_properties(self, content: str) -> int:
        """Count the number of property definitions."""
        return len(self.property_pattern.findall(content))

    def _count_using_statements(self, content: str) -> int:
        """Count the number of using statements."""
        return len(self.using_pattern.findall(content))

    def _count_namespaces(self, content: str) -> int:
        """Count the number of namespace definitions."""
        return len(self.namespace_pattern.findall(content))

    def _count_attributes(self, content: str) -> int:
        """Count the number of attribute definitions."""
        return len(self.attribute_pattern.findall(content))

    def _calculate_complexity(self, content: str) -> int:
        """Calculate cyclomatic complexity of the code."""
        complexity = 1  # Base complexity
        
        # Count control structures
        control_structures = [
            r'if\s*\([^)]*\)',
            r'else\s*if\s*\([^)]*\)',
            r'else',
            r'for\s*\([^)]*\)',
            r'foreach\s*\([^)]*\)',
            r'while\s*\([^)]*\)',
            r'do\s*{',
            r'catch\s*\([^)]*\)',
            r'&&',
            r'\|\|',
            r'\?',
            r':',
            r'case\s+[^:]+:',
            r'default:',
            r'throw\s+new',
            r'return\s+[^;]+;'
        ]
        
        for pattern in control_structures:
            complexity += len(re.findall(pattern, content))
        
        return complexity

    def get_dependencies(self, content: str) -> List[str]:
        """Extract dependencies from using statements."""
        return self.using_pattern.findall(content)

    def get_class_hierarchy(self, content: str) -> List[Tuple[str, str]]:
        """Extract class inheritance relationships."""
        inheritance_pattern = re.compile(r'class\s+(\w+)\s*:\s*(\w+(?:,\s*\w+)*)')
        return inheritance_pattern.findall(content)

    def get_method_signatures(self, content: str) -> List[str]:
        """Extract method signatures."""
        return self.method_pattern.findall(content)

    def get_property_signatures(self, content: str) -> List[str]:
        """Extract property signatures."""
        return self.property_pattern.findall(content) 