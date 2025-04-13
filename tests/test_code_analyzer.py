import pytest
from code_analyzer import CodeAnalyzer

def test_code_analyzer_initialization():
    config = {
        'complexity_threshold': 10,
        'maintainability_threshold': 20,
        'min_comment_ratio': 0.1
    }
    analyzer = CodeAnalyzer(config)
    assert analyzer.config == config

def test_analyze_code():
    analyzer = CodeAnalyzer({})
    test_code = '''
def simple_function():
    # This is a test function
    return True
'''
    result = analyzer.analyze_code(test_code)
    assert isinstance(result, dict)
    assert 'complexity' in result
    assert 'maintainability' in result
    assert 'raw_metrics' in result

def test_calculate_complexity():
    analyzer = CodeAnalyzer({})
    test_code = '''
def complex_function(x):
    if x > 0:
        if x < 10:
            return True
    return False
'''
    result = analyzer.analyze_code(test_code)
    assert result['complexity']['score'] > 0

def test_empty_code():
    analyzer = CodeAnalyzer({})
    result = analyzer.analyze_code('')
    assert isinstance(result, dict)
    assert result['raw_metrics']['loc'] == 0 