import streamlit as st
import pymysql
import pandas as pd
from datetime import datetime
import io

# ==========================================
# 1. 관리자 로그인 페이지
# ==========================================
def check_password():
    """비밀번호 검증 로직"""
    def password_entered():
        # ID: admin / PW: 1234 (필요시 변경하세요)
        if st.session_state["username"] == "admin" and st.session_state["password"] == "1234":
            st.session_state["password_correct"] = True
            del st.session_state["password"] 
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input("아이디", key="username")
        st.text_input("비밀번호", type="password", key="password")
        st.button("로그인", on_click=password_entered)
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("아이디", key="username")
        st.text_input("비밀번호", type="password", key="password")
        st.button("로그인", on_click=password_entered)
        st.error("😕 아이디나 비밀번호가 틀렸습니다.")
        return False
    else:
        return True

if check_password():
    st.title("📊 실메뉴 추출기 (최근 3개월)")
    st.write("최근 3개월간 판매된 상품의 고유 정보, 최종 판매일, 판매 수량을 조회합니다.")

    # ==========================================
    # 2. DB 연결 정보 (웹에서 접속 가능한 DB 주소여야 합니다)
    # ==========================================
    # Streamlit Cloud의 Secrets 기능이나 직접 입력으로 관리 가능합니다.
    DB_HOST = "여기에_DB_아이피_주소_입력" 
    DB_USER = "여기에_DB_아이디_입력"      
    DB_PASS = "여기에_DB_비밀번호_입력" 
    DB_NAME = "여기에_DB_이름_입력" 

    # ==========================================
    # 3. 데이터 조회 버튼 및 SQL 실행
    # ==========================================
    if st.button("데이터 조회하기"):
        try:
            # DB 연결
            conn = pymysql.connect(host=DB_HOST, user=DB_USER, password=DB_PASS, db=DB_NAME, charset='utf8')
            
            # 새롭게 업데이트된 SQL (최종 판매일, 판매 수량 추가)
            sql = """
            SELECT 
                G.cGoodcd AS '상품코드',
                G.cgoodNm AS '상품명',
                G.fSalePrc AS '상품가격',
                G.cType01 AS '주방출력 여부1',
                G.cType02 AS '주방출력 여부2',
                MAX(S.cDate) AS '최종 판매일',
                COUNT(S.cGoodcd) AS '판매 수량'
            FROM sale1100 S
            JOIN good1000 G ON S.cGoodcd = G.cGoodcd
            WHERE S.cDate >= DATE_SUB(CURDATE(), INTERVAL 3 MONTH)
            GROUP BY 
                G.cGoodcd, 
                G.cgoodNm, 
                G.fSalePrc, 
                G.cType01, 
                G.cType02;
            """
            
            # DB에서 데이터를 가져와 표(DataFrame)로 만들기
            df = pd.read_sql(sql, conn)
            conn.close()

            st.success(f"총 {len(df)}개의 메뉴 데이터를 성공적으로 불러왔습니다!")
            
            # ==========================================
            # 4. 화면에 데이터 표기 및 엑셀 다운로드
            # ==========================================
            st.dataframe(df, use_container_width=True)

            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='실메뉴_추출_데이터')
            
            st.download_button(
                label="📥 엑셀 파일로 다운로드",
                data=buffer.getvalue(),
                file_name=f"실메뉴_추출기_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.ms-excel"
            )

        except Exception as e:
            st.error(f"데이터베이스 연결 또는 조회 중 오류가 발생했습니다: {e}")
