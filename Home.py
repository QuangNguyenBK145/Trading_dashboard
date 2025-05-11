import streamlit as st

st.set_page_config(page_title="Trading Dashboard", page_icon="📈", layout="wide")

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
from utils.calculator import (
    calculate_nav_home,
    calculate_nav,
    calculate_fees_and_tax,
)
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
from scipy.interpolate import make_interp_spline

# ĐỌC DỮ LIỆU, SẮP XẾP LẠI
df = pd.read_csv("data/transaction_log.csv")
# df = pd.read_excel("Data.xlsx", sheet_name="LSMB")  # Đọc sheet LSMB từ file excel

customer_list = df["Customer"].dropna().unique().tolist()
selected_customer = st.selectbox("👤 Chọn khách hàng", customer_list)
df = df[df["Customer"] == selected_customer]
as_of_date = pd.Timestamp.today().normalize()

df_trades = pd.read_csv("data/transaction_log.csv", parse_dates=["DateTime"])
df_cashflow = pd.read_csv("data/cashflow_log.csv", parse_dates=["DateTime"])
df_price_log = pd.read_csv("data/price_log.csv", parse_dates=["Date"])

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


nav_info = calculate_nav_home(selected_customer, as_of_date, df_trades, df_cashflow)
# Phí và thuế
fee_total, tax_total = calculate_fees_and_tax(df_trades, as_of_date, selected_customer)


total_nav_today = nav_info["NAV"] + total_PnL - fee_total - tax_total
# ----------------------------------- Vẽ Home Page --------------------------------------
st.subheader("📊 NAV Tổng Quan")

col1, col2, col3 = st.columns(3)
col1.metric("💵 NAV", f"{total_nav_today:,.0f} đ")
col2.metric("📈 Tổng chi phí", f"{fee_total+tax_total:,.0f} đ")
col3.metric("✅ Lãi/lỗ đã thực hiện", f"{nav_info['Realized_PnL']:,.0f} đ")

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
    new_row = pd.DataFrame([{"Date": today, "NAV": total_nav_today}])
    df_log = pd.concat([df_log, new_row], ignore_index=True)
    df_log.to_csv(nav_log_file, index=False)
    st.success("✅ Đã lưu lịch sử NAV hôm nay!")
else:
    st.info("📌 NAV hôm nay đã được lưu rồi.")


# TÍNH VÀ VẼ ĐỒ THỊ NAV

dates_trade = df_trades[df_trades["Customer"] == selected_customer]["DateTime"]
dates_cash = df_cashflow[df_cashflow["Customer"] == selected_customer]["DateTime"]

# Lấy danh sách ngày duy nhất, sắp xếp tăng dần
date_list = pd.Series(pd.concat([dates_trade, dates_cash]).unique())
date_list = pd.to_datetime(date_list).dropna().sort_values().dt.normalize()

nav_history = []

for date in date_list:
    nav_info = calculate_nav(
        selected_customer, date, df_trades, df_cashflow, df_price_log
    )
    nav_info["Date"] = date
    nav_history.append(nav_info)

df_nav = pd.DataFrame(nav_history)
df_nav = df_nav[df_nav["NAV"] > 0]

# Tính NAV đầu & % tăng trưởng
nav_start = df_nav["NAV"].iloc[0]
nav_latest = df_nav["NAV"].iloc[-1]
pct_change = (nav_latest - nav_start) / nav_start * 100
nav_mean = df_nav["NAV"].mean()

# Làm mượt đường NAV bằng spline interpolation
x = np.arange(len(df_nav))
x_smooth = np.linspace(x.min(), x.max(), 300)
y_smooth = make_interp_spline(x, df_nav["NAV"])(x_smooth)

st.subheader("📈 Biểu đồ tăng trưởng NAV")

plt.style.use("dark_background")
plt.rcParams["font.family"] = "DejaVu Sans"
fig, ax = plt.subplots(figsize=(10, 5))

# Đường NAV mượt
ax.plot(x_smooth, y_smooth, label="NAV", color="violet", linewidth=2)

# Đường NAV trung bình
ax.hlines(
    nav_mean,
    xmin=0,
    xmax=x_smooth.max(),
    colors="orange",
    linestyles="--",
    label="NAV trung bình",
)

# Tuỳ chỉnh trục
ax.set_title(f"Biến động NAV của {selected_customer}", fontsize=14, weight="bold")
ax.set_ylabel("Giá trị NAV", fontsize=12)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))

# Gắn mốc ngày lên trục X
tick_idx = np.linspace(0, len(df_nav) - 1, 6, dtype=int)
ax.set_xticks(tick_idx)
ax.set_xticklabels(df_nav["Date"].iloc[tick_idx].dt.strftime("%Y-%m-%d"), rotation=45)

# Chú thích và hiển thị
ax.legend()
st.pyplot(fig)

if st.button("Cập nhật NAV lịch sử"):
    df_nav.to_csv("data/nav_history.csv", index=False)
    st.success("Đã cập nhật thành công")
st.subheader("📈 Biến động NAV theo thời gian")

df_nav_log = pd.read_csv("data/nav_log.csv")
df_nav_log["Date"] = pd.to_datetime(df_nav_log["Date"])

st.line_chart(df_nav_log.set_index("Date"))
