pip install dart-fss
import datetime
import dart_fss as dart

#dart api 키 설정
api_key='9c188bb242aa2d1d9cd78eb8692f50aeb963704a'
dart.set_api_key(api_key=api_key)

# 모든 상장된 기업 리스트 불러오기
corp_list = dart.get_corp_list()

#현재날짜 
now = datetime.datetime.now()
nowDate = now.strftime('%Y%m%d%H%M')

#검색시작날짜 
bgn_de = '20200101'

#검색종료 날짜
end_de = now.strftime('%Y%m%d')

# 종목검색 (주식코드)
stock_code = '010130'
company = corp_list.find_by_stock_code(stock_code, include_delisting=False)

print(company)
corp_name = print(company)

# 연결재무제표 불러오기 
#report  = 연간 ('annual') 반기 ('half') 분기('quarter')
report = 'quarter'
fs = company.extract_fs(bgn_de=bgn_de, end_de=end_de, report_tp=report, lang='ko', separator=False)

# 연결재무상태표
df_fs = fs['bs'] # 또는 df = fs[0] 또는 df = fs.show('bs')
# 연결재무상태표 추출에 사용된 Label 정보
labels_fs = fs.labels['bs']

# 연결손익계산서
df_is = fs['is'] # 또는 df = fs[1] 또는 df = fs.show('is')
# 연결손익계산서 추출에 사용된 Label 정보
labels_is = fs.labels['is']

# 연결포괄손익계산서
df_ci = fs['cis'] # 또는 df = fs[2] 또는 df = fs.show('cis')
# 연결포괄손익계산서 추출에 사용된 Label 정보
labels_ci = fs.labels['cis']

# 현금흐름표
df_cf = fs['cf'] # 또는 df = fs[3] 또는 df = fs.show('cf')
# 현금흐름표 추출에 사용된 Label 정보
labels_cf = fs.labels['cf']

# 재무제표 검색 결과를 엑셀파일로 저장
filename = corp_name+'_'+nowDate+'.xlsx'
fs.save(filename=filename)
