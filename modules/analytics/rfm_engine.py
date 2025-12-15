import pandas as pd
import os

class CRMEngine:
    def __init__(self, data_dir="./data/raw/crm"):
        self.data_dir = data_dir
        self.load_data()

    def load_data(self):
        self.customers = pd.read_csv(os.path.join(self.data_dir, "customers.csv"))
        self.sales = pd.read_csv(os.path.join(self.data_dir, "sales.csv"))
        self.sales_items = pd.read_csv(os.path.join(self.data_dir, "salesitems.csv"))
        self.products = pd.read_csv(os.path.join(self.data_dir, "products.csv"))

        # 轉換日期欄位
        self.sales["sale_date"] = pd.to_datetime(self.sales["sale_date"])
        self.sales_items["sale_date"] = pd.to_datetime(self.sales_items["sale_date"])
        self.customers["signup_date"] = pd.to_datetime(self.customers["signup_date"])

    # ---------------------------------------------------------
    # Step 1: 產生 sales_full（訂單明細 + 訂單 + 商品）
    # ---------------------------------------------------------
    def build_sales_full(self):
        # merge sales × sales_items
        df = self.sales.merge(
            self.sales_items,
            on="sale_id",
            how="inner",
            suffixes=("_order", "_item")
        )

        # merge product details
        df = df.merge(
            self.products,
            on="product_id",
            how="left"
        )

        # 確保 item_total 存在
        if "item_total" not in df.columns:
            df["item_total"] = df["unit_price"] * df["quantity"]

        self.sales_full = df
        return df

    # ---------------------------------------------------------
    # Step 2: RFM 模型
    # ---------------------------------------------------------
    def build_rfm(self):
        df = self.sales_full.copy()

        # 訂單主表（_order 欄位才是正確的 sale_date）
        sale_date_col = "sale_date_order"

        if sale_date_col not in df.columns:
            raise ValueError(f"欄位 {sale_date_col} 不存在，請檢查 merge 結果：{df.columns}")

        # 設定分析日
        analysis_date = df[sale_date_col].max() + pd.Timedelta(days=1)

        rfm = (
            df.groupby("customer_id")
            .agg(
                recency=(sale_date_col, lambda x: (analysis_date - x.max()).days),
                frequency=("sale_id", "nunique"),
                monetary=("item_total", "sum")
            )
            .reset_index()
        )

        # 五分位打分
        rfm["R_score"] = pd.qcut(rfm["recency"], 5, labels=[5,4,3,2,1]).astype(int)
        rfm["F_score"] = pd.qcut(rfm["frequency"].rank(method="first"), 5, labels=[1,2,3,4,5]).astype(int)
        rfm["M_score"] = pd.qcut(rfm["monetary"].rank(method="first"), 5, labels=[1,2,3,4,5]).astype(int)

        rfm["RFM_score"] = rfm["R_score"] + rfm["F_score"] + rfm["M_score"]

        # Segment
        def segment(row):
            if row["RFM_score"] >= 13:
                return "VIP / Champions"
            elif row["RFM_score"] >= 10:
                return "Loyal"
            elif row["RFM_score"] >= 7:
                return "Potential"
            elif row["RFM_score"] >= 5:
                return "Need Attention"
            else:
                return "At Risk / Lost"

        rfm["segment"] = rfm.apply(segment, axis=1)

        # merge demographic fields
        rfm = rfm.merge(self.customers, on="customer_id", how="left")

        self.rfm = rfm
        return rfm

    # ---------------------------------------------------------
    # Step 3: 輸出結果給 Streamlit
    # ---------------------------------------------------------
    def export_processed(self, out_dir="./data/processed/crm"):
        os.makedirs(out_dir, exist_ok=True)
        self.sales_full.to_csv(os.path.join(out_dir, "sales_full.csv"), index=False)
        self.rfm.to_csv(os.path.join(out_dir, "customers_rfm.csv"), index=False)
