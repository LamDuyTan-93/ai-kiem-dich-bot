import streamlit as st
import os
import json
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.utilities import SQLDatabase
from langchain.chains import create_sql_query_chain
from google.oauth2 import service_account
from sqlalchemy import create_engine

# 1. THIẾT LẬP GIAO DIỆN ĐIỆN THOẠI
st.set_page_config(page_title="AI Giám Sát Kiểm Dịch", page_icon="🌿", layout="centered")

# 2. LẤY MÃ KHÓA TỪ "KÉT SẮT" CỦA MÁY CHỦ
os.environ["GOOGLE_API_KEY"] = st.secrets["GOOGLE_API_KEY"]

# Đọc file JSON của BigQuery
bq_credentials_dict = json.loads(st.secrets["BIGQUERY_JSON"])
credentials = service_account.Credentials.from_service_account_info(bq_credentials_dict)

PROJECT_ID = "datagiamdinh" 
DATASET_ID = "demo1" # Hãy nhớ thay tên dataset thật của bạn vào đây

# 3. KẾT NỐI AI VÀ BIGQUERY (Đã fix lỗi kết nối xác thực)
@st.cache_resource
def get_system():
    # Tạo engine kết nối an toàn với BigQuery thông qua thư viện gốc
    bq_uri = f"bigquery://{PROJECT_ID}/{DATASET_ID}"
    engine = create_engine(bq_uri, credentials_info=bq_credentials_dict)
    db = SQLDatabase(engine)
    
    # Bật não AI Gemini Pro
    llm = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0)
    chain = create_sql_query_chain(llm, db)
    return db, chain

try:
    db, chain = get_system()
except Exception as e:
    st.error(f"Lỗi kết nối cơ sở dữ liệu: {e}")
    st.stop()

# 4. XÂY DỰNG GIAO DIỆN HIỂN THỊ
st.title("🌿 Trợ Lý AI: Hồ Sơ Kiểm Dịch 2025")

user_question = st.text_input("Nhập yêu cầu tra cứu (Ví dụ: Có bao nhiêu lô thanh long vi phạm?):")

if st.button("🔍 Tra Cứu Dữ Liệu"):
    if user_question:
        with st.spinner('Hệ thống đang quét dữ liệu đám mây...'):
            try:
                # Ép AI hiểu ngữ cảnh để viết SQL chuẩn xác hơn
                prompt_context = f"""
                Bạn là chuyên gia dữ liệu BigQuery. Bảng dữ liệu chứa hồ sơ giám định. 
                Hãy viết một câu lệnh SQL chuẩn xác để trả lời câu hỏi: {user_question}
                Chỉ trả về đúng câu lệnh SQL, KHÔNG giải thích.
                """
                sql_query = chain.invoke({"question": prompt_context})
                
                result = db.run(sql_query)
                
                st.success("Đã tìm thấy dữ liệu!")
                st.code(sql_query, language="sql") # Tùy chọn: Hiện code SQL ra cho sếp xem (có thể bỏ đi)
                st.write("**Kết quả truy xuất:**")
                st.write(result)
            except Exception as e:
                st.error(f"Hệ thống gặp khó khăn khi phân tích câu hỏi. Chi tiết lỗi: {e}")
