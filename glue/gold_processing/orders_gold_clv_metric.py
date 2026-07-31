import sys
from pyspark.context import SparkContext
from pyspark.sql.functions import (
    col,
    sum,
    when,
    coalesce,
    percent_rank
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
    args)

# =====================================================
# S3 Paths
# =====================================================

SILVER_BUCKET = "s3://orders-target-data-bucket/silver"

GOLD_BUCKET = "s3://orders-target-data-bucket/gold"

# =====================================================
# Read Silver Tables
# =====================================================

order_items = spark.read.parquet(
    f"{SILVER_BUCKET}/order_items/"
)

order_item_options = spark.read.parquet(
    f"{SILVER_BUCKET}/order_item_options/"
)

# =====================================================
# Calculate Item Revenue
# =====================================================
order_items = (

    order_items

    .withColumn(
        "ITEM_REVENUE",
        col("ITEM_PRICE") *
        col("ITEM_QUANTITY")
    )
)
# =====================================================
# Calculate Option Revenue
# =====================================================
option_revenue = (

    order_item_options

    .withColumn(
        "OPTION_REVENUE",
        col("OPTION_PRICE") *
        col("OPTION_QUANTITY")
    )

    .groupBy(
        "ORDER_ID",
        "LINEITEM_ID"
    )

    .agg(
        sum("OPTION_REVENUE")
        .alias("OPTION_REVENUE")
    )

)
# =====================================================
# Join Item Revenue + Option Revenue
# =====================================================
order_revenue = (

    order_items

    .join(
        option_revenue,
        ["ORDER_ID", "LINEITEM_ID"],
        "left"
    )

    .fillna(
        {
            "OPTION_REVENUE": 0
        }
    )

    .withColumn(
        "TOTAL_LINE_REVENUE",
        col("ITEM_REVENUE") +
        col("OPTION_REVENUE")
    )

)

# =====================================================
# Create Unified Customer ID
# =====================================================
order_revenue = (

    order_revenue

    .withColumn(
        "CUSTOMER_ID",
        coalesce(
            col("USER_ID"),
            col("PRINTED_CARD_NUMBER")
        )
    )

)

# =====================================================
# Calculate Customer Lifetime Value
# =====================================================

clv = (

    order_revenue

    .filter(
        col("CUSTOMER_ID").isNotNull()
    )

    .groupBy(
        "CUSTOMER_ID"
    )

    .agg(
        sum("TOTAL_LINE_REVENUE")
        .alias("CUSTOMER_LIFETIME_VALUE")
    )

)

# =====================================================
# Rank Customers by Lifetime Value
# =====================================================

window_spec = Window.orderBy(
    col("CUSTOMER_LIFETIME_VALUE")
)

clv = (

    clv

    .withColumn(
        "PERCENT_RANK",
        percent_rank().over(window_spec)
    )

)

# =====================================================
# Customer Segmentation
# =====================================================
clv = (

    clv

    .withColumn(

        "CLV_SEGMENT",

        when(
            col("PERCENT_RANK") >= 0.80,
            "High CLV"
        )

        .when(
            col("PERCENT_RANK") >= 0.20,
            "Medium CLV"
        )

        .otherwise(
            "Low CLV"
        )

    )

)

# =====================================================
# Write Gold Layer
# =====================================================

clv.write \
    .mode("overwrite") \
    .parquet(
        f"{GOLD_BUCKET}/customer_lifetime_value/"
    )

# =====================================================
# Commit Job
# =====================================================

job.commit()

print(
    "Customer Lifetime Value metric created successfully."
)