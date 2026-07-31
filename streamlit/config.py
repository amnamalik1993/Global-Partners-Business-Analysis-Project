import boto3

# =====================================================
# AWS Configuration
# =====================================================
AWS_REGION = "us-east-1"

S3_BUCKET = "orders-target-data-bucket"

GOLD_PREFIX = "gold"

# =====================================================
# Gold Layer Locations
# =====================================================

CUSTOMER_SEGMENTATION = (
    f"s3://{S3_BUCKET}/{GOLD_PREFIX}/customer_segmentation/"
)

CHURN_INDICATORS = (
    f"s3://{S3_BUCKET}/{GOLD_PREFIX}/customer_churn_indicators/"
)

SALES_TRENDS = (
    f"s3://{S3_BUCKET}/{GOLD_PREFIX}/sales_trends/"
)

LOYALTY_PROGRAM = (
    f"s3://{S3_BUCKET}/{GOLD_PREFIX}/loyalty_program_impact/"
)

LOCATION_PERFORMANCE = (
    f"s3://{S3_BUCKET}/{GOLD_PREFIX}/top_performing_locations/"
)

PRICING_DISCOUNT = (
    f"s3://{S3_BUCKET}/{GOLD_PREFIX}/pricing_discount_effectiveness/"
)

# =====================================================
# AWS Session
# =====================================================

session = boto3.Session(
    region_name=AWS_REGION
)

s3 = session.client("s3")