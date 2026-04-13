import streamlit as st
import pymysql
import pandas as pd
from datetime import datetime
import io

# ==========================================
# 1. 관리자 로그인 페이지
# ==========================================
def check_password():
    def password_entered():
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
    st.title("📊 실메뉴 추출기 (내 PC 전용)")
    st.write("내 PC에 설치된 DB에서 데이터를 바로 추출합니다.")

    # ==========================================
    # 2. DB 접속 정보 (비밀번호만 입력)
    # ==========================================
    st.divider()
    st.subheader("🔗 데이터베이스 접속")
    
    # 🔥 나머지 정보는 코드 내부에 숨겨서 고정합니다!
    fixed_host = "127.0.0.1"
    fixed_port = 17838
    fixed_user = "root"

    # 화면에는 오직 비밀번호 칸만 보여줍니다.
    input_pass = st.text_input("DB 비밀번호를 입력해 주세요 (PW)", type="password")

    st.divider()

    # ==========================================
    # 3. 데이터 조회 버튼 및 실행 로직
    # ==========================================
    if st.button("🚀 데이터 조회하기"):
        if not input_pass:
            st.warning("비밀번호를 입력해 주세요!")
        else:
            try:
                # 고정된 정보와 화면에서 입력받은 비밀번호를 합쳐서 연결합니다.
                conn = pymysql.connect(
                    host=fixed_host, 
                    port=fixed_port,
                    user=fixed_user, 
                    password=input_pass, 
                    db="k_db", 
                    charset='utf8'
                )
                
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
                
                df = pd.read_sql(sql, conn)
                conn.close()

                st.success(f"성공! 총 {len(df)}개의 메뉴 데이터를 성공적으로 불러왔습니다!")
                
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
                st.error("데이터베이스 접속에 실패했습니다.")
                st.error(f"원인: DB가 실행 중이 아니거나 비밀번호가 틀렸습니다. (상세오류: {e})")
