import streamlit as st
import pandas as pd
import io
import ast
import warnings
from datetime import datetime
warnings.simplefilter(action='ignore', category=FutureWarning)
warnings.filterwarnings("ignore")
pd.set_option('display.max_rows', 5000)
pd.set_option('display.max_columns', 1000)
import sys
import re
from datetime import datetime, timedelta
from pytz import timezone, all_timezones
import time
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.styles import Alignment
from openpyxl import load_workbook
from openpyxl.styles import Font
pd.set_option('display.max_rows', 5000)
pd.set_option('display.max_columns', 1000)
from openpyxl import load_workbook
# from utils import *
from io import BytesIO

def call_straddle_finder(file_loc, s_df, filename, sheet_name, spot_price):
    spot = spot_price
    df_excel = file_loc
    df = s_df
    date_pattern = r'(\d{1,2})_(\d{1,2})_(\d{4})'
    match = re.search(date_pattern, filename)
    if match:
        day, month, year = match.groups()
        extracted_date = f"{day}.{month}.{year}"
        date = extracted_date
    
    date_obj = datetime.strptime(date, "%d.%m.%Y")
    day_of_week = date_obj.strftime("%A")
    
    df = df[[ 'OI','LTP', 'Strike Price',  'LTP.1', 'OI.1']]
    for col in df.columns:
         df[col] = df[col].replace({',': ''}, regex=True).astype(float).astype('int64')
    
    df['CALL_VAR'] = df['OI']*df['LTP']
    df['PUT_VAR'] = df['OI.1']*df['LTP.1']
    df = df.rename(columns={'OI':'CALL_OI', 'LTP':'CALL_LTP', 'LTP.1':'PUT_LTP', 'OI.1':'PUT_OI'})
    
    def convert_cols(l_df, cols):
        for c in cols:
            if c in ['CALL_OI', 'PUT_OI']:
                l_df[c] = round(l_df[c]/10**5,1)
            else:
                l_df[c] = round(l_df[c]/10**7,1)
        return l_df
    
    final_df = convert_cols(df, ['CALL_OI', 'PUT_OI', 'CALL_VAR','PUT_VAR'])
    final_df = final_df.sort_values(['PUT_VAR','CALL_VAR'], ascending=[False,False]).reset_index(drop=True)
    final_df = final_df[(final_df['PUT_VAR']>10)& (final_df['CALL_VAR']>10)]
    st.dataframe(final_df, height=300)
    if sheet_name.startswith('Bank'):
        final_df = final_df[(final_df['Strike Price'] % 500 == 0)]
    elif sheet_name.startswith('Nifty'):
        final_df = final_df[(final_df['Strike Price'] % 100 == 0)]
    dic = {'Day':[day_of_week], 'Date':[date], 
           'Spot':[int(spot)], 'Strike':[int(final_df.iloc[0]['Strike Price'])],
            'Call VAR': [final_df.iloc[0]['CALL_VAR']] ,
            'Call OI': [final_df.iloc[0]['CALL_OI']],
            'Call Prem': [final_df.iloc[0]['CALL_LTP']],
             'Collective': final_df.iloc[0]['CALL_LTP']+[final_df.iloc[0]['PUT_LTP']] ,
             'Put Prem': [final_df.iloc[0]['PUT_LTP']] ,
             'Put OI': [final_df.iloc[0]['PUT_OI']], 
            'Put VAR': [final_df.iloc[0]['PUT_VAR']], 
            'lower range': [int([final_df.iloc[0]['Strike Price']] - (final_df.iloc[0]['CALL_LTP']+[final_df.iloc[0]['PUT_LTP']]))] , 
            'upper range': [int([final_df.iloc[0]['Strike Price']] + (final_df.iloc[0]['CALL_LTP']+[final_df.iloc[0]['PUT_LTP']]))] 
          }
    
    new = pd.DataFrame(dic)
    df_excel = pd.concat([df_excel, new], ignore_index=True)

    return df_excel


# Title
st.title("Straddle Finder")

# Integer inputs for Nifty and Bank spot values
nifty_spot = st.number_input("Enter Nifty Spot value:", min_value=0, value=10000)
bank_spot = st.number_input("Enter Bank Spot value:", min_value=0, value=25000)

#upload own file
own_file_main = st.file_uploader("Upload Main file", type=["csv", "xlsx"])
nifty_filename_week = st.file_uploader("Upload Nifty Weekly Data", type=["csv", "xlsx"])
nifty_filename_month = st.file_uploader("Upload Nifty Monthly Data", type=["csv", "xlsx"])
bank_filename_month = st.file_uploader("Upload Bank Monthly Data", type=["csv", "xlsx"])

# Check if all required inputs are provided
if own_file_main and nifty_filename_week and nifty_filename_month and bank_filename_month:
    own_file_main_df1 = pd.read_excel(own_file_main, sheet_name="Nifty-W" )
    own_file_main_df2 =  pd.read_excel(own_file_main, sheet_name="Nifty-M" )
    own_file_main_df4 =  pd.read_excel(own_file_main, sheet_name="Bank-M" )

    nifty_filename_week_df = pd.read_csv(nifty_filename_week)
    nifty_filename_month_df = pd.read_csv(nifty_filename_month)
    bank_filename_month_df = pd.read_csv(bank_filename_month)

    final_df_1 = call_straddle_finder(own_file_main_df1, nifty_filename_week_df,  nifty_filename_week.name, 'Nifty-W' , nifty_spot)
    final_df_2 = call_straddle_finder(own_file_main_df2, nifty_filename_month_df,  nifty_filename_month.name, 'Nifty-M' , nifty_spot)
    final_df_4 = call_straddle_finder(own_file_main_df4, bank_filename_month_df, bank_filename_month.name, 'Bank-M' , bank_spot)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        final_df_1.to_excel(writer, sheet_name='Nifty-W', index=False)
        final_df_2.to_excel(writer, sheet_name='Nifty-M', index=False)
        final_df_4.to_excel(writer, sheet_name='Bank-M', index=False)
    output.seek(0)
    st.download_button( label="Download Processed File", data=output, file_name="Share-option chain analysis-new-final.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
else:
    st.warning("Please upload all files and enter required values.")
