import pandas as pd
import os
import streamlit as st
from utils.calculator import calculate_portfolio

st.subheader("🕒 Tính danh mục tại một thời điểm")

selected_date = st.date_input("📅 Chọn ngày tính danh mục", value=pd.to_datetime("today"))

df_price_log = pd.read_csv("data/price_log.csv", parse_dates=["Date"])

df_trades = pd.read_csv("data/transaction_log.csv")
df_trades["DateTime"] = pd.to_datetime(df_trades["DateTime"])
df_trades = df_trades.sort_values(by="DateTime")  # Sắp xếp FIFO

df_customer = pd.read_csv("data/customer.csv")
customer_list = df_customer["Customer"].tolist()
selected_customer = st.selectbox("👤 Chọn khách hàng để xem danh mục", customer_list)

if st.button("📥 Tính danh mục tại thời điểm đã chọn"):
    df_danh_muc = calculate_portfolio(selected_customer, selected_date, df_trades, df_price_log)
    st.dataframe(df_danh_muc)

    total_cost = df_danh_muc["Total_Cost"].sum()
    st.metric("💼 Tổng giá vốn tại thời điểm đó", f"{total_cost:,.0f} VNĐ")

