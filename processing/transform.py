# processing/transform.py
import pandas as pd
import numpy as np

def clean_ticker_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Applies strict validation rules to ticker data.
    Implements Tasks 1.1 through 1.8.
    """
    if df.empty:
        return df

    # Work on a copy to ensure original (raw) data is untouched (Task 1.7)
    clean_df = df.copy()
    initial = len(clean_df)

    # 1.1 & 1.3: Null Handling & Positive Constraints
    # Combines dropping NaNs and ensuring OHLCV > 0
    cols_to_check = ['open', 'high', 'low', 'close', 'volume']
    for col in cols_to_check:
        clean_df = clean_df[clean_df[col].notnull() & (clean_df[col] > 0)]
    

    # 1.8: Volume Sanity
    clean_df = clean_df[clean_df['volume'] >= 100]

    # 1.2: Price Consistency (Logical checks)
    # High must be the highest, Low must be the lowest
    valid_prices = (
        (clean_df['high'] >= clean_df['low']) &
        (clean_df['high'] >= clean_df['open']) &
        (clean_df['high'] >= clean_df['close']) &
        (clean_df['low'] <= clean_df['open']) &
        (clean_df['low'] <= clean_df['close'])
    )
    clean_df = clean_df[valid_prices]

    # 1.4: Outlier Filter (Daily return > 50% is dropped)
    # Assuming the DF is sorted by date per symbol
    clean_df = clean_df.sort_values(['symbol', 'date'])
    clean_df['daily_return'] = clean_df.groupby('symbol')['close'].pct_change()
    
    # We use abs() > 0.5 as requested. 
    # Note: The first row of every symbol will be NaN, so we keep NaNs here 
    # to avoid losing the first day of history.
    clean_df = clean_df[~(clean_df['daily_return'].abs() > 0.5)]
    clean_df = clean_df.drop(columns=['daily_return'])

    # 1.5: Deduplication
    # Strict uniqueness on (date, symbol)
    clean_df = clean_df.drop_duplicates(subset=['date', 'symbol'], keep='first')

    return clean_df