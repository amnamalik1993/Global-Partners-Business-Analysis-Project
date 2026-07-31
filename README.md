# Global Partners Business Analysis Project

# 🍽️ Restaurant Customer Analytics Data Pipeline

## 📌 Project Overview

This project implements an end-to-end AWS data engineering pipeline that extracts restaurant transactional data from an Amazon RDS SQL Server database, transforms it using AWS Glue, stores it in a Medallion Architecture (Bronze, Silver, Gold) on Amazon S3, and visualizes business insights through an interactive Streamlit dashboard.

The primary objective is to create a unified analytics platform that provides actionable insights into customer behavior, spending patterns, restaurant performance, loyalty programs, and customer lifetime value (CLV).

---

# Business Objective

The restaurant organization requires a centralized analytics solution capable of:

- Calculating Customer Lifetime Value (CLV) on a daily basis
- Segmenting customers using RFM (Recency, Frequency, Monetary) analysis
- Identifying customers at risk of churn
- Monitoring sales trends and seasonal patterns
- Comparing loyalty members with non-loyalty members
- Identifying top and lowest performing restaurant locations
- Measuring the effectiveness of discounts and promotional campaigns
- Delivering business insights through an interactive dashboard for marketing and operational decision-making

---

Data Architecture Pipeline 
<img width="1693" height="929" alt="ChatGPT Image Jul 29, 2026, 12_02_38 PM" src="https://github.com/user-attachments/assets/7d446c38-e15b-48db-9a44-c697a1fd099e" />

---

# Technology Stack

| Service | Purpose |
|----------|----------|
| Amazon RDS (SQL Server) | Source transactional database |
| SQL Server Management Studio (SSMS) | Database management |
| AWS Glue | ETL processing |
| PySpark | Data transformations |
| Amazon S3 | Data Lake |
| AWS Secrets Manager | Secure credential management |
| AWS IAM | Access management |
| AWS VPC | Secure networking |
| AWS EventBridge | Pipeline scheduling |
| Streamlit | Interactive dashboard |
| GitHub | Version control |

---

# Source Data

The source system consists of three transactional tables stored in SQL Server.

## order_items

Contains order-level transaction information.


## order_item_options

Contains optional add-ons associated with each ordered item.


## date_dim

Calendar dimension used for time-based analytics.

# Data Pipeline

## Step 1 – Data Extraction

AWS Glue Job #1 extracts the SQL Server tables using a JDBC connection.

### Source

Amazon RDS SQL Server

### Tables

- order_items
- order_item_options
- date_dim

### Output

Amazon S3 Source Bucket

```
raw/

├── order_items/

├── order_item_options/

└── date_dim/
```

---

## Step 2 – Data Processing

AWS Glue Job #2 performs ETL transformations.

### Data Cleaning

- Remove duplicate records
- Handle missing values
- Standardize column names
- Convert data types
- Remove invalid transactions
- Validate business rules

### Data Integration

- Join transactional tables
- Join Date Dimension
- Generate analytical datasets

### Feature Engineering


# Medallion Architecture

The project follows the Bronze → Silver → Gold architecture.

## Bronze Layer

Purpose:

Store standardized raw data extracted from SQL Server.

```
bronze/

order_items

order_item_options

date_dim
```

---

## Silver Layer

Purpose:

Store cleaned and integrated datasets.

Processing includes:

- Data cleansing
- Duplicate removal
- Standardization
- Data enrichment
- Table joins

---

## Gold Layer

Business-ready datasets optimized for analytics.

```
gold/

customer_lifetime_value/

customer_segmentation_rfm/

churn_indicators/

sales_trends/

loyalty_program_impact/

top_performing_locations/

pricing_discount_effectiveness/

```

---

# Business Metrics

Customer Lifetime Value (CLV)

Customer Segmentation (RFM)

Churn Indicators

Sales Trends Monitoring

Loyalty Program Impact

Top Performing Locations

Pricing & Discount Effectiveness

Dashboard Features

The Streamlit dashboard includes:

- Executive KPI Cards
- Customer Lifetime Value
- Customer Segmentation
- Churn Analysis
- Sales Performance
- Loyalty Analysis
- Restaurant Performance
- Promotion Effectiveness
- Interactive Filters
- Downloadable Reports

---

# Security

## IAM

AWS IAM Roles provide secure access to:

- AWS Glue
- Amazon S3
- AWS Secrets Manager

---

## Secrets Manager

Database credentials are securely stored in AWS Secrets Manager.

No usernames or passwords are hardcoded.

---

## VPC

The SQL Server database resides within an AWS Virtual Private Cloud (VPC).

AWS Glue connects securely using:

- JDBC
- Security Groups
- Private Subnets

---

# Orchestration

AWS EventBridge schedules the ETL jobs to execute daily.

Pipeline schedule:

```
Every Day

↓

Extract SQL Server Data

↓

Load Raw Layer

↓

Run ETL

↓

Generate Gold Metrics

↓

Update Streamlit Dashboard
```

---

# Repository Structure

```
Global Partners Business Analysis Project/

│

├── glue_jobs/

│   ├── extract_rds_to_s3.py
│   ├── bronze_to_silver.py
│   └── silver_to_gold.py


│

├── streamlit/
    ├── pages/

│   ├── app.py
|   ├── config.py
|   ├── utils.py
│   └── requirements.txt

│   ├── orchestration/

|   ├── orders-analytics-piepline.json
|   └── step_functions_graph.png

├── README.md

│

└── .gitignore

