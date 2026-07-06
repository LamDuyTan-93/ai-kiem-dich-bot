import streamlit as st
import os
import json
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.utilities import SQLDatabase
from sqlalchemy import create_engine

# 1. THIẾT LẬP GIAO DIỆN
st.set_page_config(page_title="AI Giám Sát Kiểm Dịch", page_icon="🌿", layout="centered")

# --- BỘ LỌC AN TOÀN API KEY ---
raw_api_key = st.secrets["GOOGLE_API_KEY"].strip()
raw_api_key = raw_api_key.replace('"', '').replace("'", "") 
if not raw_api_key.startswith("AIza"):
    st.error("🚨 LỖI MÃ KHÓA: Mã GOOGLE_API_KEY không hợp lệ.")
    st.stop()
os.environ["GOOGLE_API_KEY"] = raw_api_key

# --- BỘ LỌC AN TOÀN CHÌA KHÓA BIGQUERY ---
try:
    raw_json = st.secrets["BIGQUERY_JSON"].strip()
    bq_credentials_dict = json.loads(raw_json)
    bq_credentials_dict["private_key"] = bq_credentials_dict["private_key"].replace('\\n', '\n')
except Exception as e:
    st.error(f"🚨 LỖI FILE JSON: Két sắt bị sai. Chi tiết: {e}")
    st.stop()

# 2. CẤU HÌNH DỮ LIỆU
PROJECT_ID = "datagiamdinh" 
DATASET_ID = "demo1" # ---> NHỚ SỬA LẠI TÊN DATASET CỦA BẠN VÀO ĐÂY

# 3. KẾT NỐI AI VÀ BIGQUERY
@st.cache_resource
def get_system():
    # Kết nối BigQuery
    bq_uri = f"bigquery://{PROJECT_ID}/{DATASET_ID}"
    engine = create_engine(bq_uri, credentials_info=bq_credentials_dict)
    db = SQLDatabase(engine)
    
    # Bật AI Gemini 1.5 Flash bằng hệ thống giao tiếp mới nhất
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0)
    return db, llm

try:
    db, llm = get_system()
except Exception as e:
    st.error(f"Lỗi kết nối cơ sở dữ liệu: {e}")
    st.stop()

# 4. GIAO DIỆN HIỂN THỊ
st.title("🌿 Trợ Lý AI: Hồ Sơ Kiểm Dịch 2025")

user_question = st.text_input("Nhập yêu cầu tra cứu (Ví dụ: Từ tháng 8 đến tháng 9 có bao nhiêu lô hàng gạo?):")

if st.button("🔍 Tra Cứu Dữ Liệu"):
    if user_question:
        with st.spinner('Hệ thống đang quét dữ liệu đám mây...'):
            try:
                # Trích xuất cấu trúc bảng
                schema = db.get_table_info()
                
                # Trò chuyện trực tiếp với AI (Không qua trung gian)
                prompt_context = f"""
                Bạn là chuyên gia dữ liệu BigQuery. Dưới đây là cấu trúc các bảng dữ liệu của tôi:
                {schema}
                
                Dựa vào cấu trúc trên, hãy viết một câu lệnh SQL chuẩn xác để trả lời câu hỏi: {user_question}
                Chỉ trả về đúng câu lệnh SQL, KHÔNG giải thích, KHÔNG dùng thẻ markdown ```sql.
                """
                
                # Gọi AI
                response = llm.invoke(prompt_context)
                
                # Dọn dẹp mã SQL
                sql_query = response.content.replace("```sql", "").replace("```", "").strip()
                
                # Chạy SQL và lấy kết quả
                result = db.run(sql_query)
                
                st.success("Đã tìm thấy dữ liệu!")
                st.code(sql_query, language="sql")
                st.write("**Kết quả:**", result)
                
            except Exception as e:
                st.error(f"Gặp sự cố khi phân tích. Chi tiết lỗi: {e}")
