from pathlib import Path
import numpy as np
import pandas as pd

SEED = 42
N_ROWS = 25000
OUT = Path(__file__).resolve().parents[1] / "data"
OUT.mkdir(exist_ok=True)

def generate_sales(n=N_ROWS, seed=SEED):
    rng = np.random.default_rng(seed)
    customers = [f"C{v:05d}" for v in range(1, 3601)]
    products = []
    categories = {
        "Electronics": ["Laptop", "Smartphone", "Headphones", "Monitor", "Keyboard"],
        "Home": ["Chair", "Desk", "Lamp", "Cookware", "Storage Box"],
        "Fashion": ["T-Shirt", "Jeans", "Sneakers", "Backpack", "Jacket"],
        "Beauty": ["Face Wash", "Moisturizer", "Sunscreen", "Shampoo", "Perfume"],
        "Sports": ["Yoga Mat", "Dumbbells", "Running Shoes", "Bottle", "Fitness Band"],
    }
    for cat, names in categories.items():
        for i in range(30):
            name = names[i % len(names)] + (f" {i//len(names)+1}" if i >= len(names) else "")
            base = {"Electronics": 18000, "Home": 2400, "Fashion": 1500, "Beauty": 650, "Sports": 2200}[cat]
            price = float(np.round(base * rng.uniform(.55, 1.8), 2))
            cost = float(np.round(price * rng.uniform(.48, .78), 2))
            products.append((f"P{len(products)+1:04d}", name, cat, price, cost))
    p_df = pd.DataFrame(products, columns=["Product_ID","Product","Category","Unit_Price","Unit_Cost"])
    p_idx = rng.integers(0, len(p_df), n)
    chosen = p_df.iloc[p_idx].reset_index(drop=True)

    start = np.datetime64("2024-01-01")
    days = rng.integers(0, 1035, n)
    dates = pd.to_datetime(start + days.astype("timedelta64[D]"))
    customer_ids = rng.choice(customers, n)
    regions = rng.choice(["North","South","East","West","Central"], n, p=[.19,.27,.16,.23,.15])
    channels = rng.choice(["Online","Store","Mobile App","Marketplace"], n, p=[.35,.27,.23,.15])
    qty = rng.choice([1,2,3,4,5], n, p=[.48,.27,.14,.07,.04])
    discount_pct = np.clip(rng.beta(1.5, 8, n) * .55, 0, .45)
    unit_price = chosen["Unit_Price"].to_numpy()
    unit_cost = chosen["Unit_Cost"].to_numpy()
    gross = qty * unit_price
    discount = np.round(gross * discount_pct, 2)
    returned = rng.choice([0, 0, 0, 0, 1], n, p=[.86,.05,.04,.03,.02]).astype(bool)
    return_pct = np.where(returned, rng.uniform(.5, 1.0, n), 0)
    returned_amount = np.round((gross-discount) * return_pct, 2)
    ship_cost = np.round(rng.uniform(25, 240, n), 2)
    payment = rng.choice(["UPI","Credit Card","Debit Card","Net Banking","Cash"], n)
    status = np.where(returned, "Returned", rng.choice(["Delivered","Delivered","Delivered","Cancelled"], n, p=[.72,.18,.07,.03]))
    df = pd.DataFrame({
        "Order_ID": [f"O{v:07d}" for v in range(1,n+1)],
        "Order_Date": dates,
        "Customer_ID": customer_ids,
        "Product_ID": chosen["Product_ID"].to_numpy(),
        "Product": chosen["Product"].to_numpy(),
        "Category": chosen["Category"].to_numpy(),
        "Region": regions,
        "Sales_Channel": channels,
        "Quantity": qty,
        "Unit_Price": unit_price,
        "Unit_Cost": unit_cost,
        "Discount_Pct": np.round(discount_pct,4),
        "Discount_Amount": discount,
        "Returned_Amount": returned_amount,
        "Shipping_Cost": ship_cost,
        "Payment_Method": payment,
        "Order_Status": status,
    })
    # Inject a small number of common data-quality issues for cleaning demonstration.
    miss_idx = rng.choice(df.index, size=max(1, n//500), replace=False)
    df.loc[miss_idx[:len(miss_idx)//2], "Region"] = None
    df.loc[miss_idx[len(miss_idx)//2:], "Payment_Method"] = None
    dupes = df.sample(frac=.003, random_state=seed)
    df = pd.concat([df, dupes], ignore_index=True)
    return df

if __name__ == "__main__":
    data = generate_sales()
    data.to_csv(OUT / "retail_sales_raw.csv", index=False)
    print(f"Created {len(data):,} raw rows at {OUT / 'retail_sales_raw.csv'}")
