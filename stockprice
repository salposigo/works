import streamlit as st
import pandas as pd
import yfinance as yf
from pykrx import stock
import re
import os
import random

st.set_page_config(page_title="📊 수정주가 및 요약 분석기", layout="wide")
st.title("📈 종목별 수정주가 및 연도별 요약 분석기")

# 📅 날짜 포맷 변환 함수
def convert_date_format(date_str, default_str):
    if not date_str:
        date_str = default_str
    if re.match(r'\d{8}$', date_str):
        return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
    return date_str

# 상태 초기화
if "matched_code" not in st.session_state:
    st.session_state.matched_code = None
    st.session_state.stock_name = None
    st.session_state.df = None
    st.session_state.summary = None

# 사용자 입력
stock_input = st.text_input("🔍 종목명 또는 종목코드", value="삼성전자")
start_input = st.text_input("조회 시작일 (YYYYMMDD 또는 YYYY-MM-DD)", value="20210101")
end_input = st.text_input("조회 종료일 (YYYYMMDD 또는 YYYY-MM-DD)", value="20241231")

start_date = convert_date_format(start_input, '20210101')
end_date = convert_date_format(end_input, '20241231')

# 종목 매칭 로직 실행 버튼
if st.button("✅ 종목 검색 및 데이터 수집"):
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
            if stock_input == name:
                matched_code = code
                stock_name = name
                break

    if not matched_code:
        st.error(f"❌ '{stock_input}'에 해당하는 종목을 찾을 수 없습니다.")
    else:
        st.session_state.matched_code = matched_code
        st.session_state.stock_name = stock_name
        st.success(f"[종목확인] {stock_name} → 종목코드: {matched_code}")

        if matched_code in stock.get_market_ticker_list(market='KOSDAQ', date=end_date.replace('-', '')):
            suffix = ".KQ"
        else:
            suffix = ".KS"
        
        ticker_yf = f"{matched_code}{suffix}"
        df_yf = yf.download(ticker_yf, start=start_date, end=end_date)

        if df_yf.empty:
            st.error(f"❌ yfinance에서 '{ticker_yf}' 데이터를 가져올 수 없습니다.")
        else:
            if isinstance(df_yf.columns, pd.MultiIndex):
                df_yf.columns = df_yf.columns.get_level_values(0)

            price_column = 'Adj Close' if 'Adj Close' in df_yf.columns else 'Close'
            df_yf = df_yf[[price_column]].rename(columns={price_column: '수정종가'})
            df_yf.index = pd.to_datetime(df_yf.index).strftime('%Y-%m-%d')

            cap_df = stock.get_market_cap_by_date(start_date.replace('-', ''), end_date.replace('-', ''), matched_code)
            cap_df.index = pd.to_datetime(cap_df.index).strftime('%Y-%m-%d')
            cap_df = cap_df[['거래량', '상장주식수']]

            df = df_yf.join(cap_df, how='inner')
            df = df.rename(columns={'상장주식수': '발행주식수'})
            df.dropna(inplace=True)
            df['시가총액'] = df['수정종가'] * df['발행주식수']
            df['연도'] = pd.to_datetime(df.index).year

            summary = (
                df.groupby('연도').apply(
                    lambda g: pd.Series({
                        '종가': g.tail(1)['수정종가'].values[0],
                        '최고가': g['수정종가'].max(),
                        '최저가': g['수정종가'].min(),
                        '연가중평균종가': (g['수정종가'] * g['거래량']).sum() / g['거래량'].sum()
                    })
                ).reset_index()
            )

            summary['회사명'] = stock_name
            summary['종목코드'] = matched_code
            summary = summary[['회사명', '종목코드', '연도', '종가', '연가중평균종가', '최저가', '최고가']]

            st.session_state.df = df
            st.session_state.summary = summary

# 결과 출력
if st.session_state.df is not None and st.session_state.summary is not None:
    st.subheader("📄 연도별 요약 통계")
    st.dataframe(st.session_state.summary, use_container_width=True)

    st.subheader("📅 일별 주가 데이터")
    st.dataframe(st.session_state.df.drop(columns='연도'), use_container_width=True)

    with st.expander("📥 데이터 다운로드"):
        from io import BytesIO
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            st.session_state.df.drop(columns='연도').to_excel(writer, sheet_name='일별주가')
            st.session_state.summary.to_excel(writer, sheet_name='연도별요약', index=False)
        output.seek(0)
        st.download_button("엑셀 다운로드", output, file_name=f"{st.session_state.stock_name}_수정주가요약.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
