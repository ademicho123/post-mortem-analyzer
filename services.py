import openai
import json
import os
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential

# Load environment variables
load_dotenv()

# Configure OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    raise ValueError("OPENAI_API_KEY not found in environment variables")

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def analyze_with_llm(prompt):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert post-mortem analyst."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            request_timeout=30  # 30 seconds timeout
        )
        return response["choices"][0]["message"]["content"]
    except Exception as e:
        raise Exception(f"LLM API error: {str(e)}")

def analyze_lessons(lines):
    if not lines:
        return {"error": "No input data provided"}
    
    try:
        prompt = f"""Analyze these post-mortem lessons and provide JSON output with:
        1. unrecoverable_lines: List of lines with no meaning
        2. common_ideas: List of themes with title, overall_confidence, and examples
        3. uncategorized_lines: Meaningful lines that didn't fit categories
        4. summary: Concise summary
        5. observations: List of key observations
        6. recommendations: List of improvement suggestions
        
        Input data:
        {'\n'.join(lines)}
        """
        
        result = analyze_with_llm(prompt)
        
        try:
            parsed_result = json.loads(result)
        except json.JSONDecodeError:
            # If JSON fails, try to extract JSON from markdown code block
            if '```json' in result:
                result = result.split('```json')[1].split('```')[0]
                parsed_result = json.loads(result)
            else:
                raise ValueError("LLM returned invalid JSON format")
        
        # Set default values for all required fields
        defaults = {
            "unrecoverable_lines": [],
            "common_ideas": [],
            "uncategorized_lines": [],
            "summary": "",
            "observations": [],
            "recommendations": []
        }
        
        for key, default in defaults.items():
            parsed_result[key] = parsed_result.get(key, default)
            
        return parsed_result
        
    except Exception as e:
        return {"error": str(e)}