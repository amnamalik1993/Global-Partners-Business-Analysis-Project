import sys

from pyspark.context import SparkContext

from pyspark.sql.functions import (
    col,
    sum,
    countDistinct,
    to_date,
    year,
    month,
    weekofyear,
    hour,
    when,
    lit
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
# Calculate Item Revenue
# =====================================================

sales_data = (

    order_items

    .withColumn(
        "TOTAL_REVENUE",
        col("ITEM_PRICE") *
        col("ITEM_QUANTITY")
    )

)


# =====================================================
# Create Date Attributes
# =====================================================

sales_data = (

    sales_data

    .withColumn(
        "SALES_DATE",
        to_date(
            col("CREATION_TIME_UTC")
        )
    )

    .withColumn(
        "YEAR",
        year(
            col("CREATION_TIME_UTC")
        )
    )

    .withColumn(
        "MONTH",
        month(
            col("CREATION_TIME_UTC")
        )
    )

    .withColumn(
        "WEEK",
        weekofyear(
            col("CREATION_TIME_UTC")
        )
    )

)


# =====================================================
# Create Time of Day Bucket
# =====================================================

sales_data = (

    sales_data

    .withColumn(
        "ORDER_HOUR",
        hour(
            col("CREATION_TIME_UTC")
        )
    )

    .withColumn(

        "TIME_OF_DAY",

        when(
            col("ORDER_HOUR") < 6,
            "Late Night"
        )

        .when(
            col("ORDER_HOUR") < 12,
            "Morning"
        )

        .when(
            col("ORDER_HOUR") < 17,
            "Afternoon"
        )

        .when(
            col("ORDER_HOUR") < 21,
            "Evening"
        )

        .otherwise(
            "Night"
        )

    )

)


# =====================================================
# Function to Create Sales Summary
# =====================================================

def create_sales_summary(
    dataframe,
    group_columns,
    period_name
):

    return (

        dataframe

        .groupBy(
            *group_columns
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

            sum(
                "ITEM_QUANTITY"
            )
            .alias(
                "ITEMS_SOLD"
            )

        )

        .withColumn(
            "SALES_PERIOD",
            lit(period_name)
        )

    )


# =====================================================
# Daily Sales
# =====================================================

daily_sales = create_sales_summary(

    sales_data,

    [
        "SALES_DATE",
        "RESTAURANT_ID",
        "ITEM_CATEGORY",
        "TIME_OF_DAY"
    ],

    "DAILY"

)


# =====================================================
# Weekly Sales
# =====================================================

weekly_sales = create_sales_summary(

    sales_data,

    [
        "YEAR",
        "WEEK",
        "RESTAURANT_ID",
        "ITEM_CATEGORY",
        "TIME_OF_DAY"
    ],

    "WEEKLY"

)


# =====================================================
# Monthly Sales
# =====================================================

monthly_sales = create_sales_summary(

    sales_data,

    [
        "YEAR",
        "MONTH",
        "RESTAURANT_ID",
        "ITEM_CATEGORY",
        "TIME_OF_DAY"
    ],

    "MONTHLY"

)


# =====================================================
# Combine Sales Summaries
# =====================================================

sales_trends = (

    daily_sales

    .unionByName(
        weekly_sales,
        allowMissingColumns=True
    )

    .unionByName(
        monthly_sales,
        allowMissingColumns=True
    )

)


# =====================================================
# Calculate Average Order Value
# =====================================================

sales_trends = (

    sales_trends

    .withColumn(

        "AVG_ORDER_VALUE",

        col("TOTAL_REVENUE")
        /
        col("TOTAL_ORDERS")

    )

)


# =====================================================
# Write Gold Layer
# =====================================================

sales_trends.write \
    .mode("overwrite") \
    .parquet(
        f"{GOLD_BUCKET}/sales_trends/"
    )


# =====================================================
# Commit Job
# =====================================================

job.commit()


print(
    "Sales trends metrics created successfully."
)