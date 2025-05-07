import requests
from bs4 import BeautifulSoup


def get_price_cp68(symbol):
    url = f"https://www.cophieu68.vn/quote/summary.php?id={symbol.lower()}&stockname_search=Submit"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        tag = soup.find(id="stockname_close")
        if tag:
            price = tag.text.strip().replace(",", "")
            return float(price)
        else:
            print(f"Không tìm thấy giá cho mã {symbol}")
            return None

    except Exception as e:
        print(f"Lỗi lấy giá {symbol}: {e}")
        return None

def get_price_change(symbol):
    url = f"https://www.cophieu68.vn/quote/summary.php?id={symbol.lower()}"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        tag = soup.find(id = "stockname_price_change")
        if tag:
            price_change = tag.text.strip().replace(",", "")
            return float(price_change)
        else:
            print(f"Không tìm thấy thay đổi giá cho mã{symbol}")
            return None
    except Exception as e:
        print(f"Lỗi lấy giá {symbol}: {e}")
        return None
    
import pandas as pd
import os

def update_price_log(uploaded_file, stocks_to_keep, log_path="data/price_log.csv"):
    df_new = pd.read_csv(uploaded_file)
    df_new.columns = df_new.columns.str.strip("<>")

    # Chỉ giữ 3 cột cần thiết
    df_new = df_new[["Ticker", "DTYYYYMMDD", "Close"]]
    df_new.rename(columns={"DTYYYYMMDD": "Date"}, inplace=True)

    # Nếu không có cột "Stock" mà lại có "Ticker" thì đổi tên
    if "Stock" not in df_new.columns:
        if "Ticker" in df_new.columns:
            df_new.rename(columns={"Ticker": "Stock"}, inplace=True)
        else:
            raise KeyError(f"Cột 'Stock' không tồn tại. Các cột hiện có: {df_new.columns.tolist()}")

    # Lọc các mã cổ phiếu cần giữ
    df_new = df_new[df_new["Stock"].isin(stocks_to_keep)].copy()

    # Chuẩn hóa định dạng cột ngày
    df_new["Date"] = pd.to_datetime(df_new["Date"]).dt.strftime("%Y-%m-%d")

    # Nếu file log chưa tồn tại hoặc rỗng
    if not os.path.exists(log_path) or os.stat(log_path).st_size == 0:
        df_new.to_csv(log_path, index=False)
        return df_new

    # Đọc dữ liệu cũ và nối thêm dữ liệu mới
    df_old = pd.read_csv(log_path)
    df_all = pd.concat([df_old, df_new], ignore_index=True)

    # Xoá các dòng trùng lặp theo ngày và mã
    df_all = df_all.drop_duplicates(subset=["Date", "Stock"], keep="last")
    df_all.to_csv(log_path, index=False)
    return df_all
