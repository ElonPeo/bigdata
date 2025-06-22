import streamlit as st
import pandas as pd
import plotly.express as px

def render_chart_page_sales(df: pd.DataFrame):
    st.title("📊 Biểu đồ thống kê")

    # Sidebar: chọn kiểu dữ liệu hiển thị
    data_type = st.sidebar.selectbox(
        "📌 Hiển thị theo",
        ["Quantity", "Total (Quantity x UnitPrice)"],
        key="data_type"
    )

    # Sidebar: chọn khoảng thời gian hiển thị
    time_range_option = st.sidebar.selectbox(
        "🕒 Khoảng thời gian hiển thị",
        ["60 phút gần nhất", "24 giờ gần nhất", "1 tuần gần nhất", "12 tháng gần nhất"],
        key="time_range_option"
    )

    # Tính total
    df["total"] = df["quantity"] * df["unitPrice"]
    df["invoiceDate"] = pd.to_datetime(df["invoiceDate"])
    df = df.set_index("invoiceDate").sort_index()

    # Lấy thời gian hiện tại
    max_time = df.index.max()

    # Thiết lập khoảng thời gian và tần suất lấy mẫu
    if time_range_option == "60 phút gần nhất":
        freq = "1min"
        min_time = max_time - pd.Timedelta(minutes=60)
    elif time_range_option == "24 giờ gần nhất":
        freq = "1H"
        min_time = max_time - pd.Timedelta(hours=24)
    elif time_range_option == "1 tuần gần nhất":
        freq = "8H"
        min_time = max_time - pd.Timedelta(days=7)
    elif time_range_option == "12 tháng gần nhất":
        freq = "1M"
        min_time = max_time - pd.DateOffset(months=12)
    else:
        freq = "1H"
        min_time = df.index.min()

    # Cắt khoảng thời gian
    recent_df = df[(df.index > min_time) & (df.index <= max_time)]

    # Nhóm và gán nhãn
    if data_type == "Quantity":
        grouped = recent_df["quantity"].resample(freq).sum().reset_index()
        y_col = "quantity"
    else:
        grouped = recent_df["total"].resample(freq).sum().reset_index()
        y_col = "total"

    # Định dạng thời gian hiển thị
    if freq in ["1min", "1H", "8H"]:
        grouped["time_label"] = grouped["invoiceDate"].dt.strftime("%Y-%m-%d %H:%M")
    elif freq == "1M":
        grouped["time_label"] = grouped["invoiceDate"].dt.strftime("%Y-%m")

    # Tổng tiền toàn bộ
    start_time = df.index.min().strftime("%Y-%m-%d %H:%M")
    end_time = df.index.max().strftime("%Y-%m-%d %H:%M")
    total_amount = df["total"].sum()

    st.markdown(
        f"### 💰 Tổng tiền: **£{total_amount:,.2f}** (Từ `{start_time}` đến `{end_time}`)"
    )

    # Biểu đồ
    st.subheader(f"📉 Biểu đồ đường theo thời gian ({time_range_option.lower()}) (`{start_time}` - > `{end_time}`) ")
    st.line_chart(grouped.set_index("time_label")[y_col], use_container_width=True)



    # ------------------------------------------------------------------------------
    st.subheader("📌 Biểu đồ phân tán: Giá cả vs Số lượng")

    scatter_df = recent_df.copy()
    scatter_df = scatter_df[(scatter_df["unitPrice"] > 0) & (scatter_df["quantity"] > 0)]

    if scatter_df.empty:
        st.warning("Không có dữ liệu phù hợp để hiển thị biểu đồ phân tán.")
    else:
        fig_scatter = px.scatter(
            scatter_df,
            x="unitPrice",
            y="quantity",
            hover_data=["stockCode", "description"],
            labels={"unitPrice": "Giá sản phẩm (£)", "quantity": "Số lượng bán"},
            title="Mối quan hệ giữa Giá và Số lượng bán (`{start_time}` - > `{end_time}`)",
            opacity=0.6,
        )
        fig_scatter.update_traces(marker=dict(size=6, line=dict(width=0.5, color='DarkSlateGrey')))
        st.plotly_chart(fig_scatter, use_container_width=True)



        # ------------------------------------------------------------------------------------
    st.subheader("🥇 Top sản phẩm theo hiệu suất bán hàng")

    chart_label = "Quantity" if data_type == "Quantity" else "Total (£)"
    col1, col2 = st.columns(2)

    # Lọc dữ liệu gần nhất (đã có recent_df)
    product_df = recent_df.copy()

    # Nhóm và tính tổng
    if data_type == "Quantity":
        product_data = product_df.groupby(["stockCode", "description"])["quantity"].sum().reset_index()
        product_data = product_data.rename(columns={"quantity": "value"})
    else:
        product_data = product_df.groupby(["stockCode", "description"])["total"].sum().reset_index()
        product_data = product_data.rename(columns={"total": "value"})

    # Gắn nhãn sản phẩm
    product_data["product_label"] = product_data["stockCode"] + " - " + product_data["description"]

    with col1:
        st.markdown("#### 🏆 Top 10 sản phẩm bán **chạy nhất**")
        top_products = product_data.sort_values(by="value", ascending=False).head(10)

        fig_bar_top = px.bar(
            top_products,
            x="product_label",
            y="value",
            labels={"value": chart_label, "product_label": "Sản phẩm"},
            title=f"Top 10 sản phẩm theo {chart_label.lower()} (`{start_time}` - > `{end_time}`)",
        )
        fig_bar_top.update_layout(xaxis_tickangle=-45, width=600, height=400)
        st.plotly_chart(fig_bar_top, use_container_width=False)

    with col2:
        st.markdown("#### 📉 Top 10 sản phẩm bán **tệ nhất**")
        bottom_products = product_data.sort_values(by="value", ascending=True).head(10)

        fig_bar_bottom = px.bar(
            bottom_products,
            x="product_label",
            y="value",
            labels={"value": chart_label, "product_label": "Sản phẩm"},
            title=f"Top 10 sản phẩm bán thấp nhất theo {chart_label.lower()} (`{start_time}` - > `{end_time}`)",
        )
        fig_bar_bottom.update_layout(xaxis_tickangle=-45, width=600, height=400)
        st.plotly_chart(fig_bar_bottom, use_container_width=False)
