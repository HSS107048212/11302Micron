import streamlit as st
import pandas as pd
import numpy as np
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium

# Page configuration
st.set_page_config(page_title="Semiconductor Supplier Risk Dashboard", layout="wide")

st.title("🌏 Geopolitical Risk Monitoring Dashboard for Semiconductor Supply Chain")
st.markdown("This dashboard visualizes real-time supplier risks based on geographic locations and risk indicators.")

# Simulate supplier names and dates
suppliers = [f"Supplier_{i+1}" for i in range(10)]
dates = pd.date_range(start="2023-01-01", periods=24, freq="M")

# Generate mock data
data = pd.DataFrame({
    "Supplier": np.repeat(suppliers, len(dates)),
    "Date": dates.tolist() * len(suppliers),
    "Frequency_of_risk_assessments": np.random.randint(0, 5, size=240),
    "Supplier_geographic_diversity_index": np.round(np.random.uniform(0.4, 0.9, size=240), 2),
    "Critical_suppliers_with_mitigation_%": np.round(np.random.uniform(0.5, 1.0, size=240), 2),
    "Production_in_high_risk_areas_%": np.round(np.random.uniform(0.1, 0.5, size=240), 2),
})

# Add geographic coordinates
np.random.seed(42)
locations = {
    f"Supplier_{i+1}": {
        "Latitude": round(np.random.uniform(23.0, 50.0), 4),
        "Longitude": round(np.random.uniform(-130.0, 150.0), 4),
    } for i in range(10)
}
data["Latitude"] = data["Supplier"].map(lambda x: locations[x]["Latitude"])
data["Longitude"] = data["Supplier"].map(lambda x: locations[x]["Longitude"])

# Extract the most recent data
latest_date = data["Date"].max()
latest_data = data[data["Date"] == latest_date].copy()

# Compute risk score
latest_data["Risk_Score"] = (
    (1 - latest_data["Supplier_geographic_diversity_index"]) * 0.3 +
    (1 - latest_data["Critical_suppliers_with_mitigation_%"]) * 0.3 +
    latest_data["Production_in_high_risk_areas_%"] * 0.3 +
    (4 - latest_data["Frequency_of_risk_assessments"]) / 4 * 0.1
)

# Tabs for UI
tab1, tab2 = st.tabs(["🗺️ Risk Map", "📋 Supplier Data Overview"])

# -------------------------------
# 🗺️ Tab 1: Risk Map
# -------------------------------
with tab1:
    st.title("🌍 Supplier Geopolitical Risk Map")
    m = folium.Map(location=[35, 100], zoom_start=2)
    marker_cluster = MarkerCluster().add_to(m)

    for _, row in latest_data.iterrows():
        popup_text = (
            f"<b>{row['Supplier']}</b><br>"
            f"Risk Assessment Frequency: {row['Frequency_of_risk_assessments']}<br>"
            f"Geographic Diversity Index: {row['Supplier_geographic_diversity_index']}<br>"
            f"Mitigation Coverage (%): {row['Critical_suppliers_with_mitigation_%']}<br>"
            f"Production in High-Risk Areas (%): {row['Production_in_high_risk_areas_%']}<br>"
            f"<b>Risk Score: {round(row['Risk_Score'], 2)}</b>"
        )
        folium.CircleMarker(
            location=[row["Latitude"], row["Longitude"]],
            radius=8,
            color="red" if row["Risk_Score"] > 0.6 else "orange" if row["Risk_Score"] > 0.4 else "green",
            fill=True,
            fill_opacity=0.7,
            popup=folium.Popup(popup_text, max_width=300)
        ).add_to(marker_cluster)

    st_folium(m, width=1000, height=600)

# -------------------------------
# 📋 Tab 2: Data Overview + Filter
# -------------------------------
with tab2:
    st.title("📋 Supplier KPI Data Overview")
    selected_supplier = st.selectbox("Select Supplier", ["All"] + suppliers)

    if selected_supplier == "All":
        display_df = data.copy()
    else:
        display_df = data[data["Supplier"] == selected_supplier]

    st.dataframe(display_df.reset_index(drop=True), use_container_width=True)
