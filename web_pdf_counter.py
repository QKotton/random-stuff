import streamlit as st
from pypdf import PdfReader
import re
import pandas as pd
# 1. Cấu hình trang Web (Dòng này phải để đầu tiên sau import)
st.set_page_config(page_title="Công cụ Đếm từ PDF", layout="wide")
st.title("Công cụ Quét & Đếm từ trong file PDF")
# 2. Cột bên trái: Khu vực nhập liệu
with st.sidebar:
    st.header("Tải file & Cấu hình")
    uploaded_files = st.file_uploader(
        "Chọn các file PDF", 
        type=['pdf'], 
        accept_multiple_files=True
    )
    
    st.header("Từ khóa cần đếm")
    keywords_input = st.text_area(
        "Nhập từ khóa (phân cách bằng dấu phẩy):", 
        value="doanh thu, lợi nhuận, tăng trưởng",
        height=100
    )
    
    btn_process = st.button("Bắt đầu Phân tích", type="primary")

# 3. Hàm xử lý logic đọc PDF
def count_words_in_pdf(uploaded_file, keywords):
    text_content = ""
    try:
        reader = PdfReader(uploaded_file)
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text_content += extracted + " "
        
        text_content = text_content.lower()
        
        counts = {}
        for word in keywords:
            word = word.strip().lower()
            if not word: 
                continue
            
            # Regex đếm từ chính xác
            pattern = r'(?<!\w)' + re.escape(word) + r'(?!\w)'
            count = len(re.findall(pattern, text_content))
            counts[word] = count
            
        return counts, None
    except Exception as e:
        return {}, str(e)

# 4. Xử lý chính khi bấm nút
if btn_process:
    if not uploaded_files:
        st.warning("Vui lòng tải lên ít nhất một file PDF!")
    elif not keywords_input.strip():
        st.warning("Vui lòng nhập từ khóa!")
    else:
        # Chuẩn bị danh sách từ khóa
        keywords_list = [k.strip() for k in keywords_input.split(',') if k.strip()]
        
        # Thanh tiến trình
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        all_results = []
        
        # Vòng lặp xử lý từng file
        for i, pdf_file in enumerate(uploaded_files):
            status_text.text(f"Đang xử lý: {pdf_file.name}...")
            progress_bar.progress((i + 1) / len(uploaded_files))
            
            counts, error = count_words_in_pdf(pdf_file, keywords_list)
            
            if error:
                st.error(f"Lỗi file {pdf_file.name}: {error}")
            else:
                row = {"Tên File": pdf_file.name}
                row.update(counts)
                all_results.append(row)

        progress_bar.empty()
        status_text.text("Hoàn tất!")
        
        # Hiển thị kết quả
        if all_results:
            st.divider()
            st.subheader("Kết quả chi tiết")
            
            df = pd.DataFrame(all_results)
            st.dataframe(df, use_container_width=True)
            
            # Nút tải xuống CSV
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Tải kết quả (CSV)",
                data=csv,
                file_name="ket_qua_dem_tu.csv",
                mime="text/csv",
            )