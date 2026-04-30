# ml/trainer.py
import pandas as pd
import numpy as np
import xgboost as xgb
import pickle
import os
from datetime import datetime
from sqlalchemy import text
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from storage.db import engine
import shap

import logging
logger = logging.getLogger(__name__)

def train_model():
    # 1. Fetch Data
    query = "SELECT * FROM features ORDER BY date ASC"
    df = pd.read_sql(query, engine)
    
    if df.empty:
        logger.warning("No features found in DB — skipping training")

        return

    # 2. Preprocessing
    # Features requested: 5 numeric + one-hot tickers
    numeric_features = ['ma_7', 'ma_21', 'rsi_14', 'daily_return', 'volatility_7']
    df = df.dropna(subset=numeric_features + ['target'])

    # One-hot encoding for the "Global" approach
    ticker_df = pd.get_dummies(df['symbol'], prefix='ticker', dtype=int)
    ticker_cols = ticker_df.columns.tolist()
    
    X = pd.concat([df[numeric_features], ticker_df], axis=1)
    y = df['target']

    X = X.astype(float)
    y = y.astype(float)
    feature_names = X.columns.tolist()

    # 3. Time-Series Split (80/20, No Shuffle)
    split = int(len(X) * 0.8)
    X_train, X_test = X.iloc[:split], X.iloc[split:]
    y_train, y_test = y.iloc[:split], y.iloc[split:]

    # 4. Train XGBoost Regressor
    model = xgb.XGBRegressor(n_estimators=100, learning_rate=0.1, max_depth=5, random_state=42)
    model.fit(X_train, y_train)

    # 5. Evaluation
    preds = model.predict(X_test)
    metrics = {
        "rmse": float(np.sqrt(mean_squared_error(y_test, preds))),
        "mae": float(mean_absolute_error(y_test, preds)),
        "r2": float(r2_score(y_test, preds))
    }
    
    logger.info(f"Model metrics — RMSE={metrics['rmse']:.4f} MAE={metrics['mae']:.4f} R²={metrics['r2']:.4f}")

    # 6. SHAP Importance
    explainer   = shap.Explainer(model, X_train)
    shap_values = explainer(X_test[:500])  # sample for speed
    shap_imp    = dict(zip(
        feature_names,
        np.abs(shap_values.values).mean(axis=0).tolist()
    ))

    model_data = {
        "model": model,
        "feature_cols": feature_names, 
        "metrics": metrics,
        "shap_importance": shap_imp
    }
    # 7. Save according to contract
    with engine.connect() as conn:
        count = conn.execute(text(
            "SELECT COUNT(*) FROM model_registry WHERE symbol = 'GLOBAL'"
        )).scalar()
    model_version = f"model_v{int(count) + 1}"

    os.makedirs('/app/models', exist_ok=True)
    model_path = f"/app/models/{model_version}.pkl"
    champ_path = "/app/models/champion.pkl"


    with open(model_path, 'wb') as f:
        pickle.dump(model_data, f)
    with open(champ_path, 'wb') as f:
        pickle.dump(model_data, f)

    # 8. Update Model Registry
    max_date = df['date'].max()
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO model_registry 
            (symbol, model_version, is_champion, rmse, mae, r2, trained_on_data_until, model_path)
            VALUES ('GLOBAL', :version, TRUE, :rmse, :mae, :r2, :max_date, :path)
        """), {
            "version": model_version, "rmse": metrics['rmse'], "mae": metrics['mae'],
            "r2": metrics['r2'], "max_date": max_date, "path": champ_path
        })

    return {"version": model_version, **metrics, "is_champion": True}

if __name__ == "__main__":
    train_model()