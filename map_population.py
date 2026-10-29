import streamlit as st
import geopandas as gpd
import folium
import pandas as pd
import numpy as np
from streamlit_folium import folium_static

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Malaysia Spatial Dashboard",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    /* Sidebar background */
    section[data-testid="stSidebar"] {
        background-color: #1e2a3a;
    }
    section[data-testid="stSidebar"] * {
        color: #e8edf3 !important;
    }
    /* Metric card style */
    div[data-testid="metric-container"] {
        background: #f0f4f8;
        border-radius: 10px;
        padding: 12px 18px;
        border-left: 4px solid #2c7be5;
    }
    /* Table header */
    thead tr th { background-color: #2c7be5 !important; color: white !important; }
    /* Title accent */
    h1 { color: #1a2e4a; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Constants ──────────────────────────────────────────────────────────────────
STATES_LIST = [
    "Johor", "Kedah", "Kelantan", "Melaka", "Negeri Sembilan",
    "Pahang", "Penang", "Perak", "Perlis", "Sabah", "Sarawak",
    "Selangor", "Terengganu", "Kuala Lumpur", "Labuan",
    "Putrajaya", "Pulau Wawasan",   # imaginary state for Task 2.4
]

COLOR_SCHEMES = {
    "Blue-Green (BuGn)": "BuGn",
    "Blues": "Blues",
    "Greens": "Greens",
    "Yellow-Orange-Red (YlOrRd)": "YlOrRd",
    "Purple (PuRd)": "PuRd",
    "Orange-Red (OrRd)": "OrRd",
}

# ── Data generation ────────────────────────────────────────────────────────────
# Task 2.1 – population between 1 M and 10 M
def generate_population_data() -> pd.DataFrame:
    np.random.seed(42)
    pop = np.random.randint(1_000_000, 10_000_000, size=len(STATES_LIST))
    return pd.DataFrame({"State": STATES_LIST, "Population": pop})

# Task 2.2 – GDP dataset
def generate_gdp_data() -> pd.DataFrame:
    np.random.seed(7)
    gdp = np.random.randint(10_000, 100_000, size=len(STATES_LIST))
    return pd.DataFrame({"State": STATES_LIST, "GDP (USD M)": gdp})

# ── GeoJSON loader ─────────────────────────────────────────────────────────────
@st.cache_data
def load_map() -> gpd.GeoDataFrame:
    return gpd.read_file("malaysia_states.geojson")

# ── Map builder ────────────────────────────────────────────────────────────────
# Task 2.3 – dynamic value column + color scheme; added tooltip layer
def build_choropleth(malaysia_map: gpd.GeoDataFrame, data: pd.DataFrame,
                     value_col: str, color_scheme: str) -> folium.Map:
    m = folium.Map(
        location=[4.2105, 101.9758],
        zoom_start=6,
        tiles="OpenStreetMap",
    )

    choropleth = folium.Choropleth(
        geo_data=malaysia_map,
        name=f"{value_col} Distribution",
        data=data,
        columns=["State", value_col],
        key_on="feature.properties.name",
        fill_color=color_scheme,
        fill_opacity=0.75,
        line_opacity=0.35,
        line_color="#ffffff",
        legend_name=f"{value_col} by State",
        nan_fill_color="#d0d0d0",
        nan_fill_opacity=0.4,
        highlight=True,
    )
    choropleth.add_to(m)

    # Tooltip on hover: bind state name from the geojson properties
    choropleth.geojson.add_child(
        folium.features.GeoJsonTooltip(
            fields=["name"],
            aliases=["State:"],
            style="font-size:13px; font-weight:bold; background:white; padding:6px 10px; border-radius:4px;",
            sticky=True,
        )
    )

    folium.LayerControl().add_to(m)
    return m

# ── Main app ───────────────────────────────────────────────────────────────────
def main():
    # ── Sidebar ──────────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown("## 🗺️ Dashboard Controls")
        st.markdown("---")

        st.markdown("**Dataset**")
        dataset_choice = st.radio(
            "Select Dataset (Task 2.2):",
            ("Population", "GDP"),
            label_visibility="collapsed",
        )

        st.markdown("---")
        st.markdown("**Colour Scheme**")
        color_label = st.selectbox(
            "Select Colour Scheme (Task 2.3):",
            list(COLOR_SCHEMES.keys()),
            label_visibility="collapsed",
        )
        color_scheme = COLOR_SCHEMES[color_label]

        st.markdown("---")
        st.caption("ℹ️ 'Pulau Wawasan' is an imaginary state added for Task 2.4. It appears in the table but cannot be rendered on the map (no geometry in GeoJSON).")

    # ── Header ────────────────────────────────────────────────────────────────
    st.title("🗺️ Malaysia Spatial Data Dashboard")
    st.markdown("Interactive choropleth map of Malaysian states with sample demographic data.")
    st.divider()

    # ── Load data ─────────────────────────────────────────────────────────────
    if dataset_choice == "Population":
        data = generate_population_data()
        value_col = "Population"
        unit = "people"
    else:
        data = generate_gdp_data()
        value_col = "GDP (USD M)"
        unit = "USD M"

    # ── Summary metrics ───────────────────────────────────────────────────────
    real_data = data[data["State"] != "Pulau Wawasan"]
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("States", f"{len(real_data)}")
    col2.metric(f"Total {dataset_choice}", f"{real_data[value_col].sum():,.0f}")
    col3.metric(f"Highest {dataset_choice}", f"{real_data[value_col].max():,.0f}")
    col4.metric(f"Lowest {dataset_choice}", f"{real_data[value_col].min():,.0f}")

    st.divider()

    # ── Two-column layout: table | map ────────────────────────────────────────
    left, right = st.columns([1, 2], gap="large")

    with left:
        st.subheader(f"📋 {dataset_choice} by State")
        display_df = (
            data.copy()
            .sort_values(value_col, ascending=False)
            .reset_index(drop=True)
        )
        # Format numbers with commas
        display_df[value_col] = display_df[value_col].apply(lambda x: f"{x:,}")
        st.dataframe(display_df, use_container_width=True, height=530)

    with right:
        st.subheader(f"🌏 {dataset_choice} Distribution Map")
        malaysia_map = load_map()
        folium_map = build_choropleth(malaysia_map, data, value_col, color_scheme)
        folium_static(folium_map, width=700, height=500)

    st.divider()
    st.caption("Data is randomly generated for demonstration purposes. Colour scheme: **" + color_label + "**.")


if __name__ == "__main__":
    main()
