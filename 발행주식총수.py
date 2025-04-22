import streamlit as st
import pandas as pd
from pykrx import stock
import re

st.title("🏢 발행주식총수 조회기 (KRX 기준)")
st.markdown("종목명 또는 종목코드를 입력하면, 해당 연도의 발행주식총수를 확인할 수 있습니다.")

# 📥 사용자 입력
stock_input = st.text_input("조회할 종목명 또는 종목코드 (예: 삼성전자 또는 005930)", value="삼성")
year_input = st.text_input("조회할 연도 (예: 2021)", value="2021")
year = year_input if re.match(r'^\d{4}$', year_input) else '2021'

# 📆 마지막 영업일 계산 함수
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

# 종목 유사 검색 함수
def find_candidates(user_input):
    tickers = stock.get_market_ticker_list(market='ALL')
    results = []

    for code in tickers:
        name = stock.get_market_ticker_name(code)
        if user_input in name or user_input == code:
            results.append((code, name))
    return results

# ✅ 상태 관리: candidates 저장
if "candidates" not in st.session_state:
    st.session_state.candidates = []
if "selected_code" not in st.session_state:
    st.session_state.selected_code = None
if "stock_name" not in st.session_state:
    st.session_state.stock_name = None

# 🔍 조회 버튼
if st.button("🔍 종목 검색"):
    candidates = find_candidates(stock_input.strip())
    if not candidates:
        st.error("❌ 해당 입력과 일치하는 종목을 찾을 수 없습니다.")
    else:
        st.session_state.candidates = candidates

# ✅ 종목 선택 단계
if st.session_state.candidates:
    options = [f"{name} ({code})" for code, name in st.session_state.candidates]
    choice = st.selectbox("🧩 선택할 종목을 고르세요:", options)

    selected_code = choice.split('(')[-1].replace(')', '').strip()
    stock_name = choice.split('(')[0].strip()

    st.session_state.selected_code = selected_code
    st.session_state.stock_name = stock_name

# ✅ 최종 조회
if st.session_state.selected_code and st.button("📊 발행주식총수 조회"):
    end_date = get_last_trading_day(year)
    if not end_date:
        st.warning(f"❌ {year}년의 마지막 영업일을 확인할 수 없습니다.")
    else:
        cap_df = stock.get_market_cap_by_date(end_date, end_date, st.session_state.selected_code)
        if cap_df.empty:
            st.warning(f"❌ {year}년 ({end_date}) 기준 데이터가 존재하지 않습니다.")
        else:
            issued_shares = int(cap_df['상장주식수'].values[0])
            st.success(f"✅ [{st.session_state.stock_name}] {year}년 기준 발행주식총수")
            st.write(f"**{issued_shares:,}주** (조회일 기준: {end_date})")
