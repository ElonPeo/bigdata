import streamlit as st
import pandas as pd
import plotly.express as px
from pandas.tseries.frequencies import to_offset
def render_chart_page_customers(df: pd.DataFrame):

    #------------------------------------------------------------------------
    data_type = st.sidebar.selectbox(
        "📌 Hiển thị theo",
        ["Quantity", "Total (Quantity x UnitPrice)"]
    )
    resample_rule = st.sidebar.selectbox(
        "⏱️ Khoảng thời gian nhóm",
        ["30min", "1H", "8H", "1D", "1W"]
    )
    df["invoiceDate"] = pd.to_datetime(df["invoiceDate"], errors="coerce")
    df = df.dropna(subset=["invoiceDate"])
    df = df.set_index("invoiceDate")
    df["total"] = df["quantity"] * df["unitPrice"]
    if data_type == "Quantity":
        grouped = df["quantity"].resample(resample_rule).sum().reset_index()
    else:
        grouped = df["total"].resample(resample_rule).sum().reset_index()

    grouped["time_label"] = grouped["invoiceDate"].dt.strftime("%Y-%m-%d %H:%M")

        # Tính khoảng thời gian gần nhất cần giữ lại
    max_time = df.index.max()
    if resample_rule == "30min":
        time_delta = pd.Timedelta(minutes=30)
    elif resample_rule == "1H":
        time_delta = pd.Timedelta(hours=1)
    elif resample_rule == "8H":
        time_delta = pd.Timedelta(hours=8)
    elif resample_rule == "1D":
        time_delta = pd.Timedelta(days=1)
    elif resample_rule == "1W":
        time_delta = pd.Timedelta(weeks=1)
    else:
        time_delta = pd.Timedelta(days=1)  # fallback

    min_time = max_time - time_delta
    recent_df = df[(df.index > min_time) & (df.index <= max_time)]
    start_str = min_time.strftime("%Y-%m-%d %H:%M")
    end_str = max_time.strftime("%Y-%m-%d %H:%M")

    # Lọc dữ liệu trong khoảng thời gian gần nhất
    recent_df = df[(df.index > min_time) & (df.index <= max_time)]



    #-------------------------------------------------------
    # --- Biểu đồ tròn theo quốc gia ---
    st.subheader("🌍 Biểu đồ tròn theo quốc gia")
    st.markdown(f"Biểu đồ tròn theo quốc gia theo {data_type.lower()} ({start_str} → {end_str})")
    # Nhóm theo quốc gia và tính tổng
    if data_type == "Quantity":
        country_data = recent_df.groupby("country")["quantity"].sum().reset_index()
    else:
        country_data = recent_df.groupby("country")["total"].sum().reset_index()

    # Sắp xếp và vẽ biểu đồ tròn
    country_data = country_data.sort_values(by=country_data.columns[1], ascending=False)

    fig_pie = px.pie(
        country_data,
        names="country",
        values=country_data.columns[1],
        title=f"Tỉ lệ {data_type.lower()} theo quốc gia (trong {resample_rule} gần nhất)"
    )
    st.plotly_chart(fig_pie, use_container_width=True)

    



    # ------------------------------------------------------------------------------------
    st.subheader("👤 Top khách hàng theo tổng chi tiêu")

    # Gộp các customerID null thành 'Unknown'
    customer_df = recent_df.copy()
    customer_df["customerID"] = customer_df["customerID"].fillna("Unknown")
    customer_df["customerID"] = customer_df["customerID"].astype(str)

    customer_spending = customer_df.groupby("customerID")["total"].sum().reset_index()
    customer_spending = customer_spending.rename(columns={"total": "total_spent"})

    top_n = 10
    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"Top 10 khách hàng chi tiêu cao nhất theo {data_type.lower()} ({start_str} → {end_str})")

        # Tạo cột xếp hạng để hiển thị thứ tự
        top_customers = customer_spending.sort_values(by="total_spent", ascending=False).head(top_n).copy()
        top_customers["Thứ tự"] = range(1, len(top_customers) + 1)

        fig_top_customers = px.bar(
            top_customers,
            x="Thứ tự",
            y="total_spent",
            labels={"total_spent": "Tổng chi tiêu (£)", "Thứ tự": "Top"},
            hover_data=["customerID"],
            title=f"Top 10 khách hàng chi tiêu cao nhất (trong {resample_rule} gần nhất)",
        )
        fig_top_customers.update_layout(width=500, height=400)
        st.plotly_chart(fig_top_customers, use_container_width=False)


    with col2:
        st.markdown(f"Top 10 khách hàng chi tiêu thấp nhất theo {data_type.lower()}  ({start_str} → {end_str})")

        bottom_customers = customer_spending.sort_values(by="total_spent", ascending=True).head(top_n).copy()
        bottom_customers["Thứ tự"] = range(1, len(bottom_customers) + 1)

        fig_bottom_customers = px.bar(
            bottom_customers,
            x="Thứ tự",
            y="total_spent",
            labels={"total_spent": "Tổng chi tiêu (£)", "Thứ tự": "Top"},
            hover_data=["customerID"],
            title=f"Top 10 khách hàng chi tiêu thấp nhất ({start_str} → {end_str})",
        )
        fig_bottom_customers.update_layout(width=500, height=400)
        st.plotly_chart(fig_bottom_customers, use_container_width=False)
