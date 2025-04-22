import streamlit as st
import pandas as pd
from pykrx import stock
import re

st.title("🏢 발행주식총수 조회기 (KRX 기준)")
st.markdown("종목명 또는 종목코드를 입력하면, 해당 연도의 발행주식총수를 확인할 수 있습니다.")

# 📥 사용자 입력
stock_input = st.text_input("조회할 종목명 또는 종목코드 (예: 삼성전자 또는 005930)", value="삼성전자")
year_input = st.text_input("조회할 연도 (예: 2021)", value="2021")
year = year_input if re.match(r'^\d{4}$', year_input) else '2021'

# 📆 마지막 영업일 계산 함수 (KOSPI 종목 중 하나 기준)
def get_last_trading_day(year):
    try:
        tickers = stock.get_market_ticker_list(f"{year}1231", market="KOSPI")
        for ticker in tickers:
            df = stock.get_market_ohlcv_by_date(f"{year}0101", f"{year}1231", ticker)
            if not df.empty:
                return df.index[-1].strftime("%Y%m%d")
    except:
        pass
    return None

# 조회 버튼
if st.button("🔍 조회하기"):

    try:
        # 🧭 종목 코드 매핑
        tickers = stock.get_market_ticker_list(market='ALL')
        code_name_map = {code: stock.get_market_ticker_name(code) for code in tickers}

        matched_code = None
        stock_name = None

        if stock_input.isdigit() and len(stock_input) == 6:
            if stock_input in code_name_map:
                matched_code = stock_input
                stock_name = code_name_map[matched_code]
        else:
            for code, name in code_name_map.items():
                if name == stock_input:
                    matched_code = code
                    stock_name = name
                    break

        if not matched_code:
            st.error(f"❌ '{stock_input}'에 해당하는 종목명을 찾을 수 없습니다.")
        else:
            # 📅 마지막 영업일 확인
            end_date = get_last_trading_day(year)
            if not end_date:
                st.warning(f"❌ {year}년의 마지막 영업일을 확인할 수 없습니다.")
            else:
                cap_df = stock.get_market_cap_by_date(end_date, end_date, matched_code)
                if cap_df.empty:
                    st.warning(f"❌ {year}년 ({end_date}) 기준 데이터가 존재하지 않습니다.")
                else:
                    issued_shares = int(cap_df['상장주식수'].values[0])
                    st.success(f"✅ [{stock_name}] {year}년 기준 발행주식총수")
                    st.write(f"**{issued_shares:,}주** (조회일 기준: {end_date})")

    except Exception as e:
        st.error(f"🚫 오류 발생: {e}")
