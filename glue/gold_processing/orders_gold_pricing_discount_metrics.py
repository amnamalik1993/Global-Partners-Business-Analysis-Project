import sys

from pyspark.context import SparkContext

from pyspark.sql.functions import (
    col,
    sum,
    countDistinct,
    when,
    lit,
    round
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
# Read Silver Tables
# =====================================================

print("Reading Silver tables")


order_items = spark.read.parquet(
    f"{SILVER_BUCKET}/order_items/"
)


order_item_options = spark.read.parquet(
    f"{SILVER_BUCKET}/order_item_options/"
)



# =====================================================
# Calculate Order Item Revenue
# =====================================================

order_revenue = (

    order_items

    .withColumn(

        "GROSS_REVENUE",

        col("ITEM_PRICE")
        *
        col("ITEM_QUANTITY")

    )

    .select(

        "ORDER_ID",

        "GROSS_REVENUE"

    )

)



# =====================================================
# Aggregate Discounts By Order
#
# OPTION_PRICE < 0 = discount
# =====================================================

order_discounts = (

    order_item_options

    .filter(

        col("OPTION_PRICE") < 0

    )

    .groupBy(

        "ORDER_ID"

    )

    .agg(

        round(

            sum(

                col("OPTION_PRICE") * -1

            ),

            2

        )

        .alias(

            "DISCOUNT_AMOUNT"

        )

    )

)



# =====================================================
# Aggregate Revenue By Order
#
# Prevent duplicate order revenue
# =====================================================

order_level_revenue = (

    order_revenue

    .groupBy(

        "ORDER_ID"

    )

    .agg(

        round(

            sum(

                "GROSS_REVENUE"

            ),

            2

        )

        .alias(

            "GROSS_REVENUE"

        )

    )

)



# =====================================================
# Combine Revenue and Discounts
# =====================================================

pricing_orders = (

    order_level_revenue

    .join(

        order_discounts,

        "ORDER_ID",

        "left"

    )


    .withColumn(

        "DISCOUNT_AMOUNT",

        when(

            col("DISCOUNT_AMOUNT").isNull(),

            0

        )

        .otherwise(

            col("DISCOUNT_AMOUNT")

        )

    )


    .withColumn(

        "DISCOUNT_STATUS",

        when(

            col("DISCOUNT_AMOUNT") > 0,

            "DISCOUNTED_ORDER"

        )

        .otherwise(

            "NON_DISCOUNTED_ORDER"

        )

    )


    .withColumn(

        "NET_REVENUE",

        round(

            col("GROSS_REVENUE")
            -
            col("DISCOUNT_AMOUNT"),

            2

        )

    )

)



# =====================================================
# Calculate Metrics
# =====================================================

pricing_metrics = (

    pricing_orders

    .groupBy(

        "DISCOUNT_STATUS"

    )

    .agg(

        countDistinct(

            "ORDER_ID"

        )

        .alias(

            "TOTAL_ORDERS"

        ),


        round(

            sum(

                "GROSS_REVENUE"

            ),

            2

        )

        .alias(

            "GROSS_REVENUE"

        ),


        round(

            sum(

                "DISCOUNT_AMOUNT"

            ),

            2

        )

        .alias(

            "DISCOUNT_AMOUNT"

        ),


        round(

            sum(

                "NET_REVENUE"

            ),

            2

        )

        .alias(

            "NET_REVENUE"

        )

    )

)



# =====================================================
# Average Order Value
# =====================================================

pricing_metrics = (

    pricing_metrics

    .withColumn(

        "AVG_ORDER_VALUE",

        round(

            col("NET_REVENUE")
            /
            col("TOTAL_ORDERS"),

            2

        )

    )

)



# =====================================================
# Overall Revenue Impact
# =====================================================

total_revenue = (

    pricing_metrics

    .agg(

        sum(

            "NET_REVENUE"

        )

        .alias(

            "TOTAL_NET_REVENUE"

        )

    )

    .collect()[0]["TOTAL_NET_REVENUE"]

)



pricing_metrics = (

    pricing_metrics

    .withColumn(

        "REVENUE_PERCENTAGE",

        round(

            (

                col("NET_REVENUE")
                /
                lit(total_revenue)

            )

            *
            100,

            2

        )

    )

)



# =====================================================
# Final Gold Dataset
# =====================================================

pricing_metrics = (

    pricing_metrics

    .select(

        "DISCOUNT_STATUS",

        "TOTAL_ORDERS",

        "GROSS_REVENUE",

        "DISCOUNT_AMOUNT",

        "NET_REVENUE",

        "AVG_ORDER_VALUE",

        "REVENUE_PERCENTAGE"

    )

)



# =====================================================
# Write Gold Layer
# =====================================================

pricing_metrics.write \
    .mode("overwrite") \
    .parquet(

        f"{GOLD_BUCKET}/pricing_discount_effectiveness/"

    )



# =====================================================
# Commit Job
# =====================================================

job.commit()


print(
    "Pricing and discount effectiveness metrics created successfully."
)