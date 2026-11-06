from pathlib import Path
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = ROOT / "outputs"
OUT.mkdir(exist_ok=True)

def load_and_clean(path=DATA / "retail_sales_raw.csv"):
    df = pd.read_csv(path, parse_dates=["Order_Date"])
    df = df.drop_duplicates()
    df["Region"] = df["Region"].fillna("Unknown")
    df["Payment_Method"] = df["Payment_Method"].fillna("Unknown")
    numeric = ["Quantity","Unit_Price","Unit_Cost","Discount_Pct","Discount_Amount",
               "Returned_Amount","Shipping_Cost"]
    for col in numeric:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=["Order_ID","Order_Date","Customer_ID","Product_ID"])
    df = df[(df["Quantity"] > 0) & (df["Unit_Price"] >= 0) & (df["Unit_Cost"] >= 0)]
    df["Gross_Sales"] = df["Quantity"] * df["Unit_Price"]
    df["Net_Revenue"] = (df["Gross_Sales"] - df["Discount_Amount"] - df["Returned_Amount"]).clip(lower=0)
    df["COGS"] = df["Quantity"] * df["Unit_Cost"]
    df["Net_Profit"] = df["Net_Revenue"] - df["COGS"] - df["Shipping_Cost"]
    df["Profit_Margin"] = np.where(df["Net_Revenue"] > 0, df["Net_Profit"] / df["Net_Revenue"], 0)
    df["Year"] = df["Order_Date"].dt.year
    df["Month"] = df["Order_Date"].dt.to_period("M").astype(str)
    df["Quarter"] = df["Order_Date"].dt.to_period("Q").astype(str)
    return df

def create_rfm(df):
    snapshot = df["Order_Date"].max() + pd.Timedelta(days=1)
    rfm = df.groupby("Customer_ID").agg(
        Recency=("Order_Date", lambda x: (snapshot-x.max()).days),
        Frequency=("Order_ID","nunique"),
        Monetary=("Net_Revenue","sum")
    ).reset_index()
    rfm["R_Score"] = pd.qcut(rfm["Recency"].rank(method="first"), 5, labels=[5,4,3,2,1]).astype(int)
    rfm["F_Score"] = pd.qcut(rfm["Frequency"].rank(method="first"), 5, labels=[1,2,3,4,5]).astype(int)
    rfm["M_Score"] = pd.qcut(rfm["Monetary"].rank(method="first"), 5, labels=[1,2,3,4,5]).astype(int)
    score = rfm[["R_Score","F_Score","M_Score"]].sum(axis=1)
    rfm["Segment"] = np.select(
        [score >= 13, (rfm["R_Score"]>=4)&(rfm["F_Score"]>=3),
         (rfm["R_Score"]<=2)&(rfm["F_Score"]>=3), score <= 7],
        ["Champions","Loyal Customers","At Risk","Low Engagement"],
        default="Potential Loyalists"
    )
    return rfm

def save_charts(df):
    sns.set_theme()
    monthly = df.groupby("Month", as_index=False).agg(Revenue=("Net_Revenue","sum"), Profit=("Net_Profit","sum"))
    plt.figure(figsize=(12,5))
    sns.lineplot(data=monthly, x="Month", y="Revenue", label="Revenue")
    sns.lineplot(data=monthly, x="Month", y="Profit", label="Profit")
    plt.xticks(rotation=60); plt.title("Monthly Revenue and Profit"); plt.tight_layout()
    plt.savefig(OUT/"monthly_revenue_profit.png", dpi=160); plt.close()

    cat = df.groupby("Category", as_index=False)["Net_Profit"].sum().sort_values("Net_Profit", ascending=False)
    plt.figure(figsize=(9,5)); plt.barh(cat["Category"], cat["Net_Profit"])
    plt.title("Profit by Product Category"); plt.tight_layout()
    plt.savefig(OUT/"profit_by_category.png", dpi=160); plt.close()

    region = df.groupby("Region", as_index=False)["Net_Revenue"].sum()
    plt.figure(figsize=(8,5)); plt.bar(region["Region"], region["Net_Revenue"])
    plt.title("Net Revenue by Region"); plt.tight_layout()
    plt.savefig(OUT/"revenue_by_region.png", dpi=160); plt.close()

def main():
    df = load_and_clean()
    df.to_csv(DATA/"retail_sales_clean.csv", index=False)
    rfm = create_rfm(df)
    rfm.to_csv(OUT/"customer_rfm_segments.csv", index=False)
    summary = {
        "rows": int(len(df)),
        "customers": int(df.Customer_ID.nunique()),
        "orders": int(df.Order_ID.nunique()),
        "net_revenue": round(float(df.Net_Revenue.sum()),2),
        "net_profit": round(float(df.Net_Profit.sum()),2),
        "profit_margin": round(float(df.Net_Profit.sum()/df.Net_Revenue.sum()),4) if df.Net_Revenue.sum() else 0,
        "return_rate": round(float((df.Order_Status=="Returned").mean()),4)
    }
    pd.Series(summary).to_json(OUT/"kpi_summary.json", indent=2)
    save_charts(df)
    print("Analysis complete. Clean data, RFM segments, KPIs and charts saved.")
    print(pd.Series(summary))
if __name__ == "__main__":
    main()
