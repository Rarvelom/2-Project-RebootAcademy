import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from geopy.geocoders import Nominatim
import time
import pydeck as pdk
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# --- PAGE SETUP ---
st.set_page_config(page_title="CO2 Emissions Dashboard", layout="wide")

# --- COLORS ---
COLOR_PRIMARY = "#1c3e6d"
COLOR_ACCENT = "#f49828"
COLOR_GREEN = "#37a387"
COLOR_GREEN_LIGHT = "#71b85e"
COLOR_YELLOW = "#fad12f"
COLOR_BG = "#f5f8fa"

# --- CUSTOM STYLE ---
st.markdown(f"""
    <style>
        .main {{
            background-color: {COLOR_BG};
            color: {COLOR_PRIMARY};
        }}
        .sidebar .sidebar-content {{
            background-color: {COLOR_PRIMARY};
            color: {COLOR_PRIMARY};
        }}
        .css-1d391kg {{
            color: {COLOR_PRIMARY};
        }}
        h2, h1, h3, .stMarkdown p, .stText, .stTitle {{
            color: {COLOR_PRIMARY};
        }}
        .block-container {{
            padding-top: 2rem;
            padding-bottom: 0rem;
            padding-left: 2rem;
            padding-right: 2rem;
        }}
        .element-container {{
            margin-bottom: 0.5rem !important;
        }}
        iframe {{
            height: 300px !important;
        }}
    </style>
""", unsafe_allow_html=True)

# --- SIDE MENU ---
#logo in optional menu: st.sidebar.image("rebooteco_logo.png", width=140)
st.sidebar.title("CO2 Emissions Dashboard")
page = st.sidebar.radio("Content", [
    "Global Trend",
    "Events and Impacts",
    "CO₂-Temperature Relationship",
    "Emissions by Region",
    "Emissions per GDP",
    "CO₂ emissions in Spain"
])

# --- Load data ---
@st.cache_data
def load_data():
    return pd.read_csv("dataset_visualizacion_co2.csv")

df = load_data()

# --- GLOBAL YEAR SLIDER ---
st.sidebar.markdown("---")
selected_year = st.sidebar.slider("Select year", min_value=1850, max_value=2025, value=2020)

# --- LOGO PER PAGE ---
st.image("rebooteco_logo.png", width=200)

# --- TITLES PER PAGE AND GRAPHICS ---
if page == "Global Trend":
    st.title("How has the global trend in CO₂ emissions evolved?")
    df_world = df[df['territory'] == 'World']
    df_world_filtered = df_world[df_world['year'] <= selected_year]

    df_world_co2 = df_world_filtered[['year', 'cement_co2', 'co2', 'co2_including_luc', 'coal_co2', 'flaring_co2', 'gas_co2', 'oil_co2', 'land_use_change_co2']]
    df_melted = df_world_co2.melt(id_vars=['year'], var_name='Segmento', value_name='Emisiones de CO₂(MtCO₂)')

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Line by emission source")
        fig1 = px.line(df_melted, x="year", y="Emisiones de CO₂(MtCO₂)", color='Segmento', title='Emisiones globales por fuente')
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        st.subheader("Comparison: Total vs Including LUC")
        fig2 = px.area(df_world_filtered, x='year', y=['co2', 'co2_including_luc'], title='CO₂ total vs con cambio de uso de tierra')
        st.plotly_chart(fig2, use_container_width=True)

    col3, col4 = st.columns(2)
    with col3:
        st.subheader("Bar Chart by Sector for Selected Year")
        df_year = df_world_filtered[df_world_filtered['year'] == selected_year]
        df_bar = df_year[['cement_co2', 'coal_co2', 'flaring_co2', 'gas_co2', 'oil_co2', 'land_use_change_co2']].sum().reset_index()
        df_bar.columns = ['Sector', 'Emissions']
        fig3 = px.bar(df_bar, x='Sector', y='Emissions', title=f'Emissions by Sector in {selected_year}')
        st.plotly_chart(fig3, use_container_width=True)

    with col4:
        st.subheader("Cumulative Emissions")
        df_world_filtered['cumulative'] = df_world_filtered['co2'].cumsum()
        fig4 = px.line(df_world_filtered, x='year', y='cumulative', title='Historical Cumulative CO₂ Emissions')
        st.plotly_chart(fig4, use_container_width=True)

elif page == "Events and Impacts":
        st.title("What periods show significant changes and what events influenced them?")

        # Create decade column and calculate aggregates
        df["decade"] = (df["year"] // 10) * 10
        df_decade = df.groupby("decade")[["co2"]].sum().reset_index()
        df_decade["co2_growth_prct"] = df_decade["co2"].pct_change() * 100

        # Key events aligned with actual peaks
        updated_events = {
        1860: "First Industrial Revolution",
        1910: "World War I",
        1940: "World War II",
        1950: "Postwar Period",
        1990: "Kyoto Protocol",
        2020: "COVID-19"
        }

        # Create interactive figure with secondary Y-axis
        import plotly.graph_objects as go

        fig = go.Figure()

        # Emissions line (primary Y-axis)
        fig.add_trace(go.Scatter(
        x=df_decade["decade"],
        y=df_decade["co2"],
        mode="lines+markers",
        name="CO₂ Emissions",
        line=dict(color=COLOR_PRIMARY, width=3),
        yaxis="y"
        ))

        # Growth percentage line (secondary Y-axis)
        fig.add_trace(go.Scatter(
        x=df_decade["decade"],
        y=df_decade["co2_growth_prct"],
        mode="lines+markers",
        name="% Growth",
        line=dict(color=COLOR_ACCENT, width=2, dash="dash"),
        yaxis="y2"
        ))

        # Annotations
        for year, label in updated_events.items():
            if year in df_decade["decade"].values:
                y_val = df_decade[df_decade["decade"] == year]["co2"].values[0]
                fig.add_annotation(
                x=year,
                y=y_val,
                text=label,
                showarrow=True,
                arrowhead=1,
                ax=20,
                ay=-40,
                font=dict(size=10),
                arrowcolor="gray"
                )

        # Layout with two Y-axes
        fig.update_layout(
        title="Evolution of CO₂ Emissions and Key Events by Decade",
        xaxis_title="Decade",
        yaxis=dict(
            title="Emissions (Mt)",
            tickfont=dict(color=COLOR_PRIMARY)
        ),
        yaxis2=dict(
            title="% Growth",
            overlaying="y",
            side="right",
            showgrid=False,
            tickfont=dict(color=COLOR_ACCENT)
        ),
        template="plotly_white",
        font=dict(color=COLOR_PRIMARY),
        legend=dict(orientation="h", y=-0.2)
        )
        st.plotly_chart(fig, use_container_width=True)

        # --- Second Chart: Replaced with Median CO₂ Growth by Decade ---
    # Ensure 'co2_growth_prct' exists in df
        df["decade"] = (df["year"] // 10) * 10
        decade_growth = (
            df.groupby("decade")["co2_growth_prct"]
            .median()
            .reset_index()
            .sort_values("decade")
        )
        decade_growth["co2_growth_prct"] = decade_growth["co2_growth_prct"].round(2)

        def assign_color(value):
            if value < -2:
                return "#102742"   # Azul más oscuro
            elif value < 0:
                return "#1c3e6d"   # Azul oscuro
            elif value < 1:
                return "#cfe97d"   # Verde-amarillo pálido
            elif value < 2:
                return "#a7d86a"   # Verde lima claro
            elif value < 3:
                return "#71b85e"   # Verde claro
            elif value < 4:
                return "#37a387"   # Verde fuerte
            elif value < 5.5:
                return "#fad12f"   # Amarillo
            elif value < 7:
                return "#f8a947"   # Amarillo-naranja
            elif value < 8.5:
                return "#f49828"   # Naranja
            else:
                return "#d94300"   # Rojo quemado fuerte

        decade_growth["color"] = decade_growth["co2_growth_prct"].apply(assign_color)

        fig2 = px.bar(
            decade_growth,
            x="decade",
            y="co2_growth_prct",
            text="co2_growth_prct",
            title="Median CO₂ Growth Rate by Decade (Global)",
            labels={"co2_growth_prct": "Median CO₂ Growth (%)", "decade": "Decade"},
            color="color",
            color_discrete_map="identity",  # usa directamente los valores hex
            template="plotly_white",
            height=600
        )

        fig2.update_traces(
            textposition="outside",
            marker_line_color='white',
            marker_line_width=1.5
        )

        fig2.update_layout(
            title_font_size=24,
            xaxis=dict(dtick=10),
            yaxis_title="Growth (%)",
            bargap=0.25,
            plot_bgcolor=COLOR_BG,
            paper_bgcolor=COLOR_BG,
            font=dict(color=COLOR_PRIMARY),
            showlegend=False
        )

        st.plotly_chart(fig2, use_container_width=True)


elif page == "CO₂-Temperature Relationship":
    st.title("Is there a relationship between CO₂ emissions and temperature increase?")
    df_world = df[df['territory'] == 'World']

    # --- Fila 1: Gráfica principal (ancho completo) ---
    df_grouped = df_world.groupby("year").agg({
        "co2": "mean",
        "temperature_change_from_ghg": "mean"
    }).reset_index()

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df_grouped["year"],
        y=df_grouped["temperature_change_from_ghg"],
        mode="lines+markers",
        name="Temperature Change (°C)",
        line=dict(color="orange", width=3)
    ))

    fig.add_trace(go.Scatter(
        x=df_grouped["year"],
        y=df_grouped["co2"],
        mode="lines",
        name="CO₂ Emissions (Metric Tons)",
        yaxis="y2",
        line=dict(color="lightblue", width=3, dash="dot")
    ))

    fig.update_layout(
        title="CO₂ Emissions and Temperature Change Over Time",
        template="plotly_white",
        xaxis=dict(title="Year"),
        yaxis=dict(title="Temperature Change (°C)", side="left"),
        yaxis2=dict(title="CO₂ Emissions (Metric Tons)", overlaying="y", side="right"),
        legend=dict(x=0.05, y=1.1, orientation="h"),
        height=600,
        plot_bgcolor=COLOR_BG,
        paper_bgcolor=COLOR_BG,
        font=dict(color=COLOR_PRIMARY)
    )

    st.plotly_chart(fig, use_container_width=True)

    # --- Fila 2: Dos columnas ---
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Sectoral Impact on Global Temperature Rise")

        df_temp_sector = df_world[[
            "year", "temperature_change_from_ghg",
            "cement_co2", "coal_co2", "flaring_co2", "gas_co2", "oil_co2", "land_use_change_co2"
        ]].dropna()

        cor_temp = df_temp_sector.drop(columns="year").corr()
        sector_corr = cor_temp["temperature_change_from_ghg"].drop("temperature_change_from_ghg").sort_values(ascending=False).reset_index()
        sector_corr.columns = ["Sector", "Correlation"]

        fig2 = px.bar(
            sector_corr,
            x="Sector",
            y="Correlation",
            title="Correlation Between CO₂ Emissions by Sector and Global Temperature Rise",
            labels={"Correlation": "Correlation with Temp Change"},
            color="Sector",
            color_discrete_sequence=[
                COLOR_ACCENT,
                COLOR_PRIMARY,
                COLOR_GREEN,
                COLOR_YELLOW,
                COLOR_GREEN_LIGHT,
                "#a0aec0"  # fallback color
            ]
        )
        fig2.update_layout(
            yaxis_range=[0, 1],
            template="plotly_white",
            plot_bgcolor=COLOR_BG,
            paper_bgcolor=COLOR_BG,
            font=dict(color=COLOR_PRIMARY)
        )

        st.plotly_chart(fig2, use_container_width=True)

    with col2:
        st.subheader("Cumulative CO₂ vs Temperature Change")

        df_filtered_scatter = df[df["continent"] != "Unknown"].dropna(subset=[
            "cumulative_co2_including_luc", "temperature_change_from_ghg"
        ])

        fig3 = px.scatter(
            df_filtered_scatter,
            x="cumulative_co2_including_luc",
            y="temperature_change_from_ghg",
            color="continent",
            title="Cumulative CO₂ vs Temperature Change from GHG",
            labels={
                "cumulative_co2_including_luc": "Cumulative CO₂ (Metric Tons)",
                "temperature_change_from_ghg": "Temperature Change (°C)",
                "continent": "Continent"
            },
            template="plotly_white"
        )

        fig3.update_traces(marker=dict(size=7, opacity=0.6))
        fig3.update_layout(
            plot_bgcolor=COLOR_BG,
            paper_bgcolor=COLOR_BG,
            font=dict(color=COLOR_PRIMARY),
            legend_title_text="Continent"
        )

        st.plotly_chart(fig3, use_container_width=True)



elif page == "Emissions by Region":
    st.title("Which continents are the biggest emitters?")
    # Primera fila: gráfica de barras ocupa toda la fila
    st.subheader("CO₂ Emissions by Continent Over Decades")
    df_continent = df[df['continent'] != 'Unknown'].groupby(["decade", "continent"], as_index=False)["co2_including_luc"].sum()
    fig1 = px.bar(df_continent,
                  x="decade",
                  y="co2_including_luc",            
                  labels={"co2_including_luc": "CO₂ Including LUC (MtCO₂)"},
                  color="continent",
                  title="CO₂ Emissions by Continent Over Decades",
                  color_discrete_sequence=px.colors.qualitative.Set2)
    st.plotly_chart(fig1, use_container_width=True)

    # Segunda fila: dos columnas
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("CO₂ Emissions by Country and Continent (Animated Map)")
        df_map = df[df['continent'] != 'Unknown'].groupby(["year", "continent", "iso_code", "territory"], as_index=False)["co2_including_luc"].sum()
        fig2 = px.scatter_geo(df_map,
                              locations="iso_code",
                              color="continent",
                              hover_name="territory",
                              size=(df_map["co2_including_luc"].abs())*2,
                              animation_frame="year",
                              projection="natural earth",
                              title="CO₂ Emissions by Country Over Time")
        st.plotly_chart(fig2, use_container_width=True)

    with col2:
        st.subheader("CO₂ Emissions Distribution in the 2010s")
        df_countries = df[(df['continent'] != 'Unknown') & (df['decade'] == 2010)] \
            .groupby(["continent", "iso_code", "territory"], as_index=False)["co2_including_luc"].sum()
        df_countries = df_countries[df_countries["co2_including_luc"] > 0]
        fig3 = px.sunburst(df_countries,
                           path=['continent', 'territory'],
                           values="co2_including_luc",
                           labels={"co2_including_luc": "CO₂ Including LUC (MtCO₂)"},
                           color='co2_including_luc',
                           hover_data=['iso_code'],
                           color_continuous_scale='RdBu',
                           title="CO₂ Emissions by Continent and Country (2010s)")
        st.plotly_chart(fig3, use_container_width=True)
    # Tercera fila: Global Share of CO₂ Emissions: China vs USA
    st.subheader("Global Share of CO₂ Emissions: China vs USA")
    df_chn_usa = df[df['territory'].isin(['China', 'United States'])][
            ['year', 'territory', 'share_global_co2_including_luc']]
    fig3 = px.line(df_chn_usa,
                       x="year",
                       y="share_global_co2_including_luc",
                       labels={"share_global_co2_including_luc": "Share Global CO₂ (%)"},
                       color='territory',
                       title="Country's Share of Global CO₂ Emissions")
    st.plotly_chart(fig3, use_container_width=True)

elif page == "Emissions per GDP":
    st.title("Which sectors are responsible for most CO₂ emissions?")
    # --- ROW 1 ---
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("CO₂ Emissions per GDP in the 2010s")
        df_gdp = df[(df['continent'] != 'Unknown') & (df['decade'] == 2010)] \
            .groupby(["continent", "iso_code", "territory"], as_index=False)["co2_including_luc_per_gdp"].sum()

        # Escalar los valores pequeños
        df_gdp["co2_including_luc_per_gdp"] = df_gdp["co2_including_luc_per_gdp"] * 1_000_000

        # Filtrar valores positivos y redondear
        df_gdp = df_gdp[df_gdp["co2_including_luc_per_gdp"] > 1]
        df_gdp["co2_including_luc_per_gdp"] = df_gdp["co2_including_luc_per_gdp"].round(0)

        df_gdp = df_gdp[df_gdp["co2_including_luc_per_gdp"].abs() > 1e-6]

        if df_gdp.empty:
            st.warning("No CO₂ per GDP data available for this period.")
        else:
            fig2 = px.sunburst(
                df_gdp,
                path=['continent', 'territory'],
                values="co2_including_luc_per_gdp",
                labels={"co2_including_luc_per_gdp": "CO₂ Including LUC (MtCO₂)"},
                color='co2_including_luc_per_gdp',
                hover_data=['iso_code'],
                color_continuous_scale='RdBu',
                title="CO₂ Emissions per GDP (2010s)"
            )
            st.plotly_chart(fig2, use_container_width=True)

    with col2:
        st.subheader("Global Share of CO₂ Emissions: DRC vs Liberia")
        df_cod_lbr = df[df['territory'].isin(['Democratic Republic of Congo', 'Liberia'])][
            ['year', 'territory', 'share_global_co2_including_luc']]
        fig1 = px.line(df_cod_lbr,
                    x="year",
                    y="share_global_co2_including_luc",
                       labels={"share_global_co2_including_luc": "Share Global CO₂ (%)"},
                    color='territory',
                    title="Country's Share of Global CO₂ Emissions")
        st.plotly_chart(fig1, use_container_width=True)

    # --- ROW 2 ---
    st.subheader("CO₂ Emissions in the DRC by Source")
    df_cod = df[df['territory'] == 'Democratic Republic of Congo'][[
            'year', 'co2_including_luc', 'land_use_change_co2']]
    df_melted_cod = df_cod.melt(id_vars='year',
                                    var_name='Source',
                                    value_name='CO₂ Emissions (MtCO₂)')
    fig4 = px.line(df_melted_cod,
                    x="year",
                    y="CO₂ Emissions (MtCO₂)",
                    color='Source',
                    title='DRC: CO₂ Emissions by Source')
    st.plotly_chart(fig4, use_container_width=True)

elif page == "CO₂ emissions in Spain":
    st.title("And what about Spain?")
    df = pd.read_csv('dataset_visualizacion_co2.csv')
    st.subheader("CO₂ emissions in Spain")
    df_co2_ESP = df.loc[df['territory'] == 'Spain'][['year', 'co2', 'co2_including_luc', 
            'coal_co2', 'flaring_co2', 
            'gas_co2', 'oil_co2', 'land_use_change_co2']]

    df_melted_co2_ESP = df_co2_ESP.melt(id_vars=['year'],
                                        value_vars=['co2', 'co2_including_luc', 'coal_co2', 'gas_co2', 'oil_co2', 'flaring_co2', 'land_use_change_co2'],
                                        var_name='Source and Land Use',
                                        value_name='CO₂ Emissions (MtCO₂)')

    fig5 = px.line(df_melted_co2_ESP, 
                x="year", 
                y="CO₂ Emissions (MtCO₂)", 
                color='Source and Land Use',
                title='CO₂ emissions in Spain')
    
    st.plotly_chart(fig5, use_container_width=True)   


st.markdown("---")
