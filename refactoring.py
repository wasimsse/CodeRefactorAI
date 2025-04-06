import os
import streamlit as st
from code_analyzer import CodeAnalyzer
from config import config

def generate_refactoring_suggestions(file_path, metrics, model, goals, constraints, custom_instructions):
    """Generate refactoring suggestions for the given file."""
    analyzer = CodeAnalyzer({})
    
    # Get the current code content
    with open(file_path, 'r') as f:
        current_code = f.read()
    
    # Prepare the prompt for the AI model
    prompt = prepare_refactoring_prompt(current_code, metrics, goals, constraints, custom_instructions)
    
    # Generate suggestions using the selected model
    suggestions = []
    
    # Example suggestion (replace with actual AI model call)
    suggestion = {
        'title': 'Improve Code Readability',
        'description': 'Refactor the code to improve readability and maintainability.',
        'before': current_code,
        'after': current_code,  # Replace with actual refactored code
        'impact': {
            'complexity_reduction': 15,
            'maintainability_improvement': 20,
            'lines_changed': 10
        }
    }
    suggestions.append(suggestion)
    
    return suggestions

def prepare_refactoring_prompt(code, metrics, goals, constraints, custom_instructions):
    """Prepare the prompt for the AI model."""
    prompt = f"""
    Please refactor the following code according to these requirements:
    
    Goals:
    {', '.join(goals)}
    
    Constraints:
    {', '.join(constraints)}
    
    Custom Instructions:
    {custom_instructions}
    
    Current Code Metrics:
    - Maintainability: {metrics.get('maintainability', 0):.1f}
    - Complexity: {metrics.get('complexity', 0):.1f}
    
    Code:
    {code}
    """
    return prompt

def apply_refactoring_suggestion(file_path, suggestion):
    """Apply a refactoring suggestion to the file."""
    try:
        with open(file_path, 'w') as f:
            f.write(suggestion['after'])
        return True
    except Exception as e:
        st.error(f"Error applying refactoring suggestion: {str(e)}")
        return False

def calculate_impact_metrics(before_metrics, after_metrics):
    """Calculate the impact metrics of a refactoring suggestion."""
    impact = {
        'complexity_reduction': 0,
        'maintainability_improvement': 0,
        'lines_changed': 0
    }
    
    # Calculate complexity reduction
    if 'complexity' in before_metrics and 'complexity' in after_metrics:
        before_complexity = before_metrics['complexity']
        after_complexity = after_metrics['complexity']
        if before_complexity > 0:
            impact['complexity_reduction'] = ((before_complexity - after_complexity) / before_complexity) * 100
    
    # Calculate maintainability improvement
    if 'maintainability' in before_metrics and 'maintainability' in after_metrics:
        before_maintainability = before_metrics['maintainability']
        after_maintainability = after_metrics['maintainability']
        if before_maintainability > 0:
            impact['maintainability_improvement'] = ((after_maintainability - before_maintainability) / before_maintainability) * 100
    
    # Calculate lines changed
    if 'loc' in before_metrics and 'loc' in after_metrics:
        impact['lines_changed'] = abs(after_metrics['loc'] - before_metrics['loc'])
    
    return impact

def validate_refactoring_suggestion(suggestion, original_metrics):
    """Validate a refactoring suggestion."""
    # Check if the suggestion has all required fields
    required_fields = ['title', 'description', 'before', 'after', 'impact']
    for field in required_fields:
        if field not in suggestion:
            return False, f"Missing required field: {field}"
    
    # Check if the impact metrics are valid
    impact = suggestion['impact']
    if not isinstance(impact, dict):
        return False, "Invalid impact metrics format"
    
    required_impact_fields = ['complexity_reduction', 'maintainability_improvement', 'lines_changed']
    for field in required_impact_fields:
        if field not in impact:
            return False, f"Missing impact metric: {field}"
    
    # Check if the code has changed
    if suggestion['before'] == suggestion['after']:
        return False, "No changes made to the code"
    
    return True, "Valid suggestion" 