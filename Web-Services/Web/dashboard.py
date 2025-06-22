import streamlit as st
import pandas as pd
import json
from streamlit_autorefresh import st_autorefresh
from Page.sales_quantity_products import render_chart_page_sales as render_chart_sales
from Page.customers_and_countries import render_chart_page_customers as render_chart_customers



st.set_page_config(layout="wide")  

st.sidebar.title("📁 Menu")
page = st.sidebar.radio(
    "Chọn trang hiển thị",
    ["Sales,Quantily and Products", "Customers and Countries", "Information"]
)


st.sidebar.markdown("---")
st.sidebar.write("⚙️ Setting")
# 🚀 Chỉ thực hiện autorefresh nếu đang bật realtime
if "realtime" not in st.session_state:
    st.session_state.realtime = True

# 👉 Nút toggle realtime trong sidebar
if st.sidebar.button("🔁 Tắt Realtime" if st.session_state.realtime else "▶️ Turn on realtime"):
    st.session_state.realtime = not st.session_state.realtime

# ✅ CHỈ GỌI MỘT LẦN nếu realtime đang bật
if st.session_state.realtime:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=2000, key="realtime_refresh")

# Hàm đọc dữ liệu
def read_data(path="received_data.jsonl"):
    rows = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                rows.append(json.loads(line))
        return pd.DataFrame(rows)
    except Exception as e:
        st.error(f"Lỗi đọc file: {e}")
        return pd.DataFrame()

# Đọc dữ liệu
df = read_data()

# Xử lý dữ liệu nếu có
if not df.empty and "invoiceDate" in df.columns:
    df["invoiceDate"] = pd.to_datetime(df["invoiceDate"], errors="coerce")
    df = df.dropna(subset=["invoiceDate"])
    df["minute"] = df["invoiceDate"].dt.strftime("%Y-%m-%d %H:%M")

    if "CustomerID" in df.columns:
        df["CustomerID"] = df["CustomerID"].astype(str)

    grouped = df.groupby("minute")["quantity"].sum().reset_index()

    if page == "Sales,Quantily and Products":
        render_chart_sales(df)

    elif page == "Customers and Countries":
        render_chart_customers(df)

    # Trang 3: Thông tin
    elif page == "Information":
        st.title("ℹ️ Thông tin hệ thống")
        st.markdown("""
        - ✅ Dashboard realtime dữ liệu từ FastAPI.
        - 🔄 Tự động làm mới mỗi giây.
        - 📁 File dữ liệu: `received_data.jsonl`.
        """)

else:
    st.warning("Không có dữ liệu được truyền vào")
