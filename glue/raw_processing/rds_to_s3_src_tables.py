import sys
import json
import boto3

from pyspark.context import SparkContext
from pyspark.sql import SparkSession

from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.utils import getResolvedOptions
# ==========================================================
# Read Glue Job Parameters
# ==========================================================
args = getResolvedOptions(
    sys.argv,
    [
        "JOB_NAME",
        "RDS_ENDPOINT",
        "DATABASE_NAME",
        "SECRET_NAME",
        "S3_RAW_PATH"
    ]
)
# ==========================================================
# Initialize Spark and Glue Context
# ==========================================================
sc = SparkContext()

glueContext = GlueContext(sc)

spark = glueContext.spark_session


job = Job(glueContext)

job.init(
    args["JOB_NAME"],
    args
)

print("Glue job started")

# ==========================================================
# Retrieve RDS Credentials From AWS Secrets Manager
# ==========================================================
secret_name = args["SECRET_NAME"]

region_name = "us-east-1"

print(
    f"Retrieving secret: {secret_name}"
)


secrets_client = boto3.client(
    "secretsmanager",
    region_name=region_name
)

secret_response = secrets_client.get_secret_value(
    SecretId=secret_name
)

secret_values = json.loads(
    secret_response["SecretString"]
)

username = secret_values["username"]

password = secret_values["password"]

print("Successfully retrieved database credentials")
# ==========================================================
# Build JDBC Connection
# ==========================================================
jdbc_url = (

    f"jdbc:sqlserver://{args['RDS_ENDPOINT']}:1433;"
    f"databaseName={args['DATABASE_NAME']}"
)

print(
    f"Connecting to database: {args['DATABASE_NAME']}"
)

connection_properties = {


    "user": username,


    "password": password,


    "driver":
    "com.microsoft.sqlserver.jdbc.SQLServerDriver"

}
# ==========================================================
# Source Tables
# ==========================================================
source_tables = [

    "dbo.order_items",

    "dbo.order_item_options",

    "dbo.date_dim"

]
# ==========================================================
# Extract Data From SQL Server
# Write To S3 Raw Layer
# ==========================================================
for table in source_tables:

    try:


        print(
            f"Starting extraction for table: {table}"
        )

        df = (

            spark.read

            .format("jdbc")

            .option(
                "url",
                jdbc_url
            )

            .option(
                "dbtable",
                table
            )

            .option(
                "user",
                connection_properties["user"]
            )

            .option(
                "password",
                connection_properties["password"]
            )

            .option(
                "driver",
                connection_properties["driver"]
            )

            .load()

        )

        record_count = df.count()

        print(
            f"{table} record count: {record_count}"
        )

        # Extract only table name
        table_name = table.split(".")[-1]

        output_path = (

            f"{args['S3_RAW_PATH']}"
            f"/{table_name}/"

        )

        print(
            f"Writing {table_name} to {output_path}"
        )

        (

            df.write

            .mode("overwrite")

            .format("parquet")

            .save(output_path)

        )

        print(
            f"{table_name} successfully loaded"
        )


    except Exception as e:

        print(
            f"Error processing table {table}"
        )


        print(str(e))


        raise e
# ==========================================================
# Complete Job
# ==========================================================
job.commit()

print(
    "Glue job completed successfully"
)