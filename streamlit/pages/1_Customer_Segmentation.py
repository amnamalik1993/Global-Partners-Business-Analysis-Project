import streamlit as st
import pandas as pd
import plotly.express as px

from utils import load_customer_segmentation


# =====================================================
# Page Configuration
# =====================================================

st.set_page_config(
    page_title="Customer Segmentation",
    page_icon="👥",
    layout="wide"
)


# =====================================================
# Load Data
# =====================================================

df = load_customer_segmentation()


# =====================================================
# Validate Data
# =====================================================

required_columns = [

    "CUSTOMER_ID",
    "RECENCY",
    "FREQUENCY",
    "MONETARY",
    "R_SCORE",
    "F_SCORE",
    "M_SCORE",
    "RFM_SCORE",
    "CUSTOMER_SEGMENT",
    "IS_LOYALTY"

]


missing_columns = [

    col

    for col in required_columns

    if col not in df.columns

]


if missing_columns:

    st.error(
        f"Missing columns: {missing_columns}"
    )

    st.stop()



# =====================================================
# Title
# =====================================================

st.title(
    "Customer Segmentation Dashboard"
)


st.markdown(
    """
    This dashboard analyzes customer purchase behavior using
    RFM (Recency, Frequency, Monetary) segmentation.
    """
)



# =====================================================
# Filters
# =====================================================

st.sidebar.header(
    "Filters"
)


segment_filter = st.sidebar.multiselect(

    "Customer Segment",

    options=df["CUSTOMER_SEGMENT"].unique(),

    default=df["CUSTOMER_SEGMENT"].unique()

)


loyalty_filter = st.sidebar.multiselect(

    "Loyalty Status",

    options=df["IS_LOYALTY"].unique(),

    default=df["IS_LOYALTY"].unique()

)



filtered_df = df[

    (df["CUSTOMER_SEGMENT"].isin(segment_filter))

    &

    (df["IS_LOYALTY"].isin(loyalty_filter))

]



# =====================================================
# KPI Metrics
# =====================================================

col1, col2, col3, col4 = st.columns(4)


col1.metric(

    "Total Customers",

    filtered_df["CUSTOMER_ID"].nunique()

)


col2.metric(

    "Average Spend",

    f"${filtered_df['MONETARY'].mean():,.2f}"

)


col3.metric(

    "Average Orders",

    round(
        filtered_df["FREQUENCY"].mean(),
        2
    )

)


col4.metric(

    "Average Recency",

    f"{filtered_df['RECENCY'].mean():.0f} days"

)



# =====================================================
# Customer Segment Distribution
# =====================================================

st.divider()

st.header(
    "Customer Segment Distribution"
)


segment_count = (

    filtered_df

    .groupby(
        "CUSTOMER_SEGMENT"
    )

    .size()

    .reset_index(
        name="CUSTOMER_COUNT"
    )

)



fig = px.bar(

    segment_count,

    x="CUSTOMER_SEGMENT",

    y="CUSTOMER_COUNT",

    text="CUSTOMER_COUNT",

    title="Customers by Segment"

)


st.plotly_chart(

    fig,

    use_container_width=True

)



# =====================================================
# RFM Behavior Analysis
# =====================================================

st.divider()

st.header(
    "RFM Behavior Analysis"
)



rfm_summary = (

    filtered_df

    .groupby(
        "CUSTOMER_SEGMENT"
    )

    .agg(

        Average_Recency=(

            "RECENCY",

            "mean"

        ),

        Average_Frequency=(

            "FREQUENCY",

            "mean"

        ),

        Average_Monetary=(

            "MONETARY",

            "mean"

        ),

        Average_RFM_Score=(

            "RFM_SCORE",

            "count"

        )

    )

    .reset_index()

)



st.dataframe(

    rfm_summary,

    use_container_width=True

)



rfm_chart = rfm_summary.melt(

    id_vars=[

        "CUSTOMER_SEGMENT"

    ],

    value_vars=[

        "Average_Recency",

        "Average_Frequency",

        "Average_Monetary"

    ],

    var_name="Metric",

    value_name="Value"

)



fig = px.bar(

    rfm_chart,

    x="CUSTOMER_SEGMENT",

    y="Value",

    color="Metric",

    barmode="group",

    title="RFM Metrics by Segment"

)


st.plotly_chart(

    fig,

    use_container_width=True

)



# =====================================================
# RFM Score Distribution
# =====================================================

st.divider()

st.header(
    "RFM Score Distribution"
)


fig = px.histogram(

    filtered_df,

    x="RFM_SCORE",

    color="CUSTOMER_SEGMENT",

    title="Customer Distribution by RFM Score"

)


st.plotly_chart(

    fig,

    use_container_width=True

)



# =====================================================
# High Value Customers
# =====================================================

st.divider()

st.header(
    "High Value Customers"
)


high_value = (

    filtered_df

    .sort_values(

        "MONETARY",

        ascending=False

    )

    .head(20)

)



st.dataframe(

    high_value[

        [

            "CUSTOMER_ID",

            "MONETARY",

            "FREQUENCY",

            "RECENCY",

            "RFM_SCORE",

            "CUSTOMER_SEGMENT",

            "IS_LOYALTY"

        ]

    ],

    use_container_width=True

)



# =====================================================
# Loyalty Impact
# =====================================================

st.divider()

st.header(
    "Loyalty Status Comparison"
)


loyalty_summary = (

    filtered_df

    .groupby(

        "IS_LOYALTY"

    )

    .agg(

        Average_Spend=(

            "MONETARY",

            "mean"

        ),

        Average_Frequency=(

            "FREQUENCY",

            "mean"

        ),

        Average_Recency=(

            "RECENCY",

            "mean"

        )

    )

    .reset_index()

)


st.dataframe(

    loyalty_summary,

    use_container_width=True

)