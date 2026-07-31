import streamlit as st
import plotly.express as px
from utils import (
    load_pricing_discount,
    currency,
    integer
)
# =====================================================
# Page Configuration
# =====================================================
st.set_page_config(

    page_title="Pricing & Discount Effectiveness",

    page_icon="🏷️",

    layout="wide"

)
# =====================================================
# Title
# =====================================================
st.title(
    "🏷️ Pricing & Discount Effectiveness Dashboard"
)

st.markdown(
"""
Analyze how discounts and promotions impact:

- Revenue
- Order volume
- Customer purchasing behavior
- Net revenue after discounts

Used to optimize pricing strategies.
"""
)
# =====================================================
# Load Data
# =====================================================
df = load_pricing_discount()

if df.empty:

    st.error(

        """
        Pricing discount data unavailable.

        Verify Gold path:

        gold/pricing_discount_effectiveness/

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
# -----------------------------------------------------
# Discount Status Filter
# -----------------------------------------------------
if "DISCOUNT_STATUS" in df.columns:

    discount_values = sorted(

        df["DISCOUNT_STATUS"]

        .dropna()

        .unique()

        .tolist()

    )

    selected_discount = st.sidebar.multiselect(

        "Discount Status",

        discount_values,

        default=discount_values

    )

    filtered_df = filtered_df[

        filtered_df["DISCOUNT_STATUS"]

        .isin(selected_discount)

    ]
# -----------------------------------------------------
# Category Filter
# -----------------------------------------------------
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
    "Pricing Impact Overview"
)


col1, col2, col3, col4 = st.columns(4)

with col1:

    st.metric(

        "Gross Revenue",

        currency(

            filtered_df["GROSS_REVENUE"]

            .sum()

        )

    )


with col2:

    st.metric(

        "Discount Given",

        currency(

            filtered_df["DISCOUNT_AMOUNT"]

            .sum()

        )

    )


with col3:

    st.metric(

        "Net Revenue",

        currency(

            filtered_df["NET_REVENUE"]

            .sum()

        )

    )


with col4:

    discount_rate = (

        filtered_df["DISCOUNT_AMOUNT"]

        .sum()

        /

        filtered_df["GROSS_REVENUE"]

        .sum()

        *

        100

    )

    st.metric(

        "Discount Rate",

        f"{discount_rate:.2f}%"

    )
# =====================================================
# Discount vs Full Price Revenue
# =====================================================
st.divider()

st.header(

    "Discounted vs Full-Price Revenue"

)

revenue_comparison = (

    filtered_df

    .groupby(

        "DISCOUNT_STATUS"

    )

    .agg(

        GROSS_REVENUE=(

            "GROSS_REVENUE",

            "sum"

        ),

        NET_REVENUE=(

            "NET_REVENUE",

            "sum"

        )

    )

    .reset_index()

)

fig = px.bar(

    revenue_comparison,

    x="DISCOUNT_STATUS",

    y=[

        "GROSS_REVENUE",

        "NET_REVENUE"

    ],

    barmode="group",

    title="Total vs Net Revenue"

)

st.plotly_chart(

    fig,

    use_container_width=True

)
# =====================================================
# Discount Impact on Orders
# =====================================================
st.divider()

st.header(

    "Order Volume Impact"

)

if "TOTAL_ORDERS" in filtered_df.columns:


    orders = (

        filtered_df

        .groupby(

            "DISCOUNT_STATUS"

        )

        .agg(

            ORDERS=(

                "TOTAL_ORDERS",

                "sum"

            )

        )

        .reset_index()

    )


    fig = px.bar(

        orders,

        x="DISCOUNT_STATUS",

        y="ORDERS",

        text="ORDERS",

        title="Orders by Discount Status"

    )


    st.plotly_chart(

        fig,

        use_container_width=True

    )
# =====================================================
# Average Order Value Impact
# =====================================================
st.divider()

st.header(

    "Average Order Value Impact"

)

if "AVG_ORDER_VALUE" in filtered_df.columns:


    avg_order = (

        filtered_df

        .groupby(

            "DISCOUNT_STATUS"

        )

        .agg(

            AVG_ORDER_VALUE=(

                "AVG_ORDER_VALUE",

                "mean"

            )

        )

        .reset_index()

    )

    fig = px.bar(

        avg_order,

        x="DISCOUNT_STATUS",

        y="AVG_ORDER_VALUE",

        text="AVG_ORDER_VALUE",

        title="Average Order Value Comparison"

    )

    st.plotly_chart(

        fig,

        use_container_width=True

    )
# =====================================================
# Category Discount Analysis
# =====================================================
if "ITEM_CATEGORY" in filtered_df.columns:

    st.divider()

    st.header(

        "Discount Effect by Menu Category"

    )

    category_discount = (

        filtered_df

        .groupby(

            [

                "ITEM_CATEGORY",

                "DISCOUNT_STATUS"

            ]

        )

        .agg(

            NET_REVENUE=(

                "NET_REVENUE",

                "sum"

            )

        )

        .reset_index()

    )

    fig = px.bar(

        category_discount,

        x="ITEM_CATEGORY",

        y="NET_REVENUE",

        color="DISCOUNT_STATUS",

        barmode="group",

        title="Net Revenue by Category and Discount Type"

    )

    st.plotly_chart(

        fig,

        use_container_width=True

    )
# =====================================================
# Restaurant Discount Performance
# =====================================================
if "RESTAURANT_ID" in filtered_df.columns:

    st.divider()

    st.header(

        "Restaurant Promotion Performance"

    )

    restaurant_discount = (

        filtered_df

        .groupby(

            [

                "RESTAURANT_ID",

                "DISCOUNT_STATUS"

            ]

        )

        .agg(

            NET_REVENUE=(

                "NET_REVENUE",

                "sum"

            )

        )

        .reset_index()

    )

    fig = px.bar(

        restaurant_discount,

        x="RESTAURANT_ID",

        y="NET_REVENUE",

        color="DISCOUNT_STATUS",

        barmode="group",

        title="Restaurant Revenue by Discount Strategy"

    )

    st.plotly_chart(

        fig,

        use_container_width=True

    )
# =====================================================
# Detail Table
# =====================================================
st.divider()
st.header(

    "Pricing Detail Data"

)

st.dataframe(

    filtered_df.sort_values(

        "NET_REVENUE",

        ascending=False

    ),

    use_container_width=True

)