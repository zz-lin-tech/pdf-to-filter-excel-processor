import streamlit as st
import pdfplumber
import pandas as pd
import os
import tempfile


def process_pdfs(pdf_files):
    all_data = []

    for pdf_path in pdf_files:
        with pdfplumber.open(pdf_path) as pdf:
            data = []
            file_name = os.path.basename(pdf_path).replace('.pdf', '')
            for page in pdf.pages:
                tables = page.extract_tables()
                if tables:
                    for table in tables:
                        for row in table:
                            cleaned_row = [cell.replace('\n', '') if isinstance(cell, str) else cell for cell in row]
                            data.append(cleaned_row)

            df = pd.DataFrame(data)
            start_indices = df[df.apply(lambda row: row.astype(str).str.contains('表体').any(), axis=1)].index
            end_indices = df[df.apply(lambda row: row.astype(str).str.contains('报关单草稿').any(), axis=1)].index

            if len(start_indices) > 0 and len(end_indices) > 0:
                start_index = start_indices[0] + 2
                end_index = end_indices[0]
                df_filtered = df.iloc[start_index:end_index]
                df_filtered.columns = df_filtered.iloc[0]
                df_filtered = df_filtered[1:]
                columns_to_keep = ["备案序号", "申报数量", "申报总价"]
                df_filtered = df_filtered[columns_to_keep]
                df_filtered["信息来源"] = file_name
                df_filtered["备案序号"] = pd.to_numeric(df_filtered["备案序号"], errors='coerce')
                df_filtered["申报数量"] = pd.to_numeric(df_filtered["申报数量"], errors='coerce')
                df_filtered["申报总价"] = pd.to_numeric(df_filtered["申报总价"], errors='coerce')
                all_data.append(df_filtered)

    combined_df = pd.concat(all_data, ignore_index=True)
    combined_df["累计申报数量"] = combined_df.groupby("备案序号")["申报数量"].transform('sum')
    combined_df["累计申报总价"] = combined_df.groupby("备案序号")["申报总价"].transform('sum')
    combined_df = combined_df.drop_duplicates(subset=["备案序号"])
    columns_to_keep_0 = ["备案序号", "累计申报数量", "累计申报总价"]
    combined_df = combined_df[columns_to_keep_0]
    full_index = pd.Index(range(1, 501), name="备案序号")
    combined_df = combined_df.set_index("备案序号").reindex(full_index).reset_index()
    combined_df = combined_df.sort_values(by="备案序号")
    return combined_df


st.title('PDF to Excel Processor')
# 添加使用说明
st.markdown("""
### 使用说明
1. 点击 **Browse files** 按钮上传一个或多个 PDF 文件。
2. 上传完成后，点击 **Process** 按钮处理文件。
3. 处理完成后，点击 **Download Excel file** 按钮下载生成的 Excel 文件。
""")

# 添加使用说明
st.markdown("""
### 使用说明
1. 点击 **Browse files** 按钮上传一个或多个 PDF 文件。
2. 上传完成后，点击 **Process** 按钮处理文件。
3. 处理完成后，点击 **Download Excel file** 按钮下载生成的 Excel 文件。
""")
uploaded_files = st.file_uploader("Upload PDF files", type="pdf", accept_multiple_files=True)

if st.button('Process'):
    if uploaded_files:
        file_paths = []
        for uploaded_file in uploaded_files:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                tmp_file.write(uploaded_file.getbuffer())
                file_paths.append(tmp_file.name)

        result_df = process_pdfs(file_paths)
        output_path = os.path.join(tempfile.gettempdir(), 'A客户.xlsx')
        result_df.to_excel(output_path, index=False)

        with open(output_path, "rb") as f:
            st.download_button(label="Download Excel file", data=f, file_name="A客户.xlsx",
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    else:
        st.error("Please upload at least one PDF file.")



