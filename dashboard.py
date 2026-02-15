import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Set page config
st.set_page_config(page_title="Sales Analytics Dashboard", layout="wide")

# Title
st.title("📊 Sales Analytics Dashboard")
st.markdown("Interactive analysis of Online Retail data including Revenue, Trends, and Customer Segmentation.")

# Load Data
@st.cache_data
def load_data():
    file_path = "e:/sales_Data _analysis/processed_online_retail.csv"
    try:
        df = pd.read_csv(file_path)
        df['InvoiceDate'] = pd.to_datetime(df['InvoiceDate'])
        return df
    except FileNotFoundError:
        st.error(f"File not found: {file_path}. Please generate the data first.")
        return None

df = load_data()

if df is not None:
    # Sidebar Filters
    st.sidebar.header("Filters")
    
    # Date Filter
    min_date = df['InvoiceDate'].min()
    max_date = df['InvoiceDate'].max()
    
    date_range = st.sidebar.date_input(
        "Select Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )
    
    # Country Filter
    countries = ["All"] + sorted(df['Country'].unique().tolist())
    selected_country = st.sidebar.selectbox("Select Country", countries)

    # Filter Logic
    mask = (df['InvoiceDate'].dt.date >= date_range[0]) & (df['InvoiceDate'].dt.date <= date_range[1])
    if selected_country != "All":
        mask = mask & (df['Country'] == selected_country)
    
    filtered_df = df.loc[mask]

    # --- KPIs ---
    st.markdown("### Key Performance Indicators")
    col1, col2, col3, col4 = st.columns(4)
    
    total_revenue = filtered_df['Revenue'].sum()
    total_customers = filtered_df['CustomerID'].nunique()
    total_invoices = filtered_df['InvoiceNo'].nunique()
    avg_rev_customer = total_revenue / total_customers if total_customers else 0

    col1.metric("Total Revenue", f"${total_revenue:,.2f}")
    col2.metric("Total Customers", f"{total_customers:,}")
    col3.metric("Total Invoices", f"{total_invoices:,}")
    col4.metric("Avg Revenue/Customer", f"${avg_rev_customer:,.2f}")

    st.markdown("---")

    # --- Charts Row 1 ---
    col_left, col_right = st.columns(2)

    # 1. Monthly Revenue Trend
    with col_left:
        st.subheader("Monthly Revenue Trend")
        # Grouper by Month
        monthly_sales = filtered_df.groupby(pd.Grouper(key='InvoiceDate', freq='M'))['Revenue'].sum().reset_index()
        fig_trend = px.line(monthly_sales, x='InvoiceDate', y='Revenue', markers=True, title="Revenue Over Time")
        st.plotly_chart(fig_trend, use_container_width=True)

    # 2. Customer Segmentation
    with col_right:
        st.subheader("Customer Segmentation")
        if 'Segment' in filtered_df.columns:
            # Count DISTINCT customers per segment
            # We need to drop duplicates on CustomerID first to count segments correctly per customer
            unique_customers = filtered_df[['CustomerID', 'Segment']].drop_duplicates()
            segment_counts = unique_customers['Segment'].value_counts().reset_index()
            segment_counts.columns = ['Segment', 'Count']
            
            fig_segment = px.pie(segment_counts, values='Count', names='Segment', title="Customer Distribution", hole=0.4)
            st.plotly_chart(fig_segment, use_container_width=True)
        else:
            st.warning("Segment column not found in data.")

    # --- Charts Row 2 ---
    col_left_2, col_right_2 = st.columns(2)

    # 3. Top 10 Countries
    with col_left_2:
        st.subheader("Top 10 Countries by Revenue")
        country_sales = filtered_df.groupby('Country')['Revenue'].sum().sort_values(ascending=False).head(10).reset_index()
        fig_country = px.bar(country_sales, x='Revenue', y='Country', orientation='h', title="Top Countries", text_auto='.2s')
        fig_country.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_country, use_container_width=True)

    # 4. Top 10 Products
    with col_right_2:
        st.subheader("Top 10 Products by Revenue")
        product_sales = filtered_df.groupby('Description')['Revenue'].sum().sort_values(ascending=False).head(10).reset_index()
        fig_product = px.bar(product_sales, x='Revenue', y='Description', orientation='h', title="Top Products", text_auto='.2s')
        fig_product.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_product, use_container_width=True)

    # --- Data Preview ---
    with st.expander("View Raw Data"):
        st.dataframe(filtered_df.head(100))
