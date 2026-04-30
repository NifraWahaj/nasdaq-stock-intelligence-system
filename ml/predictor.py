# ml/predictor.py
import pandas as pd
import pickle
import os
from sqlalchemy import text
from datetime import timedelta
from storage.db import engine

import logging
logger = logging.getLogger(__name__)

def make_predictions():
    # 1. Load Champion
    path = "/app/models/champion.pkl"
    if not os.path.exists(path):
        logger.warning("Champion model not found at /app/models/champion.pkl — skipping predictions")
        return
    
    with open(path, 'rb') as f:
        payload = pickle.load(f)
    
    model = payload['model']
    feature_cols = payload['feature_cols']
    
    # 2. Fetch Latest Features per Ticker
    query = "SELECT DISTINCT ON (symbol) * FROM features ORDER BY symbol, date DESC"
    df = pd.read_sql(query, engine)

    # 3. Align Features (One-Hot Encoding)
    ticker_df = pd.get_dummies(df['symbol'], prefix='ticker')
    X = pd.concat([df[['ma_7', 'ma_21', 'rsi_14', 'daily_return', 'volatility_7']], ticker_df], axis=1)
    
    # Fill missing ticker columns with 0
    for col in feature_cols:
        if col not in X.columns:
            X[col] = 0
    X = X[feature_cols] # Ensure exact order

    # 4. Predict
    df['predicted_close'] = model.predict(X)
    
    # 5. Calculate Next Trading Day (Skip Weekends)
    last_date = df['date'].max()
    next_date = last_date + timedelta(days=1)
    if next_date.weekday() >= 5: # Sat=5, Sun=6
        next_date += timedelta(days=(7 - next_date.weekday()))

    with engine.connect() as conn:
        row = conn.execute(text("""
            SELECT model_version FROM model_registry
            WHERE symbol = 'GLOBAL' AND is_champion = TRUE
            ORDER BY trained_at DESC LIMIT 1
        """)).fetchone()
    champion_version = row.model_version if row else "unknown"

    # 6. Insert Predictions
    with engine.begin() as conn:
        for _, row in df.iterrows():
            conn.execute(text("""
                INSERT INTO predictions (date, symbol, predicted_close, model_version)
                VALUES (:date, :symbol, :pred, :version)
                ON CONFLICT (date, symbol) DO NOTHING
            """), {
                "date": next_date, "symbol": row['symbol'], 
                "pred": float(row['predicted_close']), "version": champion_version
            })
        
        # 7. Backfill actual_close
        conn.execute(text("""
            UPDATE predictions p
            SET actual_close = pr.close
            FROM prices pr
            WHERE p.actual_close IS NULL 
            AND p.symbol = pr.symbol 
            AND p.date = pr.date
        """))

if __name__ == "__main__":
    make_predictions()