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
    st.title("📊 실메뉴 추출기 (최근 3개월)")
    st.write("어느 곳에서든 매장의 DB 정보만 입력하면 데이터를 추출할 수 있습니다.")

    # ==========================================
    # 2. DB 접속 정보 수기 입력 화면
    # ==========================================
    st.divider()
    st.subheader("🔗 데이터베이스 접속 정보 입력")
    
    st.markdown("매장 PC의 외부 접속용 아이피를 모를 경우 아래 링크를 눌러 확인하세요.")
    st.markdown("[**👉 매장 PC 공인 IP 확인하기 (클릭)**](https://search.naver.com/search.naver?query=내아이피)", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        input_host = st.text_input("1. DB 주소 (공인 IP)", placeholder="예: 123.45.67.89")
        # 🔥 포트 번호 기본값을 17838로 변경했습니다!
        input_port = st.text_input("2. 포트 번호 (PORT)", value="17838") 
    with col2:
        input_user = st.text_input("3. DB 아이디 (ID)", placeholder="예: root")
        input_pass = st.text_input("4. DB 비밀번호 (PW)", type="password")

    st.divider()

    # ==========================================
    # 3. 데이터 조회 버튼 및 실행 로직
    # ==========================================
    if st.button("🚀 위 정보로 DB 연결 및 데이터 조회하기"):
        if not input_host or not input_port or not input_user or not input_pass:
            st.warning("아이피, 포트, 아이디, 비밀번호를 모두 입력해 주세요!")
        else:
            try:
                port_num = int(input_port)

                # DB 이름은 k_db로 고정
                conn = pymysql.connect(
                    host=input_host, 
                    port=port_num,
                    user=input_user, 
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
                st.error(f"원인: 아이피/비밀번호가 틀렸거나, 매장 공유기의 '포트포워딩'이 안 되어 있을 수 있습니다. (상세오류: {e})")
