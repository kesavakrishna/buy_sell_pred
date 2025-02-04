from huggingface_hub import InferenceClient
import os

def query_model(prompt, model_name="google/flan-t5-base", api_token=None):
    """
    Query a language model using HuggingFace's Inference API
    
    Args:
        prompt (str): The input prompt for the model
        model_name (str): Name of the model to use
        api_token (str): HuggingFace API token
        
    Returns:
        str: Model response
    """
    if not api_token:
        raise ValueError("API token is required. Please provide your HuggingFace token.")

    try:
        # Initialize the client with your token
        client = InferenceClient(
            model=model_name,
            token=api_token
        )
        
        # Send the request to the model
        response = client.text_generation(
            prompt,
            max_new_tokens=250,
            temperature=0.7,
            top_k=50,
            top_p=0.95
        )
        
        return response
        
    except Exception as e:
        return f"Error occurred: {str(e)}"

# Usage example
if __name__ == "__main__":
    # Method 1: Set token directly in code (not recommended for production)
    API_TOKEN = "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"  # Replace with your token
    
    # Method 2: Get token from environment variable (recommended)
    # API_TOKEN = os.getenv("HUGGINGFACE_TOKEN")
    
    prompt = "should i invest in btc."
    
    # Using a smaller, more reliable free model
    response = query_model(
        prompt, 
        model_name="google/flan-t5-base",
        api_token=API_TOKEN
    )
    print("LLM Response:\n", response)