import pandas as pd
import datetime

def get_instrument_token(symbol, instruments_df):
    """
    Finds the nearest upcoming weekly expiry token for the given symbol
    (NIFTY or BANKNIFTY) from the instruments DataFrame.

    Parameters:
        symbol (str): e.g., "NIFTY" or "BANKNIFTY"
        instruments_df (pd.DataFrame): instrument master with trading_symbol, token, exch_seg

    Returns:
        dict: {'token': ..., 'exch_seg': ...} or None if not found
    """
    today = datetime.date.today()

    # Filter symbol and NFO segment
    expiry_range = instruments_df[
        (instruments_df['trading_symbol'].str.startswith(symbol)) &
        (instruments_df['exch_seg'] == 'NFO')
    ].copy()

    if expiry_range.empty:
        return None

    # Extract expiry date from trading_symbol
    expiry_range['expiry_date'] = expiry_range['trading_symbol'].str.extract(r'(\d{2}[A-Z]{3}\d{2})')
    expiry_range['expiry_date'] = pd.to_datetime(expiry_range['expiry_date'], format='%d%b%y', errors='coerce')
    expiry_range = expiry_range.dropna(subset=['expiry_date'])

    upcoming = expiry_range[expiry_range['expiry_date'] >= pd.Timestamp(today)]
    if upcoming.empty:
        return None

    nearest = upcoming.sort_values('expiry_date').iloc[0]
    return {
        "token": nearest['token'],
        "exch_seg": nearest['exch_seg']
    }
