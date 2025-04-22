import streamlit as st
import pandas as pd
import requests
import datetime
import zipfile
import xml.etree.ElementTree as ET
from io import BytesIO

# ✅ 오픈 DART API 키
API_KEY = "ded0a691495e144e7e75186617f1cec29d41f661"

# ✅ corp_code.xml 로딩 함수
def load_corp_codes():
    url = f"https://opendart.fss.or.kr/api/corpCode.xml?crtfc_key={API_KEY}"
    res = requests.get(url)
    if res.status_code == 200:
        z = zipfile.ZipFile(BytesIO(res.content))
        xml_data = z.read(z.namelist()[0])
        root = ET.fromstring(xml_data)
        data = [
            {
                'corp_code': item.find('corp_code').text,
                'corp_name': item.find('corp_name').text,
                'stock_code': item.find('stock_code').text
            }
            for item in root.findall('list') if item.find('stock_code') is not None and item.find('stock_code').text
        ]
        return pd.DataFrame(data)
    return pd.DataFrame()

# ✅ 공시 리스트 불러오기
def get_report_list(corp_code, bgn_de, end_de, report_tp):
    url = (
        f"https://opendart.fss.or.kr/api/list.json"
        f"?crtfc_key={API_KEY}&corp_code={corp_code}&bgn_de={bgn_de}&end_de={end_de}&pblntf_detail_ty={report_tp}&page_count=100"
    )
    res = requests.get(url)
    return res.json()

# ✅ XBRL 데이터 조회 함수 (CFS → OFS fallback)
def get_xbrl_financials_with_fallback(rcept_no):
    for fs_div in ['CFS', 'OFS']:
        url = f"https://opendart.fss.or.kr/api/fnlttSinglAcntAll.json?crtfc_key={API_KEY}&rcept_no={rcept_no}&fs_div={fs_div}"
        res = requests.get(url)
        if res.status_code == 200 and res.json().get("status") == "000":
            df = pd.DataFrame(res.json()['list'])
            if not df.empty:
                return df, fs_div
    return pd.DataFrame(), None

# ✅ Streamlit UI 시작
st.set_page_config(page_title="📊 오픈DART 재무제표 조회기", layout="wide")
st.title("📊 오픈 DART API 기반 연결/별도 재무제표 직접 조회")

# 날짜 범위 선택
today = datetime.date.today()
start_date = st.date_input("검색 시작일", datetime.date(today.year - 1, 1, 1))
end_date = st.date_input("검색 종료일", today)
report_type = st.selectbox("공시유형 선택", options=[("사업보고서", "A001"), ("반기보고서", "A002"), ("분기보고서", "A003")], format_func=lambda x: x[0])

# 종목코드 입력
stock_input = st.text_input("📌 종목코드 또는 기업명 입력 (예: 005930 또는 삼성전자)", value="005930")
if 'corp_df' not in st.session_state:
    with st.spinner("상장기업 목록 불러오는 중..."):
        st.session_state.corp_df = load_corp_codes()

corp_df = st.session_state.corp_df
if 'selected_corp' not in st.session_state:
    st.session_state.selected_corp = None
if 'matched_df' not in st.session_state:
    st.session_state.matched_df = pd.DataFrame()
if 'selectbox_name' not in st.session_state:
    st.session_state.selectbox_name = None

# 검색 트리거
matched = corp_df[(corp_df['stock_code'] == stock_input) | (corp_df['corp_name'].str.contains(stock_input))]
if not matched.empty:
    st.session_state.matched_df = matched.copy()

# 유사 기업 선택
if len(st.session_state.matched_df) > 1:
    st.session_state.selectbox_name = st.selectbox("⚠️ 유사한 기업이 여러 개 있습니다. 하나를 선택하세요:", st.session_state.matched_df['corp_name'].tolist())

# 공시자료 조회 버튼
if st.button("🔍 공시자료 조회"):
    if len(st.session_state.matched_df) == 1:
        st.session_state.selected_corp = st.session_state.matched_df.iloc[0]
    elif st.session_state.selectbox_name:
        selected_row = st.session_state.matched_df[st.session_state.matched_df['corp_name'] == st.session_state.selectbox_name].iloc[0]
        st.session_state.selected_corp = selected_row

# 재무제표 조회 출력
if st.session_state.selected_corp is not None:
    corp_code = st.session_state.selected_corp['corp_code']
    corp_name = st.session_state.selected_corp['corp_name']
    st.info(f"✅ 조회 대상: {corp_name} ({st.session_state.selected_corp['stock_code']})")

    bgn_de = start_date.strftime('%Y%m%d')
    end_de = end_date.strftime('%Y%m%d')
    report_tp = report_type[1]

    with st.spinner("📡 DART로부터 공시 목록 수신 중..."):
        result = get_report_list(corp_code, bgn_de, end_de, report_tp)

    if result.get("status") != "000" or not result.get("list"):
        st.warning("❌ 해당 기간에 제출된 공시 또는 재무제표가 없습니다.")
    else:
        report_df = pd.DataFrame(result['list'])
        report_df = report_df[['rcept_no', 'report_nm', 'rcept_dt']]
        report_df['접수일'] = pd.to_datetime(report_df['rcept_dt'])

        selected_rcept = st.selectbox("📂 재무제표 열람할 보고서를 선택하세요:", report_df['report_nm'] + " / " + report_df['rcept_dt'])
        rcept_no = report_df[report_df['report_nm'] + " / " + report_df['rcept_dt'] == selected_rcept]['rcept_no'].values[0]

        with st.spinner("📊 재무제표 불러오는 중..."):
            fs_df, fs_type = get_xbrl_financials_with_fallback(rcept_no)

        if fs_df.empty:
            st.error("❌ 연결(CFS) 또는 별도(OFS) 재무제표 데이터가 존재하지 않습니다.")
        else:
            st.success(f"📈 조회된 재무제표 유형: {fs_type}")
            display_df = fs_df[['fs_nm', 'sj_nm', 'account_nm', 'thstrm_amount']].rename(columns={
                'fs_nm': '재무제표명', 'sj_nm': '재무제표구분', 'account_nm': '계정명', 'thstrm_amount': '당기 금액'
            })
            st.dataframe(display_df, use_container_width=True)

            excel_filename = f"{corp_name}_재무제표_{fs_type}.xlsx"
            st.download_button("⬇️ 재무제표 Excel 다운로드", data=display_df.to_excel(index=False), file_name=excel_filename)
