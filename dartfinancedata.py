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
            for item in root.findall('list') if item.find('stock_code').text
        ]
        return pd.DataFrame(data)
    return pd.DataFrame()

# ✅ 공시 리스트 불러오기
def get_report_list(corp_code, bgn_de, end_de, report_tp):
    url = (
        f"https://opendart.fss.or.kr/api/list.json"
        f"?crtfc_key={API_KEY}&corp_code={corp_code}&bgn_de={bgn_de}&end_de={end_de}&pblntf_detail_ty={report_tp}"
    )
    res = requests.get(url)
    return res.json()

# ✅ Streamlit UI 시작
st.set_page_config(page_title="📄 오픈DART 공시 조회기", layout="wide")
st.title("📄 오픈 DART API를 통한 공시 보고서 조회")

# 날짜 범위 선택
today = datetime.date.today()
def_year = str(today.year - 1)
start_date = st.date_input("검색 시작일", datetime.date(today.year - 1, 1, 1))
end_date = st.date_input("검색 종료일", today)
report_type = st.selectbox("공시유형 선택", options=[("사업보고서", "A001"), ("반기보고서", "A002"), ("분기보고서", "A003")], format_func=lambda x: x[0])

# 종목코드 입력 및 조회
stock_input = st.text_input("📌 종목코드 또는 기업명 입력 (예: 005930 또는 삼성전자)", value="005930")
if 'corp_df' not in st.session_state:
    with st.spinner("상장기업 목록 불러오는 중..."):
        st.session_state.corp_df = load_corp_codes()

corp_df = st.session_state.corp_df

if st.button("🔍 공시자료 조회"):
    # 종목코드 또는 기업명으로 검색
    match_df = corp_df[(corp_df['stock_code'] == stock_input) | (corp_df['corp_name'].str.contains(stock_input))]

    if match_df.empty:
        st.error("❌ 해당 종목코드 또는 기업명을 찾을 수 없습니다.")
    elif len(match_df) > 1:
        st.warning("⚠️ 검색 결과가 여러 건입니다. 좀 더 구체적인 이름을 입력해주세요.")
        st.dataframe(match_df)
    else:
        corp_code = match_df.iloc[0]['corp_code']
        corp_name = match_df.iloc[0]['corp_name']
        st.info(f"✅ 조회 대상: {corp_name} ({stock_input})")

        bgn_de = start_date.strftime('%Y%m%d')
        end_de = end_date.strftime('%Y%m%d')
        report_tp = report_type[1]

        with st.spinner("📡 DART로부터 데이터 수신 중..."):
            result = get_report_list(corp_code, bgn_de, end_de, report_tp)

        if result.get("status") == "013":
            st.warning("❌ 해당 기간에 제출된 공시가 없습니다.")
        elif result.get("status") != "000":
            st.error(f"🚫 오류 발생: {result.get('message')}")
        else:
            report_df = pd.DataFrame(result['list'])
            report_df = report_df[['rcept_no', 'report_nm', 'rcept_dt', 'flr_nm', 'rm']]
            report_df['접수일'] = pd.to_datetime(report_df['rcept_dt'])
            report_df['공시링크'] = report_df['rcept_no'].apply(lambda x: f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={x}")
            st.success(f"📄 총 {len(report_df)}건의 보고서가 조회되었습니다.")
            st.dataframe(report_df[['접수일', 'report_nm', 'flr_nm', '공시링크']], use_container_width=True)

            csv = report_df.to_csv(index=False).encode('utf-8-sig')
            st.download_button("⬇️ 보고서 목록 CSV 다운로드", data=csv, file_name=f"{corp_name}_dart_reports.csv")