import streamlit as st
import plotly.express as px
from utils import (
    load_churn_indicators,
    currency,
    integer
)
# =====================================================
# Page Configuration
# =====================================================

st.set_page_config(

    page_title="Churn Risk Dashboard",

    page_icon="⚠️",

    layout="wide"

)
# =====================================================
# Title
# =====================================================
st.title(
    "⚠️ Customer Churn Risk Dashboard"
)


st.markdown(

"""
Identify customers who may require retention campaigns.

Risk indicators:

- Days since last order
- Average order interval
- Spending decline
- Customer inactivity
"""

)
# =====================================================
# Load Data
# =====================================================
df = load_churn_indicators()


if df.empty:

    st.error(

        """
        Churn indicator data unavailable.

        Verify Gold path:

        gold/customer_churn_indicators/

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
# Churn Status Filter
# =====================================================
if "CHURN_STATUS" in df.columns:


    churn_values = sorted(

        df["CHURN_STATUS"]

        .dropna()

        .unique()

        .tolist()

    )


    selected_status = st.sidebar.multiselect(

        "Customer Risk Status",

        churn_values,

        default=churn_values

    )


    filtered_df = filtered_df[

        filtered_df["CHURN_STATUS"]

        .isin(selected_status)

    ]
# =====================================================
# KPI Section
# =====================================================
st.header(
    "Customer Risk Overview"
)

col1, col2, col3, col4 = st.columns(4)

# Total Customers

with col1:

    st.metric(

        "Customers Analyzed",

        integer(

            filtered_df["CUSTOMER_ID"]

            .nunique()

        )

    )
# At Risk Customers

with col2:


    if "CHURN_STATUS" in filtered_df.columns:


        risk_count = (

            filtered_df

            [

                filtered_df["CHURN_STATUS"]

                .str.contains(

                    "RISK",

                    case=False,

                    na=False

                )

            ]

            .shape[0]

        )


        st.metric(

            "At Risk Customers",

            integer(risk_count)

        )

# Avg Inactivity

with col3:


    if "DAYS_SINCE_LAST_ORDER" in filtered_df.columns:


        st.metric(

            "Avg Days Since Last Order",

            round(

                filtered_df

                [

                    "DAYS_SINCE_LAST_ORDER"

                ]

                .mean(),

                1

            )

        )

# Avg Spend

with col4:


    if "TOTAL_SPEND" in filtered_df.columns:


        st.metric(

            "Average Customer Spend",

            currency(

                filtered_df

                [

                    "TOTAL_SPEND"

                ]

                .mean()

            )

        )
# =====================================================
# Customer Risk Distribution
# =====================================================
st.divider()

st.header(

    "Customer Risk Distribution"

)

if "CHURN_STATUS" in filtered_df.columns:


    churn_summary = (

        filtered_df

        .groupby(

            "CHURN_STATUS"

        )

        .size()

        .reset_index(

            name="CUSTOMERS"

        )

    )

    fig = px.bar(

        churn_summary,

        x="CHURN_STATUS",

        y="CUSTOMERS",

        text="CUSTOMERS",

        title="Customers by Risk Category"

    )

    st.plotly_chart(

        fig,

        use_container_width=True

    )
# =====================================================
# Days Since Last Order Analysis
# =====================================================
if "DAYS_SINCE_LAST_ORDER" in filtered_df.columns:


    st.divider()


    st.header(

        "Customer Inactivity Analysis"

    )


    fig = px.histogram(

        filtered_df,

        x="DAYS_SINCE_LAST_ORDER",

        nbins=40,

        title="Distribution of Days Since Last Purchase"

    )


    st.plotly_chart(

        fig,

        use_container_width=True

    )
# =====================================================
# Average Order Gap
# =====================================================
if "AVG_ORDER_GAP_DAYS" in filtered_df.columns:


    st.divider()


    st.header(

        "Purchase Frequency Gap"

    )


    fig = px.box(

        filtered_df,

        x="CHURN_STATUS",

        y="AVG_ORDER_GAP_DAYS",

        title="Average Days Between Orders by Risk Status"

    )


    st.plotly_chart(

        fig,

        use_container_width=True

    )
# =====================================================
# Spend Trend Impact
# =====================================================
if "SPEND_CHANGE_PERCENT" in filtered_df.columns:


    st.divider()


    st.header(

        "Spend Change Indicator"

    )


    fig = px.scatter(

        filtered_df,

        x="DAYS_SINCE_LAST_ORDER",

        y="SPEND_CHANGE_PERCENT",

        color="CHURN_STATUS",

        hover_name="CUSTOMER_ID",

        title=

        "Inactivity vs Spending Change"

    )

    st.plotly_chart(

        fig,

        use_container_width=True

    )
# =====================================================
# Customers Requiring Action
# =====================================================
st.divider()

st.header(

    "Customers Requiring Retention Actions"

)
risk_customers = (

    filtered_df

    .sort_values(

        by=[

            "DAYS_SINCE_LAST_ORDER",

            "SPEND_CHANGE_PERCENT"

        ],

        ascending=[

            False,

            True

        ]

    )

    .head(50)

)
st.dataframe(

    risk_customers,

    use_container_width=True

)