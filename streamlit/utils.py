import streamlit as st
import pandas as pd
import boto3
import awswrangler as wr

from config import (
    AWS_REGION,
    CUSTOMER_SEGMENTATION,
    CHURN_INDICATORS,
    SALES_TRENDS,
    LOYALTY_PROGRAM,
    LOCATION_PERFORMANCE,
    PRICING_DISCOUNT
)
# =====================================================
# AWS Session
# =====================================================
session = boto3.Session(
    region_name=AWS_REGION
)
# =====================================================
# Generic Parquet Reader
# =====================================================
@st.cache_data(show_spinner=False)
def load_parquet(path):

    try:

        df = wr.s3.read_parquet(
            path=path,
            boto3_session=session
        )

        return df

    except Exception as e:

        st.error(
            f"Unable to read\n{path}\n\n{e}"
        )

        return pd.DataFrame()
# =====================================================
# Customer Segmentation
# =====================================================
@st.cache_data(show_spinner=False)
def load_customer_segmentation():

    return load_parquet(
        CUSTOMER_SEGMENTATION
    )
# =====================================================
# Churn Indicators
# =====================================================
@st.cache_data(show_spinner=False)
def load_churn_indicators():

    return load_parquet(
        CHURN_INDICATORS
    )
# =====================================================
# Sales Trends
# =====================================================
@st.cache_data(show_spinner=False)
def load_sales_trends():

    df = load_parquet(
        SALES_TRENDS
    )

    if not df.empty:

        if "SALES_DATE" in df.columns:

            df["SALES_DATE"] = pd.to_datetime(
                df["SALES_DATE"]
            )

    return df
# =====================================================
# Loyalty Program
# =====================================================
@st.cache_data(show_spinner=False)
def load_loyalty_program():

    return load_parquet(
        LOYALTY_PROGRAM
    )
# =====================================================
# Location Performance
# =====================================================
@st.cache_data(show_spinner=False)
def load_location_performance():

    return load_parquet(
        LOCATION_PERFORMANCE
    )
# =====================================================
# Pricing & Discount
# =====================================================
@st.cache_data(show_spinner=False)
def load_pricing_discount():

    return load_parquet(
        PRICING_DISCOUNT
    )
# =====================================================
# Sidebar Filter
# =====================================================
def create_restaurant_filter(df):

    if "RESTAURANT_ID" not in df.columns:

        return df

    restaurants = sorted(
        df["RESTAURANT_ID"]
        .dropna()
        .unique()
        .tolist()
    )

    selected = st.sidebar.multiselect(

        "Restaurant",

        restaurants,

        default=restaurants

    )

    return df[
        df["RESTAURANT_ID"]
        .isin(selected)
    ]
# =====================================================
# Date Filter
# =====================================================
def create_date_filter(df):

    if "SALES_DATE" not in df.columns:

        return df

    min_date = df["SALES_DATE"].min()

    max_date = df["SALES_DATE"].max()

    start_date, end_date = st.sidebar.date_input(

        "Date Range",

        value=(
            min_date,
            max_date
        )

    )

    return df[

        (df["SALES_DATE"] >= pd.to_datetime(start_date))
        &
        (df["SALES_DATE"] <= pd.to_datetime(end_date))

    ]
# =====================================================
# KPI Card
# =====================================================
def kpi(
    label,
    value,
    delta=None
):

    st.metric(

        label=label,

        value=value,

        delta=delta

    )
# =====================================================
# Currency Formatter
# =====================================================
def currency(value):

    return "${:,.2f}".format(value)
# =====================================================
# Percentage Formatter
# =====================================================
def percent(value):

    return "{:.2f}%".format(value)
# =====================================================
# Number Formatter
# =====================================================
def integer(value):

    return "{:,.0f}".format(value)