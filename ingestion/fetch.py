import time
import yfinance as yf
import pandas as pd
from tenacity import retry, stop_after_attempt, wait_exponential

TICKERS = ["AAPL","MSFT","GOOGL","AMZN","NVDA","META","TSLA","INTC","AMD","NFLX"]

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=4, max=30), reraise=True)
def _fetch_one(ticker: str, period: str) -> pd.DataFrame:
    df = yf.download(ticker, period=period, auto_adjust=True, progress=False, threads=False)
    if df.empty:
        raise ValueError(f"Empty response for {ticker}")
    df.reset_index(inplace=True)
    df.columns = [c.lower() for c in df.columns]
    df.rename(columns={"datetime": "date"}, errors="ignore", inplace=True)
    df["symbol"] = ticker
    return df[["date","symbol","open","high","low","close","volume"]]

def fetch_all(period="2y") -> pd.DataFrame:
    frames, failed = [], []
    for i, t in enumerate(TICKERS):
        try:
            frames.append(_fetch_one(t, period))
        except Exception as e:
            print(f"[WARN] {t} failed: {e}")
            failed.append(t)
        if i < len(TICKERS) - 1:
            time.sleep(0.5)
    if not frames:
        raise RuntimeError(f"All tickers failed: {failed}")
    print(f"Fetched {len(frames)}/{len(TICKERS)} tickers | failed: {failed or 'none'}")
    return pd.concat(frames, ignore_index=True)


if __name__ == "__main__":
    print("Starting Local Ingestion Test (No Database)...")
    
    try:
        # 1. Execute the fetch
        df_all = fetch_all(period="1mo") # Using 1 month just for a quick test
        
        # 2. Verify the data structure
        print("\n--- Data Preview ---")
        print(df_all.head())
        print(f"\nTotal Rows Collected: {len(df_all)}")
        print(f"Columns: {list(df_all.columns)}")
        
        # 3. Save a temporary local copy (Proof of work)
        df_all.to_csv("ingestion_test.csv", index=False)
        print("\nSuccess! Data saved to 'ingestion_test.csv'.")
        print("You can open this file in VS Code to verify the data is clean.")
        
    except Exception as e:
        print(f"Ingestion Failed: {e}")