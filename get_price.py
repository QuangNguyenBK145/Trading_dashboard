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
