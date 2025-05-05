import pandas as pd
from collections import defaultdict, deque
from get_price import get_price_cp68
import streamlit as st

# ĐỌC DỮ LIỆU, SẮP XẾP LẠI
df = pd.read_excel("Data.xlsx", sheet_name="LSMB")  # Đọc sheet LSMB từ file excel
df = df.sort_values("Date")  # Sắp xếp theo thời gian để đúng trình tự FIFO
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
        {
            "Stock": stock,
            "Quantity": total_qty,
            "Avg_Price": round(avg_price, 2),
            "Total_Cost": round(total_cost, 0),
        }
    )

# TRẢ KẾT QUẢ RA DATAFRAME
df_danh_muc = pd.DataFrame(danh_muc)
df_danh_muc["Market_price"] = df_danh_muc["Stock"].apply(get_price_cp68) * 1000
df_danh_muc["Market_Value"] = df_danh_muc["Market_price"] * df_danh_muc["Quantity"]
df_danh_muc["PnL"] = (
    df_danh_muc["Market_Value"] - df_danh_muc["Quantity"] * df_danh_muc["Avg_Price"]
)
df_danh_muc["PnL_perc"] = (
    df_danh_muc["PnL"] / (df_danh_muc["Quantity"] * df_danh_muc["Avg_Price"]) * 100
)

# GIAO DIỆN STREAMLIT
st.set_page_config(page_title="Dashboard Portfolio Managetment", layout="wide")
st.title("📈 Danh Mục Đầu Tư")

total_PnL = df_danh_muc["PnL"].sum()
st.metric("Tổng lãi/Lỗ chưa thực hiện", f"{total_PnL:,.0f} VNĐ", delta_color="normal")


# TÔ MÀU LÃI LỖ
def highlight_pnl(val):
    color = "green" if val > 0 else "red" if val < 0 else "black"
    return f"color: {color}"


st.dataframe(
    df_danh_muc.style.format(
        {
            "Avg_Price": "{:,.0f}",
            "Market_price": "{:,.0f}",
            "Market_Value": "{:,.0f}",
            "PnL_perc": "{:,.2f} %",
            "PnL": "{:,.0f}",
        }
    ).applymap(highlight_pnl, subset=["PnL", "PnL_perc"])
)
