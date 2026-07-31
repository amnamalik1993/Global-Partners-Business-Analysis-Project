import sys

from pyspark.context import SparkContext

from pyspark.sql.functions import (
    col,
    sum,
    countDistinct,
    avg,
    datediff,
    min,
    max,
    lit,
    dense_rank
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

SILVER_BUCKET = (
    "s3://orders-target-data-bucket/silver"
)

GOLD_BUCKET = (
    "s3://orders-target-data-bucket/gold"
)
# =====================================================
# Read Silver Order Items
# =====================================================

order_items = spark.read.parquet(
    f"{SILVER_BUCKET}/order_items/"
)

# =====================================================
# Calculate Revenue
# =====================================================

location_sales = (

    order_items

    .withColumn(

        "TOTAL_REVENUE",

        col("ITEM_PRICE")
        *
        col("ITEM_QUANTITY")

    )

)
# =====================================================
# Create Sales Date
# =====================================================

location_sales = (

    location_sales

    .withColumn(

        "SALES_DATE",

        col("CREATION_TIME_UTC")

    )

)
# =====================================================
# Aggregate Location Metrics
# =====================================================

location_metrics = (

    location_sales

    .groupBy(

        "RESTAURANT_ID"

    )

    .agg(

        sum(
            "TOTAL_REVENUE"
        )
        .alias(
            "TOTAL_REVENUE"
        ),


        countDistinct(
            "ORDER_ID"
        )
        .alias(
            "TOTAL_ORDERS"
        ),


        countDistinct(
            "SALES_DATE"
        )
        .alias(
            "ACTIVE_DAYS"
        ),


        min(
            "SALES_DATE"
        )
        .alias(
            "FIRST_ORDER_DATE"
        ),


        max(
            "SALES_DATE"
        )
        .alias(
            "LAST_ORDER_DATE"
        )

    )

)
# =====================================================
# Calculate Orders Per Day / Week
# =====================================================

location_metrics = (

    location_metrics

    .withColumn(

        "ORDERS_PER_DAY",

        col("TOTAL_ORDERS")
        /
        col("ACTIVE_DAYS")

    )

    .withColumn(

        "ACTIVE_WEEKS",

        col("ACTIVE_DAYS")
        /
        lit(7)

    )

    .withColumn(

        "ORDERS_PER_WEEK",

        col("TOTAL_ORDERS")
        /
        col("ACTIVE_WEEKS")

    )

)
# =====================================================
# Calculate Average Order Value
# =====================================================

location_metrics = (

    location_metrics

    .withColumn(

        "AVG_ORDER_VALUE",

        col("TOTAL_REVENUE")
        /
        col("TOTAL_ORDERS")

    )

)
# =====================================================
# Rank Locations By Revenue
# =====================================================

rank_window = Window.orderBy(
    col("TOTAL_REVENUE").desc()
)


location_metrics = (

    location_metrics

    .withColumn(

        "REVENUE_RANK",

        dense_rank()
        .over(rank_window)

    )

)
# =====================================================
# Write Gold Layer
# =====================================================

location_metrics.write \
    .mode("overwrite") \
    .parquet(
        f"{GOLD_BUCKET}/top_performing_locations/"
    )
# =====================================================
# Commit Job
# =====================================================
job.commit()

print(
    "Top performing location metrics created successfully."
)