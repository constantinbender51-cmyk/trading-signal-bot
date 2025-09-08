> ⚠️ **Clarification**  
> This repository – along with every other “bot” project in the `constantinbender51-cmyk` namespace – is **scrap / legacy code** and should **not** be treated as a working or profitable trading system.  
>  
> The **only** repos that still receive updates and are intended for forward-testing are:  
> - `constantinbender51-cmyk/sigtrabot`  
> - `constantinbender51-cmyk/DeepSeekGenerator-v.-1.4` (a.k.a. “DeepSignal v. 1.4”)  
>  
> Complete list of repos that remain **functionally maintained** (but still **unproven** in live, statistically-significant trading):  
> - `constantinbender51-cmyk/Kraken-futures-API`  
> - `constantinbender51-cmyk/sigtrabot`  
> - `constantinbender51-cmyk/binance-btc-data`  
> - `constantinbender51-cmyk/SigtraConfig`  
> - `constantinbender51-cmyk/Simple-bot-complex-behavior-project-`  
> - `constantinbender51-cmyk/DeepSeekGenerator-v.-1.4`  
>  
> > None of the above has demonstrated **statistically significant profitability** in out-of-sample, live trading; **DeepSignal v. 1.4** is merely **showing early promise** and remains experimental.


# Trading Signal Generator

A FastAPI application that fetches OHLC data from Kraken and generates trading signals using DeepSeek AI.

## Features

- Fetches 1-week hourly OHLC data for PF_XBTUSD from Kraken
- Generates trading signals using DeepSeek AI
- Returns JSON responses with signal, reason, and confidence
- Deployable on Railway

## Setup

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and add your DeepSeek API key
4. Run locally: `uvicorn src.main:app --reload`

## API Endpoints

- `GET /` - Root endpoint
- `GET /health` - Health check
- `GET /generate-signal` - Generate trading signal

## Deployment on Railway

1. Fork this repository
2. Connect your GitHub account to Railway
3. Create new project from GitHub repo
4. Add environment variable `DEEPSEEK_API_KEY` in Railway dashboard
5. Deploy automatically

## Environment Variables

- `DEEPSEEK_API_KEY` - Your DeepSeek API key
- `PORT` - Port number (default: 8000)
