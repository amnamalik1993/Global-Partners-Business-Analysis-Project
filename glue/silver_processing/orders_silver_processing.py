import sys

from pyspark.context import SparkContext
from pyspark.sql.functions import (
    col,
    trim,
    when,
    to_timestamp,
    to_date
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

BRONZE_BUCKET = "s3://orders-target-data-bucket/bronze"

SILVER_BUCKET = "s3://orders-target-data-bucket/silver"

# =====================================================
# 1. ORDER ITEMS TRANSFORMATION
# =====================================================

print("Processing order_items")

# =====================================================
# 1. ORDER ITEMS TRANSFORMATION
# =====================================================

print("Processing order_items")


order_items = spark.read \
    .option("header", True) \
    .option("inferSchema", True) \
    .parquet(
        f"{BRONZE_BUCKET}/order_items/"
    )


# Check source columns
print("Order Items Columns:")
print(order_items.columns)


order_items_clean = (

    order_items

    # Remove duplicate line items

    .dropDuplicates(
        ["LINEITEM_ID"]
    )

    # Standardize text columns

    .withColumn(
        "APP_NAME",
        trim(
            col("APP_NAME")
        )
    )

    .withColumn(
        "RESTAURANT_ID",
        trim(
            col("RESTAURANT_ID")
        )
    )

    .withColumn(
        "CURRENCY",
        trim(
            col("CURRENCY")
        )
    )

    .withColumn(
        "ITEM_CATEGORY",
        trim(
            col("ITEM_CATEGORY")
        )
    )

    .withColumn(
        "ITEM_NAME",
        trim(
            col("ITEM_NAME")
        )
    )

    # Timestamp conversion

    .withColumn(
        "CREATION_TIME_UTC",
        to_timestamp(
            col("CREATION_TIME_UTC")
        )
    )

    # Numeric conversions

    .withColumn(
        "ITEM_PRICE",
        col("ITEM_PRICE")
        .cast("decimal(10,2)")
    )

    .withColumn(
        "ITEM_QUANTITY",
        col("ITEM_QUANTITY")
        .cast("integer")
    )

    # Loyalty flag cleanup

    .withColumn(
        "IS_LOYALTY",
        when(
        col("IS_LOYALTY").cast("integer") == 1,
        True
    )
    .otherwise(False)
    )   

    # User ID quality flag

    .withColumn(
        "USER_ID_STATUS",
        when(
            (col("USER_ID").isNull()) |
            (trim(col("USER_ID")) == ""),
            "MISSING_USER_ID"
        )
        .otherwise(
            "VALID_USER_ID"
        )
    )

    # Clean printed card number

    .withColumn(
        "PRINTED_CARD_NUMBER",
        trim(
            col("PRINTED_CARD_NUMBER")
        )
    )

    # Card number quality flag

    .withColumn(
        "CARD_NUMBER_STATUS",
        when(
            (col("PRINTED_CARD_NUMBER").isNull()) |
            (col("PRINTED_CARD_NUMBER") == ""),
            "MISSING_CARD_NUMBER"
        )
        .otherwise(
            "VALID_CARD_NUMBER"
        )
    )

    # Remove invalid transactions

    .filter(
        (col("ITEM_QUANTITY").isNotNull()) &
        (col("ITEM_QUANTITY") > 0)
    )

)

# Write Silver

order_items_clean.write \
    .mode("overwrite") \
    .parquet(
        f"{SILVER_BUCKET}/order_items/"
    )
# =====================================================
# 2. ORDER ITEM OPTIONS TRANSFORMATION
# =====================================================
print("Processing order_item_options")

options = spark.read \
    .option("header", True) \
    .option("inferSchema", True) \
    .parquet(
        f"{BRONZE_BUCKET}/order_item_options/"
    )
# =====================================================
# Standardize option fields BEFORE duplicate checking
# =====================================================
options_standardized = (

    options

    .withColumn(
        "OPTION_NAME",
        trim(
            col("OPTION_NAME")
        )
    )

    .withColumn(
        "OPTION_GROUP_NAME",
        trim(
            col("OPTION_GROUP_NAME")
        )
    )

    .withColumn(
        "OPTION_PRICE",
        col("OPTION_PRICE")
        .cast("decimal(10,2)")
    )

    .withColumn(
        "OPTION_QUANTITY",
        col("OPTION_QUANTITY")
        .cast("integer")
    )

)

duplicate_columns = [

    "ORDER_ID",
    "LINEITEM_ID",
    "OPTION_GROUP_NAME",
    "OPTION_NAME",
    "OPTION_PRICE",
    "OPTION_QUANTITY"

]

# =====================================================
# Remove duplicate groups completely
# Keep only combinations appearing once
# =====================================================
options_clean = (

    options_standardized

    .groupBy(
        duplicate_columns
    )

    .count()

    .filter(
        col("count") == 1
    )

    .drop(
        "count"
    )

)
options_clean.write \
    .mode("overwrite") \
    .parquet(
        f"{SILVER_BUCKET}/order_item_options/"
    )
# =====================================================
# 3. DATE DIM TRANSFORMATION
# =====================================================
print("Processing date_dim")

date_dim = spark.read \
    .option("header", True) \
    .option("inferSchema", True) \
    .parquet(
        f"{BRONZE_BUCKET}/date_dim/"
    )

date_dim_clean = (

    date_dim

    .dropDuplicates(
        ["date_key"]
    )

    .withColumn(
        "date_key",
        to_date(
            col("date_key")
        )
    )

    .withColumn(
        "year",
        col("year")
        .cast("integer")
    )

    .withColumn(
        "month",
        col("month")
        .cast("integer")
    )

    .withColumn(
        "week",
        col("week")
        .cast("integer")
    )

    .withColumn(
        "day_of_week",
        trim(
        col("day_of_week")
        )
    )

    .withColumn(
        "is_weekend",
        col("is_weekend")
        .cast("boolean")
    )

    .withColumn(
        "is_holiday",
        col("is_holiday")
        .cast("boolean")
    )
    
    .withColumn(
    "holiday_name",
    trim(
        col("holiday_name")
    )
  )

)

date_dim_clean.write \
    .mode("overwrite") \
    .parquet(
        f"{SILVER_BUCKET}/date_dim/"
    )

# =====================================================
# Job Completion
# =====================================================
job.commit()

print(
    "Bronze to Silver transformation completed successfully"
)