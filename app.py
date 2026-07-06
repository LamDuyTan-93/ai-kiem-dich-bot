import streamlit as st
import google.generativeai as genai
from google.cloud import bigquery
import os
import json

# 1. THIẾT LẬP GIAO DIỆN
st.set_page_config(page_title="AI Giám Sát Kiểm Dịch", page_icon="🌿", layout="centered")

# 2. XỬ LÝ KHÓA BẢO MẬT (Dọn dẹp rác)
try:
    api_key = st.secrets["GOOGLE_API_KEY"].strip().replace('"', '').replace("'", "")
    genai.configure(api_key=api_key)
    
    # Cấu hình BigQuery từ JSON
    raw_json = st.secrets["BIGQUERY_JSON"].strip()
    bq_creds = json.loads(raw_json)
    # Lưu tạm file json để BigQuery Client nhận diện
    with open("service_account.json", "w") as f:
        json.dump(bq_creds, f)
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "service_account.json"
except Exception as e:
    st.error(f"Lỗi cấu hình Két sắt: {e}")
    st.stop()

# 3. KHỞI TẠO AI VÀ BIGQUERY
# Sử dụng mô hình 'gemini-1.5-flash' với đường dẫn chuẩn models/
model = genai.GenerativeModel(model_name="models/gemini-1.5-flash")
bq_client = bigquery.Client()

# 4. GIAO DIỆN CHÍNH
st.title("🌿 Trợ Lý AI: Kiểm Dịch 2025")
user_question = st.text_input("Nhập câu hỏi tra cứu:")

if st.button("🔍 Tra Cứu"):
    if user_question:
        with st.spinner('Đang phân tích dữ liệu...'):
            try:
                # Bước A: AI viết SQL
                prompt = f"Viết lệnh SQL truy vấn BigQuery cho câu hỏi: '{user_question}'. Chỉ trả về mã SQL, không giải thích."
                response = model.generate_content(prompt)
                sql_query = response.text.replace("```sql", "").replace("```", "").strip()
                
                # Bước B: Thực thi SQL
                query_job = bq_client.query(sql_query)
                results = query_job.result()
                
                # Bước C: Hiển thị
                st.success("Kết quả truy vấn:")
                st.code(sql_query, language="sql")
                for row in results:
                    st.write(dict(row))
                    
            except Exception as e:
                st.error(f"Lỗi thực thi: {e}")
