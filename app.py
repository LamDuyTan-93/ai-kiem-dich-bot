import streamlit as st
import google.generativeai as genai
from google.cloud import bigquery
import os
import json

# 1. CẤU HÌNH GIAO DIỆN
st.set_page_config(page_title="AI Kiểm Dịch 2025", page_icon="🌿")
st.title("🌿 Trợ Lý AI: Hồ Sơ Kiểm Dịch")

# 2. XỬ LÝ KHÓA BẢO MẬT (Dọn rác & Khởi tạo)
@st.cache_resource
def init_clients():
    # Load API Key
    api_key = st.secrets["GOOGLE_API_KEY"].strip().replace('"', '').replace("'", "")
    genai.configure(api_key=api_key)
    
    # Load BQ JSON
    raw_json = st.secrets["BIGQUERY_JSON"].strip()
    bq_creds = json.loads(raw_json)
    
    # Lưu credential tạm thời
    with open("service_account.json", "w") as f:
        json.dump(bq_creds, f)
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "service_account.json"
    
    # Khởi tạo clients
    model = genai.GenerativeModel("models/gemini-1.5-flash")
    bq_client = bigquery.Client()
    return model, bq_client

try:
    model, bq_client = init_clients()
except Exception as e:
    st.error(f"Lỗi khởi tạo: {e}")
    st.stop()

# 3. GIAO DIỆN CHỨC NĂNG
user_input = st.text_input("Nhập yêu cầu tra cứu (Ví dụ: Có bao nhiêu lô thanh long?):")

if st.button("🔍 Tra Cứu"):
    if user_input:
        with st.spinner('AI đang phân tích và truy vấn...'):
            try:
                # Prompt hướng dẫn AI viết SQL
                prompt = f"""
                Bạn là chuyên gia dữ liệu BigQuery. Hãy viết câu lệnh SQL để trả lời câu hỏi: '{user_input}'.
                Chỉ trả về mã SQL, không giải thích.
                """
                
                # Gọi Gemini
                response = model.generate_content(prompt)
                sql_query = response.text.replace("```sql", "").replace("```", "").strip()
                
                # Hiển thị SQL đã tạo
                st.code(sql_query, language="sql")
                
                # Thực thi SQL trên BigQuery
                query_job = bq_client.query(sql_query)
                results = query_job.result()
                
                # Hiển thị kết quả
                st.success("Kết quả truy vấn:")
                for row in results:
                    st.write(dict(row))
                    
            except Exception as e:
                st.error(f"Lỗi hệ thống: {e}")
