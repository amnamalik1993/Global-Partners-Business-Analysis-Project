import sys

from pyspark.context import SparkContext

from pyspark.sql.functions import (
    col,
    max,
    min,
    sum,
    avg,
    lag,
    datediff,
    when,
    coalesce,
    lit,
    countDistinct,
    months_between
)

from pyspark.sql.window import Window

from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.utils import getResolvedOptions

# =====================================================
# Initialize Glue Job
# =====================================================
args = getResolvedOptions(
    sys.argv,
    ["JOB_NAME"]
)

sc = SparkContext()

glueContext = GlueContext(sc)

spark = glueContext.spark_session


job = Job(glueContext)

job.init(
    args["JOB_NAME"],
    args
)
# =====================================================
# S3 Paths
# =====================================================
SILVER_BUCKET = "s3://orders-target-data-bucket/silver"

GOLD_BUCKET = "s3://orders-target-data-bucket/gold"

# =====================================================
# Read Silver Order Items
# =====================================================

order_items = spark.read.parquet(
    f"{SILVER_BUCKET}/order_items/"
)

# =====================================================
# Create Customer ID
# USER_ID preferred
# PRINTED_CARD_NUMBER fallback
# =====================================================
order_items = (

    order_items

    .withColumn(
        "CUSTOMER_ID",
        coalesce(
            col("USER_ID"),
            col("PRINTED_CARD_NUMBER")
        )
    )

    .filter(
        col("CUSTOMER_ID").isNotNull()
    )
)
# =====================================================
# Calculate Revenue
# =====================================================
order_items = (

    order_items

    .withColumn(
        "ORDER_REVENUE",
        col("ITEM_PRICE") *
        col("ITEM_QUANTITY")
    )
)
# =====================================================
# Find Dataset Reference Date
# =====================================================
reference_date = (

    order_items

    .select(
        max(
            "CREATION_TIME_UTC"
        )
        .alias(
            "MAX_DATE"
        )
    )

    .collect()[0]["MAX_DATE"]

)

print(
    f"Reference Date: {reference_date}"
)
# =====================================================
# Calculate Last Order Date
# =====================================================
customer_last_order = (

    order_items

    .groupBy(
        "CUSTOMER_ID"
    )

    .agg(

        max(
            "CREATION_TIME_UTC"
        )
        .alias(
            "LAST_ORDER_DATE"
        )

    )

    .withColumn(

        "DAYS_SINCE_LAST_ORDER",

        datediff(

            lit(reference_date),

            col("LAST_ORDER_DATE")

        )
    )
)
# =====================================================
# Calculate Average Gap Between Orders
# =====================================================
order_window = Window \
    .partitionBy(
        "CUSTOMER_ID"
    ) \
    .orderBy(
        "CREATION_TIME_UTC"
    )
order_gaps = (

    order_items

    .select(
        "CUSTOMER_ID",
        "ORDER_ID",
        "CREATION_TIME_UTC"
    )

    .withColumn(

        "PREVIOUS_ORDER_DATE",

        lag(
            "CREATION_TIME_UTC"
        )
        .over(order_window)

    )

    .withColumn(

        "ORDER_GAP_DAYS",

        datediff(

            col("CREATION_TIME_UTC"),

            col("PREVIOUS_ORDER_DATE")

        )

    )

)
average_gap = (

    order_gaps

    .groupBy(
        "CUSTOMER_ID"
    )

    .agg(

        avg(
            "ORDER_GAP_DAYS"
        )
        .alias(
            "AVG_ORDER_GAP_DAYS"
        )

    )
)
# =====================================================
# Spend Change Calculation
#
# Recent 90 days vs Previous 90 days
# =====================================================
recent_period_start = reference_date.replace(
    day=1
)

spend_periods = (

    order_items

    .withColumn(

        "DAYS_FROM_REFERENCE",

        datediff(

            lit(reference_date),

            col("CREATION_TIME_UTC")

        )

    )

    .withColumn(

        "SPEND_PERIOD",

        when(

            col("DAYS_FROM_REFERENCE") <= 90,

            "RECENT"

        )

        .when(

            col("DAYS_FROM_REFERENCE") <= 180,

            "PREVIOUS"

        )

    )

    .filter(
        col("SPEND_PERIOD").isNotNull()
    )

)
spend_change = (

    spend_periods

    .groupBy(
        "CUSTOMER_ID"
    )

    .pivot(
        "SPEND_PERIOD"
    )

    .agg(
        sum("ORDER_REVENUE")
    )

    .fillna(0)

)
spend_change = (

    spend_change

    .withColumnRenamed(
        "RECENT",
        "RECENT_SPEND"
    )

    .withColumnRenamed(
        "PREVIOUS",
        "PREVIOUS_SPEND"
    )

    .withColumn(

        "SPEND_CHANGE_PERCENT",

        when(

            col("PREVIOUS_SPEND") > 0,

            (

                (
                    col("RECENT_SPEND")
                    -
                    col("PREVIOUS_SPEND")
                )
                /
                col("PREVIOUS_SPEND")

            )
            *
            100

        )
        .otherwise(
            0
        )

    )

)
# =====================================================
# Combine Customer Churn Metrics
# =====================================================
customer_churn = (

    customer_last_order

    .join(

        average_gap,

        "CUSTOMER_ID",

        "left"

    )

    .join(

        spend_change,

        "CUSTOMER_ID",

        "left"

    )

)
# =====================================================
# Assign Churn Status
# =====================================================
customer_churn = (

    customer_churn

    .withColumn(

        "CHURN_STATUS",

        when(

            col("DAYS_SINCE_LAST_ORDER") > 90,

            "High Risk"

        )

        .when(

            col("DAYS_SINCE_LAST_ORDER") > 45,

            "At Risk"

        )

        .otherwise(

            "Active"

        )

    )

)
# =====================================================
# Write Gold Layer
# =====================================================
customer_churn.write \
    .mode("overwrite") \
    .parquet(
        f"{GOLD_BUCKET}/customer_churn_indicators/"
    )
# =====================================================
# Commit Job
# =====================================================
job.commit()

print(
    "Customer churn indicators created successfully."
)