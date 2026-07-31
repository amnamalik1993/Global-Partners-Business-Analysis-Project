import sys

from pyspark.context import SparkContext

from pyspark.sql.functions import (
    col,
    sum,
    countDistinct,
    when,
    coalesce
)

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
# Create Customer Identifier
#
# USER_ID preferred
# Card number fallback
# =====================================================

customer_orders = (

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

customer_orders = (

    customer_orders

    .withColumn(

        "ORDER_REVENUE",

        col("ITEM_PRICE")
        *
        col("ITEM_QUANTITY")

    )

)
# =====================================================
# Aggregate Customer Metrics
# =====================================================

loyalty_metrics = (

    customer_orders

    .groupBy(

        "CUSTOMER_ID",

        "IS_LOYALTY"

    )

    .agg(

        sum(
            "ORDER_REVENUE"
        )
        .alias(
            "TOTAL_SPEND"
        ),


        countDistinct(
            "ORDER_ID"
        )
        .alias(
            "TOTAL_ORDERS"
        )

    )

)
# =====================================================
# Calculate Average Spend
# =====================================================

loyalty_metrics = (

    loyalty_metrics

    .withColumn(

        "AVG_ORDER_VALUE",

        col("TOTAL_SPEND")
        /
        col("TOTAL_ORDERS")

    )

)
# =====================================================
# Add Loyalty Status
# =====================================================

loyalty_metrics = (

    loyalty_metrics

    .withColumn(

        "LOYALTY_STATUS",

        when(

            col("IS_LOYALTY") == True,

            "LOYALTY_MEMBER"

        )

        .otherwise(

            "NON_LOYALTY_MEMBER"

        )

    )


    .withColumn(

        "LIFETIME_VALUE",

        col("TOTAL_SPEND")

    )

)
# =====================================================
# Write Gold Layer
# =====================================================

loyalty_metrics.write \
    .mode("overwrite") \
    .parquet(
        f"{GOLD_BUCKET}/loyalty_program_impact/"
    )
# =====================================================
# Commit Job
# =====================================================
job.commit()

print(
    "Loyalty program impact metrics created successfully."
)