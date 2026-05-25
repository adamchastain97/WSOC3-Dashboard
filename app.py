import pandas as pd
import streamlit as st
import plotly.express as px


# Load data
df = pd.read_excel("WSOC Dataset.xlsx")
st.write(df.columns)

# -----------------------------
# PAGE CONFIG
# -----------------------------
st.set_page_config(page_title="WSOC Dashboard", layout="wide")

# -----------------------------
# LOAD DATA
# -----------------------------
@st.cache_data
def load_data():
    df = pd.read_excel("WSOC Dataset.xlsx")
    df["Date"] = pd.to_datetime(df["Date"])
    return df

df = load_data()

# Clean column names (removes hidden spaces)
df.columns = df.columns.str.strip()

# -----------------------------
# METRICS
# -----------------------------
metrics = [
    "Total Player Load",
    "Total Distance",
    "Total A3+D3",
    "HSD >9mph Tot (mi)",
    "VHSD > 13mph",
    "VHSD Exposures > 13mph"
]

# -----------------------------
# COLORS
# -----------------------------
clemson_orange = "#F56600"
clemson_purple = "#522D80"

# -----------------------------
# SIDEBAR FILTERS
# -----------------------------
st.sidebar.header("Filters")

metric = st.sidebar.selectbox("Select Metric", metrics)

datetype = st.sidebar.multiselect(
    "Date Type",
    sorted(df["DateType"].dropna().unique())
)

date = st.sidebar.multiselect(
    "Date",
    sorted(df["Date"].dt.strftime("%Y-%m-%d").unique())
)

matchday = st.sidebar.multiselect(
    "Match Day",
    df["Match Day"].dropna().unique()
)

position = st.sidebar.multiselect(
    "Position",
    df["Position Name"].dropna().unique()
)

player = st.sidebar.multiselect(
    "Player",
    df["Name"].dropna().unique()
)

# -----------------------------
# FILTER DATA
# -----------------------------
filtered = df.copy()

if datetype:
    filtered = filtered[filtered["DateType"].isin(datetype)]

if date:
    filtered = filtered[
        filtered["Date"].dt.strftime("%Y-%m-%d").isin(date)
    ]

if matchday:
    filtered = filtered[filtered["Match Day"].isin(matchday)]

if position:
    filtered = filtered[filtered["Position Name"].isin(position)]

if player:
    filtered = filtered[filtered["Name"].isin(player)]

# -----------------------------
# OUTLIER DETECTION
# -----------------------------
threshold = filtered[metric].quantile(0.95)
filtered["Outlier"] = filtered[metric] > threshold

# -----------------------------
# MAIN TITLE
# -----------------------------
st.title("WSOC Load Dashboard")
st.markdown("Track microcycle loads and identify outliers")

# -----------------------------
# BOXPLOT
# -----------------------------
try:
    fig = px.box(
        filtered,
        x="DateType",   # adjust if needed
        y=metric,
        points="all",
        color="Outlier",
        facet_col="Year"
    )
    
    st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error(f"Plot error: {e}")
    st.write(filtered.head())

for col in metrics:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# -----------------------------
# SUMMARY STATS
# -----------------------------
st.subheader("Summary Stats")

summary = filtered.groupby("DateType")[metric].agg([
    "mean", "median", "max", "min"
]).reset_index()

st.dataframe(summary)

# -----------------------------
# DOWNLOAD DATA
# -----------------------------
st.subheader("Download Filtered Data")

csv = filtered.to_csv(index=False).encode("utf-8")

st.download_button(
    "Download CSV",
    csv,
    "filtered_data.csv",
    "text/csv"
)
