
import os

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

def generate_risk_assessment(vulnerability_text: str, api_key: Optional[str] = None) -> Dict[str, str]:
    """
    Generate a 3-bullet risk assessment using Google Gemini.
    Returns a dictionary with keys: 'impact', 'attack_vector', 'fix'.
    """
    if not api_key:
        api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        return {
            "error": "Missing API Key. Please set OPENAI_API_KEY in environment variables."
        }

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)

        prompt = f"""
        Analyze the following vulnerability description and provide a 3-bullet summary acting as a Cyber Security Expert.
        
        Vulnerability: {vulnerability_text}
        
        Format the response EXACTLY as follows (no markdown bolding, just text):
        Impact: [1-sentence impact analysis]
        Attack Vector: [1-sentence explanation of how it is exploited]
        Suggested Fix: [1-sentence mitigation recommendation]
        """

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a cybersecurity expert dealing with vulnerability analysis."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=150
        )
        
        text = response.choices[0].message.content
        
        # Parse the response
        result = {}
        for line in text.split('\n'):
            line = line.strip()
            if line.startswith("Impact:"):
                result['impact'] = line.replace("Impact:", "").strip()
            elif line.startswith("Attack Vector:"):
                result['attack_vector'] = line.replace("Attack Vector:", "").strip()
            elif line.startswith("Suggested Fix:"):
                result['fix'] = line.replace("Suggested Fix:", "").strip()
        
        # Fallback if parsing failed but we got text
        if not result and text:
            result['raw'] = text
            
        return result

    except Exception as e:
        logger.error(f"AI Risk Assessment failed: {e}")
        return {"error": f"AI Generation failed: {str(e)}"}
