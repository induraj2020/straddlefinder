import streamlit as st
import pandas as pd
import io

# Title
st.title("Straddle Finder")

# Integer inputs for Nifty and Bank spot values
nifty_spot = st.number_input("Enter Nifty Spot value:", min_value=0, value=10000)
bank_spot = st.number_input("Enter Bank Spot value:", min_value=0, value=25000)

# File uploads
nifty_file_week = st.file_uploader("Upload Nifty Weekly Data", type=["csv", "xlsx"])
nifty_file_month = st.file_uploader("Upload Nifty Monthly Data", type=["csv", "xlsx"])
bank_file_week = st.file_uploader("Upload Bank Weekly Data", type=["csv", "xlsx"])
bank_file_month = st.file_uploader("Upload Bank Monthly Data", type=["csv", "xlsx"])

# Check if all required inputs are provided
if nifty_file_week and nifty_file_month and bank_file_week and bank_file_month:
    
    # Example data processing (merging all dataframes into one for simplicity)
    def process_file(file):
        if file.name.endswith(".csv"):
            return pd.read_csv(file)
        else:
            return pd.read_excel(file)

    # Process all files
    nifty_week_df = process_file(nifty_file_week)
    nifty_month_df = process_file(nifty_file_month)
    bank_week_df = process_file(bank_file_week)
    bank_month_df = process_file(bank_file_month)

    # Example processing: Add Nifty Spot and Bank Spot to all dataframes
    nifty_week_df["Nifty_Spot"] = nifty_spot
    nifty_month_df["Nifty_Spot"] = nifty_spot
    bank_week_df["Bank_Spot"] = bank_spot
    bank_month_df["Bank_Spot"] = bank_spot

    # Concatenate all data (Example)
    final_df = pd.concat([nifty_week_df, nifty_month_df, bank_week_df, bank_month_df])

    # Button to download the processed file
    output = io.BytesIO()
    final_df.to_csv(output, index=False)
    output.seek(0)

    st.download_button(
        label="Download Processed File",
        data=output,
        file_name="processed_data.csv",
        mime="text/csv"
    )
else:
    st.warning("Please upload all files and enter required values.")
