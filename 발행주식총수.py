import pandas as pd
from pykrx import stock
import re

# 📥 사용자 입력
stock_input = input("조회할 종목명 또는 종목코드를 입력하세요 (예: 삼성전자 또는 005930): ").strip()
year_input = input("조회할 연도 (기본값: 2021): ").strip()
year = year_input if re.match(r'^\d{4}$', year_input) else '2021'

# 🧭 종목명 또는 종목코드 확인
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
    raise ValueError(f"❌ '{stock_input}'에 해당하는 종목명을 찾을 수 없습니다.")

# 📊 pykrx에서 발행주식총수 조회
end_date = f"{year}1231"
cap_df = stock.get_market_cap_by_date(end_date, end_date, matched_code)

if cap_df.empty:
    raise ValueError(f"❌ {year}년 데이터가 존재하지 않습니다.")

issued_shares = int(cap_df['상장주식수'].values[0])

# ✅ 결과 출력
print(f"\n[조회결과] {stock_name} ({matched_code})")
print(f"{year}년 기준 발행주식총수: {issued_shares:,}주")