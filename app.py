def fetch_option_chain(symbol="NIFTY"):
    import time
    import random

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.nseindia.com/",
        "Connection": "keep-alive",
    }

    session = requests.Session()
    try:
        # Establish session and cookies
        session.get("https://www.nseindia.com", headers=headers, timeout=5)
        url = f"https://www.nseindia.com/api/option-chain-indices?symbol={symbol}"
        response = session.get(url, headers=headers, timeout=5)

        if response.status_code != 200:
            st.warning("NSE temporarily blocked us. Trying again in a few seconds...")
            time.sleep(random.uniform(1, 3))
            response = session.get(url, headers=headers, timeout=5)

        if response.status_code != 200:
            raise Exception("Failed to fetch data from NSE")

        data = response.json()
        expiry_list = data["records"]["expiryDates"]
        all_data = data["records"]["data"]
        df = pd.json_normalize(all_data, sep='_')
        return df, expiry_list
    except Exception as e:
        st.error("Failed to fetch data from NSE.")
        return pd.DataFrame(), []
