import streamlit as st
from pykrx import stock
import pandas as pd
import re

# 날짜 포맷 정리 함수
def clean_date(date_str):
    return re.sub(r"[-]", "", date_str.strip())

# 종목코드 찾기 함수 (부분 일치)
def find_ticker(input_str, date):
    input_str = input_str.strip()
    if input_str.isdigit() and len(input_str) == 6:
        try:
            name = stock.get_market_ticker_name(input_str)
            return [(input_str, name)]
        except:
            return []

    matched = []
    for market in ["KOSPI", "KOSDAQ"]:
        tickers = stock.get_market_ticker_list(date, market=market)
        for code in tickers:
            name = stock.get_market_ticker_name(code)
            if input_str in name:
                matched.append((code, name))
    return matched

# 지수 코드 매핑
INDEX_MAP = {
    "코스피": "1001",
    "코스닥": "2001",
}

# Streamlit UI
st.title("📊 주식 베타 분석기 (pykrx 기반)")
st.markdown("종목명 또는 종목코드를 입력하면, 선택한 시장지수 대비 베타 값을 계산해줍니다.")

user_input = st.text_input("🎯 종목명 또는 종목코드", value="유비쿼스")
start_input = st.text_input("⏱ 시작일 (YYYYMMDD 또는 YYYY-MM-DD)", value="2023-01-01")
end_input = st.text_input("⏱ 종료일 (YYYYMMDD 또는 YYYY-MM-DD)", value="2023-12-31")
index_name = st.selectbox("📈 시장 지수 선택", ["코스피", "코스닥"])

if st.button("📥 베타 계산"):
    start_date = clean_date(start_input)
    end_date = clean_date(end_input)
    index_code = INDEX_MAP.get(index_name)

    matches = find_ticker(user_input, end_date)
    if not matches:
        st.error("❌ 일치하는 종목을 찾을 수 없습니다.")
    else:
        # 단일 또는 다중 종목 선택 처리
        if len(matches) == 1:
            stock_code, stock_name = matches[0]
        else:
            choice = st.selectbox("여러 종목이 일치합니다. 선택하세요:", [f"{n} ({c})" for c, n in matches])
            idx = [f"{n} ({c})" for c, n in matches].index(choice)
            stock_code, stock_name = matches[idx]

        try:
            stock_df = stock.get_market_ohlcv_by_date(start_date, end_date, stock_code)
            market_df = stock.get_index_ohlcv_by_date(start_date, end_date, index_code)

            stock_ret = stock_df['종가'].pct_change()
            market_ret = market_df['종가'].pct_change()
            df = pd.concat([stock_ret, market_ret], axis=1).dropna()
            df.columns = ['Stock_Return', 'Market_Return']

            beta = df.cov().iloc[0, 1] / df['Market_Return'].var()

            st.success(f"✅ 종목: {stock_name} ({stock_code})")
            st.success(f"📆 분석 기간: {start_date} ~ {end_date}")
            st.info(f"📊 계산된 **베타 값**: `{beta:.4f}`")
        except Exception as e:
            st.error(f"❌ 데이터 수집 중 오류 발생: {e}")