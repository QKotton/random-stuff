import streamlit as st
from pypdf import PdfReader
import re
import pandas as pd

# 1. Cấu hình trang Web
st.set_page_config(page_title="Công cụ Phân tích PDF chuyên sâu", layout="wide")
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
    
    # Thêm tùy chọn hiển thị phần trăm
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
        
        # Đếm tổng số từ (Word Count)
        total_words = len(re.findall(r'\b\w+\b', text_content))
        
        text_content = text_content.lower()
        
        counts = {}
        percents = {}
        for word in keywords:
            word = word.strip().lower()
            if not word: continue
            
            # Regex đếm từ chính xác
            pattern = r'(?<!\w)' + re.escape(word) + r'(?!\w)'
            count = len(re.findall(pattern, text_content))
            counts[word] = count
            
            # Tính phần trăm (làm tròn 4 chữ số thập phân)
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
                # Tạo hàng dữ liệu cơ bản
                row = {
                    "Tên File": pdf_file.name,
                    "Tổng số từ": total_count
                }
                
                # Thêm số lần xuất hiện
                row.update(counts)
                
                # Nếu người dùng muốn xem phần trăm, thêm các cột phần trăm
                if show_percent:
                    row.update(percents)
                
                all_results.append(row)

        progress_bar.empty()
        status_text.success("Hoàn tất phân tích!")
        
        if all_results:
            st.divider()
            st.subheader("Bảng kết quả phân tích")
            
            df = pd.DataFrame(all_results)
            
            # Làm đẹp bảng hiển thị
            st.dataframe(df.style.highlight_max(axis=0, color='#e6f3ff'), use_container_width=True)
            
            # Hiển thị thống kê tổng quát
            col1, col2, col3 = st.columns(3)
            col1.metric("Tổng số file", len(all_results))
            col2.metric("Tổng số từ", f"{df['Tổng số từ'].sum():,}")
            col3.info("Mẹo: Bạn có thể nhấn vào tiêu đề cột để sắp xếp!")

            # Nút tải xuống CSV
            csv = df.to_csv(index=False).encode('utf-8-sig') # Dùng utf-8-sig để Excel không lỗi font tiếng Việt
            st.download_button(
                label="📥 Tải kết quả về máy (CSV)",
                data=csv,
                file_name="phat_hien_tu_khoa_pdf.csv",
                mime="text/csv",
            )
