def calculate_portfolio(customer_name):
    df_cust = df_trades[df_trades["Customer"] == customer_name].copy()
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
        market_price = get_price_cp68(stock)  # Hàm lấy giá web chồng đã có
        market_value = market_price * total_qty
        pnl = market_value - total_cost

        data.append(
            {
                "Customer": customer_name,
                "Stock": stock,
                "Quantity": total_qty,
                "Avg_Price": round(avg_price),
                "Total_Cost": round(total_cost),
                "Market_Price": round(market_price),
                "Market_Value": round(market_value),
                "PnL": round(pnl),
            }
        )

    return pd.DataFrame(data)
