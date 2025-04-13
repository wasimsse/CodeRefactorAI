import ast
import javalang
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from enum import Enum
import re
import streamlit as st
from llama_integration import run_local_model_refactoring, llama_cpp_manager
from local_models import local_model_manager

class RefactoringType(Enum):
    EXTRACT_METHOD = "Extract Method"
    RENAME_VARIABLE = "Rename Variable"
    EXTRACT_CLASS = "Extract Class"
    MOVE_METHOD = "Move Method"
    INLINE_METHOD = "Inline Method"
    INTRODUCE_PARAMETER = "Introduce Parameter"
    ENCAPSULATE_FIELD = "Encapsulate Field"
    REPLACE_CONDITIONAL = "Replace Conditional"
    INTRODUCE_INTERFACE = "Introduce Interface"
    REMOVE_DUPLICATION = "Remove Duplication"

@dataclass
class RefactoringSuggestion:
    type: RefactoringType
    title: str
    description: str
    before_code: str
    after_code: str
    start_line: int
    end_line: int
    confidence: float
    impact: Dict[str, float]
    prerequisites: List[str]
    risks: List[str]

class RefactoringEngine:
    def __init__(self):
        self.model_manager = local_model_manager
        self.llm_manager = llama_cpp_manager
        self.patterns = {
            'long_method': (
                r'(public|private|protected)\s+\w+\s+\w+\s*\([^)]*\)\s*\{(?:[^}]*\}){50,}',
                "Method is too long and may need to be split"
            ),
            'complex_condition': (
                r'if\s*\([^)]+(?:&&|\|\|)[^)]+\)',
                "Complex condition that could be simplified"
            ),
            'duplicate_code': (
                r'(.{50,})\1+',
                "Possible code duplication detected"
            ),
            'magic_number': (
                r'\b\d{4,}\b(?!\s*[\'"])',
                "Magic number that should be converted to a named constant"
            ),
            'long_parameter_list': (
                r'(public|private|protected)\s+\w+\s+\w+\s*\([^)]{80,}\)',
                "Method has too many parameters"
            )
        }

    def perform_refactoring(self,
                          code: str,
                          refactoring_type: str,
                          goals: List[str],
                          constraints: List[str],
                          model_id: Optional[str] = None) -> Optional[str]:
        """
        Perform code refactoring using the specified model
        """
        # If no model specified, use the first available model
        if not model_id:
            available_models = self.model_manager.get_available_models()
            if not available_models:
                st.error("No models available for refactoring")
                return None
            model_id = available_models[0]
        
        # Get model configuration
        model_config = self.model_manager.get_model_config(model_id)
        if not model_config:
            st.error(f"Model configuration not found: {model_id}")
            return None
            
        # Check if model supports code refactoring
        if "capabilities" not in model_config or "code_refactoring" not in model_config["capabilities"]:
            st.error(f"Model {model_id} does not support code refactoring")
            return None
            
        # Perform refactoring using the local model
        refactored_code = run_local_model_refactoring(
            model_id=model_id,
            code=code,
            refactoring_type=refactoring_type,
            goals=goals,
            constraints=constraints
        )
        
        return refactored_code
        
    def analyze_code_quality(self, code: str, model_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Analyze code quality using the specified model
        """
        # If no model specified, use the first available model
        if not model_id:
            available_models = self.model_manager.get_available_models()
            if not available_models:
                st.error("No models available for code analysis")
                return None
            model_id = available_models[0]
        
        # Get model configuration
        model_config = self.model_manager.get_model_config(model_id)
        if not model_config:
            st.error(f"Model configuration not found: {model_id}")
            return None
            
        # Check if model supports code analysis
        if "capabilities" not in model_config or "code_analysis" not in model_config["capabilities"]:
            st.error(f"Model {model_id} does not support code analysis")
            return None
            
        try:
            # Load or get cached model
            model = self.llm_manager.load_model(
                model_id,
                model_config["path"],
                model_config.get("parameters", {})
            )
            
            if not model:
                return None
                
            # Analyze code quality
            return self.llm_manager.analyze_code_quality(model, code)
            
        except Exception as e:
            st.error(f"Error analyzing code: {str(e)}")
            return None
            
    def get_available_models(self) -> List[str]:
        """Get list of available models that support code refactoring"""
        all_models = self.model_manager.get_available_models()
        return [
            model_id for model_id in all_models
            if "capabilities" in self.model_manager.get_model_config(model_id)
            and "code_refactoring" in self.model_manager.get_model_config(model_id)["capabilities"]
        ]

    def analyze_code(self, code: str, filename: str) -> List[RefactoringSuggestion]:
        """Analyze code and return refactoring suggestions."""
        suggestions = []
        
        # Determine file type
        if filename.endswith('.java'):
            return self._analyze_java_code(code)
        elif filename.endswith('.py'):
            return self._analyze_python_code(code)
        else:
            return []  # Unsupported file type

    def _analyze_java_code(self, code: str) -> List[RefactoringSuggestion]:
        """Analyze Java code for refactoring opportunities."""
        suggestions = []
        
        try:
            # Parse Java code
            tree = javalang.parse.parse(code)
            
            # Analyze classes
            for path, node in tree.filter(javalang.tree.ClassDeclaration):
                suggestions.extend(self._analyze_java_class(node, code))
            
            # Analyze methods
            for path, node in tree.filter(javalang.tree.MethodDeclaration):
                suggestions.extend(self._analyze_java_method(node, code))
            
            # Pattern-based analysis
            for pattern_name, (pattern, message) in self.patterns.items():
                matches = re.finditer(pattern, code, re.MULTILINE)
                for match in matches:
                    suggestion = self._create_suggestion_from_pattern(
                        pattern_name, message, match, code
                    )
                    if suggestion:
                        suggestions.append(suggestion)
            
            return suggestions
            
        except Exception as e:
            # Return basic suggestions if parsing fails
            return self._analyze_java_basic(code)

    def _analyze_java_class(self, node, code: str) -> List[RefactoringSuggestion]:
        """Analyze a Java class for refactoring opportunities."""
        suggestions = []
        
        # Check class size
        methods = [m for m in node.methods]
        fields = [f for f in node.fields]
        
        if len(methods) > 10 or len(fields) > 10:
            suggestions.append(
                RefactoringSuggestion(
                    type=RefactoringType.EXTRACT_CLASS,
                    title=f"Large Class: {node.name}",
                    description=f"Class '{node.name}' has {len(methods)} methods and {len(fields)} fields. Consider splitting it into smaller classes.",
                    before_code=self._get_node_source(node, code),
                    after_code="",
                    start_line=node.position.line if node.position else 0,
                    end_line=node.position.line + 10 if node.position else 10,
                    confidence=0.8,
                    impact={
                        'maintainability': 0.7,
                        'readability': 0.8,
                        'complexity': -0.6
                    },
                    prerequisites=["Identify related methods and fields"],
                    risks=["Breaking changes", "Need to update references"]
                )
            )
        
        return suggestions

    def _analyze_java_method(self, node, code: str) -> List[RefactoringSuggestion]:
        """Analyze a Java method for refactoring opportunities."""
        suggestions = []
        
        # Check method length
        method_body = self._get_node_source(node, code)
        lines = method_body.split('\n')
        
        if len(lines) > 30:
            suggestions.append(
                RefactoringSuggestion(
                    type=RefactoringType.EXTRACT_METHOD,
                    title=f"Long Method: {node.name}",
                    description=f"Method '{node.name}' is {len(lines)} lines long. Consider breaking it into smaller methods.",
                    before_code=method_body,
                    after_code="",
                    start_line=node.position.line if node.position else 0,
                    end_line=node.position.line + len(lines) if node.position else len(lines),
                    confidence=0.9,
                    impact={
                        'maintainability': 0.8,
                        'readability': 0.7,
                        'complexity': -0.5
                    },
                    prerequisites=["Identify logical segments"],
                    risks=["Method visibility", "Parameter passing"]
                )
            )
        
        # Check parameter count
        if len(node.parameters) > 5:
            suggestions.append(
                RefactoringSuggestion(
                    type=RefactoringType.INTRODUCE_PARAMETER,
                    title=f"Too Many Parameters: {node.name}",
                    description=f"Method '{node.name}' has {len(node.parameters)} parameters. Consider introducing a parameter object.",
                    before_code=method_body,
                    after_code="",
                    start_line=node.position.line if node.position else 0,
                    end_line=node.position.line + 1 if node.position else 1,
                    confidence=0.7,
                    impact={
                        'maintainability': 0.6,
                        'readability': 0.8,
                        'complexity': -0.4
                    },
                    prerequisites=["Create parameter class"],
                    risks=["Breaking change"]
                )
            )
        
        return suggestions

    def _analyze_java_basic(self, code: str) -> List[RefactoringSuggestion]:
        """Perform basic Java analysis when parsing fails."""
        suggestions = []
        lines = code.split('\n')
        
        # Look for long methods using regex
        method_pattern = r'(public|private|protected)\s+[\w<>[\]]+\s+\w+\s*\([^)]*\)\s*\{'
        current_method = None
        method_start = 0
        method_lines = 0
        
        for i, line in enumerate(lines):
            if re.search(method_pattern, line):
                if current_method and method_lines > 30:
                    suggestions.append(
                        RefactoringSuggestion(
                            type=RefactoringType.EXTRACT_METHOD,
                            title=f"Long Method",
                            description=f"Method is {method_lines} lines long. Consider breaking it into smaller methods.",
                            before_code='\n'.join(lines[method_start:i]),
                            after_code="",
                            start_line=method_start + 1,
                            end_line=i + 1,
                            confidence=0.6,
                            impact={
                                'maintainability': 0.5,
                                'readability': 0.6,
                                'complexity': -0.4
                            },
                            prerequisites=["Review method logic"],
                            risks=["Basic analysis only"]
                        )
                    )
                current_method = line
                method_start = i
                method_lines = 0
            elif current_method:
                method_lines += 1
        
        return suggestions

    def _get_node_source(self, node, code: str) -> str:
        """Get source code for a Java AST node."""
        if hasattr(node, 'position') and node.position:
            start_line = node.position.line - 1
            lines = code.split('\n')
            # Find the end of the node by matching braces
            brace_count = 0
            end_line = start_line
            for i in range(start_line, len(lines)):
                brace_count += lines[i].count('{') - lines[i].count('}')
                if brace_count == 0:
                    end_line = i + 1
                    break
            return '\n'.join(lines[start_line:end_line])
        return ""

    def _analyze_python_code(self, code: str) -> List[RefactoringSuggestion]:
        """Analyze Python code for refactoring opportunities."""
        suggestions = []
        
        # Parse the code into an AST
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return []  # Return empty list if code cannot be parsed
        
        # Analyze methods
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                suggestions.extend(self._analyze_method(node, code))
            elif isinstance(node, ast.ClassDef):
                suggestions.extend(self._analyze_class(node, code))
        
        # Pattern-based analysis
        for pattern_name, (pattern, message) in self.patterns.items():
            matches = re.finditer(pattern, code, re.MULTILINE)
            for match in matches:
                suggestion = self._create_suggestion_from_pattern(
                    pattern_name, message, match, code
                )
                if suggestion:
                    suggestions.append(suggestion)
        
        return suggestions

    def _analyze_method(self, node: ast.FunctionDef, code: str) -> List[RefactoringSuggestion]:
        """Analyze a method for potential refactoring opportunities."""
        suggestions = []
        
        # Check method length
        method_lines = len(node.body)
        if method_lines > 20:  # Threshold for long methods
            suggestions.append(
                RefactoringSuggestion(
                    type=RefactoringType.EXTRACT_METHOD,
                    title=f"Long Method: {node.name}",
                    description=f"Method '{node.name}' is {method_lines} lines long. Consider breaking it into smaller methods.",
                    before_code=self._get_node_source(node, code),
                    after_code="",  # To be generated
                    start_line=node.lineno,
                    end_line=node.end_lineno or node.lineno,
                    confidence=0.8,
                    impact={
                        'maintainability': 0.7,
                        'readability': 0.8,
                        'complexity': -0.6
                    },
                    prerequisites=["No side effects in extracted code"],
                    risks=["May affect method visibility", "Could impact performance"]
                )
            )
        
        # Check parameter count
        if len(node.args.args) > 5:  # Threshold for too many parameters
            suggestions.append(
                RefactoringSuggestion(
                    type=RefactoringType.INTRODUCE_PARAMETER,
                    title=f"Too Many Parameters: {node.name}",
                    description=f"Method '{node.name}' has {len(node.args.args)} parameters. Consider introducing a parameter object.",
                    before_code=self._get_node_source(node, code),
                    after_code="",  # To be generated
                    start_line=node.lineno,
                    end_line=node.end_lineno or node.lineno,
                    confidence=0.7,
                    impact={
                        'maintainability': 0.6,
                        'readability': 0.7,
                        'complexity': -0.4
                    },
                    prerequisites=["Create new parameter class/dataclass"],
                    risks=["Breaking change for method callers"]
                )
            )
        
        return suggestions

    def _analyze_class(self, node: ast.ClassDef, code: str) -> List[RefactoringSuggestion]:
        """Analyze a class for potential refactoring opportunities."""
        suggestions = []
        
        # Count methods and attributes
        method_count = len([n for n in node.body if isinstance(n, ast.FunctionDef)])
        attr_count = len([n for n in node.body if isinstance(n, ast.Assign)])
        
        # Check for God Class
        if method_count > 10 or attr_count > 10:  # Thresholds for God Class
            suggestions.append(
                RefactoringSuggestion(
                    type=RefactoringType.EXTRACT_CLASS,
                    title=f"God Class: {node.name}",
                    description=f"Class '{node.name}' has {method_count} methods and {attr_count} attributes. Consider splitting it into smaller classes.",
                    before_code=self._get_node_source(node, code),
                    after_code="",  # To be generated
                    start_line=node.lineno,
                    end_line=node.end_lineno or node.lineno,
                    confidence=0.9,
                    impact={
                        'maintainability': 0.9,
                        'readability': 0.8,
                        'complexity': -0.7
                    },
                    prerequisites=["Identify related methods and attributes"],
                    risks=["Major restructuring required", "Could affect dependent code"]
                )
            )
        
        return suggestions

    def _create_suggestion_from_pattern(
        self, pattern_name: str, message: str, match: re.Match, code: str
    ) -> Optional[RefactoringSuggestion]:
        """Create a refactoring suggestion from a pattern match."""
        start_pos = match.start()
        end_pos = match.end()
        
        # Get line numbers
        start_line = code.count('\n', 0, start_pos) + 1
        end_line = code.count('\n', 0, end_pos) + 1
        
        # Map pattern to refactoring type
        refactoring_type = {
            'long_method': RefactoringType.EXTRACT_METHOD,
            'complex_condition': RefactoringType.REPLACE_CONDITIONAL,
            'duplicate_code': RefactoringType.REMOVE_DUPLICATION,
            'magic_number': RefactoringType.RENAME_VARIABLE,
            'long_parameter_list': RefactoringType.INTRODUCE_PARAMETER
        }.get(pattern_name)
        
        if not refactoring_type:
            return None
        
        return RefactoringSuggestion(
            type=refactoring_type,
            title=f"{refactoring_type.value} Opportunity",
            description=message,
            before_code=match.group(0),
            after_code="",  # To be generated
            start_line=start_line,
            end_line=end_line,
            confidence=0.7,
            impact={
                'maintainability': 0.6,
                'readability': 0.7,
                'complexity': -0.5
            },
            prerequisites=[],
            risks=["May require additional testing"]
        )

    def _get_node_source(self, node: ast.AST, code: str) -> str:
        """Get source code for an AST node."""
        start_pos = node.lineno
        end_pos = node.end_lineno or node.lineno
        lines = code.split('\n')
        return '\n'.join(lines[start_pos - 1:end_pos])

# Create singleton instance
refactoring_engine = RefactoringEngine() 