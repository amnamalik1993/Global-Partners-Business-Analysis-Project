import streamlit as st
import plotly.express as px
import pandas as pd

from utils import (
    load_location_performance,
    currency,
    integer
)
# =====================================================
# Page Configuration
# =====================================================
st.set_page_config(

    page_title="Location Performance",

    page_icon="📍",

    layout="wide"

)
# =====================================================
# Title
# =====================================================
st.title(
    "📍 Restaurant Location Performance Dashboard"
)

st.markdown(
"""
Analyze restaurant locations based on:

- Revenue performance
- Order volume
- Average order value
- Customer engagement
- Operational efficiency

Used for expansion decisions, staffing, and promotions.
"""
)
# =====================================================
# Load Data
# =====================================================
df = load_location_performance()

if df.empty:

    st.error(

        """
        Location performance data unavailable.

        Verify Gold path:

        gold/top_performing_locations/

        """

    )

    st.stop()
# =====================================================
# Data Type Cleanup for Plotly
# =====================================================
numeric_columns = [

    "TOTAL_REVENUE",

    "TOTAL_ORDERS",

    "AVG_ORDER_VALUE",

    "ORDERS_PER_DAY",

    "ORDERS_PER_WEEK",

    "CUSTOMER_RETENTION_RATE"

]

for column in numeric_columns:

    if column in df.columns:

        df[column] = pd.to_numeric(

            df[column],

            errors="coerce"

        )
# =====================================================
# Sidebar Filters
# =====================================================
st.sidebar.header(
    "Filters"
)

filtered_df = df.copy()


if "RESTAURANT_ID" in df.columns:


    restaurants = sorted(

        df["RESTAURANT_ID"]

        .dropna()

        .unique()

        .tolist()

    )

    selected_restaurants = st.sidebar.multiselect(

        "Restaurant",

        restaurants,

        default=restaurants

    )

    filtered_df = filtered_df[

        filtered_df["RESTAURANT_ID"]

        .isin(selected_restaurants)

    ]

# =====================================================
# KPI Overview
# =====================================================

st.header(
    "Location Overview"
)

col1, col2, col3, col4 = st.columns(4)

with col1:

    st.metric(

        "Locations",

        integer(

            filtered_df["RESTAURANT_ID"]

            .nunique()

        )

    )

with col2:

    st.metric(

        "Total Revenue",

        currency(

            filtered_df["TOTAL_REVENUE"]

            .sum()

        )

    )

with col3:

    st.metric(

        "Total Orders",

        integer(

            filtered_df["TOTAL_ORDERS"]

            .sum()

        )

    )

with col4:

    st.metric(

        "Average Order Value",

        currency(

            filtered_df["AVG_ORDER_VALUE"]

            .mean()

        )

    )

# =====================================================
# Revenue Ranking
# =====================================================
st.divider()

st.header(
    "Restaurant Revenue Ranking"
)

revenue_rank = (

    filtered_df

    .sort_values(

        "TOTAL_REVENUE",

        ascending=False

    )

)

fig = px.bar(

    revenue_rank,

    x="RESTAURANT_ID",

    y="TOTAL_REVENUE",

    title="Restaurant Revenue Ranking",

    text="TOTAL_REVENUE"

)

st.plotly_chart(

    fig,

    use_container_width=True

)
# =====================================================
# Top Performing Locations
# =====================================================

st.divider()

st.header(

    "Top Performing Restaurants"

)

top_locations = (

    filtered_df

    .sort_values(

        "TOTAL_REVENUE",

        ascending=False

    )

    .head(10)

)

st.dataframe(

    top_locations,

    use_container_width=True

)
# =====================================================
# Average Order Value Comparison
# =====================================================
st.divider()

st.header(

    "Average Order Value by Location"

)


if "AVG_ORDER_VALUE" in filtered_df.columns:


    fig = px.bar(

        filtered_df.sort_values(

            "AVG_ORDER_VALUE",

            ascending=False

        ),

        x="RESTAURANT_ID",

        y="AVG_ORDER_VALUE",

        title="Average Customer Spend per Order",

        text="AVG_ORDER_VALUE"

    )


    st.plotly_chart(

        fig,

        use_container_width=True

    )
# =====================================================
# Order Volume Analysis
# =====================================================
st.divider()

st.header(

    "Order Volume Performance"

)



if (

    "TOTAL_ORDERS" in filtered_df.columns

    and

    "AVG_ORDER_VALUE" in filtered_df.columns

):

    scatter_df = filtered_df.copy()


    scatter_df["AVG_ORDER_VALUE"] = (

        scatter_df["AVG_ORDER_VALUE"]

        .fillna(0)

    )

    fig = px.scatter(

        scatter_df,

        x="TOTAL_ORDERS",

        y="TOTAL_REVENUE",

        size="AVG_ORDER_VALUE",

        hover_name="RESTAURANT_ID",

        title="Revenue vs Order Volume"

    )

    st.plotly_chart(

        fig,

        use_container_width=True

    )
# =====================================================
# Orders Per Day / Week
# =====================================================
if (

    "ORDERS_PER_DAY" in filtered_df.columns

    or

    "ORDERS_PER_WEEK" in filtered_df.columns

):

    st.divider()

    st.header(

        "Operational Activity"

    )

    activity_columns = []


    if "ORDERS_PER_DAY" in filtered_df.columns:

        activity_columns.append(

            "ORDERS_PER_DAY"

        )

    if "ORDERS_PER_WEEK" in filtered_df.columns:

        activity_columns.append(

            "ORDERS_PER_WEEK"

        )

    activity = filtered_df[

        [

            "RESTAURANT_ID"

        ]

        +

        activity_columns

    ]

    st.dataframe(

        activity,

        use_container_width=True

    )

# =====================================================
# Customer Retention Analysis
# =====================================================
if "CUSTOMER_RETENTION_RATE" in filtered_df.columns:


    st.divider()


    st.header(

        "Customer Retention by Location"

    )

    fig = px.bar(

        filtered_df.sort_values(

            "CUSTOMER_RETENTION_RATE",

            ascending=False

        ),

        x="RESTAURANT_ID",

        y="CUSTOMER_RETENTION_RATE",

        title="Customer Retention Rate"

    )


    st.plotly_chart(

        fig,

        use_container_width=True

    )

# =====================================================
# Complete Dataset
# =====================================================
st.divider()

st.header(

    "Location Details"

)

st.dataframe(

    filtered_df,

    use_container_width=True

)