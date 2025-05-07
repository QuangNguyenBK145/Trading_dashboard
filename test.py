import pandas as pd
from datetime import date

def normalize_price_file(df):
    df = df.rename(columns={
        df.columns[0]: "Stock",
        df.columns[1]: "Date",
        df.columns[2]: "Close_Price"
    })
    df["Date"] = pd.to_datetime(df["Date"].astype(str), format="%Y%m%d")
    df = df[["Date", "Stock", "Close_Price"]]
    return df

def update_price_log_from_upload(uploaded_df, transaction_df, path="data/price_log.csv"):
    tickers_in_trans = transaction_df["Stock"].unique()
    df_filtered = uploaded_df[uploaded_df["Stock"].isin(tickers_in_trans)]

    try:
        df_log = pd.read_csv(path, parse_dates=["Date"])
    except FileNotFoundError:
        df_log = pd.DataFrame(columns=["Date", "Stock", "Close_Price"])

    df_all = pd.concat([df_log, df_filtered], ignore_index=True)
    df_all.drop_duplicates(subset=["Date", "Stock"], keep="last", inplace=True)
    df_all.to_csv(path, index=False)

def append_today_prices(df_today_prices, path="data/price_log.csv"):
    try:
        df_log = pd.read_csv(path, parse_dates=["Date"])
    except FileNotFoundError:
        df_log = pd.DataFrame(columns=["Date", "Stock", "Close_Price"])

    df_today_prices["Date"] = pd.to_datetime(date.today())
    df_all = pd.concat([df_log, df_today_prices], ignore_index=True)
    df_all.drop_duplicates(subset=["Date", "Stock"], keep="last", inplace=True)
    df_all.to_csv(path, index=False)
