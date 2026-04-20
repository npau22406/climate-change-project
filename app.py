import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

# to run the program
# python -m streamlit run app.py

st.set_page_config(page_title = "Climate Dashboard", layout = "wide")

st.title("Climate Change Dashboard")
st.write("Explore global and country-level temperature trends using interactive visualizations.")


@st.cache_data
def load_data():
    BASE_DIR = Path(__file__).resolve().parent
    DATA_DIR = BASE_DIR / "dataset"

    global_df = pd.read_csv(DATA_DIR / "GlobalTemperatures.csv")
    country_df = pd.read_csv(DATA_DIR / "GlobalLandTemperaturesByCountry.csv")

    global_df["dt"] = pd.to_datetime(global_df["dt"])
    global_df["Year"] = global_df["dt"].dt.year
    global_df["Month"] = global_df["dt"].dt.month
    global_df["Decade"] = (global_df["Year"] // 10) * 10

    country_df["dt"] = pd.to_datetime(country_df["dt"])
    country_df["Year"] = country_df["dt"].dt.year
    country_df["Month"] = country_df["dt"].dt.month
    country_df["Decade"] = (country_df["Year"] // 10) * 10

    global_clean = global_df[["dt", "Year", "Month", "Decade", "LandAverageTemperature"]].dropna().copy()
    country_clean = country_df[["dt", "Year", "Month", "Decade", "Country", "AverageTemperature"]].dropna().copy()

    baseline_temp = global_clean["LandAverageTemperature"].mean()
    global_clean["TemperatureAnomaly"] = global_clean["LandAverageTemperature"] - baseline_temp

    return global_clean, country_clean, baseline_temp


global_clean, country_clean, baseline_temp = load_data()

# Sidebar
available_countries = sorted(country_clean["Country"].unique())
default_countries = ["United States", "India", "China", "Brazil", "Australia", "Germany"]
default_countries = [c for c in default_countries if c in available_countries]

# Default values
selected_countries = ["United States", "India", "China", "Brazil", "Australia", "Germany"]

min_year = int(country_clean["Year"].min())
max_year = int(country_clean["Year"].max())
year_range = (1850, max_year)

if not selected_countries:
    st.warning("Please select at least one country.")
    st.stop()

min_year = int(country_clean["Year"].min())
max_year = int(country_clean["Year"].max())

year_range = st.sidebar.slider(
    "Select year range",
    min_value = min_year,
    max_value = max_year,
    value = (1850, max_year),
)

# Filter data
filtered_country = country_clean[
    (country_clean["Country"].isin(selected_countries))
    & (country_clean["Year"] >= year_range[0])
    & (country_clean["Year"] <= year_range[1])
].copy()

filtered_global = global_clean[
    (global_clean["Year"] >= year_range[0])
    & (global_clean["Year"] <= year_range[1])
].copy()

# Build yearly global data once
yearly_global = filtered_global.groupby("Year", as_index = False)["LandAverageTemperature"].mean()
yearly_global["RollingAvg10"] = (
    yearly_global["LandAverageTemperature"].rolling(window = 10, min_periods = 1).mean()
)
yearly_global["TemperatureAnomaly"] = yearly_global["LandAverageTemperature"] - baseline_temp


# 1. Annotated Trend
st.subheader("1. Annotated Global Temperature Trend")

fig_annotated = go.Figure()

fig_annotated.add_trace(
    go.Scatter(
        x = yearly_global["Year"],
        y = yearly_global["LandAverageTemperature"],
        mode = "lines",
        name = "Yearly Average",
        line = dict(width = 1, color = "green"),
        hovertemplate = "Year: %{x}<br>Yearly Avg: %{y:.2f} °C<extra></extra>",
    )
)

fig_annotated.add_trace(
    go.Scatter(
        x = yearly_global["Year"],
        y = yearly_global["RollingAvg10"],
        mode = "lines",
        name = "10-Year Rolling Avg",
        line = dict(width = 3, color = "red"),
        hovertemplate = "Year: %{x}<br>Rolling Avg: %{y:.2f} °C<extra></extra>",
    )
)

# Annotation helper values
min_row = yearly_global.loc[yearly_global["RollingAvg10"].idxmin()]
max_row = yearly_global.loc[yearly_global["RollingAvg10"].idxmax()]
rapid_warming = yearly_global[yearly_global["Year"] >= 1970].iloc[0]

fig_annotated.add_annotation(
    x = min_row["Year"],
    y = min_row["RollingAvg10"],
    text = "Period of lower temperatures",
    showarrow = True,
    arrowhead = 2,
    arrowcolor = "white",
    ax = 110,
    ay = 25,
)

fig_annotated.add_annotation(
    x = rapid_warming["Year"],
    y = rapid_warming["RollingAvg10"],
    text = "Rapid warming begins",
    showarrow = True,
    arrowhead = 2,
    arrowcolor = "white",
    ax = -70,
    ay = -50,
)

fig_annotated.add_annotation(
    x = max_row["Year"],
    y = max_row["RollingAvg10"],
    text = "Highest sustained temperature",
    showarrow = True,
    arrowhead = 2,
    arrowcolor = "white",
    ax = -130,
    ay = -30,
)

fig_annotated.update_layout(
    title = "Annotated Global Temperature Trend",
    xaxis_title = "Year",
    yaxis_title = "Average Temperature (°C)",
    template = "plotly_white",
    hovermode = "x unified",
)

st.plotly_chart(fig_annotated, use_container_width = True)

st.markdown(
    """
    **Interpretation:**  
    This chart combines yearly temperatures with a 10-year rolling average to highlight the long-term warming trend.  
    The annotations mark a cooler historical period, the beginning of more rapid warming, and the highest sustained temperatures in recent years.  
    The key insight is that global warming is not only visible over time, but becomes especially pronounced in the modern period.
    """
)


# 2. Stripes
st.subheader("2. Temperature Anomaly Stripes")

fig_stripes  =  px.imshow(
    [yearly_global["TemperatureAnomaly"].values],
    aspect = "auto",
    color_continuous_scale = "RdBu_r",
    origin = "lower",
)

fig_stripes.update_xaxes(
    tickmode = "array",
    tickvals = list(range(0, len(yearly_global), max(1, len(yearly_global) // 12))),
    ticktext = yearly_global["Year"].iloc[list(range(0, len(yearly_global), max(1, len(yearly_global) // 12)))],
    title = "Year",
)
fig_stripes.update_yaxes(showticklabels = False, title = "")
fig_stripes.update_traces(
    hovertemplate = "Year: %{x}<br>Anomaly: %{z:.2f} °C<extra></extra>"
)
fig_stripes.update_layout(
    title = "Temperature Anomaly Stripes Over Time",
    template = "plotly_white",
    coloraxis_colorbar = dict(title = "Anomaly (°C)"),
)

st.plotly_chart(fig_stripes, use_container_width = True)

st.markdown(
    """
    **Interpretation:**  
    The color stripes show how temperature anomalies shift from cooler tones in earlier years to warmer tones in recent decades.  
    This makes the long-term change visually immediate, even without focusing on exact numerical values.  
    The key insight is that recent decades are dominated by positive anomalies, reinforcing sustained warming.
    """
)


# 3. Box Plot
st.subheader("3. Temperature Distribution by Time Period")

period_data = filtered_global.copy()
period_data = period_data[period_data["Year"] >= 1740].copy()
period_data["TimePeriod"] = (period_data["Year"] // 20) * 20
period_data["TimePeriod"] = period_data["TimePeriod"].astype(str)

ordered_periods = sorted(period_data["TimePeriod"].unique(), key = lambda x: int(x))

fig_box = px.box(
    period_data,
    x = "TimePeriod",
    y = "LandAverageTemperature",
    category_orders = {"TimePeriod": ordered_periods},
    title = "Temperature Distribution by Time Period",
    labels = {"TimePeriod": "Time Period", "LandAverageTemperature": "Average Temperature (°C)"},
)

fig_box.update_layout(template = "plotly_white")

st.plotly_chart(fig_box, use_container_width = True)

st.markdown(
    """
    **Interpretation:**  
    This box plot shows how the full distribution of temperatures changes across time periods rather than only comparing averages.  
    Rising medians and an upward shift in the boxes indicate that the overall temperature distribution has moved higher over time.  
    The key insight is that warming affects the full range of temperatures, not just isolated values.
    """
)


# 4. Interactive Plot
st.subheader("4. Country vs Global Temperature Comparison")

selected_country_compare = st.selectbox(
    "Choose a country to compare with the global average",
    options=available_countries,
    index=available_countries.index("United States") if "United States" in available_countries else 0
)

country_compare = country_clean[
    (country_clean["Country"] == selected_country_compare) &
    (country_clean["Year"] >= year_range[0]) &
    (country_clean["Year"] <= year_range[1])
].copy()

country_compare_yearly = country_compare.groupby("Year", as_index = False)["AverageTemperature"].mean()
global_compare_yearly = filtered_global.groupby("Year", as_index = False)["LandAverageTemperature"].mean()

fig_compare = go.Figure()

fig_compare.add_trace(go.Scatter(
    x = global_compare_yearly["Year"],
    y = global_compare_yearly["LandAverageTemperature"],
    mode = "lines",
    name = "Global Average",
    line = dict(width = 2, color = "red"),
    hovertemplate="Year: %{x}<br>Global Avg: %{y:.2f} °C<extra></extra>"
))

fig_compare.add_trace(go.Scatter(
    x = country_compare_yearly["Year"],
    y = country_compare_yearly["AverageTemperature"],
    mode = "lines",
    name = selected_country_compare,
    line = dict(width = 2, color = "green"),
    hovertemplate = f"Year: %{{x}}<br>{selected_country_compare}: %{{y:.2f}} °C<extra></extra>"
))

fig_compare.update_layout(
    title = f"{selected_country_compare} vs Global Average Temperature Over Time",
    xaxis_title = "Year",
    yaxis_title = "Average Temperature (°C)",
    template = "plotly_white",
    hovermode = "x unified"
)

st.plotly_chart(fig_compare, use_container_width = True)

st.markdown(
    """
    **Interpretation:**  
    This interactive visualization compares the global average temperature trend with the selected country's temperature trend over time.  
    This is important because it shows how national temperature patterns relate to the broader global warming trend.  
    The key insight is that although countries differ in baseline temperature and variability, their long-term trends generally move in the same upward direction as the global average.
    """
)
