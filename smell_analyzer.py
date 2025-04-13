import ast
import re
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
from enum import Enum

class SmellType(Enum):
    CODE_SMELL = "code_smell"
    DESIGN_SMELL = "design_smell"
    ARCHITECTURAL_SMELL = "architectural_smell"

class SmellSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class Smell:
    type: SmellType
    name: str
    description: str
    severity: SmellSeverity
    location: str
    line_numbers: List[int]
    metrics: Dict[str, Any]
    recommendations: List[str]

class SmellAnalyzer:
    def __init__(self):
        self.code_smells = {
            'long_method': {
                'threshold': 50,  # lines of code
                'description': 'Method is too long and may be hard to understand and maintain'
            },
            'complex_method': {
                'threshold': 15,  # cyclomatic complexity
                'description': 'Method has high cyclomatic complexity'
            },
            'duplicate_code': {
                'threshold': 0.8,  # similarity ratio
                'description': 'Similar code blocks detected that could be refactored'
            },
            'long_parameter_list': {
                'threshold': 5,  # number of parameters
                'description': 'Method has too many parameters'
            },
            'data_clumps': {
                'threshold': 3,  # number of repeated parameter groups
                'description': 'Groups of parameters that are frequently used together'
            },
            'primitive_obsession': {
                'threshold': 3,  # number of primitive types used together
                'description': 'Excessive use of primitive types instead of custom types'
            },
            'feature_envy': {
                'threshold': 0.7,  # ratio of external method calls
                'description': 'Method makes more calls to other objects than to its own'
            },
            'inappropriate_intimacy': {
                'threshold': 0.6,  # ratio of direct field access
                'description': 'Class has too much knowledge about another class'
            },
            'message_chains': {
                'threshold': 3,  # length of method call chain
                'description': 'Long chain of method calls that could be simplified'
            },
            'middle_man': {
                'threshold': 0.8,  # ratio of delegated methods
                'description': 'Class that mostly delegates to another class'
            }
        }
        
        self.design_smells = {
            'god_class': {
                'threshold': 1000,  # lines of code
                'description': 'Class has too many responsibilities'
            },
            'feature_envy': {
                'threshold': 0.7,  # ratio of external method calls
                'description': 'Class makes more calls to other classes than to its own'
            },
            'data_class': {
                'threshold': 0.8,  # ratio of getter/setter methods
                'description': 'Class that only contains data and no behavior'
            },
            'refused_bequest': {
                'threshold': 0.5,  # ratio of unused inherited methods
                'description': 'Subclass doesn\'t use most of the inherited methods'
            },
            'parallel_inheritance_hierarchies': {
                'threshold': 2,  # number of parallel hierarchies
                'description': 'Two inheritance hierarchies that mirror each other'
            },
            'lazy_class': {
                'threshold': 100,  # lines of code
                'description': 'Class that doesn\'t do enough to justify its existence'
            },
            'speculative_generality': {
                'threshold': 0.3,  # ratio of unused parameters
                'description': 'Class or method has unused parameters or functionality'
            },
            'temporary_field': {
                'threshold': 0.4,  # ratio of rarely used fields
                'description': 'Field that is only used in certain circumstances'
            },
            'comments': {
                'threshold': 0.2,  # ratio of commented code
                'description': 'Excessive comments indicating unclear code'
            },
            'primitive_obsession': {
                'threshold': 0.6,  # ratio of primitive types
                'description': 'Excessive use of primitive types instead of objects'
            }
        }
        
        self.architectural_smells = {
            'cyclic_dependency': {
                'threshold': 1,  # number of cycles
                'description': 'Circular dependencies between modules'
            },
            'unstable_dependency': {
                'threshold': 0.7,  # ratio of unstable dependencies
                'description': 'Module depends on unstable components'
            },
            'god_module': {
                'threshold': 0.8,  # ratio of module responsibilities
                'description': 'Module has too many responsibilities'
            },
            'scattered_concern': {
                'threshold': 0.6,  # ratio of scattered functionality
                'description': 'Functionality is scattered across multiple modules'
            },
            'dense_structure': {
                'threshold': 0.7,  # ratio of internal dependencies
                'description': 'Too many dependencies between components'
            }
        }

    def analyze_file(self, file_path: str, content: str) -> List[Smell]:
        """Analyze a single file for code and design smells."""
        smells = []
        
        # Get file extension
        file_ext = file_path.lower().split('.')[-1] if '.' in file_path else ''
        
        # Only analyze Python files for now
        if file_ext != 'py':
            return [Smell(
                type=SmellType.CODE_SMELL,
                name='Unsupported File Type',
                description=f'File type .{file_ext} is not currently supported for smell analysis',
                severity=SmellSeverity.LOW,
                location=file_path,
                line_numbers=[],
                metrics={},
                recommendations=['Convert to Python if possible', 'Use language-specific analyzers']
            )]
        
        try:
            tree = ast.parse(content)
            
            # Analyze code smells
            code_smells = self._analyze_code_smells(tree, file_path)
            if code_smells:
                smells.extend(code_smells)
            
            # Analyze design smells
            design_smells = self._analyze_design_smells(tree, file_path)
            if design_smells:
                smells.extend(design_smells)
            
            # Analyze architectural smells
            arch_smells = self._analyze_architectural_smells(tree, file_path)
            if arch_smells:
                smells.extend(arch_smells)
            
        except SyntaxError as e:
            smells.append(Smell(
                type=SmellType.CODE_SMELL,
                name='Syntax Error',
                description=f'Could not parse file: {str(e)}',
                severity=SmellSeverity.HIGH,
                location=f"{file_path}:{getattr(e, 'lineno', 0)}",
                line_numbers=[getattr(e, 'lineno', 0)],
                metrics={'error_offset': getattr(e, 'offset', 0)},
                recommendations=['Fix the syntax error', 'Validate the code with a linter']
            ))
        except Exception as e:
            smells.append(Smell(
                type=SmellType.CODE_SMELL,
                name='Analysis Error',
                description=f'Error analyzing file: {str(e)}',
                severity=SmellSeverity.MEDIUM,
                location=file_path,
                line_numbers=[],
                metrics={},
                recommendations=['Check file encoding', 'Validate file contents']
            ))
        
        return smells

    def _analyze_code_smells(self, tree: ast.AST, file_path: str) -> List[Smell]:
        """Analyze code smells in the AST."""
        smells = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Check for long method
                if len(node.body) > self.code_smells['long_method']['threshold']:
                    smells.append(Smell(
                        type=SmellType.CODE_SMELL,
                        name='Long Method',
                        description=self.code_smells['long_method']['description'],
                        severity=SmellSeverity.HIGH,
                        location=f"{file_path}:{node.lineno}",
                        line_numbers=[node.lineno],
                        metrics={'lines': len(node.body)},
                        recommendations=[
                            'Extract method to break down the functionality',
                            'Consider using the Strategy pattern for complex logic',
                            'Split the method into smaller, focused methods'
                        ]
                    ))
                
                # Check for long parameter list
                if len(node.args.args) > self.code_smells['long_parameter_list']['threshold']:
                    smells.append(Smell(
                        type=SmellType.CODE_SMELL,
                        name='Long Parameter List',
                        description=self.code_smells['long_parameter_list']['description'],
                        severity=SmellSeverity.MEDIUM,
                        location=f"{file_path}:{node.lineno}",
                        line_numbers=[node.lineno],
                        metrics={'parameters': len(node.args.args)},
                        recommendations=[
                            'Introduce a Parameter Object',
                            'Use Builder pattern for complex parameter sets',
                            'Consider using keyword arguments for clarity'
                        ]
                    ))
                
                # Check for complex method
                complexity = self._calculate_cyclomatic_complexity(node)
                if complexity > self.code_smells['complex_method']['threshold']:
                    smells.append(Smell(
                        type=SmellType.CODE_SMELL,
                        name='Complex Method',
                        description=self.code_smells['complex_method']['description'],
                        severity=SmellSeverity.HIGH,
                        location=f"{file_path}:{node.lineno}",
                        line_numbers=[node.lineno],
                        metrics={'complexity': complexity},
                        recommendations=[
                            'Extract conditional logic into separate methods',
                            'Consider using Strategy pattern for complex branching',
                            'Use early returns to reduce nesting'
                        ]
                    ))
        
        return smells

    def _analyze_design_smells(self, tree: ast.AST, file_path: str) -> List[Smell]:
        """Analyze design smells in the AST."""
        smells = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Check for god class
                if len(node.body) > self.design_smells['god_class']['threshold']:
                    smells.append(Smell(
                        type=SmellType.DESIGN_SMELL,
                        name='God Class',
                        description=self.design_smells['god_class']['description'],
                        severity=SmellSeverity.HIGH,
                        location=f"{file_path}:{node.lineno}",
                        line_numbers=[node.lineno],
                        metrics={'methods': len([n for n in node.body if isinstance(n, ast.FunctionDef)])},
                        recommendations=[
                            'Extract related functionality into separate classes',
                            'Apply Single Responsibility Principle',
                            'Consider using Facade pattern for complex subsystems'
                        ]
                    ))
                
                # Check for data class
                getter_setter_ratio = self._calculate_getter_setter_ratio(node)
                if getter_setter_ratio > self.design_smells['data_class']['threshold']:
                    smells.append(Smell(
                        type=SmellType.DESIGN_SMELL,
                        name='Data Class',
                        description=self.design_smells['data_class']['description'],
                        severity=SmellSeverity.MEDIUM,
                        location=f"{file_path}:{node.lineno}",
                        line_numbers=[node.lineno],
                        metrics={'getter_setter_ratio': getter_setter_ratio},
                        recommendations=[
                            'Move behavior into the class',
                            'Consider using Value Objects',
                            'Apply Tell-Don\'t-Ask principle'
                        ]
                    ))
        
        return smells

    def _analyze_architectural_smells(self, tree: ast.AST, file_path: str) -> List[Smell]:
        """Analyze architectural smells in the AST."""
        smells = []
        
        # This is a simplified version. In a real implementation, you would need to
        # analyze the entire project structure and dependencies
        imports = [node for node in ast.walk(tree) if isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom)]
        
        if len(imports) > 10:  # Arbitrary threshold for demonstration
            smells.append(Smell(
                type=SmellType.ARCHITECTURAL_SMELL,
                name='Unstable Dependencies',
                description=self.architectural_smells['unstable_dependency']['description'],
                severity=SmellSeverity.MEDIUM,
                location=file_path,
                line_numbers=[imp.lineno for imp in imports],
                metrics={'imports': len(imports)},
                recommendations=[
                    'Review and reduce external dependencies',
                    'Consider using dependency injection',
                    'Implement interface segregation'
                ]
            ))
        
        return smells

    def _calculate_cyclomatic_complexity(self, node: ast.AST) -> int:
        """Calculate cyclomatic complexity of a node."""
        complexity = 1
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.Try, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        
        return complexity

    def _calculate_getter_setter_ratio(self, node: ast.ClassDef) -> float:
        """Calculate the ratio of getter/setter methods to total methods."""
        methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]
        if not methods:
            return 0.0
        
        getter_setters = [m for m in methods if m.name.startswith(('get_', 'set_'))]
        return len(getter_setters) / len(methods)

    def get_refactoring_recommendations(self, smell: Smell) -> List[str]:
        """Get specific refactoring recommendations for a smell."""
        # This could be expanded with more sophisticated recommendation logic
        return smell.recommendations

    def get_smell_statistics(self, smells: List[Smell]) -> Dict[str, Any]:
        """Generate statistics about detected smells."""
        stats = {
            'total_smells': len(smells),
            'by_type': {
                'code_smells': len([s for s in smells if s.type == SmellType.CODE_SMELL]),
                'design_smells': len([s for s in smells if s.type == SmellType.DESIGN_SMELL]),
                'architectural_smells': len([s for s in smells if s.type == SmellType.ARCHITECTURAL_SMELL])
            },
            'by_severity': {
                'low': len([s for s in smells if s.severity == SmellSeverity.LOW]),
                'medium': len([s for s in smells if s.severity == SmellSeverity.MEDIUM]),
                'high': len([s for s in smells if s.severity == SmellSeverity.HIGH]),
                'critical': len([s for s in smells if s.severity == SmellSeverity.CRITICAL])
            }
        }
        return stats 