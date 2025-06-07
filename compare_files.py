import streamlit as st
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import PatternFill
from io import BytesIO

st.set_page_config(page_title="File Comparison Tool", layout="centered")
st.title("🔍 Compare Two Files (CSV or Excel)")
st.write("Upload two files (CSV or Excel). The app will highlight numeric values that are not present in the other file.")

# File uploaders
data1 = st.file_uploader("Upload first file", type=["csv", "xlsx", "xls"], key="file1")
data2 = st.file_uploader("Upload second file", type=["csv", "xlsx", "xls"], key="file2")

# Helper to read file
def read_data(uploaded_file):
    if uploaded_file.name.lower().endswith('.csv'):
        return pd.read_csv(uploaded_file)
    else:
        return pd.read_excel(uploaded_file)

# Highlighting logic (from your script)
def highlight_diffs_in_files(df1, df2):
    red = PatternFill(start_color="FF9999", end_color="FF9999", fill_type="solid")

    def extract_numeric_values(df):
        values = set()
        for col in df.columns:
            for val in df[col]:
                try:
                    num = float(val)
                    values.add(round(num, 2))
                except:
                    continue
        return values

    values1 = extract_numeric_values(df1)
    values2 = extract_numeric_values(df2)

    def save_with_highlight(df, other_values):
        wb = Workbook()
        ws = wb.active
        ws.append(df.columns.tolist())
        for row_idx, row in enumerate(df.itertuples(index=False), start=2):
            for col_idx, val in enumerate(row, start=1):
                if pd.isna(val) or (isinstance(val, str) and val.strip() == ""):
                    ws.cell(row=row_idx, column=col_idx, value=val)
                    continue
                try:
                    num = float(val)
                    cell = ws.cell(row=row_idx, column=col_idx, value=val)
                    if round(num, 2) not in other_values:
                        cell.fill = red
                except (ValueError, TypeError):
                    ws.cell(row=row_idx, column=col_idx, value=val)
        bio = BytesIO()
        wb.save(bio)
        bio.seek(0)
        return bio

    out1 = save_with_highlight(df1, values2)
    out2 = save_with_highlight(df2, values1)
    return out1, out2

# Use session state to persist results until new files are uploaded
if 'outputs' not in st.session_state:
    st.session_state['outputs'] = None
    st.session_state['last_files'] = (None, None)

# Detect if new files are uploaded and clear outputs if so
current_files = (data1.name if data1 else None, data2.name if data2 else None)
if current_files != st.session_state['last_files']:
    st.session_state['outputs'] = None
    st.session_state['last_files'] = current_files

if data1 and data2:
    try:
        df1 = read_data(data1)
        df2 = read_data(data2)
        st.success("Files uploaded! Click below to compare.")
        if st.button("Compare Files"):
            out1, out2 = highlight_diffs_in_files(df1, df2)
            st.session_state['outputs'] = (out1, out2)
        if st.session_state['outputs']:
            out1, out2 = st.session_state['outputs']
            st.write("### Download Results:")
            st.download_button(
                label="Download Highlighted File 1",
                data=out1,
                file_name="file1_highlighted.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            st.download_button(
                label="Download Highlighted File 2",
                data=out2,
                file_name="file2_highlighted.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    except Exception as e:
        st.error(f"Error processing files: {e}")