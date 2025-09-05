from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import aiohttp
import asyncio
import json
import os
import re
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Trading Signal Generator", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def fetch_ohlc_data():
    """
    Fetch one week of hourly OHLC data for PF_XBTUSD from Kraken
    """
    base_url = "https://api.kraken.com/0/public/OHLC"
    pair = "PF_XBTUSD"
    interval = 60  # 1 hour in minutes
    
    # Calculate timestamps for one week ago
    end_time = datetime.now()
    start_time = end_time - timedelta(weeks=1)
    
    params = {
        'pair': pair,
        'interval': interval,
        'since': int(start_time.timestamp())
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(base_url, params=params, timeout=30) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data.get('error'):
                        error_msg = data['error'][0] if data['error'] else "Unknown error"
                        raise Exception(f"Kraken API error: {error_msg}")
                    
                    # Extract OHLC data
                    ohlc_data = data['result'].get(pair, [])
                    
                    if not ohlc_data:
                        raise Exception("No OHLC data returned from Kraken")
                    
                    # Convert to structured format
                    formatted_data = []
                    for candle in ohlc_data:
                        formatted_data.append({
                            'timestamp': candle[0],
                            'open': float(candle[1]),
                            'high': float(candle[2]),
                            'low': float(candle[3]),
                            'close': float(candle[4]),
                            'volume': float(candle[6])
                        })
                    
                    return formatted_data
                else:
                    raise Exception(f"HTTP error: {response.status}")
                    
    except Exception as e:
        print(f"Error fetching OHLC data: {e}")
        return None

def format_ohlc_for_prompt(ohlc_data):
    """
    Format OHLC data for the DeepSeek prompt
    """
    if not ohlc_data:
        return "No OHLC data available"
    
    # Get the most recent 24 candles for the prompt (to avoid token limits)
    recent_data = ohlc_data[-24:]
    
    formatted = "Recent OHLC data (timestamp, open, high, low, close, volume):\n"
    for candle in recent_data:
        dt = datetime.fromtimestamp(candle['timestamp'])
        formatted += f"{dt.strftime('%Y-%m-%d %H:%M')}: {candle['open']:.2f}, {candle['high']:.2f}, {candle['low']:.2f}, {candle['close']:.2f}, {candle['volume']:.2f}\n"
    
    return formatted

async def generate_signal(ohlc_data):
    """
    Generate trading signal using DeepSeek API
    """
    deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
    
    if not deepseek_api_key:
        print("DeepSeek API key not found in environment variables")
        return {
            "signal": "HOLD",
            "reason": "API key not configured",
            "confidence": 0.1
        }
    
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
        "model": "deepseek-chat",
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
                json=payload,
                timeout=60
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    content = data['choices'][0]['message']['content']
                    
                    # Try to parse the JSON response
                    try:
                        signal_data = json.loads(content.strip())
                        return signal_data
                    except json.JSONDecodeError:
                        # If JSON parsing fails, try to extract JSON from the response
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
                    print(f"DeepSeek API error: {response.status} - {error_text}")
                    return {
                        "signal": "HOLD",
                        "reason": f"API error: {response.status}",
                        "confidence": 0.1
                    }
                    
    except Exception as e:
        print(f"Error calling DeepSeek API: {e}")
        return {
            "signal": "HOLD",
            "reason": f"API connection error: {str(e)}",
            "confidence": 0.1
        }

@app.get("/")
async def root():
    return {"message": "Trading Signal Generator API", "status": "active"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/generate-signal")
async def generate_trading_signal():
    try:
        print("Fetching OHLC data from Kraken...")
        ohlc_data = await fetch_ohlc_data()
        
        if not ohlc_data:
            raise HTTPException(status_code=500, detail="Failed to fetch OHLC data")
        
        print(f"Fetched {len(ohlc_data)} OHLC data points")
        print("Generating signal using DeepSeek...")
        
        signal_response = await generate_signal(ohlc_data)
        
        return {
            "success": True,
            "data": signal_response,
            "ohlc_data_points": len(ohlc_data),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"Error in generate_trading_signal: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating signal: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
