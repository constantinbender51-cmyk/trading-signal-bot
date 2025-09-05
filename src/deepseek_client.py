import aiohttp
import json
import os
from .kraken_client import format_ohlc_for_prompt

async def generate_signal(ohlc_data):
    """
    Generate trading signal using DeepSeek API
    """
    deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
    
    if not deepseek_api_key:
        raise Exception("DeepSeek API key not found in environment variables")
    
    # Format OHLC data for the prompt
    ohlc_formatted = format_ohlc_for_prompt(ohlc_data)
    
    prompt = f"""
    Generate a trading signal for PF_XBTUSD based on the following OHLC data.
    
    {ohlc_formatted}
    
    Analyze this data and provide a JSON response with:
    1. "signal": either "BUY", "SELL", or "HOLD"
    2. "reason": a brief technical analysis explanation (2-3 sentences)
    3. "confidence": a number between 0.1 and 1.0 indicating confidence level
    
    Respond ONLY with a valid JSON object. Do not include any other text.
    """
    
    headers = {
        "Authorization": f"Bearer {deepseek_api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "deepseek-chat",  # Adjust based on available models
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.1,
        "max_tokens": 500
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers=headers,
                json=payload
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    content = data['choices'][0]['message']['content']
                    
                    # Try to parse the JSON response
                    try:
                        signal_data = json.loads(content)
                        return signal_data
                    except json.JSONDecodeError:
                        # If JSON parsing fails, try to extract JSON from the response
                        import re
                        json_match = re.search(r'\{.*\}', content, re.DOTALL)
                        if json_match:
                            return json.loads(json_match.group())
                        else:
                            return {
                                "signal": "HOLD",
                                "reason": "Failed to parse AI response",
                                "confidence": 0.1
                            }
                else:
                    error_text = await response.text()
                    raise Exception(f"DeepSeek API error: {response.status} - {error_text}")
                    
    except Exception as e:
        print(f"Error calling DeepSeek API: {e}")
        return {
            "signal": "HOLD",
            "reason": f"API error: {str(e)}",
            "confidence": 0.1
        }
