import streamlit as st
import pandas as pd
import requests
import datetime
import os
from io import BytesIO

# ✅ API 키 리스트
api_keys = [
    '9b6a75c780e758dbedb8c1c88c55c5ee',
    '7890516e808b71c7973cfff05dafa9c9',
    '187674987af1cb83d8e19ad8bb5057dc'
]

# ✅ 보고서 이름 매핑
report_map = {
    'income-statement': 'IS',
    'balance-sheet-statement': 'BS',
    'cash-flow-statement': 'CF'
}

# ✅ 보고서 추출 함수
def fetch_financial_report(ticker, report_type, from_date, to_date):
    for api_key in api_keys:
        url = f"https://financialmodelingprep.com/api/v3/{report_type}/{ticker}?period=quarter&from={from_date}&to={to_date}&apikey={api_key}"
        try:
            res = requests.get(url, timeout=10)
            data = res.json()
            if isinstance(data, list) and len(data) > 0:
                return pd.DataFrame.from_records(data)
        except:
            continue
    return pd.DataFrame()

# ✅ Streamlit UI 시작
st.set_page_config(page_title="📊 재무제표 추출기", layout="wide")
st.title("📑 미국 주식 재무제표 다운로드 (FMP API)")

# 사용자 입력 받기
ticker = st.text_input("종목 티커 입력 (예: AAPL, MSFT, TSLA)", value="AAPL")
from_date = st.date_input("시작 날짜", value=datetime.date(2021, 1, 1)).strftime("%Y-%m-%d")
to_date = st.date_input("종료 날짜", value=datetime.date.today()).strftime("%Y-%m-%d")

# 조회 버튼
download = st.button("📥 재무제표 가져오기")

if download:
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M")
    zip_buffer = BytesIO()
    results = {}

    for report in report_map:
        df = fetch_financial_report(ticker, report, from_date, to_date)
        if not df.empty:
            results[report_map[report]] = df.T  # 전치해서 가독성 높이기
        else:
            st.warning(f"⚠️ {report} 데이터 불러오기 실패 또는 데이터 없음.")

    if results:
        st.success(f"✅ {ticker} 재무제표 {len(results)}개 종류 로드 완료")
        for name, df in results.items():
            st.subheader(f"📊 {name} Report")
            st.dataframe(df, use_container_width=True)

        with BytesIO() as buffer:
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                for name, df in results.items():
                    df.to_excel(writer, sheet_name=name)
            buffer.seek(0)
            st.download_button("⬇️ 엑셀 다운로드", buffer, file_name=f"{ticker}_재무제표_{timestamp}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    else:
        st.error("❌ 모든 보고서 요청 실패. API Key 제한 혹은 티커 오류일 수 있습니다.")
