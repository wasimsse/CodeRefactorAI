import sys
import logging
from llama_integration import llama_cpp_manager, logger
from local_models import local_model_manager

# Configure logging
logging.basicConfig(level=logging.INFO)

def test_simple_refactoring():
    # Simple test code to refactor
    test_code = """
def add_numbers(a, b):
    result = a + b
    return result
    """
    
    # Get model config
    model_id = "codellama-7b"
    model_config = local_model_manager.get_model_config(model_id)
    logger.info(f"Using model: {model_id}")
    
    # Load model
    model = llama_cpp_manager.load_model(
        model_id,
        model_config["path"],
        model_config["parameters"]
    )
    
    if not model:
        logger.error("Failed to load model")
        return
    
    # Generate refactoring
    refactored_code = llama_cpp_manager.generate_refactoring(
        model=model,
        code=test_code,
        refactoring_type="Improve readability",
        goals=["Make code more concise"],
        constraints=["Preserve functionality"]
    )
    
    logger.info("\nOriginal code:")
    logger.info(test_code)
    
    if refactored_code:
        logger.info("\nRefactored code:")
        logger.info(refactored_code)
    else:
        logger.error("\nRefactoring failed")

if __name__ == "__main__":
    test_simple_refactoring() 