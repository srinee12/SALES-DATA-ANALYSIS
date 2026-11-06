# Power BI dashboard build guide

## 1. Load data
1. Open Power BI Desktop → Get Data → Text/CSV.
2. Import `data/retail_sales_clean.csv`.
3. Confirm `order_date` is Date, IDs are Text, and monetary fields are Decimal Number.
4. Create a Calendar table:

```DAX
Calendar = CALENDAR(MIN(sales[order_date]), MAX(sales[order_date]))
Year = YEAR('Calendar'[Date])
Month = FORMAT('Calendar'[Date], "MMM")
Month Year = FORMAT('Calendar'[Date], "YYYY-MM")
Month Sort = YEAR('Calendar'[Date])*100 + MONTH('Calendar'[Date])
```

Mark Calendar as the date table and relate Calendar[Date] to sales[order_date].

## 2. Create measures
Copy measures from `DAX_Measures.dax`.

## 3. Recommended report pages
### Page 1 — Executive Overview
- KPI cards: Total Revenue, Total Profit, Total Orders, Total Customers, Profit Margin %
- Line chart: Revenue by Month Year
- Clustered bar: Profit by Category
- Donut: Revenue by Sales Channel
- Slicers: Date, Region, Category, Sales Channel

### Page 2 — Product & Regional Performance
- Matrix: Region × Category with Revenue and Profit
- Bar chart: Top 10 Products by Profit
- Scatter: Revenue vs Profit by Product
- Slicers: Category, Region

### Page 3 — Customer Insights
- Bar chart: Top customers by revenue
- Repeat customer count and AOV cards
- Customer segment distribution (import `outputs/customer_rfm_segments.csv`)
- Table: Customer_ID, Recency, Frequency, Monetary, Segment

### Page 4 — Returns & Discount Analysis
- Return line rate and returned value cards
- Return rate by category
- Profit margin by discount band (create a calculated column or Power Query conditional column)
- Table of returned transactions

## 4. Design tips
Use a consistent 16:9 canvas, restrained colors, clear titles, aligned KPI cards, and descriptive tooltips. Add a last-refreshed date and a note that the dataset is synthetic.
