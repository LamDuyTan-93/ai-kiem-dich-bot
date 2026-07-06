import streamlit as st
import os
import json
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.utilities import SQLDatabase
from langchain.chains import create_sql_query_chain
from google.oauth2 import service_account

# 1. THIẾT LẬP GIAO DIỆN ĐIỆN THOẠI
st.set_page_config(page_title="AI Giám Sát Kiểm Dịch", page_icon="🌿", layout="centered")

# 2. LẤY MÃ KHÓA TỪ "KÉT SẮT" CỦA MÁY CHỦ (Streamlit Secrets)
os.environ["GOOGLE_API_KEY"] = st.secrets["GOOGLE_API_KEY"]

# Đọc file JSON của BigQuery từ két sắt
bq_credentials_dict = json.loads(st.secrets["BIGQUERY_JSON"])
credentials = service_account.Credentials.from_service_account_info(bq_credentials_dict)

# TRỌNG TÂM: Bạn nhớ đổi tên Project và Dataset dưới đây nhé
PROJECT_ID = "ten-project-cua-ban" 
DATASET_ID = "ten_dataset_cua_ban" 

# 3. KẾT NỐI AI VÀ BIGQUERY
@st.cache_resource
def get_system():
    # Nối BigQuery
    bq_uri = f"bigquery://{PROJECT_ID}/{DATASET_ID}"
    db = SQLDatabase.from_uri(bq_uri, credentials_path=None, credentials_info=bq_credentials_dict)
    
    # Bật não AI Gemini Pro
    llm = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0)
    chain = create_sql_query_chain(llm, db)
    return db, chain

db, chain = get_system()

# 4. XÂY DỰNG GIAO DIỆN HIỂN THỊ
st.title("🌿 Trợ Lý AI: Hồ Sơ Kiểm Dịch 2025")

user_question = st.text_input("Nhập yêu cầu tra cứu (Ví dụ: Các lô sầu riêng vi phạm trong tháng này?):")

if st.button("🔍 Tra Cứu Dữ Liệu"):
    if user_question:
        with st.spinner('Hệ thống đang quét dữ liệu đám mây...'):
            try:
                # Dịch tiếng Việt sang SQL và chạy
                sql_query = chain.invoke({"question": f"Chỉ trả về câu lệnh SQL BigQuery cho câu hỏi: {user_question}"})
                result = db.run(sql_query)
                
                # Trả kết quả
                st.success("Đã tìm thấy dữ liệu!")
                st.write(result)
            except Exception as e:
                st.error("Câu hỏi hơi phức tạp hoặc dữ liệu không tồn tại. Vui lòng thử lại với từ khóa khác.")