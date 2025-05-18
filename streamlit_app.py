import streamlit as st
import pandas as pd
import numpy as np
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
import matplotlib.pyplot as plt

# → 港口供應商位置資訊（根據用戶提供）
supplier_location_df = pd.DataFrame({
    "Supplier": [
        "Shanghai", "Singapore", "Ningbo-Zhoushan", "Shenzhen", "Busan",
        "Qingdao", "Tianjin", "Rotterdam", "Kaohsiung", "Tokyo"
    ],
    "Country/Region": [
        "China", "Singapore", "China", "China", "South Korea",
        "China", "China", "Netherlands", "Taiwan", "Japan"
    ],
    "Latitude": [
        31.2304, 1.2644, 29.9348, 22.5431, 35.0951,
        36.0671, 38.9792, 51.9550, 22.6163, 35.6275
    ],
    "Longitude": [
        121.4910, 103.8226, 121.8096, 113.8895, 129.0403,
        120.3208, 117.7173, 4.1146, 120.2980, 139.7630
    ]
})

suppliers = supplier_location_df["Supplier"].tolist()
dates = pd.date_range(start="2023-01-01", periods=24, freq="M")

# → KPI 模擬資料
np.random.seed(42)
data = pd.DataFrame({
    "Supplier": np.repeat(suppliers, len(dates)),
    "Date": dates.tolist() * len(suppliers),
    "Frequency_of_risk_assessments": np.random.randint(0, 5, size=240),
    "Supplier_geographic_diversity_index": np.round(np.random.uniform(0.4, 0.9, size=240), 2),
    "Critical_suppliers_with_mitigation_%": np.round(np.random.uniform(0.5, 1.0, size=240), 2),
    "Production_in_high_risk_areas_%": np.round(np.random.uniform(0.1, 0.5, size=240), 2),
    "Forecast": np.random.randint(800, 1200, size=240),
    "Actual": np.random.randint(800, 1200, size=240),
    "Planned_Supply_Units": np.random.randint(1000, 2000, size=240),
    "Delivered_Supply_Units": np.random.randint(800, 2200, size=240),
    "Units_Produced": np.random.randint(500, 1000, size=240),
    "Machine/Shift_Hours_Available": np.random.randint(100, 200, size=240),
    "Std_Prod_Rate": np.random.randint(5, 10, size=240),
    "Date_Ramp_Trigger": pd.date_range(start="2022-12-01", periods=240, freq="D"),
    "Date_Target_Capacity_Achieved": pd.date_range(start="2023-01-01", periods=240, freq="D"),
    "SKU_ID": np.random.choice([f"SKU_{i}" for i in range(50)], size=240),
    "#_Approved_Suppliers_Per_SKU": np.random.randint(1, 4, size=240),
    "Lead_Time_Days": np.random.randint(5, 60, size=240),
    "Supplier_Risk_Score": np.round(np.random.uniform(0.1, 1.0, size=240), 2),
    "Country_Risk_Index": np.round(np.random.uniform(0.1, 1.0, size=240), 2),
})

# — 基本 KPI 計算 —
data["Forecast_Accuracy"] = (1 - abs(data["Forecast"] - data["Actual"]) / data["Actual"]) * 100
data["Supply_Adherence_%"] = (data["Delivered_Supply_Units"] / data["Planned_Supply_Units"]) * 100
data["Capacity_Utilization_%"] = (
    data["Units_Produced"] /
    (data["Machine/Shift_Hours_Available"] * data["Std_Prod_Rate"])
) * 100
data["Ramp_Up_Time_Days"] = (data["Date_Target_Capacity_Achieved"] - data["Date_Ramp_Trigger"]).dt.days
data["Is_Dual_Sourced"] = data["#_Approved_Suppliers_Per_SKU"] >= 2
data["Risk_Adjusted_Lead_Time"] = data["Lead_Time_Days"]  # 示例中乘除後相同

# — 新增三個模擬指標 —
data["Score_of_News"] = np.round(np.random.uniform(0, 1, size=len(data)), 2)
data["Score_of_Social_Media"] = np.round(np.random.uniform(0, 1, size=len(data)), 2)
data["Audit_Score"] = np.round(np.random.uniform(0, 1, size=len(data)), 2)

# — 雙源採購比率 —
dual_sourcing_ratio = (
    data.groupby("Date")["Is_Dual_Sourced"]
    .mean()
    .mul(100)
    .reset_index()
    .rename(columns={"Is_Dual_Sourced": "%_Dual_Sourcing"})
)

# — 合併地理位置 —
data = data.merge(supplier_location_df, on="Supplier", how="left")

# — 分頁順序（五個 Tab） —
tab4, tab2, tab3, tab1, tab5 = st.tabs([
    "📍 Overview",
    "📋 Supplier Data",
    "📋 KPI Charts",
    "🗺️ Risk Map",
    "📰 Political Issues News"
])

# Tab 4: Location Table
with tab4:
    st.title("📍 Supplier overview")
    st.dataframe(supplier_location_df, use_container_width=True)

# Tab 2: KPI Data Overview
with tab2:
    st.title("📋 Supplier KPI Data Overview")
    selected_supplier = st.selectbox("Select Supplier", ["All"] + suppliers)
    df_filtered = data if selected_supplier == "All" else data[data["Supplier"] == selected_supplier]
    st.dataframe(df_filtered.reset_index(drop=True), use_container_width=True)

# Tab 3: KPI 時序圖
with tab3:
    st.title("📈 Time Series KPI Visualization")
    kpi_options = [
        "Forecast_Accuracy", "Supply_Adherence_%", "Capacity_Utilization_%",
        "Ramp_Up_Time_Days", "Risk_Adjusted_Lead_Time", "%_Dual_Sourcing"
    ]
    selected_kpi = st.selectbox("Select KPI", kpi_options)
    selected_supplier_chart = st.selectbox("Select Supplier for Chart", ["All"] + suppliers)

    if selected_kpi == "%_Dual_Sourcing":
        chart_data = dual_sourcing_ratio.copy()
        chart_title = "% Dual Sourcing Rate (All Suppliers)"
    elif selected_supplier_chart == "All":
        chart_data = data.groupby("Date")[selected_kpi].mean().reset_index()
        chart_title = f"Average {selected_kpi} Over Time"
    else:
        chart_data = data[data["Supplier"] == selected_supplier_chart][["Date", selected_kpi]]
        chart_title = f"{selected_kpi} for {selected_supplier_chart}"

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(chart_data["Date"], chart_data[selected_kpi], marker='o')
    ax.set_title(chart_title)
    ax.set_xlabel("Date")
    ax.set_ylabel(selected_kpi)
    ax.grid(True)
    st.pyplot(fig)

# Tab 1: 風險地圖
with tab1:
    st.title("🌍 Supplier Geopolitical Risk Map")
    latest_date = data["Date"].max()
    latest_data = data[data["Date"] == latest_date].copy()

    # — 考量新指標的加權風險分數計算 —
    latest_data["Risk_Score"] = (
          (1 - latest_data["Supplier_geographic_diversity_index"]) * 0.25
        + (1 - latest_data["Critical_suppliers_with_mitigation_%"]) * 0.25
        +  latest_data["Production_in_high_risk_areas_%"] * 0.20
        + ((4 - latest_data["Frequency_of_risk_assessments"]) / 4) * 0.10
        + (1 - latest_data["Score_of_News"]) * 0.05
        + (1 - latest_data["Score_of_Social_Media"]) * 0.10
        + (1 - latest_data["Audit_Score"]) * 0.05
    )

    m = folium.Map(location=[30, 110], zoom_start=3)
    marker_cluster = MarkerCluster().add_to(m)
    for _, row in latest_data.iterrows():
        color = (
            "red" if row["Risk_Score"] > 0.6
            else "orange" if row["Risk_Score"] > 0.4
            else "green"
        )
        popup_html = (
            f"<b><span style='color:{color}'>{row['Supplier']}</span></b><br>"
            f"<span style='color:{color}'>Risk Score: {row['Risk_Score']:.2f}</span><br>"
            f"High Risk Production %: {row['Production_in_high_risk_areas_%']:.2f}<br>"
            f"Mitigation %: {row['Critical_suppliers_with_mitigation_%']:.2f}<br>"
            f"News Score: {row['Score_of_News']:.2f}<br>"
            f"Social Media Score: {row['Score_of_Social_Media']:.2f}<br>"
            f"Audit Score: {row['Audit_Score']:.2f}<br>"
        )
        popup = folium.Popup(popup_html, max_width=250)
        folium.CircleMarker(
            location=[row["Latitude"], row["Longitude"]],
            radius=8,
            color=color,
            fill=True,
            fill_opacity=0.7,
            popup=popup
        ).add_to(marker_cluster)

    st_folium(m, width=1000, height=600)

# Tab 5: 顯示政治議題新聞 Excel（含 City 下拉選單過濾）
with tab5:
    st.title("📰 Political Issues")

    # 讀取資料
    news_df = pd.read_excel("news_Supply_Chain_Political_Issues.xlsx")

    # 建立下拉選單：City
    cities = news_df["city"].dropna().unique().tolist()
    selected_city = st.selectbox("Select City", ["All"] + cities)

    # 根據所選 City 過濾
    if selected_city != "All":
        filtered_df = news_df[news_df["city"] == selected_city]
    else:
        filtered_df = news_df

    # 顯示過濾後的 DataFrame
    st.dataframe(filtered_df.reset_index(drop=True), use_container_width=True)

