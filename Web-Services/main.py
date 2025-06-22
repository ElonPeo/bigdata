from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from datetime import datetime
import json
import os

app = FastAPI()

# ✅ Xác định đường dẫn tuyệt đối đến thư mục Web và file received_data.jsonl
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # thư mục chứa main.py
WEB_DIR = os.path.join(BASE_DIR, "Web")
DATA_FILE = os.path.join(WEB_DIR, "received_data.jsonl")

# Các trường bắt buộc
REQUIRED_FIELDS = ["description", "quantity", "invoiceDate"]

@app.post("/ingest")
async def ingest_data(request: Request):
    data = await request.json()
    valid_records = []

    def is_valid(record):
        try:
            if not all(record.get(field) not in [None, ""] for field in REQUIRED_FIELDS):
                return False
            quantity = float(record.get("quantity"))
            if quantity < 0:
                return False
            return True
        except (ValueError, TypeError):
            return False

    # Lọc dữ liệu hợp lệ
    if isinstance(data, list):
        valid_records = [record for record in data if is_valid(record)]
    elif isinstance(data, dict):
        if is_valid(data):
            valid_records = [data]
    else:
        return {"message": "❌ Dữ liệu không hợp lệ"}

    # Ghi vào file nếu hợp lệ
        # Ghi vào file nếu hợp lệ
    if valid_records:
        os.makedirs(WEB_DIR, exist_ok=True)  # Đảm bảo thư mục Web tồn tại
        with open(DATA_FILE, "a", encoding="utf-8") as f:
            for record in valid_records:
                # ⚙️ Nếu customerID bị thiếu hoặc null, gán giá trị mặc định
                if record.get("customerID") in [None, ""]:
                    record["customerID"] = "unknown CustomerID"

                f.write(json.dumps(record) + "\n")

        os.makedirs(WEB_DIR, exist_ok=True)  # Đảm bảo thư mục Web tồn tại
        with open(DATA_FILE, "a", encoding="utf-8") as f:
            for record in valid_records:
                f.write(json.dumps(record) + "\n")

    return {
        "message": f"✅ Đã ghi {len(valid_records)} bản ghi hợp lệ",
        "skipped": (len(data) if isinstance(data, list) else 1) - len(valid_records)
    }

@app.get("/api/data")
async def get_data():
    if not os.path.exists(DATA_FILE):
        return JSONResponse(content={"labels": [], "data": []})

    labels = []
    quantities = []

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        for line in f:
            try:
                record = json.loads(line.strip())
                invoice_date = record.get("invoiceDate")
                quantity = record.get("quantity")

                if not invoice_date or quantity is None:
                    continue

                # Parse time: "2020-01-01 12:00:00"
                dt = datetime.strptime(invoice_date, "%Y-%m-%d %H:%M:%S")
                label = dt.strftime("%H:%M")

                labels.append(label)
                quantities.append(quantity)
            except Exception:
                continue  # Bỏ qua dòng lỗi

    return JSONResponse(content={"labels": labels[-20:], "data": quantities[-20:]})
