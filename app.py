import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import streamlit as st

# --------------------------------------------------
# Dashboard setup
# --------------------------------------------------
st.set_page_config(
    page_title="WSOC Total Distance Dashboard",
    layout="wide"
)

st.title("WSOC Total Distance Boxplot Dashboard")

# --------------------------------------------------
# File path
# --------------------------------------------------
file_path = r"C:\Users\adamc\OneDrive\Desktop\Data Projects\WSOC Dataset.xlsx"

# --------------------------------------------------
# Column names
# --------------------------------------------------
date_col = "Date"
lookup_date_col = "Date.1"
date_type_col = "DateType"
metric_col = "Total Distance (mi) (m)"

# --------------------------------------------------
# Load and prepare data
# --------------------------------------------------
@st.cache_data
def load_data(file_path):
    sheets = pd.read_excel(file_path, sheet_name=None)

    all_data = []

    for sheet_name, sheet in sheets.items():
        sheet = sheet.copy()

        sheet[date_col] = pd.to_datetime(
            sheet[date_col],
            errors="coerce"
        ).dt.normalize()

        sheet[lookup_date_col] = pd.to_datetime(
            sheet[lookup_date_col],
            errors="coerce"
        ).dt.normalize()

        date_type_lookup = (
            sheet[[lookup_date_col, date_type_col]]
            .dropna(subset=[lookup_date_col, date_type_col])
            .drop_duplicates(subset=[lookup_date_col])
            .set_index(lookup_date_col)[date_type_col]
        )

        sheet["CleanDateType"] = sheet[date_col].map(date_type_lookup)

        sheet["SourceSheet"] = sheet_name
        all_data.append(sheet)

    df = pd.concat(all_data, ignore_index=True)

    df = df.dropna(
        subset=[date_col, metric_col, "CleanDateType"]
    ).copy()

    df["Year"] = df[date_col].dt.year
    df["DateLabel"] = df[date_col].dt.strftime("%m/%d/%Y")

    return df


df = load_data(file_path)

# --------------------------------------------------
# Sidebar filters
# --------------------------------------------------
st.sidebar.header("Filters")

year_options = sorted(df["Year"].dropna().unique())

selected_year = st.sidebar.selectbox(
    "Select Year",
    year_options
)

year_df = df[df["Year"] == selected_year].copy()

date_type_order = [
    "MD -4", "MD -3", "MD -2", "MD -1",
    "MD",
    "MD +1", "MD +2", "MD +3", "MD +4",
    "MD +1/-2", "MD +2/-1", "MD +3/-1", "MD +4/-1"
]

available_date_types = [
    date_type for date_type in date_type_order
    if date_type in year_df["CleanDateType"].unique()
]

extra_date_types = sorted(
    date_type for date_type in year_df["CleanDateType"].dropna().unique()
    if date_type not in available_date_types
)

date_type_options = available_date_types + extra_date_types

selected_date_type = st.sidebar.selectbox(
    "Select DateType",
    date_type_options
)

plot_df = year_df[
    year_df["CleanDateType"] == selected_date_type
].copy()

# --------------------------------------------------
# Plot
# --------------------------------------------------
st.subheader(
    f"Total Distance by Individual Date: {selected_year} - {selected_date_type}"
)

if plot_df.empty:
    st.warning("No data available for this year and DateType.")
else:
    date_order = (
        plot_df[[date_col, "DateLabel"]]
        .drop_duplicates()
        .sort_values(date_col)["DateLabel"]
        .tolist()
    )

    sns.set_theme(style="whitegrid")

    fig, ax = plt.subplots(figsize=(20, 7))

    sns.boxplot(
        data=plot_df,
        x="DateLabel",
        y=metric_col,
        order=date_order,
        color="#6f8fb8",
        ax=ax
    )

    ax.set_title(
        f"Total Distance by Individual Date - {selected_year} - {selected_date_type}"
    )
    ax.set_xlabel("Individual Date")
    ax.set_ylabel("Total Distance")
    ax.tick_params(axis="x", rotation=90)

    st.pyplot(fig)

# --------------------------------------------------
# Optional data table
# --------------------------------------------------
with st.expander("View Filtered Data"):
    st.dataframe(
        plot_df[
            [
                "Name",
                date_col,
                "DateLabel",
                "CleanDateType",
                metric_col,
                "Year"
            ]
        ],
        use_container_width=True
    )
