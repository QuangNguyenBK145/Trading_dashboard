import streamlit as st

st.set_page_config(
    page_title="Trading Dashboard",
    page_icon="📈",
    layout="wide"
)

with st.sidebar:
    st.markdown("## 💼 Portfolio Dashboard")
    st.caption("📊 Quản lý danh mục đầu tư thông minh")
    st.markdown("---")

st.title("📊 Trading Dashboard")
st.markdown("Chọn chức năng bên trái để bắt đầu:")

import pandas as pd
from collections import defaultdict, deque
from utils.get_price import get_price_cp68, get_price_change
import plotly.graph_objects as go
import plotly.express as px
from datetime import date
import os


# ĐỌC DỮ LIỆU, SẮP XẾP LẠI
df = pd.read_csv("data/transaction_log.csv")
# df = pd.read_excel("Data.xlsx", sheet_name="LSMB")  # Đọc sheet LSMB từ file excel

customer_list = df["Customer"].dropna().unique().tolist()
selected_customer = st.selectbox("👤 Chọn khách hàng", customer_list)
df = df[df["Customer"] == selected_customer]


df = df.sort_values("DateTime")  # Sắp xếp theo thời gian để đúng trình tự FIFO
df["Order"] = df[
    "Order"
].str.upper()  # Chuyển tất cả các lệnh thành chữ in hoa: "MUA", "BÁN"

# TẠO KHO LƯU TRỮ DANH MỤC THEO MÃ CỔ PHIẾU
inventory = defaultdict(deque)  # Cần note hỏi lại

# DUYỆT TỪNG DÒNG GIAO DỊCH
for _, row in df.iterrows():
    stock = row["Stock"]
    order = row["Order"]
    qty = row["Volume"]
    price = row["Price"]

    # XỬ LÝ LỆNH MUA (THÊM VÀO HÀNG TỒN FIFO)
    if order == "MUA":
        inventory[stock].append({"qty": qty, "price": price})
    # XỬ LÝ LỆNH BÁN (TRỪ DẦN THEO FIFO)
    elif order == "BÁN":
        sell_qty = qty
        while sell_qty > 0 and inventory[stock]:
            mua = inventory[stock][0]
            if sell_qty >= mua["qty"]:
                sell_qty -= mua["qty"]
                inventory[stock].popleft()  # hỏi popleft là gì
            else:
                mua["qty"] -= sell_qty
                sell_qty = 0

# TỔNG HỢP LẠI DANH MỤC HIỆN TẠI
danh_muc = []

for stock, lots in inventory.items():
    total_qty = sum(l["qty"] for l in lots)
    if total_qty == 0:
        continue
    total_cost = sum(l["qty"] * l["price"] for l in lots)
    avg_price = total_cost / total_qty
    danh_muc.append(
        {"Stock": stock, "Quantity": total_qty, "Avg_Price": round(avg_price, 2)}
    )

# TRẢ KẾT QUẢ RA DATAFRAME
df_danh_muc = pd.DataFrame(danh_muc)
df_danh_muc["Market_price"] = df_danh_muc["Stock"].apply(get_price_cp68) * 1000
df_danh_muc["Buy Value"] = df_danh_muc["Avg_Price"] * df_danh_muc["Quantity"]
df_danh_muc["Market_Value"] = df_danh_muc["Market_price"] * df_danh_muc["Quantity"]
df_danh_muc["PnL"] = (
    df_danh_muc["Market_Value"] - df_danh_muc["Quantity"] * df_danh_muc["Avg_Price"]
)
df_danh_muc["PnL_perc"] = (
    df_danh_muc["PnL"] / (df_danh_muc["Quantity"] * df_danh_muc["Avg_Price"]) * 100
)
df_danh_muc["Day change"] = (
    df_danh_muc["Stock"].apply(get_price_change) * df_danh_muc["Quantity"] * 1000
)
total_PnL = df_danh_muc["PnL"].sum()
day_change_value = (df_danh_muc["Day change"]).sum()
# TRẢ KẾT QUẢ RA DATAFRAME
if st.button("🔁 Cập nhật giá thị trường"):
    df_danh_muc["Market_price"] = df_danh_muc["Stock"].apply(get_price_cp68) * 1000

    df_danh_muc["Market_Value"] = df_danh_muc["Market_price"] * df_danh_muc["Quantity"]
    df_danh_muc["PnL"] = (
        df_danh_muc["Market_Value"] - df_danh_muc["Quantity"] * df_danh_muc["Avg_Price"]
    )
    df_danh_muc["PnL_perc"] = (
        df_danh_muc["PnL"] / (df_danh_muc["Quantity"] * df_danh_muc["Avg_Price"]) * 100
    )
    st.success("Đã cập nhật giá thành công!")


col1, col2, col3 = st.columns(3)
with col1:
    st.metric(
        "Tổng lãi/Lỗ chưa thực hiện", f"{total_PnL:,.0f} VNĐ", delta_color="normal"
    )
with col2:
    st.metric("Tổng số mã sinh lời", (df_danh_muc["PnL"] > 0).sum())
with col3:
    st.metric(
        "Tổng thay đổi hôm nay", f"{day_change_value:,.0f} VND", delta_color="inverse"
    )


# TÔ MÀU LÃI LỖ
def highlight_pnl(val):
    color = "green" if val > 0 else "red" if val < 0 else "black"
    return f"color: {color}"


st.dataframe(
    df_danh_muc.style.format(
        {
            "Avg_Price": "{:,.0f} VNĐ",
            "Market_price": "{:,.0f} VNĐ",
            "Market_Value": "{:,.0f} VNĐ",
            "Buy Value": "{:,.0f} VNĐ",
            "PnL_perc": "{:,.2f} %",
            "PnL": "{:,.0f} VNĐ",
            "Day change": "{:,.0f} VNĐ",
        }
    ).applymap(highlight_pnl, subset=["PnL", "PnL_perc", "Day change"])
)

# Vẽ đồ thị cột thể hiện lãi lỗ
# Chuẩn bị dữ liệu
waterfall_data = df_danh_muc[["Stock", "PnL"]].copy()
waterfall_data.loc[len(waterfall_data.index)] = ["Tổng", waterfall_data["PnL"].sum()]

# Tạo biểu đồ Waterfall
fig = go.Figure(
    go.Waterfall(
        name="PnL",
        orientation="v",
        measure=["relative"] * (len(waterfall_data) - 1) + ["total"],
        x=waterfall_data["Stock"],
        y=waterfall_data["PnL"],
        text=[f"{v:,.0f}" for v in waterfall_data["PnL"]],
        textposition="outside",
        increasing={"marker": {"color": "green"}},
        decreasing={"marker": {"color": "red"}},
        totals={"marker": {"color": "blue"}},
    )
)

fig.update_layout(
    title="💧 Waterfall Chart – Lãi/Lỗ theo Mã Cổ Phiếu",
    yaxis_title="PnL (VNĐ)",
    xaxis_title="Mã cổ phiếu",
    height=500,
)

st.plotly_chart(fig, use_container_width=True)


st.subheader("🥧 Tỷ trọng giá trị các mã trong Danh mục")

# Pie chart theo Market Value
fig = px.pie(
    df_danh_muc,
    names="Stock",
    values="Market_Value",
    title="Phân bổ danh mục theo giá trị thị trường",
    hole=0.4,  # donut chart
)

fig.update_traces(textinfo="percent+label")

st.plotly_chart(fig, use_container_width=True)

### TẠO BẢNG CẬP NHẬT GIÁ TRỊ NAV
# Tính tổng NAV    -     sẽ sửa lại sau
total_NAV = df_danh_muc["Market_Value"].sum()
today = date.today().strftime("%Y-%m-%d")

# Ghi vào file log
nav_log_file = "Data/nav_log.csv"

# Nếu file chưa tồn tại, tạo header
if not os.path.exists(nav_log_file):
    pd.DataFrame(columns=["Date", "NAV"]).to_csv(nav_log_file, index=False)

# Ghi thêm dòng mới
df_log = pd.read_csv(nav_log_file)

# Kiểm tra ngày hôm nay đã có log --> không ghi trùng
if today not in df_log["Date"].values:
    new_row = pd.DataFrame([{"Date": today, "NAV": total_NAV}])
    df_log = pd.concat([df_log, new_row], ignore_index=True)
    df_log.to_csv(nav_log_file, index=False)
    st.success("✅ Đã lưu lịch sử NAV hôm nay!")
else:
    st.info("📌 NAV hôm nay đã được lưu rồi.")

st.subheader("📈 Biến động NAV theo thời gian")

df_nav_log = pd.read_csv(nav_log_file)
df_nav_log["Date"] = pd.to_datetime(df_nav_log["Date"])

st.line_chart(df_nav_log.set_index("Date"))
