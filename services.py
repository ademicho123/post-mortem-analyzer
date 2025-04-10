import openai
import json
import os
import re
import streamlit as st
import logging
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from openai import OpenAIError, APIConnectionError, APIError, RateLimitError, BadRequestError

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get API key from Streamlit secrets or from environment variable (for local development)
def get_api_key():
    # First try to get from Streamlit secrets
    if hasattr(st, 'secrets') and 'OPENAI_API_KEY' in st.secrets:
        return st.secrets['OPENAI_API_KEY']
    # Fall back to environment variable (for local development)
    elif os.getenv("OPENAI_API_KEY"):
        return os.getenv("OPENAI_API_KEY")
    else:
        raise ValueError("No OpenAI API key found in Streamlit secrets or environment variables")

# Initialize OpenAI client
client = openai.OpenAI(api_key=get_api_key())

# Get model from Streamlit secrets or use default
def get_model():
    if hasattr(st, 'secrets') and 'OPENAI_MODEL' in st.secrets:
        return st.secrets['OPENAI_MODEL']
    elif os.getenv("OPENAI_MODEL"):
        return os.getenv("OPENAI_MODEL")
    else:
        return "gpt-3.5-turbo"  # Default model

MODEL = get_model()

def create_llm_prompt(lines):
    """Create a prompt that explicitly asks for structured JSON"""
    return f"""Analyze these post-mortem lessons and return ONLY a strict JSON object with exactly this structure:

{{
    "unrecoverable_lines": [
        "line 1 with no meaning",
        "line 2 with no meaning"
    ],
    "common_ideas": [
        {{
            "title": "specific theme title",
            "overall_confidence": 80,
            "examples": [
                {{
                    "text": "specific example text",
                    "confidence": 75
                }}
            ]
        }}
    ],
    "uncategorized_lines": [
        "meaningful uncategorized line 1",
        "meaningful uncategorized line 2"
    ],
    "summary": "concise summary text",
    "observations": [
        "key observation 1",
        "key observation 2"
    ],
    "recommendations": [
        "recommendation 1",
        "recommendation 2"
    ]
}}

Replace all example text with your actual analysis.
Important instructions:
- "confidence" values must be integers between 0-100
- All JSON arrays and objects must be properly formatted
- Make sure all quotes are properly escaped within strings
- DO NOT include any text, comments, or code blocks outside of the JSON structure
- Do NOT use markdown code blocks - return just the raw JSON object
- Include all required fields exactly as shown

Here are the post-mortem lessons to analyze:

{'\n'.join(lines)}

Remember: Return ONLY the valid JSON object with no additional text before or after."""

def extract_json_from_text(text):
    """Attempt to extract JSON from text that might have additional content"""
    # Try to find JSON-like pattern (starting with { and ending with })
    json_pattern = r'(\{[\s\S]*\})$'  # Match the last occurrence of a JSON block
    match = re.search(json_pattern, text)
    if match:
        return match.group(1)
    return text

@retry(
    stop=stop_after_attempt(5),  # More retries
    wait=wait_exponential(multiplier=1, min=4, max=30),  # Longer backoff
    retry=retry_if_exception_type((APIError, APIConnectionError, RateLimitError, BadRequestError)),
    reraise=True
)
def analyze_with_llm(prompt):
    try:
        logger.info(f"Using model: {MODEL}")
        
        # Basic API call without response_format
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "You are an expert post-mortem analyst. Return only valid, properly formatted JSON with the exact structure requested."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            timeout=90  # Increased timeout
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"API request failed: {str(e)}")
        raise

def attempt_json_repair(text):
    """Try to repair common JSON formatting issues"""
    # Remove any code block markers
    text = re.sub(r'```json|```', '', text).strip()
    
    # Extract just the JSON part
    text = extract_json_from_text(text)
    
    # Fix common escape character issues
    text = text.replace('\\"', '"')
    text = text.replace('\\n', ' ')
    
    return text

def validate_response_structure(parsed_result):
    """Ensure the response has the correct structure"""
    required_structure = {
        "unrecoverable_lines": list,
        "common_ideas": list,
        "uncategorized_lines": list,
        "summary": str,
        "observations": list,
        "recommendations": list
    }
    
    for field, field_type in required_structure.items():
        if field not in parsed_result or not isinstance(parsed_result[field], field_type):
            raise ValueError(f"Missing or invalid field: {field}")
    
    # Validate common_ideas structure
    for idea in parsed_result["common_ideas"]:
        if not all(key in idea for key in ["title", "overall_confidence", "examples"]):
            raise ValueError("Invalid common_ideas structure")
        for example in idea["examples"]:
            if not all(key in example for key in ["text", "confidence"]):
                raise ValueError("Invalid example structure in common_ideas")

def analyze_lessons(lines):
    if not lines:
        return {"error": "No input data provided"}
    
    try:
        prompt = create_llm_prompt(lines)
        result = analyze_with_llm(prompt)
        
        # Log the raw response for debugging
        logger.info(f"Raw LLM response (first 200 chars): {result[:200]}...")
        
        try:
            # Clean the response
            result = result.strip()
            
            # Remove code blocks if present
            if result.startswith("```json") and result.endswith("```"):
                result = result[7:-3].strip()
            elif result.startswith("```") and result.endswith("```"):
                result = result[3:-3].strip()
                
            # Try to parse the JSON
            try:
                parsed_result = json.loads(result)
            except json.JSONDecodeError:
                # If initial parsing fails, try to repair the JSON
                logger.warning("Initial JSON parsing failed, attempting repair")
                repaired_result = attempt_json_repair(result)
                parsed_result = json.loads(repaired_result)
                
        except json.JSONDecodeError as e:
            # Return more detailed error with the actual response for debugging
            error_msg = f"Failed to parse JSON: {str(e)}. First 500 chars of response: {result[:500]}"
            logger.error(error_msg)
            return {"error": "The analysis response was malformed. Please try again.", 
                    "debug_info": error_msg}
        
        # Validate structure
        validate_response_structure(parsed_result)
        
        # Ensure all confidence values are integers
        for idea in parsed_result["common_ideas"]:
            idea["overall_confidence"] = int(idea["overall_confidence"])
            for example in idea["examples"]:
                example["confidence"] = int(example["confidence"])
        
        return parsed_result
        
    except ValueError as e:
        logger.error(f"Invalid response structure: {str(e)}")
        return {"error": f"Analysis failed: {str(e)}"}
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}")
        return {"error": f"An unexpected error occurred: {str(e)}"}