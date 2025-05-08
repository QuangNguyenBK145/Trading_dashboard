import pandas as pd
from utils.get_price import get_price_cp68, get_price_change, get_market_price_from_log


def calculate_portfolio(customer_name, as_of_date, df_trades, df_price_log):
    df_cust = df_trades[
        (df_trades["Customer"] == customer_name) &
        (df_trades["DateTime"] <= pd.to_datetime(as_of_date))
    ].copy()
    df_cust = df_cust.sort_values("DateTime")

    holdings = {}

    for _, row in df_cust.iterrows():
        stock = row["Stock"]
        volume = int(row["Volume"])
        price = float(row["Price"])
        order = row["Order"]

        if stock not in holdings:
            holdings[stock] = []

        if order == "Mua":
            holdings[stock].append({"volume": volume, "price": price})
        elif order == "Bán":
            vol_to_sell = volume
            while vol_to_sell > 0 and holdings[stock]:
                batch = holdings[stock][0]
                if batch["volume"] <= vol_to_sell:
                    vol_to_sell -= batch["volume"]
                    holdings[stock].pop(0)
                else:
                    batch["volume"] -= vol_to_sell
                    vol_to_sell = 0

    # Tính danh mục hiện tại
    data = []
    for stock, batches in holdings.items():
        total_qty = sum(b["volume"] for b in batches)
        if total_qty == 0:
            continue
        total_cost = sum(b["volume"] * b["price"] for b in batches)
        avg_price = total_cost / total_qty
        market_price = get_market_price_from_log(stock, as_of_date, df_price_log) * 1000
        if market_price is None:
            continue
        market_value = market_price * total_qty
        pnl = market_value - total_cost

        data.append({
            "Customer": customer_name,
            "Stock": stock,
            "Quantity": total_qty,
            "Avg_Price": round(avg_price),
            "Total_Cost": round(total_cost),
            "Market_Price": round(market_price),
            "Market_Value": round(market_value),
            "PnL": round(pnl)
        })

    return pd.DataFrame(data)

def calculate_cashflow(customer_name, as_of_date, df_cashflow):
    """
    Tính tổng tiền mặt đã nộp/rút của khách hàng đến thời điểm nhất định.
    
    Args:
        customer_name (str): Tên khách hàng
        as_of_date (str or pd.Timestamp): Ngày tính NAV
        df_cashflow (DataFrame): Dữ liệu log nộp/rút

    Returns:
        float: Tổng tiền mặt ròng
    """
    as_of_date = pd.to_datetime(as_of_date)

    df = df_cashflow[
        (df_cashflow["Customer"] == customer_name) &
        (df_cashflow["DateTime"] <= as_of_date)
    ]

    return df["Amount"].sum()

def calculate_realized_pnl(customer_name, as_of_date, df_trades):
    """
    Tính lãi/lỗ đã thực hiện (realized PnL) từ các giao dịch bán của khách hàng.

    Args:
        customer_name (str): Tên khách hàng
        as_of_date (str or pd.Timestamp): Ngày cần tính
        df_trades (DataFrame): Dữ liệu giao dịch

    Returns:
        float: Tổng realized PnL
    """
    df_cust = df_trades[
        (df_trades["Customer"] == customer_name) &
        (df_trades["DateTime"] <= pd.to_datetime(as_of_date))
    ].copy()
    df_cust = df_cust.sort_values("DateTime")

    holdings = {}
    realized_pnl = 0

    for _, row in df_cust.iterrows():
        stock = row["Stock"]
        volume = int(row["Volume"])
        price = float(row["Price"])
        order = row["Order"]

        if stock not in holdings:
            holdings[stock] = []

        if order == "Mua":
            holdings[stock].append({"volume": volume, "price": price})
        elif order == "Bán":
            vol_to_sell = volume
            while vol_to_sell > 0 and holdings[stock]:
                batch = holdings[stock][0]
                batch_vol = batch["volume"]
                batch_price = batch["price"]

                if batch_vol <= vol_to_sell:
                    realized_pnl += (price - batch_price) * batch_vol
                    vol_to_sell -= batch_vol
                    holdings[stock].pop(0)
                else:
                    realized_pnl += (price - batch_price) * vol_to_sell
                    batch["volume"] -= vol_to_sell
                    vol_to_sell = 0

    return round(realized_pnl)

def calculate_nav_home(customer_name, as_of_date, df_trades, df_cashflow):
    """
    Tính NAV tổng hợp của khách hàng đến một ngày cụ thể.

    Args:
        customer_name (str)
        as_of_date (str or pd.Timestamp)
        df_trades (DataFrame)
        df_cashflow (DataFrame)
        df_price_log (DataFrame)

    Returns:
        dict: Thông tin NAV và các thành phần
    """
    # Tính từng phần
    net_cash = calculate_cashflow(customer_name, as_of_date, df_cashflow)
    realized_pnl = calculate_realized_pnl(customer_name, as_of_date, df_trades)
    
    # Tổng NAV
    nav = net_cash + realized_pnl

    return {
        "Customer": customer_name,
        "Date": as_of_date,
        "Net_Cash": round(net_cash),
        "Realized_PnL": round(realized_pnl),
        "NAV": round(nav)
    }

def calculate_nav(customer_name, as_of_date, df_trades, df_cashflow, df_price_log):
    """
    Tính NAV tổng hợp của khách hàng đến một ngày cụ thể.

    Args:
        customer_name (str)
        as_of_date (str or pd.Timestamp)
        df_trades (DataFrame)
        df_cashflow (DataFrame)
        df_price_log (DataFrame)

    Returns:
        dict: Thông tin NAV và các thành phần
    """
    # Tính từng phần
    net_cash = calculate_cashflow(customer_name, as_of_date, df_cashflow)
    realized_pnl = calculate_realized_pnl(customer_name, as_of_date, df_trades)
    df_portfolio = calculate_portfolio(customer_name, as_of_date, df_trades, df_price_log)
    unrealized_pnl = df_portfolio["PnL"].sum() if not df_portfolio.empty else 0

    # Tổng NAV
    nav = net_cash + realized_pnl + unrealized_pnl

    return {
        "Customer": customer_name,
        "Date": as_of_date,
        "Net_Cash": round(net_cash),
        "Realized_PnL": round(realized_pnl),
        "Unrealized_PnL": round(unrealized_pnl),
        "NAV": round(nav)
    }