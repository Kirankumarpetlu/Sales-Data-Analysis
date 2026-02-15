import pandas as pd
import datetime as dt
import os

def process_data(input_file, output_file):
    print(f"Loading data from {input_file}...")
    try:
        df = pd.read_excel(input_file)
    except FileNotFoundError:
        print(f"Error: File not found at {input_file}")
        return

    print(f"Initial shape: {df.shape}")

    # Data Cleaning
    print("Cleaning data...")
    # Remove null CustomerIDs
    df = df.dropna(subset=['Customer ID'])
    
    # Remove negative Quantity and Price
    df = df[(df['Quantity'] > 0) & (df['Price'] > 0)]
    
    # Type conversion
    df['Customer ID'] = df['Customer ID'].astype(int)
    
    # Rename columns for consistency
    df.rename(columns={
        'Invoice': 'InvoiceNo', 
        'Price': 'UnitPrice', 
        'Customer ID': 'CustomerID'
    }, inplace=True)

    # Feature Engineering
    df['Revenue'] = df['Quantity'] * df['UnitPrice']
    df['InvoiceDate'] = pd.to_datetime(df['InvoiceDate'])
    
    print(f"Shape after cleaning: {df.shape}")

    # RFM Analysis
    print("Performing RFM Analysis...")
    snapshot_date = df['InvoiceDate'].max() + dt.timedelta(days=1)
    
    rfm = df.groupby('CustomerID').agg({
        'InvoiceDate': lambda x: (snapshot_date - x.max()).days,
        'InvoiceNo': 'nunique',
        'Revenue': 'sum'
    }).reset_index()

    rfm.rename(columns={
        'InvoiceDate': 'Recency',
        'InvoiceNo': 'Frequency',
        'Revenue': 'Monetary'
    }, inplace=True)

    # Calculate RFM Scores (quartiles)
    # Recency: Lower is better (4 is best)
    rfm['R_score'] = pd.qcut(rfm['Recency'], 4, labels=[4, 3, 2, 1])
    
    # Frequency: Higher is better (1 is lowest, might need rank method='first' for ties)
    rfm['F_score'] = pd.qcut(rfm['Frequency'].rank(method='first'), 4, labels=[1, 2, 3, 4])
    
    # Monetary: Higher is better
    rfm['M_score'] = pd.qcut(rfm['Monetary'], 4, labels=[1, 2, 3, 4])

    # Combine Scores
    rfm['RFM_Score'] = rfm['R_score'].astype(str) + rfm['F_score'].astype(str) + rfm['M_score'].astype(str)

    # Segmentation Logic (Matching notebook)
    def segment_customer(row):
        if row['RFM_Score'] == '444':
            return 'Best Customers'
        elif row['F_score'] == 4:
            return 'Loyal Customers'
        elif row['R_score'] == 4:
            return 'Recent Customers'
        elif row['M_score'] == 4:
            return 'Big Spenders'
        else:
            return 'Regular Customers'

    rfm['Segment'] = rfm.apply(segment_customer, axis=1)

    print("RFM Analysis complete.")
    print(rfm[['CustomerID', 'Recency', 'Frequency', 'Monetary', 'RFM_Score', 'Segment']].head())
    print("\nSegment Counts:")
    print(rfm['Segment'].value_counts())

    # Merge RFM back to main dataframe? 
    # Usually for dashboards we want the transaction data augmented with customer segments, 
    # OR two separate tables. Let's merge it so the user has one rich table for Tableau.
    # Actually, a single flat file is easiest for Tableau/PBI beginners.
    
    print("Merging RFM data back to transaction level...")
    final_df = df.merge(rfm[['CustomerID', 'Recency', 'Frequency', 'Monetary', 'R_score', 'F_score', 'M_score', 'RFM_Score', 'Segment']], on='CustomerID', how='left')
    
    print(f"Exporting to {output_file}...")
    final_df.to_csv(output_file, index=False)
    print("Export successful.")

if __name__ == "__main__":
    input_path = r"e:/sales_Data _analysis/online_retail_II.xlsx"
    output_path = r"e:/sales_Data _analysis/processed_online_retail.csv"
    
    process_data(input_path, output_path)
