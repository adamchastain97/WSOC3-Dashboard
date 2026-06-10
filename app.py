import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import streamlit as st

st.set_page_config(
    page_title="WSOC Performance Dashboard",
    layout="wide"
)

st.title("WSOC Performance Boxplot Dashboard")

date_col = "Date"
lookup_date_col = "Date.1"
date_type_col = "DateType"

outlier_metric_col = "Total Distance (mi) (m)"

metric_options = {
    "Total Player Load": "Total Player Load",
    "Total Distance (mi) (m)": "Total Distance (mi) (m)",
    "Total A3+D3": "Total A3+D3",
    "HSD >9mph": "HSD >9mph Tot (mi)",
    "VHSD >13mph": "VHSD > 13mph",
    "VHSD Exposures >13mph": "VHSD Exposures > 13mph"
}


def clean_text(value):
    if pd.isna(value):
        return ""
    return str(value).strip().lower()


@st.cache_data
def load_main_data(uploaded_file):
    sheets = pd.read_excel(uploaded_file, sheet_name=None)
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
        subset=[date_col, outlier_metric_col, "CleanDateType"]
    ).copy()

    df["Year"] = df[date_col].dt.year
    df["DateLabel"] = df[date_col].dt.strftime("%m/%d/%Y")

    return df


@st.cache_data
def load_outliers(uploaded_file):
    outliers = pd.read_excel(uploaded_file)

    outliers["Date"] = pd.to_datetime(
        outliers["Date"],
        errors="coerce"
    ).dt.normalize()

    outliers["Year"] = pd.to_numeric(
        outliers["Year"],
        errors="coerce"
    )

    outliers["CleanDateType"] = outliers["Date Type"].astype(str).str.strip()
    outliers["OutlierDistanceRounded"] = outliers["Total Dist. (mi) (m)"].round(3)
    outliers["CleanName"] = outliers["Name"].apply(clean_text)

    return outliers.dropna(
        subset=["Year", "Date", "CleanDateType", "OutlierDistanceRounded"]
    )


def apply_outlier_filter(df, outliers, match_mode):
    df = df.copy()

    df["CleanName"] = df["Name"].apply(clean_text)
    df["DistanceRounded"] = df[outlier_metric_col].round(3)

    if match_mode == "Strict: name + date + DateType + distance":
        outlier_keys = (
            outliers[
                [
                    "Year",
                    "Date",
                    "CleanDateType",
                    "OutlierDistanceRounded",
                    "CleanName"
                ]
            ]
            .drop_duplicates()
            .copy()
        )

        outlier_keys["IsOutlier"] = True

        filtered = df.merge(
            outlier_keys,
            left_on=[
                "Year",
                date_col,
                "CleanDateType",
                "DistanceRounded",
                "CleanName"
            ],
            right_on=[
                "Year",
                "Date",
                "CleanDateType",
                "OutlierDistanceRounded",
                "CleanName"
            ],
            how="left"
        )

    else:
        outlier_keys = (
            outliers[
                [
                    "Year",
                    "Date",
                    "CleanDateType",
                    "OutlierDistanceRounded"
                ]
            ]
            .drop_duplicates()
            .copy()
        )

        outlier_keys["IsOutlier"] = True

        filtered = df.merge(
            outlier_keys,
            left_on=[
                "Year",
                date_col,
                "CleanDateType",
                "DistanceRounded"
            ],
            right_on=[
                "Year",
                "Date",
                "CleanDateType",
                "OutlierDistanceRounded"
            ],
            how="left"
        )

    removed = filtered["IsOutlier"].fillna(False).sum()
    filtered = filtered[filtered["IsOutlier"] != True].copy()

    return filtered, int(removed)


st.sidebar.header("Files")

main_file = st.sidebar.file_uploader(
    "Upload WSOC Dataset.xlsx",
    type=["xlsx"]
)

outlier_file = st.sidebar.file_uploader(
    "Upload WSOC Outliers 23-26.xlsx",
    type=["xlsx"]
)

if main_file is None:
    st.info("Upload your WSOC Dataset.xlsx file to begin.")
    st.stop()

df = load_main_data(main_file)

if outlier_file is not None:
    outliers = load_outliers(outlier_file)

    match_mode = st.sidebar.selectbox(
        "Outlier matching method",
        [
            "Flexible: date + DateType + rounded distance",
            "Strict: name + date + DateType + distance"
        ]
    )

    df, removed_count = apply_outlier_filter(df, outliers, match_mode)

    st.sidebar.success(f"Filtered out {removed_count} outlier rows.")
else:
    st.sidebar.warning("No outlier file uploaded. Showing unfiltered data.")

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

available_metric_options = {
    display_name: column_name
    for display_name, column_name in metric_options.items()
    if column_name in year_df.columns
}

selected_metric_label = st.sidebar.selectbox(
    "Select Metric",
    list(available_metric_options.keys())
)

selected_metric = available_metric_options[selected_metric_label]

plot_df = year_df[
    year_df["CleanDateType"] == selected_date_type
].copy()

plot_df = plot_df.dropna(subset=[selected_metric])

st.subheader(
    f"{selected_metric_label} by Individual Date: {selected_year} - {selected_date_type}"
)

if plot_df.empty:
    st.warning("No data available for this year, DateType, and metric after filtering.")
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
        y=selected_metric,
        order=date_order,
        color="#6f8fb8",
        showfliers=False,
        ax=ax
    )

    ax.set_title(
        f"{selected_metric_label} by Individual Date - {selected_year} - {selected_date_type}"
    )
    ax.set_xlabel("Individual Date")
    ax.set_ylabel(selected_metric_label)
    ax.tick_params(axis="x", rotation=90)

    st.pyplot(fig)

with st.expander("View Filtered Data"):
    columns_to_show = [
        "Name",
        date_col,
        "DateLabel",
        "CleanDateType",
        selected_metric,
        "Year"
    ]

    st.dataframe(
        plot_df[columns_to_show],
        use_container_width=True
    )
