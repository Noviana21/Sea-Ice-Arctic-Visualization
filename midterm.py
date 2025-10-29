import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(layout="wide")
st.title('Proses Pembersihan Data Es Arktik')
st.write("""
Aplikasi ini digunakan dalam proses pembersihan data yang dilakukan pada dataset NSIDC.
""")

try:
    file_path = 'data_es_arktik_SORTED_1979-2025.csv'
    df_raw = pd.read_csv(file_path)

    st.header('1. Data Mentah (Sebelum Dibersihkan)')
    st.write("Berikut adalah 5 baris pertama dari data asli Anda. Perhatikan kolom `Data-type` dan `Region`.")
    st.dataframe(df_raw.head(5))

    st.header('2. Proses Pembersihan Interaktif')
    st.write("Silakan pilih proses cleaning yang ingin Anda terapkan:")

    df_cleaned = df_raw.copy()

    handle_missing = st.checkbox('Terapkan Proses 1: Hapus Baris dengan Nilai Hilang (-9999)')
    if handle_missing:
        rows_before = len(df_cleaned)
        # Hapus baris dimana Extent adalah -9999 (atau nilai lain jika ada)
        df_cleaned = df_cleaned[df_cleaned['Extent'] != -9999.0]
        rows_after = len(df_cleaned)
        st.info(f"Berhasil! Menghapus {rows_before - rows_after} baris yang mengandung nilai -9999.")

    remove_cols = st.checkbox('Terapkan Proses 2: Hapus Kolom Tidak Relevan (Data-type & Region)')
    if remove_cols:
        cols_to_drop = ['Data-type', 'Region']
        existing_cols_to_drop = [col for col in cols_to_drop if col in df_cleaned.columns]
        if existing_cols_to_drop:
            df_cleaned = df_cleaned.drop(columns=existing_cols_to_drop)
            st.info(f"Berhasil! Menghapus kolom: {', '.join(existing_cols_to_drop)}.")

    st.header('3. Data Final (Setelah Dibersihkan)')
    st.write("Ini adalah tampilan data setelah proses pembersihan yang Anda pilih diterapkan.")
    st.dataframe(df_cleaned)

except FileNotFoundError:
    st.error(f"Error: File 'data_es_arktik_SORTED_1979-2025.csv' tidak ditemukan.")
    st.warning("Pastikan Anda sudah membuat subfolder bernama 'data' dan meletakkan file CSV Anda di dalamnya.")