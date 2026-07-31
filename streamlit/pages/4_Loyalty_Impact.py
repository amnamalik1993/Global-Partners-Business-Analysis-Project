import streamlit as st
import plotly.express as px
from utils import (
    load_loyalty_program,
    currency,
    integer
)
# =====================================================
# Page Configuration
# =====================================================
st.set_page_config(

    page_title="Loyalty Program Impact",

    page_icon="⭐",

    layout="wide"

)
# =====================================================
# Title
# =====================================================
st.title(
    "⭐ Loyalty Program Impact Dashboard"
)

st.markdown(
"""
Compare loyalty members versus non-members to evaluate:

- Spending behavior
- Repeat purchases
- Customer lifetime value
- Loyalty program effectiveness
"""
)
# =====================================================
# Load Data
# =====================================================
df = load_loyalty_program()

if df.empty:

    st.error(

        """
        Loyalty program data unavailable.

        Verify Gold path:

        gold/loyalty_program_impact/

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

if "LOYALTY_STATUS" in df.columns:


    loyalty_status = sorted(

        df["LOYALTY_STATUS"]

        .dropna()

        .unique()

        .tolist()

    )

    selected_status = st.sidebar.multiselect(

        "Loyalty Status",

        loyalty_status,

        default=loyalty_status

    )

    filtered_df = filtered_df[

        filtered_df["LOYALTY_STATUS"]

        .isin(selected_status)

    ]
# =====================================================
# KPI Overview
# =====================================================
st.header(
    "Loyalty Program Overview"
)
col1, col2, col3, col4 = st.columns(4)

with col1:

    st.metric(

        "Customers",

        integer(

            filtered_df["CUSTOMER_ID"]

            .nunique()

        )

    )
with col2:

    st.metric(

        "Total Revenue",

        currency(

            filtered_df["TOTAL_SPEND"]

            .sum()

        )

    )
with col3:

    st.metric(

        "Avg Customer Spend",

        currency(

            filtered_df["TOTAL_SPEND"]

            .mean()

        )

    )
with col4:

    st.metric(

        "Avg Orders / Customer",

        round(

            filtered_df["TOTAL_ORDERS"]

            .mean(),

            2

        )

    )
# =====================================================
# Loyalty Customer Distribution
# =====================================================
st.divider()

st.header(
    "Customer Distribution by Loyalty Status"
)
customer_distribution = (

    filtered_df

    .groupby(

        "LOYALTY_STATUS"

    )

    .agg(

        CUSTOMERS=(

            "CUSTOMER_ID",

            "nunique"

        )

    )

    .reset_index()

)
fig = px.pie(

    customer_distribution,

    names="LOYALTY_STATUS",

    values="CUSTOMERS",

    title="Loyalty Membership Distribution"

)
st.plotly_chart(

    fig,

    use_container_width=True

)
# =====================================================
# Average Spend Comparison
# =====================================================
st.divider()

st.header(

    "Average Spend Comparison"

)
avg_spend = (

    filtered_df

    .groupby(

        "LOYALTY_STATUS"

    )

    .agg(

        AVG_SPEND=(

            "TOTAL_SPEND",

            "mean"

        )

    )

    .reset_index()

)

fig = px.bar(

    avg_spend,

    x="LOYALTY_STATUS",

    y="AVG_SPEND",

    text="AVG_SPEND",

    title="Average Customer Spend: Loyalty vs Non-Loyalty"

)

st.plotly_chart(

    fig,

    use_container_width=True

)
# =====================================================
# Lifetime Value Comparison
# =====================================================
st.divider()

st.header(

    "Customer Lifetime Value Comparison"

)

if "LIFETIME_VALUE" in filtered_df.columns:


    lifetime = (

        filtered_df

        .groupby(

            "LOYALTY_STATUS"

        )

        .agg(

            AVG_LTV=(

                "LIFETIME_VALUE",

                "mean"

            )

        )

        .reset_index()

    )

    fig = px.bar(

        lifetime,

        x="LOYALTY_STATUS",

        y="AVG_LTV",

        text="AVG_LTV",

        title="Average Lifetime Value by Loyalty Status"

    )

    st.plotly_chart(

        fig,

        use_container_width=True

    )
# =====================================================
# Repeat Purchase Behavior
# =====================================================
st.divider()

st.header(

    "Repeat Purchase Behavior"

)
repeat_purchase = (

    filtered_df

    .groupby(

        "LOYALTY_STATUS"

    )

    .agg(

        AVG_REPEAT_ORDERS=(

            "TOTAL_ORDERS",

            "mean"

        )

    )

    .reset_index()

)
fig = px.bar(

    repeat_purchase,

    x="LOYALTY_STATUS",

    y="AVG_REPEAT_ORDERS",

    text="AVG_REPEAT_ORDERS",

    title="Average Orders per Customer"

)
st.plotly_chart(

    fig,

    use_container_width=True

)
# =====================================================
# Revenue Contribution
# =====================================================
st.divider()

st.header(

    "Revenue Contribution by Loyalty Status"

)
revenue = (

    filtered_df

    .groupby(

        "LOYALTY_STATUS"

    )

    .agg(

        REVENUE=(

            "TOTAL_SPEND",

            "sum"

        )

    )

    .reset_index()

)
fig = px.pie(

    revenue,

    names="LOYALTY_STATUS",

    values="REVENUE",

    title="Revenue Share: Loyalty vs Non-Loyalty"

)
st.plotly_chart(

    fig,

    use_container_width=True

)
# =====================================================
# Customer Detail Table
# =====================================================
st.divider()

st.header(

    "Customer Loyalty Details"

)
st.dataframe(

    filtered_df.sort_values(

        "TOTAL_SPEND",

        ascending=False

    ),

    use_container_width=True

)