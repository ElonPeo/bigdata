# api_server/main_api.py

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import pandas as pd
import json
import os

# Import các hàm xử lý dữ liệu và mô hình từ thư mục cha của api_server
# (Giả định models/ và utils/ nằm trong cùng cấp với api_server/ hoặc đã được copy vào api_server/)
# Để đơn giản, tôi sẽ giả định chúng đã được copy vào trong api_server/
# Nếu không, bạn cần điều chỉnh đường dẫn import:
# from models.forecasting import predict_sales_with_prophet
# from utils.data_processing import aggregate_daily_sales, get_rfm_data
# Hoặc copy các folder models và utils vào thư mục api_server
# Trong ví dụ này, tôi sẽ giả định copy vào
# Nếu bạn không muốn copy, thì các import sẽ là:
# from ..models.forecasting import predict_sales_with_prophet
# from ..models.recommendation import get_product_recommendations
# from ..models.clv_prediction import segment_customers_rfm
# from ..utils.data_processing import preprocess_dataframe, aggregate_daily_sales, get_rfm_data

# **Để làm ví dụ này hoạt động, hãy đảm bảo bạn copy thư mục `models` và `utils` vào trong thư mục `api_server`**
# Hoặc điều chỉnh đường dẫn import cho phù hợp với cấu trúc dự án của bạn.
# Ví dụ đơn giản:

# Giả định models và utils được copy vào api_server
from models.forecasting import predict_sales_with_prophet
from models.recommendation import get_product_recommendations
from models.clv_prediction import segment_customers_rfm
from utils.data_processing import preprocess_dataframe, aggregate_daily_sales, get_rfm_data

app = FastAPI(
    title="Sales Prediction & Analysis API",
    description="API để dự đoán doanh số, đề xuất sản phẩm và phân đoạn khách hàng từ dữ liệu giao dịch.",
    version="1.0.0"
)

# Đường dẫn tới file dữ liệu (giả định nằm cùng cấp với main_api.py)
DATA_FILE_PATH = "../received_data.jsonl" # Hoặc 'received_data.jsonl' nếu file này nằm trong api_server/

# Hàm đọc dữ liệu (tương tự như Streamlit)
def read_data_for_api(path=DATA_FILE_PATH):
    rows = []
    if not os.path.exists(path):
        raise FileNotFoundError(f"File dữ liệu không tồn tại: {path}")
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                rows.append(json.loads(line))
        return pd.DataFrame(rows)
    except json.JSONDecodeError as e:
        raise ValueError(f"Lỗi phân tích cú pháp JSON trong file {path}: {e}")
    except Exception as e:
        raise Exception(f"Lỗi khi đọc file dữ liệu {path}: {e}")

# Định nghĩa request body cho endpoint dự đoán doanh số
class SalesForecastRequest(BaseModel):
    periods: int = 7 # Mặc định dự đoán 7 ngày

@app.get("/")
async def read_root():
    return {"message": "Chào mừng đến với Sales Prediction & Analysis API!"}

@app.post("/predict_sales/")
async def predict_sales(request: SalesForecastRequest):
    """
    Dự đoán doanh số bán hàng trong tương lai.
    """
    try:
        df_raw = read_data_for_api()
        df = preprocess_dataframe(df_raw.copy())
        
        if df.empty:
            raise HTTPException(status_code=400, detail="Không có dữ liệu hoặc dữ liệu bị lỗi để dự đoán doanh số.")
        
        df_daily_sales = aggregate_daily_sales(df)
        if df_daily_sales.empty or df_daily_sales.shape[0] < 2:
            raise HTTPException(status_code=400, detail="Không đủ dữ liệu doanh số hàng ngày để huấn luyện mô hình Prophet (cần ít nhất 2 ngày).")

        # Prophet không trả về figure trực tiếp qua API, chỉ dữ liệu
        forecast_df, _ = predict_sales_with_prophet(df_daily_sales, periods=request.periods)
        
        if forecast_df.empty:
             raise HTTPException(status_code=500, detail="Lỗi trong quá trình dự đoán doanh số.")

        # Lọc các ngày dự đoán và chuyển đổi sang định dạng JSON
        last_history_date = df_daily_sales['ds'].max()
        future_forecast = forecast_df[forecast_df['ds'] > last_history_date].to_dict(orient="records")
        
        # Để Streamlit có thể vẽ lại biểu đồ, cần gửi lại dữ liệu lịch sử và dự đoán.
        # Hoặc frontend sẽ tự vẽ lại biểu đồ từ dữ liệu mà nó đang có.
        # Ở đây ta gửi dữ liệu dự đoán dưới dạng JSON.
        # Frontend sẽ có trách nhiệm hiển thị.
        
        return JSONResponse(content={"forecast": future_forecast})

    except (FileNotFoundError, ValueError, Exception) as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/recommend_products/")
async def recommend_products(min_support: float = 0.01, min_confidence: float = 0.5):
    """
    Đề xuất sản phẩm dựa trên luật kết hợp (Apriori).
    """
    try:
        df_raw = read_data_for_api()
        df = preprocess_dataframe(df_raw.copy())
        
        if df.empty:
            raise HTTPException(status_code=400, detail="Không có dữ liệu hoặc dữ liệu bị lỗi để đề xuất sản phẩm.")
            
        rules_df = get_product_recommendations(df, min_support=min_support, min_confidence=min_confidence)
        
        if rules_df.empty:
            return JSONResponse(content={"recommendations": [], "message": "Không tìm thấy luật đề xuất nào với ngưỡng đã chọn."})

        return JSONResponse(content={"recommendations": rules_df.to_dict(orient="records")})

    except (FileNotFoundError, ValueError, Exception) as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/segment_customers/")
async def segment_customers(n_clusters: int = 4):
    """
    Phân đoạn khách hàng dựa trên chỉ số RFM bằng K-Means.
    """
    try:
        df_raw = read_data_for_api()
        df = preprocess_dataframe(df_raw.copy())
        
        if df.empty:
            raise HTTPException(status_code=400, detail="Không có dữ liệu hoặc dữ liệu bị lỗi để phân đoạn khách hàng.")
        
        rfm_df = get_rfm_data(df)
        if rfm_df.empty or rfm_df.shape[0] < n_clusters:
            raise HTTPException(status_code=400, detail=f"Không đủ dữ liệu khách hàng để phân cụm (cần ít nhất {n_clusters} khách hàng).")
            
        segmented_rfm_df, _ = segment_customers_rfm(rfm_df.copy(), n_clusters=n_clusters)
        
        if segmented_rfm_df.empty:
            raise HTTPException(status_code=500, detail="Lỗi trong quá trình phân đoạn khách hàng.")

        # Trả về tóm tắt của các cụm
        cluster_summary = segmented_rfm_df.groupby('Cluster_Ranked').agg(
            AvgRecency=('Recency', 'mean'),
            AvgFrequency=('Frequency', 'mean'),
            AvgMonetary=('Monetary', 'mean'),
            NumCustomers=('CustomerID', 'nunique')
        ).sort_values(by='AvgMonetary', ascending=False).reset_index()

        return JSONResponse(content={"cluster_summary": cluster_summary.to_dict(orient="records")})

    except (FileNotFoundError, ValueError, Exception) as e:
        raise HTTPException(status_code=500, detail=str(e))