import streamlit as st
import os
import json
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.utilities import SQLDatabase
from langchain.chains import create_sql_query_chain
from sqlalchemy import create_engine

# 1. THIẾT LẬP GIAO DIỆN ĐIỆN THOẠI
st.set_page_config(page_title="AI Giám Sát Kiểm Dịch", page_icon="🌿", layout="centered")

# --- BỘ LỌC AN TOÀN API KEY ---
raw_api_key = st.secrets["GOOGLE_API_KEY"].strip()
raw_api_key = raw_api_key.replace('"', '').replace("'", "") 

if not raw_api_key.startswith("AIza"):
    st.error("🚨 LỖI MÃ KHÓA: Mã GOOGLE_API_KEY không hợp lệ. Vui lòng kiểm tra lại Két sắt (Secrets).")
    st.stop()
    
os.environ["GOOGLE_API_KEY"] = raw_api_key

# --- BỘ LỌC AN TOÀN CHÌA KHÓA BIGQUERY ---
try:
    raw_json = st.secrets["BIGQUERY_JSON"].strip()
    bq_credentials_dict = json.loads(raw_json)
    
    # BƯỚC KHẮC PHỤC CHÌA KHÓA: Tự động chuyển đổi '\n' thành xuống dòng thực sự
    bq_credentials_dict["private_key"] = bq_credentials_dict["private_key"].replace('\\n', '\n')
    
except Exception as e:
    st.error(f"🚨 LỖI FILE JSON: Cấu trúc Két sắt bị sai. Chi tiết: {e}")
    st.stop()

# 2. CẤU HÌNH DỮ LIỆU
PROJECT_ID = "datagiamdinh" 
DATASET_ID = "demo1" # ---> NHỚ SỬA TÊN DATASET CỦA BẠN VÀO ĐÂY 

# 3. KẾT NỐI AI VÀ BIGQUERY
@st.cache_resource
def get_system():
    # Tạo kết nối an toàn với BigQuery
    bq_uri = f"bigquery://{PROJECT_ID}/{DATASET_ID}"
    engine = create_engine(bq_uri, credentials_info=bq_credentials_dict)
    db = SQLDatabase(engine)
    
    # Bật não AI Gemini 1.5 Pro (Đã cập nhật model mới nhất để tránh lỗi 404)
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash-latest", temperature=0)
    chain = create_sql_query_chain(llm, db)
    return db, chain

try:
    db, chain = get_system()
except Exception as e:
    st.error(f"Lỗi kết nối cơ sở dữ liệu: {e}")
    st.stop()

# 4. GIAO DIỆN HIỂN THỊ
st.title("🌿 Trợ Lý AI: Hồ Sơ Kiểm Dịch 2025")

user_question = st.text_input("Nhập yêu cầu tra cứu (Ví dụ: Có bao nhiêu lô thanh long vi phạm?):")

if st.button("🔍 Tra Cứu Dữ Liệu"):
    if user_question:
        with st.spinner('Hệ thống đang quét dữ liệu đám mây (Có thể mất 30s cho lần đầu tiên)...'):
            try:
                # Ép AI hiểu ngữ cảnh để viết SQL chuẩn xác hơn
                prompt_context = f"""
                Bạn là chuyên gia dữ liệu BigQuery. Bảng dữ liệu chứa hồ sơ giám định. 
                Hãy viết một câu lệnh SQL chuẩn xác để trả lời câu hỏi: {user_question}
                Chỉ trả về đúng câu lệnh SQL, KHÔNG giải thích, không dùng markdown ```sql.
                """
                sql_query = chain.invoke({"question": prompt_context})
                
                # Dọn dẹp câu lệnh SQL nếu AI lỡ bọc thêm markdown định dạng
                sql_query = sql_query.replace("```sql", "").replace("```", "").strip()
                
                result = db.run(sql_query)
                
                st.success("Đã tìm thấy dữ liệu!")
                st.code(sql_query, language="sql")
                st.write("**Kết quả:**", result)
            except Exception as e:
                st.error(f"Gặp sự cố khi phân tích. Lời khuyên: Hãy thử đặt câu hỏi ngắn gọn hơn bằng các từ khóa có trong tiêu đề cột. Chi tiết lỗi: {e}")
