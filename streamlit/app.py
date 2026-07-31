import streamlit as st

from utils import (
    load_customer_segmentation,
    load_churn_indicators,
    load_sales_trends,
    load_loyalty_program,
    load_location_performance,
    load_pricing_discount,
    currency,
    integer
)
# =====================================================
# Page Configuration
# =====================================================
st.set_page_config(

    page_title="Restaurant Analytics Dashboard",

    page_icon="🍽️",

    layout="wide"

)
# =====================================================
# Dashboard Title
# =====================================================
st.title(
    "🍽️ Restaurant Customer & Sales Analytics Dashboard"
)

st.markdown(
    """
    This dashboard provides business insights across:

    - Customer Segmentation
    - Churn Risk Indicators
    - Sales Trends & Seasonality
    - Loyalty Program Performance
    - Restaurant Location Performance
    - Pricing & Discount Effectiveness

    Data Source:
    AWS S3 Gold Layer
    """
)
# =====================================================
# Load Gold Data
# =====================================================
with st.spinner(
    "Loading Gold layer metrics..."
):

    customer_df = load_customer_segmentation()

    churn_df = load_churn_indicators()

    sales_df = load_sales_trends()

    loyalty_df = load_loyalty_program()

    location_df = load_location_performance()

    pricing_df = load_pricing_discount()
# =====================================================
# Validate Data Availability
# =====================================================
datasets = {

    "Customer Segmentation": customer_df,

    "Churn Indicators": churn_df,

    "Sales Trends": sales_df,

    "Loyalty Program": loyalty_df,

    "Location Performance": location_df,

    "Pricing Discounts": pricing_df

}


missing = []


for name, df in datasets.items():

    if df.empty:

        missing.append(name)


if missing:

    st.warning(

        f"""
        The following Gold datasets could not be loaded:

        {', '.join(missing)}

        Verify:
        - S3 path
        - IAM permissions
        - Glue Gold jobs
        """

    )
# =====================================================
# Executive Summary KPIs
# =====================================================
st.header(
    "Executive Summary"
)



col1, col2, col3, col4 = st.columns(4)
# -----------------------------------------------------
# Total Customers
# -----------------------------------------------------
with col1:

    if not customer_df.empty:

        customers = (
            customer_df["CUSTOMER_ID"]
            .nunique()
        )

        st.metric(

            "Total Customers",

            integer(customers)

        )

    else:

        st.metric(
            "Total Customers",
            "N/A"
        )
# -----------------------------------------------------
# Total Revenue
# -----------------------------------------------------
with col2:

    if not sales_df.empty:

        revenue = (

            sales_df["TOTAL_REVENUE"]
            .sum()

        )

        st.metric(

            "Total Revenue",

            currency(revenue)

        )

    else:

        st.metric(
            "Total Revenue",
            "N/A"
        )
# -----------------------------------------------------
# Total Orders
# -----------------------------------------------------
with col3:

    if not sales_df.empty:

        orders = (

            sales_df["TOTAL_ORDERS"]
            .sum()

        )

        st.metric(

            "Total Orders",

            integer(orders)

        )

    else:

        st.metric(
            "Total Orders",
            "N/A"
        )
# -----------------------------------------------------
# At Risk Customers
# -----------------------------------------------------
with col4:

    if not churn_df.empty:


        if "CHURN_STATUS" in churn_df.columns:

            risk = (

                churn_df

                [
                    churn_df["CHURN_STATUS"]
                    ==
                    "AT_RISK"
                ]

                .shape[0]

            )

        else:

            risk = 0


        st.metric(

            "Customers At Risk",

            integer(risk)

        )


    else:

        st.metric(

            "Customers At Risk",

            "N/A"

        )
# =====================================================
# Quick Business Insights
# =====================================================
st.divider()

st.header(
    "Business Questions Answered"
)

insight_col1, insight_col2 = st.columns(2)

with insight_col1:

    st.markdown(

        """
        ### Customer Analytics

        ✓ Which customers are high-value?

        ✓ Which customers are likely to churn?

        ✓ How does loyalty membership impact behavior?

        """

    )

with insight_col2:

    st.markdown(

        """
        ### Operational Analytics

        ✓ Which restaurants perform best?

        ✓ What are peak sales periods?

        ✓ Are discounts increasing revenue?

        """

    )
# =====================================================
# Dashboard Navigation
# =====================================================
st.divider()

st.info(

    """
    Use the navigation menu on the left side of Streamlit
    to open individual dashboards:

    1. Customer Segmentation
    2. Churn Risk Indicators
    3. Sales Trends & Seasonality
    4. Loyalty Program Impact
    5. Location Performance
    6. Pricing & Discount Effectiveness
    """

)