-- 1. Executive KPI snapshot
SELECT COUNT(DISTINCT order_id) AS orders,
       COUNT(DISTINCT customer_id) AS customers,
       SUM(net_revenue) AS net_revenue,
       SUM(net_profit) AS net_profit,
       ROUND(100.0 * SUM(net_profit) / NULLIF(SUM(net_revenue),0),2) AS profit_margin_pct
FROM sales;

-- 2. Monthly revenue, profit and growth using LAG
WITH monthly AS (
  SELECT DATE_TRUNC('month', order_date)::date AS month_start,
         SUM(net_revenue) AS revenue, SUM(net_profit) AS profit
  FROM sales GROUP BY 1
)
SELECT month_start, revenue, profit,
       ROUND(100.0 * (revenue-LAG(revenue) OVER(ORDER BY month_start))
             / NULLIF(LAG(revenue) OVER(ORDER BY month_start),0),2) AS revenue_mom_growth_pct
FROM monthly ORDER BY month_start;

-- 3. Category profitability ranking
SELECT category, SUM(net_revenue) AS revenue, SUM(net_profit) AS profit,
       ROUND(100.0*SUM(net_profit)/NULLIF(SUM(net_revenue),0),2) AS margin_pct,
       DENSE_RANK() OVER(ORDER BY SUM(net_profit) DESC) AS profit_rank
FROM sales GROUP BY category ORDER BY profit_rank;

-- 4. Regional performance
SELECT region, COUNT(DISTINCT order_id) AS orders,
       SUM(net_revenue) AS revenue, SUM(net_profit) AS profit
FROM sales GROUP BY region ORDER BY revenue DESC;

-- 5. Customer lifetime value proxy and customer ranking
WITH customer_value AS (
  SELECT customer_id, COUNT(DISTINCT order_id) AS order_count,
         SUM(net_revenue) AS lifetime_revenue, SUM(net_profit) AS lifetime_profit,
         MAX(order_date) AS last_order_date
  FROM sales GROUP BY customer_id
)
SELECT *, DENSE_RANK() OVER(ORDER BY lifetime_revenue DESC) AS revenue_rank
FROM customer_value ORDER BY lifetime_revenue DESC LIMIT 20;

-- 6. Discount impact analysis
SELECT CASE WHEN discount_pct < .05 THEN '0-5%'
            WHEN discount_pct < .15 THEN '5-15%'
            WHEN discount_pct < .25 THEN '15-25%' ELSE '25%+' END AS discount_band,
       COUNT(*) AS lines, SUM(net_revenue) AS revenue, SUM(net_profit) AS profit,
       ROUND(100.0*SUM(net_profit)/NULLIF(SUM(net_revenue),0),2) AS margin_pct
FROM sales GROUP BY 1 ORDER BY 1;

-- 7. Return analysis
SELECT category, COUNT(*) AS line_count,
       SUM(CASE WHEN order_status='Returned' THEN 1 ELSE 0 END) AS returned_lines,
       ROUND(100.0*AVG(CASE WHEN order_status='Returned' THEN 1.0 ELSE 0.0 END),2) AS return_rate_pct,
       SUM(returned_amount) AS returned_value
FROM sales GROUP BY category ORDER BY return_rate_pct DESC;

-- 8. Top products within each region (window function)
WITH product_region AS (
  SELECT region, product, SUM(net_profit) AS profit
  FROM sales GROUP BY region, product
), ranked AS (
  SELECT *, ROW_NUMBER() OVER(PARTITION BY region ORDER BY profit DESC) AS rn
  FROM product_region
)
SELECT region, product, profit FROM ranked WHERE rn <= 5 ORDER BY region, rn;

-- 9. Repeat customer rate
WITH customer_orders AS (
  SELECT customer_id, COUNT(DISTINCT order_id) AS orders
  FROM sales GROUP BY customer_id
)
SELECT COUNT(*) FILTER (WHERE orders > 1) AS repeat_customers,
       COUNT(*) AS total_customers,
       ROUND(100.0*COUNT(*) FILTER (WHERE orders > 1)/NULLIF(COUNT(*),0),2) AS repeat_customer_pct
FROM customer_orders;

-- 10. Channel mix
SELECT sales_channel, SUM(net_revenue) AS revenue,
       SUM(net_profit) AS profit,
       ROUND(100.0*SUM(net_revenue)/SUM(SUM(net_revenue)) OVER(),2) AS revenue_share_pct
FROM sales GROUP BY sales_channel ORDER BY revenue DESC;
