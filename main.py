from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
from src.kraken_client import fetch_ohlc_data
from src.deepseek_client import generate_signal

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

@app.get("/")
async def root():
    return {"message": "Trading Signal Generator API", "status": "active"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/generate-signal")
async def generate_trading_signal():
    try:
        # Fetch OHLC data from Kraken
        ohlc_data = await fetch_ohlc_data()
        
        if not ohlc_data:
            raise HTTPException(status_code=500, detail="Failed to fetch OHLC data")
        
        # Generate signal using DeepSeek
        signal_response = await generate_signal(ohlc_data)
        
        return {
            "success": True,
            "data": signal_response,
            "ohlc_data_points": len(ohlc_data)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating signal: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
