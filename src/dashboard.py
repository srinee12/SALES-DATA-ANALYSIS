from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "retail_sales_clean.csv"

st.set_page_config(page_title="Retail Sales Intelligence", page_icon="📊", layout="wide")
st.title("Retail Sales & Customer Intelligence")
st.caption("Interactive portfolio dashboard | Synthetic retail transactions")

@st.cache_data
def get_data():
    if not DATA.exists():
        st.error("Clean dataset not found. Run: python src/generate_data.py && python src/analysis.py")
        st.stop()
    d = pd.read_csv(DATA, parse_dates=["Order_Date"])
    return d

df = get_data()
with st.sidebar:
    st.header("Filters")
    dates = st.date_input("Order date range", [df.Order_Date.min().date(), df.Order_Date.max().date()])
    regions = st.multiselect("Region", sorted(df.Region.unique()), default=sorted(df.Region.unique()))
    categories = st.multiselect("Category", sorted(df.Category.unique()), default=sorted(df.Category.unique()))
    channels = st.multiselect("Sales channel", sorted(df.Sales_Channel.unique()), default=sorted(df.Sales_Channel.unique()))

filtered = df.copy()
if len(dates) == 2:
    filtered = filtered[filtered.Order_Date.between(pd.Timestamp(dates[0]), pd.Timestamp(dates[1]) + pd.Timedelta(days=1))]
filtered = filtered[filtered.Region.isin(regions) & filtered.Category.isin(categories) & filtered.Sales_Channel.isin(channels)]

revenue = filtered.Net_Revenue.sum()
profit = filtered.Net_Profit.sum()
orders = filtered.Order_ID.nunique()
customers = filtered.Customer_ID.nunique()
margin = profit/revenue if revenue else 0
returns = (filtered.Order_Status=="Returned").mean() if len(filtered) else 0

cols = st.columns(5)
for col, label, value in zip(cols, ["Net Revenue","Net Profit","Orders","Customers","Profit Margin"],
                              [f"₹{revenue:,.0f}",f"₹{profit:,.0f}",f"{orders:,}",f"{customers:,}",f"{margin:.1%}"]):
    col.metric(label, value)
st.metric("Returned line rate", f"{returns:.1%}")

monthly = filtered.assign(Month=filtered.Order_Date.dt.to_period("M").astype(str)).groupby("Month",as_index=False).agg(Net_Revenue=("Net_Revenue","sum"),Net_Profit=("Net_Profit","sum"))
c1,c2 = st.columns(2)
with c1:
    st.subheader("Revenue and profit trend")
    if len(monthly): st.plotly_chart(px.line(monthly,x="Month",y=["Net_Revenue","Net_Profit"],markers=True),use_container_width=True)
with c2:
    st.subheader("Profit by category")
    cat = filtered.groupby("Category",as_index=False).Net_Profit.sum().sort_values("Net_Profit",ascending=False)
    if len(cat): st.plotly_chart(px.bar(cat,x="Category",y="Net_Profit",color="Category"),use_container_width=True)

c3,c4 = st.columns(2)
with c3:
    st.subheader("Regional performance")
    reg = filtered.groupby("Region",as_index=False).Net_Revenue.sum()
    if len(reg): st.plotly_chart(px.bar(reg,x="Region",y="Net_Revenue",color="Region"),use_container_width=True)
with c4:
    st.subheader("Channel contribution")
    ch = filtered.groupby("Sales_Channel",as_index=False).Net_Revenue.sum()
    if len(ch): st.plotly_chart(px.pie(ch,names="Sales_Channel",values="Net_Revenue",hole=.45),use_container_width=True)

st.subheader("Top 10 products by profit")
top = filtered.groupby(["Product","Category"],as_index=False).agg(Revenue=("Net_Revenue","sum"),Profit=("Net_Profit","sum")).nlargest(10,"Profit")
st.dataframe(top, use_container_width=True, hide_index=True)
st.subheader("Filtered transaction detail")
st.dataframe(filtered.head(1000), use_container_width=True, hide_index=True)
st.download_button("Download filtered data", filtered.to_csv(index=False).encode("utf-8"), "filtered_sales.csv", "text/csv")
