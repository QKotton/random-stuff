import streamlit as st
from pypdf import PdfReader
import re
import pandas as pd

# 1. Cấu hình trang Web
st.set_page_config(page_title="Công cụ Phân tích PDF chuyên sâu", layout="wide")

# --- PHẦN MỚI: CSS ĐỂ CHỈNH MÀU BẢNG ---
st.markdown("""
    <style>
    /* Ép nền của bảng thành màu đen và chữ thành màu trắng */
    .stDataFrame div[data-testid="stTable"] {
        background-color: #121212 !important;
    }
    .stDataFrame table {
        color: white !important;
        background-color: #121212 !important;
    }
    th {
        background-color: #333333 !important;
        color: white !important;
    }
    td {
        background-color: #1E1E1E !important;
        color: white !important;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("📊 Phân tích Mật độ Từ khóa trong PDF")

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
    
    show_percent = st.checkbox("Hiển thị tỷ lệ phần trăm (%)", value=True)
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
        
        # Đếm tổng số từ
        total_words = len(re.findall(r'\b\w+\b', text_content))
        text_content = text_content.lower()
        
        counts = {}
        percents = {}
        for word in keywords:
            word = word.strip().lower()
            if not word: continue
            
            pattern = r'(?<!\w)' + re.escape(word) + r'(?!\w)'
            count = len(re.findall(pattern, text_content))
            counts[word] = count
            
            if total_words > 0:
                percents[f"{word} (%)"] = round((count / total_words) * 100, 4)
            else:
                percents[f"{word} (%)"] = 0
            
        return counts, percents, total_words, None
    except Exception as e:
        return {}, {}, 0, str(e)

# 4. Xử lý chính khi bấm nút
if btn_process:
    if not uploaded_files:
        st.warning("Vui lòng tải lên ít nhất một file PDF!")
    elif not keywords_input.strip():
        st.warning("Vui lòng nhập từ khóa!")
    else:
        keywords_list = [k.strip() for k in keywords_input.split(',') if k.strip()]
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        all_results = []
        
        for i, pdf_file in enumerate(uploaded_files):
            status_text.text(f"Đang xử lý: {pdf_file.name}...")
            progress_bar.progress((i + 1) / len(uploaded_files))
            
            counts, percents, total_count, error = count_words_in_pdf(pdf_file, keywords_list)
            
            if error:
                st.error(f"Lỗi file {pdf_file.name}: {error}")
            else:
                row = {"Tên File": pdf_file.name, "Tổng số từ": total_count}
                row.update(counts)
                if show_percent:
                    row.update(percents)
                all_results.append(row)

        progress_bar.empty()
        status_text.success("Hoàn tất phân tích!")
        
        if all_results:
            st.divider()
            st.subheader("Bảng kết quả phân tích")
            
            df = pd.DataFrame(all_results)
            
            # --- PHẦN CHỈNH STYLE CHO DATAFRAME ---
            # Sử dụng định dạng màu tối để tương phản với chữ trắng
            styled_df = df.style.set_properties(**{
                'background-color': '#1E1E1E',
                'color': 'white',
                'border-color': '#444444'
            }).highlight_max(axis=0, color='#004d99') # Highlight xanh đậm cho dễ nhìn trên nền tối
            
            st.dataframe(styled_df, use_container_width=True)
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Tổng số file", len(all_results))
            col2.metric("Tổng số từ", f"{df['Tổng số từ'].sum():,}")
            col3.info("Bảng đã được chuyển sang chế độ màu tối (Dark) để dễ đọc chữ trắng.")

            csv = df.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="📥 Tải kết quả về máy (CSV)",
                data=csv,
                file_name="ket_qua_phan_tich.csv",
                mime="text/csv",
            )