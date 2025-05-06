import pandas as pd
import os
import streamlit as st
from get_price import get_price_cp68, get_price_change
from calculator import calculate_portfolio

df_trades = pd.read_csv("data/transactions_log.csv")
df_trades["DateTime"] = pd.to_datetime(df_trades["DateTime"])
df_trades = df_trades.sort_values(by="DateTime")  # Sắp xếp FIFO

df_customer = pd.read_csv("data/customer.csv")
customer_list = df_customer["Customer"].tolist()
selected_customer = st.selectbox("👤 Chọn khách hàng để xem danh mục", customer_list)

if st.button("📥 Tính danh mục hiện tại"):
    df_danh_muc = calculate_portfolio(selected_customer)
    st.dataframe(df_danh_muc)

    total_pnl = df_danh_muc["PnL"].sum()
    st.metric("📊 Tổng Lãi/Lỗ (tạm tính)", f"{total_pnl:,.0f} VNĐ")
