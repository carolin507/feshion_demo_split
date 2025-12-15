import pandas as pd
import os

DATA_DIR = "./data/raw/crm"   # ← 依你專案目錄調整，但你截圖看起來相同

customers = pd.read_csv(os.path.join(DATA_DIR, "customers.csv"))
sales = pd.read_csv(os.path.join(DATA_DIR, "sales.csv"))
sales_items = pd.read_csv(os.path.join(DATA_DIR, "salesitems.csv"))
products = pd.read_csv(os.path.join(DATA_DIR, "products.csv"))

print("=== customers.csv ===")
print(customers.columns)

print("\n=== sales.csv ===")
print(sales.columns)

print("\n=== salesitems.csv ===")
print(sales_items.columns)

print("\n=== products.csv ===")
print(products.columns)
