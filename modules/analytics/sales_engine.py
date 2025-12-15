# modules/analytics/sales_engine.py

import pandas as pd
import os

class SalesEngine:
    def __init__(self, data_path="data/raw/sales/women_sales.csv"):
        self.data_path = data_path
        self.sales = pd.read_csv(self.data_path)
        self.clean_data()

    # ------------------------------
    # Step 1: Data cleaning
    # ------------------------------
    def clean_data(self):
        df = self.sales.copy()

        # 轉換日期格式
        df["order_date"] = pd.to_datetime(df["order_date"])

        # 建立時間欄位
        df["year"] = df["order_date"].dt.year
        df["month"] = df["order_date"].dt.month
        df["day"] = df["order_date"].dt.day
        df["weekday"] = df["order_date"].dt.day_name()

        # 建立價格帶欄位
        df["price_band"] = pd.cut(
            df["unit_price"],
            bins=[0, 20, 50, 100, 200, 500, 2000],
            labels=["<20", "20-50", "50-100", "100-200", "200-500", "500+"]
        )

        self.sales_clean = df

    # ------------------------------
    # Step 2: Summary tables
    # ------------------------------
    def build_summary(self):
        df = self.sales_clean.copy()

        # 日期銷售
        daily_sales = df.groupby("order_date")["revenue"].sum().reset_index()

        # 月份銷售
        monthly_sales = df.groupby(["year", "month"])["revenue"].sum().reset_index()

        # 品項銷售（SKU）
        sku_sales = (
            df.groupby("sku")[["quantity", "revenue"]]
            .sum()
            .sort_values("revenue", ascending=False)
            .reset_index()
        )

        # 顏色銷售
        color_sales = df.groupby("color")["revenue"].sum().reset_index()

        # 尺寸銷售
        size_sales = df.groupby("size")["revenue"].sum().reset_index()

        # 價格帶銷售
        price_band_sales = df.groupby("price_band")["revenue"].sum().reset_index()

        self.daily_sales = daily_sales
        self.monthly_sales = monthly_sales
        self.sku_sales = sku_sales
        self.color_sales = color_sales
        self.size_sales = size_sales
        self.price_band_sales = price_band_sales

        return {
            "daily": daily_sales,
            "monthly": monthly_sales,
            "sku": sku_sales,
            "color": color_sales,
            "size": size_sales,
            "price_band": price_band_sales,
        }

    # ------------------------------
    # Step 3: Export processed data
    # ------------------------------
    def export_processed(self, out_dir="data/processed/sales"):
        os.makedirs(out_dir, exist_ok=True)

        self.sales_clean.to_csv(os.path.join(out_dir, "sales_clean.csv"), index=False)
        self.daily_sales.to_csv(os.path.join(out_dir, "daily_sales.csv"), index=False)
        self.monthly_sales.to_csv(os.path.join(out_dir, "monthly_sales.csv"), index=False)
        self.sku_sales.to_csv(os.path.join(out_dir, "sku_sales.csv"), index=False)
        self.color_sales.to_csv(os.path.join(out_dir, "color_sales.csv"), index=False)
        self.size_sales.to_csv(os.path.join(out_dir, "size_sales.csv"), index=False)
        self.price_band_sales.to_csv(os.path.join(out_dir, "price_band_sales.csv"), index=False)

        print("Sales processed files exported!")
