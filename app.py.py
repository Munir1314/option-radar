
import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(page_title="Option Radar", layout="wide")

def fetch_option_chain(symbol="NIFTY"):
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.nseindia.com/option-chain"
    }
    session = requests.Session()
    session.get("https://www.nseindia.com", headers=headers)
    response = session.get(f"https://www.nseindia.com/api/option-chain-indices?symbol={symbol}", headers=headers)

    if response.status_code != 200:
        st.error("Failed to fetch data from NSE.")
        return pd.DataFrame(), []
    
    data = response.json()
    expiry_list = data["records"]["expiryDates"]
    all_data = data["records"]["data"]
    df = pd.json_normalize(all_data, sep='_')
    return df, expiry_list

def get_atm_strike(df):
    df_filtered = df[df['CE_lastPrice'].notnull()]
    spot_price = df_filtered.iloc[0]['CE_underlyingValue']
    df['diff'] = abs(df['strikePrice'] - spot_price)
    atm_strike = df.loc[df['diff'].idxmin(), 'strikePrice']
    return int(atm_strike), spot_price

def filter_strikes(df, atm, count, expiry):
    df = df[df['expiryDate'] == expiry]
    return df[(df['strikePrice'] >= atm - count*50) & (df['strikePrice'] <= atm + count*50)]

def detect_signals(df):
    conditions = []
    for _, row in df.iterrows():
        ce_oi_change = row.get('CE_changeinOpenInterest', 0)
        ce_price_change = row.get('CE_lastPrice', 0)
        if ce_oi_change > 0 and ce_price_change > 0:
            signal = "Long Buildup"
        elif ce_oi_change > 0 and ce_price_change < 0:
            signal = "Short Buildup"
        elif ce_oi_change < 0 and ce_price_change > 0:
            signal = "Short Covering"
        elif ce_oi_change < 0 and ce_price_change < 0:
            signal = "Long Unwinding"
        else:
            signal = "-"
        conditions.append(signal)
    df['Signal'] = conditions
    return df

def plot_pcr(df):
    total_ce = df['CE_openInterest'].sum()
    total_pe = df['PE_openInterest'].sum()
    pcr = total_pe / total_ce if total_ce else 0

    fig = go.Figure(data=[
        go.Bar(name='CE OI', x=df['strikePrice'], y=df['CE_openInterest'], marker_color='orange'),
        go.Bar(name='PE OI', x=df['strikePrice'], y=df['PE_openInterest'], marker_color='green'),
    ])
    fig.update_layout(barmode='group', title=f"PCR: {pcr:.2f}", xaxis_title="Strike Price", yaxis_title="Open Interest")
    st.plotly_chart(fig, use_container_width=True)

st.title("📊 Option Radar")
st.caption("“Spot the Signals. Track the Trend.”")

tab1, tab2 = st.tabs(["NIFTY", "BANKNIFTY"])

for tab, symbol in zip([tab1, tab2], ["NIFTY", "BANKNIFTY"]):
    with tab:
        with st.spinner("Fetching option chain data..."):
            df, expiries = fetch_option_chain(symbol)
        
        if df.empty:
            continue

        expiry = st.selectbox("Select Expiry", expiries, key=symbol+"_expiry")
        strike_range = st.slider("Strikes ±ATM", 1, 20, 5, key=symbol+"_slider")

        atm_strike, spot = get_atm_strike(df)
        st.info(f"**Spot Price:** {spot:.2f} | **ATM Strike:** {atm_strike}")

        filtered_df = filter_strikes(df, atm_strike, strike_range, expiry)
        signal_df = detect_signals(filtered_df.copy())

        st.subheader("Signal Table")
        st.dataframe(signal_df[['strikePrice', 'CE_openInterest', 'PE_openInterest', 'Signal']], use_container_width=True)

        st.subheader("Put/Call Ratio Chart")
        plot_pcr(signal_df)

st.experimental_rerun()
