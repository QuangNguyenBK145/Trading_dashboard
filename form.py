import os
import pandas as pd
from datetime import datetime
import streamlit as st

cash_flow_file = "data/cashflow_log.csv"

# Tạo file nếu chưa có
if not os.path.exists(cash_flow_file):
    pd.DataFrame(columns=["Customer", "DateTime", "Action", "Amount", "Note"]).to_csv(
        cash_flow_file, index=False
    )

df_customer = pd.read_csv("data/customer.csv")
customer_list = df_customer["Customer"].tolist()

st.subheader("💰 Giao dịch Nộp/Rút tiền")
with st.form("cashflow_form", clear_on_submit=True):
    col1, col2 = st.columns(2)

    with col1:
        action = st.selectbox("Loại giao dịch", ["Nộp tiền", "Rút tiền"])
    with col2:
        amount = st.number_input("Số tiền (VND)", min_value=0, step=1_000_000)

    customer = st.selectbox("👤 Chọn khách hàng", customer_list)
    note = st.text_input("Ghi chú tuỳ chọn", placeholder="Ví dụ: Nộp tiền từ MB Bank")
    submitted = st.form_submit_button("💾 Ghi giao dịch")
    if submitted:
        sign = 1 if action == "Nộp tiền" else -1
        final_amount = sign * amount
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        new_row = pd.DataFrame(
            [
                {
                    "Customer": customer.upper(),
                    "DateTime": now,
                    "Action": action,
                    "Amount": final_amount,
                    "Note": note,
                }
            ]
        )
        df_cash = pd.read_csv(cash_flow_file)
        df_cash = pd.concat([df_cash, new_row], ignore_index=False)
        df_cash.to_csv(cash_flow_file, index=False)

        st.success(f"✅ Đã ghi: {action} {amount:,.0f} VNĐ")

st.markdown("### 📋 Giao dịch tiền gần đây")
df_cash = pd.read_csv(cash_flow_file)
df_filtered = df_cash[df_cash["Customer"] == customer]
st.dataframe(df_filtered.tail(10).style.format({"Amount": "{:,.0f} VNĐ"}))

######## FORM TRANSACTION

transaction_file = "data/transaction_log.csv"
# Tạo file nếu chưa có
if not os.path.exists(transaction_file):
    pd.DataFrame(
        columns=["DateTime", "Customer", "Stock", "Order", "Volume", "Price", "Note"]
    ).to_csv(transaction_file, index=False)

st.subheader("📝 Nhập Giao Dịch Mua/Bán Cổ Phiếu")
with st.form("trade_form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        customer = st.selectbox("Khách hàng", customer_list)
        stock = st.text_input("🆔 Mã cổ phiếu", placeholder="VD: FPT").upper()
        order_type = st.selectbox("📈 Loại giao dịch", ["Mua", "Bán"])

    with col2:
        volume = st.number_input("📦 Khối lượng", min_value=1, step=100)
        price = st.number_input("💵 Giá (VNĐ)", min_value=0.0, step=100.0)

    note = st.text_input("🗒️ Ghi chú (tuỳ chọn)")

    submitted = st.form_submit_button("💾 Ghi giao dịch")

    if submitted:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        new_trade = pd.DataFrame(
            [
                {
                    "DateTime": now,
                    "Customer": customer,
                    "Stock": stock,
                    "Order": order_type,
                    "Volume": volume,
                    "Price": price,
                    "Note": note,
                }
            ]
        )

        df_trades = pd.read_csv(transaction_file)
        df_trades = pd.concat([df_trades, new_trade], ignore_index=True)
        df_trades.to_csv(transaction_file, index=False)

        st.success(
            f"✅ Đã ghi giao dịch {order_type.lower()} {volume} {stock} cho {customer}"
        )

st.markdown("### 📋 Giao dịch gần đây theo khách hàng")

df_trades = pd.read_csv(transaction_file)
df_recent_trades = df_trades[df_trades["Customer"] == customer].tail(10)

st.dataframe(df_recent_trades)
#### Cập nhật giao dịch bằng file
st.subheader("📤 Nhập giao dịch từ file Excel")

uploaded_file = st.file_uploader(
    "Tải lên file giao dịch (.xlsx hoặc .csv)", type=["xlsx", "csv"]
)

if uploaded_file is not None:
    try:
        # Đọc file Excel hoặc CSV
        if uploaded_file.name.endswith(".csv"):
            df_import = pd.read_csv(uploaded_file)
        else:
            df_import = pd.read_excel(uploaded_file)

        # Kiểm tra các cột bắt buộc
        required_cols = ["DateTime", "Customer", "Stock", "Order", "Volume", "Price"]
        if all(col in df_import.columns for col in required_cols):
            # Load giao dịch hiện tại
            df_existing = pd.read_csv(transaction_file)

            # Gộp dữ liệu KHÔNG xoá trùng
            df_combined = pd.concat([df_existing, df_import], ignore_index=True)

            # Ghi lại file
            df_combined.to_csv(transaction_file, index=False)
            st.success("✅ Đã nhập file thành công và ghi toàn bộ giao dịch!")

        else:
            st.warning("⚠️ File thiếu cột bắt buộc: " + ", ".join(required_cols))

    except Exception as e:
        st.error(f"❌ Lỗi khi xử lý file: {e}")
