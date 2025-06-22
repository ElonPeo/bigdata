import time
import requests
import pandas as pd

# Cấu hình
API_ENDPOINT = "http://localhost:8000/ingest"  # Đầu nhận dữ liệu

# Đọc dữ liệu từ Excel
df = pd.read_excel("Data/Online_Retail.xlsx")

# Xử lý thời gian: cắt về phút
df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"])
df["InvoiceMinute"] = df["InvoiceDate"].dt.floor("min")

# Nhóm dữ liệu theo từng phút
grouped = df.groupby("InvoiceMinute")

# Gửi dữ liệu theo từng phút
for invoice_minute, group in grouped:
    print(f"\n⏱️ Gửi {len(group)} dòng cho phút: {invoice_minute}")

    payloads = []
    for _, row in group.iterrows():
        payloads.append({
            "invoiceNo": row["InvoiceNo"],
            "stockCode": str(row["StockCode"]),
            "description": str(row["Description"]),
            "quantity": int(row["Quantity"]),
            "unitPrice": float(row["UnitPrice"]),
            "invoiceDate": row["InvoiceDate"].strftime("%Y-%m-%d %H:%M:%S"),
            "customerID": str(row["CustomerID"]),
            "country": row["Country"]
        })

    # Gửi tất cả dòng trong phút đó cùng lúc
    try:
        res = requests.post(API_ENDPOINT, json=payloads)
        print(f"✅ Đã gửi {len(payloads)} dòng | Status: {res.status_code}")
    except Exception as e:
        print("❌ Lỗi khi gửi:", e)

    # Đợi 1 giây rồi mới gửi phút tiếp theo
    time.sleep(1)
