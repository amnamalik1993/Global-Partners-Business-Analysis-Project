import sys

from pyspark.context import SparkContext

from pyspark.sql.functions import (
    col,
    sum,
    max,
    countDistinct,
    when,
    coalesce,
    datediff,
    lit,
    percent_rank,
    concat
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

print("Reading silver order_items")


order_items = spark.read.parquet(
    f"{SILVER_BUCKET}/order_items/"
)



# =====================================================
# Create Customer Identifier
#
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
        "LINE_REVENUE",
        col("ITEM_PRICE") *
        col("ITEM_QUANTITY")
    )

)



# =====================================================
# Reference Date
#
# Important:
# Dataset is historical 2023 data
# Do not use current date
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
    f"RFM Reference Date: {reference_date}"
)



# =====================================================
# Calculate Customer RFM Metrics
# =====================================================


customer_rfm = (

    order_items

    .groupBy(
        "CUSTOMER_ID"
    )

    .agg(

        max(
            "CREATION_TIME_UTC"
        )
        .alias(
            "LAST_PURCHASE_DATE"
        ),


        countDistinct(
            "ORDER_ID"
        )
        .alias(
            "FREQUENCY"
        ),


        sum(
            "LINE_REVENUE"
        )
        .alias(
            "MONETARY"
        ),


        max(
            "IS_LOYALTY"
        )
        .alias(
            "IS_LOYALTY"
        )

    )


    .withColumn(

        "RECENCY",

        datediff(

            lit(reference_date),

            col("LAST_PURCHASE_DATE")

        )

    )

)



# =====================================================
# Create RFM Scores
# =====================================================


recency_window = Window.orderBy(
    col("RECENCY")
)


frequency_window = Window.orderBy(
    col("FREQUENCY")
)


monetary_window = Window.orderBy(
    col("MONETARY")
)



customer_rfm = (

    customer_rfm


    # -------------------------
    # Recency Score
    # Lower days = better
    # -------------------------

    .withColumn(

        "R_SCORE",

        when(
            percent_rank()
            .over(recency_window) <= 0.20,
            5
        )

        .when(
            percent_rank()
            .over(recency_window) <= 0.40,
            4
        )

        .when(
            percent_rank()
            .over(recency_window) <= 0.60,
            3
        )

        .when(
            percent_rank()
            .over(recency_window) <= 0.80,
            2
        )

        .otherwise(
            1
        )

    )


    # -------------------------
    # Frequency Score
    # Higher orders = better
    # -------------------------

    .withColumn(

        "F_SCORE",

        when(
            percent_rank()
            .over(frequency_window) >= 0.80,
            5
        )

        .when(
            percent_rank()
            .over(frequency_window) >= 0.60,
            4
        )

        .when(
            percent_rank()
            .over(frequency_window) >= 0.40,
            3
        )

        .when(
            percent_rank()
            .over(frequency_window) >= 0.20,
            2
        )

        .otherwise(
            1
        )

    )


    # -------------------------
    # Monetary Score
    # Higher spend = better
    # -------------------------

    .withColumn(

        "M_SCORE",

        when(
            percent_rank()
            .over(monetary_window) >= 0.80,
            5
        )

        .when(
            percent_rank()
            .over(monetary_window) >= 0.60,
            4
        )

        .when(
            percent_rank()
            .over(monetary_window) >= 0.40,
            3
        )

        .when(
            percent_rank()
            .over(monetary_window) >= 0.20,
            2
        )

        .otherwise(
            1
        )

    )

)



# =====================================================
# Create Combined RFM Score
# =====================================================

customer_rfm = (

    customer_rfm

    .withColumn(
        "RFM_SCORE",
        concat(
            col("R_SCORE"),
            col("F_SCORE"),
            col("M_SCORE")
        )
    )

)



# =====================================================
# Customer Segmentation Rules
# =====================================================


customer_rfm = (

    customer_rfm

    .withColumn(

        "CUSTOMER_SEGMENT",


        when(

            (col("R_SCORE") >= 4) &

            (col("F_SCORE") >= 4) &

            (col("M_SCORE") >= 4),

            "VIP"

        )


        .when(

            (col("R_SCORE") >= 4) &

            (col("F_SCORE") <= 2),

            "New Customer"

        )


        .when(

            (col("R_SCORE") <= 2) &

            (col("F_SCORE") <= 2),

            "Churn Risk"

        )


        .otherwise(

            "Regular Customer"

        )

    )

)



# =====================================================
# Final Gold Dataset
# =====================================================


customer_segmentation = (

    customer_rfm

    .select(

        "CUSTOMER_ID",

        "LAST_PURCHASE_DATE",

        "RECENCY",

        "FREQUENCY",

        "MONETARY",

        "R_SCORE",

        "F_SCORE",

        "M_SCORE",

        "RFM_SCORE",

        "CUSTOMER_SEGMENT",

        "IS_LOYALTY"

    )

)



# =====================================================
# Write Gold Layer
# =====================================================


print("Writing customer segmentation Gold layer")


customer_segmentation.write \
    .mode("overwrite") \
    .parquet(
        f"{GOLD_BUCKET}/customer_segmentation/"
    )



# =====================================================
# Commit Job
# =====================================================

job.commit()


print(
    "Customer segmentation RFM Gold metric created successfully."
)