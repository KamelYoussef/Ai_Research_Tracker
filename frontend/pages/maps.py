import streamlit as st
import pandas as pd
import sys
from pathlib import Path
import plotly.express as px
sys.path.append(str(Path(__file__).resolve().parent.parent))
from streamlit_option_menu import option_menu
from data.fetch_utils import logout, maps, select_month
from components.charts import display_overview_map
import yaml

with open("data/data.yml", "r") as f:
    yaml_data = yaml.safe_load(f)

if 'logged_in' in st.session_state and st.session_state.logged_in:
    pass
else:
    st.switch_page("login.py")

st.set_page_config(page_title="Maps", layout="wide")
header_col1, header_col2, _ ,header_col3 = st.columns([2.5, 1.5, 2, 2.5])
with header_col1:
    st.header("📊 Google Places Ranking")
with header_col3:
    month = select_month()
st.divider()

# Sidebar buttons
with st.sidebar:
    selected = option_menu(
        menu_title="Menu",  # Optional
        options=["Tracker", "Investigator", "Maps", "Clear Cache", "Logout", "Settings"],
        icons=["eye", "search", "geo-alt", "arrow-clockwise", "box-arrow-left", "gear"],  # Optional icons
        menu_icon="list",
        default_index=2
    )

if selected == "Tracker":
    st.switch_page("pages/webapp.py")

elif selected == "Investigator":
    st.switch_page("pages/ai_tracking.py")

elif selected == "Clear Cache":
    st.cache_data.clear()
    st.success("Cache cleared!")

elif selected == "Logout":
    logout()

elif selected == "Settings":
    st.switch_page("pages/user_management.py")

# ---------------------
# Load data
if maps(month, is_city=True) is None:
    st.error(f"No data available.")
else:
    df = maps(month, is_city=True)

    # Clean data types
    df['Avg Rank'] = pd.to_numeric(df['Avg Rank'], errors='coerce')
    df['Rating'] = pd.to_numeric(df['Rating'], errors='coerce')
    df['Reviews'] = pd.to_numeric(df['Reviews'], errors='coerce')
    df["Rating"] = df["Rating"].fillna(df.groupby("City")["Rating"].transform("mean"))
    df["Reviews"] = df["Reviews"].fillna(df.groupby("City")["Reviews"].transform("mean"))

    # ---------------------
    # 1. OVERALL VIEW
    st.header("Overview")

    col1, col2 = st.columns(2)

    with col1:
        # Compute average rank per keyword across all cities
        keyword_avg = df.groupby("Keyword", as_index=False)["Avg Rank"].mean().round(2)
        keyword_avg['Color Rank'] = keyword_avg['Avg Rank'].apply(lambda x: min(x, 10))

        # Calculate mean across all keywords
        overall_mean = keyword_avg['Avg Rank'].mean()

        fig_overall = px.bar(
            keyword_avg,
            x="Keyword",
            y="Avg Rank",
            color="Color Rank",
            text="Avg Rank",
            title="Average Rank by Keyword (All Cities)",
            color_continuous_scale="OrRd",
            range_color=(1, 10),
            height=400
        )

        # Add horizontal mean line
        fig_overall.add_shape(
            type="line",
            x0=-0.5,
            x1=len(keyword_avg) - 0.5,
            y0=overall_mean,
            y1=overall_mean,
            line=dict(color="orange", width=2, dash="dash")
        )

        # Add annotation for mean line
        fig_overall.add_annotation(
            x=4.5,  # or use x=4.5 depending on layout
            y=overall_mean,
            text=f"Overall Avg. Rank: {overall_mean:.2f}",
            showarrow=False,
            yshift=10,
            font=dict(color="orange")
        )

        st.plotly_chart(fig_overall)

    with col2:
        st.markdown("<div style='height: 140px;'></div>", unsafe_allow_html=True)
        m1, m2, m3, _ = st.columns(4)
        m2.metric("🔢 Avg. Rank", f"{df['Avg Rank'].mean():.2f}")
        m2.metric("⭐ Avg. Rating", f"{df['Rating'].mean():.2f}")
        #m3.metric("🗣️ Total Reviews", f"{int(df['Reviews'].sum() / df['Keyword'].nunique())}")
        #m3.metric("🗣️ Avg. Reviews", f"{int(df['Reviews'].mean())}")

    st.divider()
    # ---------------------
    # 2. VIEW BY Location
    st.markdown("""
        <style>
        div[data-testid="stSelectbox"] {
            max-width: 300px;
        }
        </style>
    """, unsafe_allow_html=True)
    st.header("🏙️ City View")

    #map
    df_avg = df.groupby("City", as_index=False)["Avg Rank"].mean()
    display_overview_map(df_avg)
    st.markdown("""
            <div style="display: flex; align-items: center; gap: 10px;">
                <div style="width: 30px; height: 20px; background-color: rgb(255, 0, 0);"></div> Rank above 5
                <div style="width: 30px; height: 20px; background-color: rgb(0, 180, 0);"></div> Rank below 5
                <div style="width: 30px; height: 20px; background-color: rgb(128, 128, 128);"></div> No Rank
            </div>
            """, unsafe_allow_html=True)

    st.divider()

    selected_city = st.selectbox("Select a City", sorted(df['City'].unique()))
    city_data = df[df['City'] == selected_city]
    col5, col6 = st.columns(2)


    with col5:
        # Ensure values above 10 are capped visually for coloring
        city_data['Color Rank'] = city_data['Avg Rank'].apply(lambda x: min(x, 10))

        # Calculate mean
        mean_rank = city_data['Avg Rank'].mean()

        #st.subheader(f"Average Rank by Keyword in {selected_city}")
        fig2 = px.bar(
            city_data,
            x="Keyword",
            y="Avg Rank",
            color="Color Rank",
            text="Avg Rank",
            title=f"Average Rank by Keyword in {selected_city}",
            color_continuous_scale="OrRd",
            range_color=(1, 10),
            height=400
        )

        # Add horizontal line for mean
        fig2.add_shape(
            type="line",
            x0=-0.5, x1=len(city_data['Keyword']) - 0.5,  # full width of x-axis
            y0=mean_rank, y1=mean_rank,
            line=dict(color="orange", width=2, dash="dash"),
        )

        # Optional: Add annotation for the line
        fig2.add_annotation(
            x=4.5,  # position on x-axis
            y=mean_rank,
            text=f"Avg. Rank: {mean_rank:.2f}",
            showarrow=False,
            yshift=10,
            font=dict(color="orange")
        )

        st.plotly_chart(fig2)

    with col6:
        st.markdown("<div style='height: 140px;'></div>", unsafe_allow_html=True)
        col7, col8, col9, _ = st.columns(4)
        col8.metric("🔢 Avg. Rank", f"{city_data['Avg Rank'].mean():.2f}")
        col8.metric("⭐ Avg. Rating", f"{city_data['Rating'].mean():.2f}")
        #col9.metric("🗣️ Total Reviews", f"{int(city_data['Reviews'].sum() / city_data['Keyword'].nunique())}")

    # ---------------------
    # Optional: raw table
    with st.expander("📄 Explore Data"):
        label_keys = ["top_41"]
        city_to_label = {}
        for key in label_keys:
            if key in yaml_data:
                for city in yaml_data[key]:
                    city_to_label[city] = key

        # Add to DataFrame
        df["Labels"] = df["City"].map(city_to_label).fillna("None")

        st.dataframe(df)

with st.sidebar:
    st.markdown("""
    <style>
    /* Make sidebar container relative and reserve footer space */
    div[data-testid="stSidebar"] > div:nth-child(1) {
        position: relative;
        padding-bottom: 4rem; /* Reserve space for footer */
    }

    /* Add padding below the navigation menu */
    [data-testid="stSidebarNav"] {
        padding-bottom: 2rem;
    }

    /* Absolutely position the footer right under the nav, pinned to sidebar bottom */
    [data-testid="stSidebarNav"] + div {
        position: absolute;
        bottom: 0;
        width: 100%;
        display: flex;
        justify-content: center;
        align-items: center;
    }
    </style>

    <div>
      <p style="margin: 0; font-size: 0.8rem; color: #888;">
        © 2025 Presence AI
      </p>
      <p style="margin: 0; font-size: 0.8rem; color: #888;">
        A portion of the revenue is donated to support Palestine 🇵🇸
      </p>
    </div>
    """, unsafe_allow_html=True)
