import streamlit as st
import google.generativeai as genai
from google.cloud import bigquery
import os

# 1. CẤU HÌNH API
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
model = genai.GenerativeModel('gemini-1.5-flash')

# 2. GIAO DIỆN
st.title("🌿 Trợ Lý AI: Kiểm Dịch")
question = st.text_input("Nhập yêu cầu tra cứu:")

if st.button("🔍 Tra Cứu"):
    with st.spinner('Đang phân tích...'):
        # Yêu cầu AI viết SQL dựa trên mô tả bảng của bạn
        prompt = f"Bạn là chuyên gia SQL. Hãy viết câu lệnh SQL cho câu hỏi này: {question}. Chỉ trả về code SQL."
        response = model.generate_content(prompt)
        sql = response.text.replace("```sql", "").replace("```", "").strip()
        
        st.code(sql)
        # Tại đây bạn có thể dùng client của bigquery để thực thi sql
        st.write("SQL đã tạo thành công, bạn hãy chạy câu lệnh này trong BigQuery.")
