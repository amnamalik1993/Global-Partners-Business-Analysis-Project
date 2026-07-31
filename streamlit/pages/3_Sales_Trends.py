import streamlit as st
import plotly.express as px
from utils import (
    load_sales_trends,
    currency,
    integer
)
# =====================================================
# Page Configuration
# =====================================================
st.set_page_config(

    page_title="Sales Trends Dashboard",

    page_icon="📈",

    layout="wide"

)
# =====================================================
# Title
# =====================================================
st.title(
    "📈 Sales Trends & Seasonality Dashboard"
)


st.markdown(
"""
Analyze revenue patterns across:

- Daily sales activity
- Weekly and monthly trends
- Restaurant locations
- Menu categories
- Ordering time periods

Used for inventory planning and operational decisions.
"""
)
# =====================================================
# Load Data
# =====================================================
df = load_sales_trends()

if df.empty:

    st.error(

        """
        Sales trend data unavailable.

        Verify Gold path:

        gold/sales_trends/

        """

    )

    st.stop()
# =====================================================
# Sidebar Filters
# =====================================================
st.sidebar.header(
    "Filters"
)

filtered_df = df.copy()
# =====================================================
# Sales Period Filter
# =====================================================
if "SALES_PERIOD" in df.columns:

    periods = sorted(

        df["SALES_PERIOD"]

        .dropna()

        .unique()

        .tolist()

    )

    selected_period = st.sidebar.multiselect(

        "Sales Period",

        periods,

        default=periods

    )

    filtered_df = filtered_df[

        filtered_df["SALES_PERIOD"]

        .isin(selected_period)

    ]
# =====================================================
# Restaurant Filter
# =====================================================
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
# Category Filter
# =====================================================
if "ITEM_CATEGORY" in df.columns:

    categories = sorted(

        df["ITEM_CATEGORY"]

        .dropna()

        .unique()

        .tolist()

    )

    selected_categories = st.sidebar.multiselect(

        "Menu Category",

        categories,

        default=categories

    )

    filtered_df = filtered_df[

        filtered_df["ITEM_CATEGORY"]

        .isin(selected_categories)

    ]
# =====================================================
# KPI Summary
# =====================================================
st.header(
    "Sales Overview"
)

col1, col2, col3, col4 = st.columns(4)

with col1:

    st.metric(

        "Revenue",

        currency(

            filtered_df["TOTAL_REVENUE"]

            .sum()

        )

    )

with col2:

    st.metric(

        "Orders",

        integer(

            filtered_df["TOTAL_ORDERS"]

            .sum()

        )

    )

with col3:

    st.metric(

        "Items Sold",

        integer(

            filtered_df["ITEMS_SOLD"]

            .sum()

        )

    )

with col4:

    st.metric(

        "Avg Order Value",

        currency(

            filtered_df["AVG_ORDER_VALUE"]

            .mean()

        )

    )
# =====================================================
# Monthly Sales Trend
# =====================================================
st.divider()

st.header(
    "Monthly Revenue Trend"
)

if (

    "MONTH" in filtered_df.columns

    and

    "YEAR" in filtered_df.columns

):

    monthly = (

        filtered_df

        .groupby(

            [

                "YEAR",

                "MONTH"

            ]

        )

        [

            "TOTAL_REVENUE"

        ]

        .sum()

        .reset_index()

    )

    monthly["PERIOD"] = (

        monthly["YEAR"]

        .astype(str)

        +

        "-"

        +

        monthly["MONTH"]

        .astype(str)

    )

    fig = px.line(

        monthly,

        x="PERIOD",

        y="TOTAL_REVENUE",

        markers=True,

        title="Monthly Revenue Trend"

    )

    st.plotly_chart(

        fig,

        use_container_width=True

    )
# =====================================================
# Revenue by Category
# =====================================================
if "ITEM_CATEGORY" in filtered_df.columns:

    st.divider()

    st.header(

        "Revenue by Menu Category"

    )

    category_sales = (

        filtered_df

        .groupby(

            "ITEM_CATEGORY"

        )

        [

            "TOTAL_REVENUE"

        ]

        .sum()

        .reset_index()

        .sort_values(

            "TOTAL_REVENUE",

            ascending=False

        )

    )

    fig = px.bar(

        category_sales,

        x="ITEM_CATEGORY",

        y="TOTAL_REVENUE",

        title="Revenue Contribution by Category",

        text="TOTAL_REVENUE"

    )

    st.plotly_chart(

        fig,

        use_container_width=True

    )
# =====================================================
# Location Performance Over Time
# =====================================================
if "RESTAURANT_ID" in filtered_df.columns:

    st.divider()

    st.header(

        "Restaurant Revenue Comparison"

    )

    location_sales = (

        filtered_df

        .groupby(

            "RESTAURANT_ID"

        )

        [

            "TOTAL_REVENUE"

        ]

        .sum()

        .reset_index()

        .sort_values(

            "TOTAL_REVENUE",

            ascending=False

        )

        .head(20)

    )

    fig = px.bar(

        location_sales,

        x="RESTAURANT_ID",

        y="TOTAL_REVENUE",

        title="Top 20 Restaurants by Revenue",

        text="TOTAL_REVENUE"

    )

    st.plotly_chart(

        fig,

        use_container_width=True

    )
# =====================================================
# Time of Day Analysis
# =====================================================
if "TIME_OF_DAY" in filtered_df.columns:


    st.divider()

    st.header(

        "Peak Ordering Periods"

    )

    time_sales = (

        filtered_df

        .groupby(

            "TIME_OF_DAY"

        )

        [

            "TOTAL_REVENUE"

        ]

        .sum()

        .reset_index()

    )

    fig = px.bar(

        time_sales,

        x="TIME_OF_DAY",

        y="TOTAL_REVENUE",

        title="Revenue by Time of Day",

        text="TOTAL_REVENUE"

    )

    st.plotly_chart(

        fig,

        use_container_width=True

    )
# =====================================================
# Detailed Data Table
# =====================================================
st.divider()

st.header(

    "Sales Detail"

)

st.dataframe(

    filtered_df,

    use_container_width=True

)