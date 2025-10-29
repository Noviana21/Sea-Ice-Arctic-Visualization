import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# --- KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="Dashboard Es Arktik",
    layout="wide"
)

# --- DATA BERSIH ---
@st.cache_data
def load_data(file_path):
    try:
        df = pd.read_csv(file_path)
        cols_to_drop = ['Data-type', 'Region']
        existing_cols_to_drop = [col for col in cols_to_drop if col in df.columns]
        if existing_cols_to_drop:
            df = df.drop(columns=existing_cols_to_drop)
        return df
    except FileNotFoundError:
        st.error(f"Error: File '{file_path}' tidak ditemukan.")
        st.info("Pastikan file 'real.csv' Anda berada di lokasi yang benar.")
        st.stop()

file_path = 'real.csv' 
df_original = load_data(file_path) 

# --- FILTER ---

month_map = {
    1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'Mei', 6: 'Jun',
    7: 'Jul', 8: 'Agu', 9: 'Sep', 10: 'Okt', 11: 'Nov', 12: 'Des'
}
month_order = ['Jan', 'Feb', 'Mar', 'Apr', 'Mei', 'Jun', 'Jul', 'Agu', 'Sep', 'Okt', 'Nov', 'Des']
month_name_map = {name: num for num, name in month_map.items()}

st.sidebar.header('Filter Dashboard (Poin Opsional #3)')

# Filter 1: Rentang Tahun
min_year = int(df_original['Year'].min())
max_year = int(df_original['Year'].max())
selected_years = st.sidebar.slider(
    "1. Pilih Rentang Tahun:",
    min_year,
    max_year,
    (min_year, max_year) 
)

# Filter 2: Pilihan Bulan
selected_months_names = st.sidebar.multiselect(
    "2. Pilih Bulan untuk Dianalisis:",
    options=month_order,
    default=month_order 
)

if not selected_months_names:
    st.sidebar.warning("Silakan pilih minimal satu bulan.")
    st.stop()

# --- TERAPKAN FILTER KE DATA ---
selected_months_nums = [month_name_map[name] for name in selected_months_names]
df = df_original[
    (df_original['Year'] >= selected_years[0]) &
    (df_original['Year'] <= selected_years[1]) &
    (df_original['Month'].isin(selected_months_nums))
].copy()

if df.empty and (selected_years[0] != min_year or selected_years[1] != max_year or len(selected_months_names) != 12):
    st.warning("Tidak ada data untuk filter yang Anda pilih. Harap sesuaikan filter Anda.")
    st.stop()


# --- DASHBOARD ---
st.title('Dashboard Analisis Pencairan Es Laut Arktik')
st.markdown(f"""
Dashboard ini memvisualisasikan data historis luas es laut di Arktik dari tahun **{selected_years[0]}** hingga **{selected_years[1]}**,
berdasarkan data dari NSIDC (National Snow and Ice Data Center). Gunakan filter di sidebar untuk menjelajahi data.
""")

# --- VISUALISASI Q1: TREN JANGKA PANJANG ---
st.header('Q1. Tren Luas Es Laut dari Waktu ke Waktu')
st.write("""
Grafik di bawah ini menunjukkan tren rata-rata tahunan luas es laut di Arktik.
Grafik ini menjawab pertanyaan "Bagaimana tren luas es laut dari waktu ke waktu? Dan seberapa signifikan penurunannya?"
Garis biru menunjukkan fluktuasi tahunan, sementara garis oranye menyoroti penurunan jangka panjang yang konsisten selama lebih dari empat dekade. \n
Di sini juga digunakan metriks baru, yaitu "5-year moving average" untuk menghaluskan kebisingan data, sehingga garis tren jauh lebih halus dan jelas. Metriks ini juga menunjukkan arah pergerakan data yang sebenarnya tanpa terganggu oleh fluktuasi jangka pendek.
""")

if not df.empty:
    yearly_avg_extent = df.groupby('Year')['Extent'].mean().reset_index()

    fig = px.line(
        yearly_avg_extent,
        x='Year',
        y='Extent',
        title=f'Rata-Rata Tahunan Luas Es ({", ".join(selected_months_names)})',
        labels={'Year': 'Tahun', 'Extent': 'Rata-Rata Luas Es (juta km²)'},
        template='plotly_white'
    )
    fig.update_traces(
        mode='lines+markers',
        name='Rata-Rata Tahunan',
        line=dict(color='blue', width=3)
    )
    if len(yearly_avg_extent) >= 5: 
        fig.add_scatter(
            x=yearly_avg_extent['Year'],
            y=yearly_avg_extent['Extent'].rolling(window=5, center=True, min_periods=1).mean(),
            mode='lines',
            line=dict(color='orange', width=2),
            name='Rata-Rata Bergerak 5 Tahun'
        )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("Tidak cukup data untuk menampilkan tren Q1 dengan filter saat ini.")


# --- VISUALISASI Q2: SIKLUS MUSIMAN ---
st.header('Q2. Puncak dan Titik Terendah Luas Es')

if not df.empty and df['Month'].nunique() > 1: 
    monthly_avg_extent = df.groupby('Month')['Extent'].mean().reset_index()
    monthly_avg_extent['MonthName'] = monthly_avg_extent['Month'].map(month_map)

    peak_month = monthly_avg_extent.loc[monthly_avg_extent['Extent'].idxmax()]
    min_month = monthly_avg_extent.loc[monthly_avg_extent['Extent'].idxmin()]

    col1, col2 = st.columns(2)
    col1.metric(
        label=f"Puncak Luas Es ({selected_years[0]}-{selected_years[1]})", 
        value=f"{peak_month['MonthName']}",
        delta=f"{peak_month['Extent']:.2f} juta km²",
        delta_color="off"
    )
    col2.metric(
        label=f"Titik Terendah ({selected_years[0]}-{selected_years[1]})", 
        value=f"{min_month['MonthName']}",
        delta=f"{min_month['Extent']:.2f} juta km²",
        delta_color="off"
    )

    col_chart, col_desc = st.columns([2, 1])

    with col_chart:
        fig2 = px.bar(
            monthly_avg_extent,
            x='MonthName',
            y='Extent',
            title=f'Siklus Musiman Rata-Rata ({selected_years[0]}-{selected_years[1]})', 
            labels={'MonthName': 'Bulan', 'Extent': 'Rata-Rata Luas Es (juta km²)'},
            template='plotly_white',
            color='Extent',
            color_continuous_scale=px.colors.sequential.Tealgrn
        )
        filtered_month_order = [month for month in month_order if month in selected_months_names]
        fig2.update_xaxes(categoryorder='array', categoryarray=filtered_month_order)
        st.plotly_chart(fig2, use_container_width=True)

    with col_desc:
        st.subheader("Analisis Siklus Musiman")
        st.markdown(f"""
        Grafik visualisasi ini menjawab pertanyaan "Kapan puncak luas es laut terjadi? Dan kapan titik terendah luas es laut?". \n
        Berdasarkan data dari **{selected_years[0]}** hingga **{selected_years[1]}**:
        * **Puncak (Maksimum):** Luas es secara konsisten mencapai puncaknya di **{peak_month['MonthName']}**.
        * **Titik Terendah (Minimum):** Es menyusut ke titik terendahnya di **{min_month['MonthName']}**.
        """)
else:
     st.warning("Pilih minimal 2 bulan berbeda di filter sidebar untuk melihat siklus musiman.")


# --- VISUALISASI Q3: LAJU PENCAIRAN PER DEKADE ---
st.header('Q3. Laju Pencairan Es')
st.write("""
Pertanyaan "Apakah laju pencairan es (penurunan luas dari titik tertinggi ke titik terendah) semakin cepat dalam dekade terakhir dibandingkan dengan dekade 1980-an?" 
dijawab dengan menciptakan **metrik baru**: "Laju Pencairan Tahunan",
yaitu selisih antara luas es di puncaknya (Maret) dan titik terendahnya (September) setiap tahun.
""")

try:
    if 3 in selected_months_nums and 9 in selected_months_nums:
        df_q3_filtered = df_original[
            (df_original['Year'] >= selected_years[0]) &
            (df_original['Year'] <= selected_years[1])
        ]
        df_seasonal = df_q3_filtered[df_q3_filtered['Month'].isin([3, 9])]
        df_pivot = df_seasonal.pivot(index='Year', columns='Month', values='Extent').reset_index()
        df_pivot.columns.name = None
        df_pivot = df_pivot.rename(columns={3: 'March_Extent', 9: 'September_Extent'})
        df_pivot = df_pivot.dropna(subset=['March_Extent', 'September_Extent'])

        if not df_pivot.empty:
            df_pivot['Melt_Rate'] = df_pivot['March_Extent'] - df_pivot['September_Extent']

            min_decade = (df_pivot['Year'].min() // 10) * 10
            max_decade = (df_pivot['Year'].max() // 10) * 10 + 10
            if max_decade <= min_decade + 10: 
                min_decade = (min_year // 10) * 10
                max_decade = min_decade + 10
                if max_decade <= min_decade: max_decade = min_decade + 10 

            bins = list(range(min_decade, max_decade + 10, 10))
            if len(bins) < 2: 
                bins = list(range(1970, 2040, 10))
            labels = [f"{b}s" for b in bins[:-1]]

            df_pivot['Decade'] = pd.cut(df_pivot['Year'], bins=bins, labels=labels, right=False)
            decade_melt_avg = df_pivot.groupby('Decade', observed=True)['Melt_Rate'].mean().reset_index()

            col_chart_q3, col_desc_q3 = st.columns([2, 1])
            with col_chart_q3:
                fig3 = px.bar(
                    decade_melt_avg,
                    x='Decade',
                    y='Melt_Rate',
                    title='Rata-Rata Laju Pencairan Musiman (Maret - September) per Dekade',
                    labels={'Decade': 'Dekade', 'Melt_Rate': 'Rata-Rata Es yang Mencair (juta km²)'},
                    template='plotly_white',
                    color='Melt_Rate',
                    color_continuous_scale='Oranges'
                )
                st.plotly_chart(fig3, use_container_width=True)

            with col_desc_q3:
                st.subheader("Laju Pencairan Musiman Semakin Besar")
                st.markdown("""
                Seperti yang ditunjukkan oleh grafik di samping, untuk dekade **2000-an**, **2010-an**, dan **2020-an** secara jelas lebih tinggi daripada batang untuk dekade **1980-an** dan **1990-an**.
                Hal ini menunjukkan bahwa jumlah total es yang hilang setiap musim panas semakin besar dalam beberapa dekade terakhir.
                """)
        else:
            st.warning("Tidak ada data Maret & September yang cukup dalam rentang tahun yang dipilih.")
    else:
        st.info("Pilih bulan Maret dan September di filter sidebar untuk melihat analisis laju pencairan.")
except Exception as e:
    st.error(f"Terjadi kesalahan saat memproses data untuk Q3: {e}")


# --- VISUALISASI Q4: PREDIKSI SEDERHANA ---
st.header("Q4. Kapan Arktik Akan 'Bebas Es' di Musim Panas?")
st.write("""
Bagian ini mencoba memproyeksikan masa depan berdasarkan tren saat ini dengan menggunakan model statistik sederhana (Regresi Linear) pada data 20 tahun terakhir (2005-2025)
untuk memprediksi kapan luas es di bulan September (musim panas) akan mencapai "batas bebas es" (1 juta km²).
**Visualisasi ini tidak dipengaruhi oleh filter di sidebar.**
""")

try:
    df_september = df_original[df_original['Month'] == 9].copy()

    if not df_september.empty:
        current_year = df_september['Year'].max()
        start_year_for_trend = max(current_year - 20, df_september['Year'].min()) # Ambil 20 tahun terakhir atau sejak data dimulai
        df_fit = df_september[df_september['Year'] >= start_year_for_trend]

        if len(df_fit) > 1:
            coeffs = np.polyfit(df_fit['Year'], df_fit['Extent'], 1)
            trend_fn = np.poly1d(coeffs)
            future_years = np.array(range(1990, 2061))
            predicted_extent = trend_fn(future_years)

            if abs(coeffs[0]) > 1e-6:
                ice_free_year = (1.0 - coeffs[1]) / coeffs[0]
            else:
                ice_free_year = np.inf 

            col_chart_q4, col_desc_q4 = st.columns([2, 1])

            with col_chart_q4:
                fig4 = px.scatter(
                    df_september,
                    x='Year',
                    y='Extent',
                    title="Proyeksi 'Bebas Es' Musim Panas Arktik (Bulan September)",
                    labels={'Year': 'Tahun', 'Extent': 'Luas Es (juta km²)'},
                    template='plotly_white'
                )
                fig4.add_scatter(
                    x=future_years,
                    y=predicted_extent,
                    mode='lines',
                    line=dict(color='red', width=3, dash='dash'),
                    name=f'Tren (Basis {start_year_for_trend}-{current_year})'
                )
                fig4.add_hline( 
                    y=1.0,
                    line_dash="dot",
                    line_color="black",
                    annotation_text="Batas 'Bebas Es' (1 juta km²)"
                )
                fig4.update_xaxes(range=[1990, 2060])
                st.plotly_chart(fig4, use_container_width=True)

            with col_desc_q4:
                st.subheader("Analisis Prediktif")
                if np.isinf(ice_free_year) or ice_free_year < 1979:
                    st.warning("Tren saat ini tidak memberikan proyeksi 'bebas es' yang realistis dalam rentang waktu yang ditampilkan.")
                else:
                    st.metric(label="Tahun 'Bebas Es' (Diproyeksikan)", value=f"{int(ice_free_year)}")
                    st.markdown(f"""
                    Berdasarkan tren linear yang sangat curam dalam {current_year - start_year_for_trend + 1} tahun terakhir, model sederhana ini memproyeksikan bahwa
                    Arktik dapat mengalami musim panas 'bebas es' sekitar tahun **{int(ice_free_year)}**.
                    """)
        else:
            st.warning("Tidak cukup data (kurang dari 2 tahun) untuk membuat prediksi.")
    else:
        st.warning("Tidak ada data bulan September untuk membuat prediksi.")
except Exception as e:
    st.error(f"Terjadi kesalahan saat memproses data untuk Q4 (Prediksi): {e}")


# --- RAW DATA ---
st.markdown("---") 
st.header("Informasi Mengenai Data yang Digunakan")

file_path_raw_display = 'data_es_arktik_SORTED_1979-2025.csv'
try:
    df_raw_display = pd.read_csv(file_path_raw_display)
except FileNotFoundError:
    df_raw_display = None 
    st.warning(f"File contoh data mentah '{file_path_raw_display}' tidak ditemukan.")

col_data, col_attributes = st.columns([1, 1])

with col_data:
    st.subheader("Contoh Data Mentah")
    if df_raw_display is not None:
        st.dataframe(df_raw_display.head())
    else:
        st.write("Tidak dapat menampilkan contoh data mentah.")


with col_attributes:
    st.subheader("Penjelasan Atribut (Data Mentah)")
    attribute_data = {
        'Atribut': ['Year', 'Month', 'Data-type', 'Region', 'Extent', 'Area'],
        'Deskripsi': [
            'Tahun pencatatan data.',
            'Bulan pencatatan data (1-12).',
            'Kode tipe data internal NSIDC (misal: NSIDC-0051).',
            'Wilayah data (N = Northern Hemisphere/Arktik).',
            'Luas area lautan dengan konsentrasi es ≥ 15% (juta km²).',
            'Luas total area lautan yang tertutup es (juta km²).'
        ]
    }
    df_attributes = pd.DataFrame(attribute_data)
    st.table(df_attributes.set_index('Atribut'))

    # --- INSIGHT ACTIONABLE ---
st.markdown("---")
st.header("Insight Actionable")

col_insight1, col_insight2 = st.columns(2) 

with col_insight1:
    st.subheader("Proyeksi Krisis & Adaptasi Daerah Pesisir")
    st.markdown(f"""
    **Insight:** Proyeksi statistik (Q4) menunjukkan Arktik berpotensi mengalami musim panas "bebas es" sekitar tahun **{int(ice_free_year) if 'ice_free_year' in locals() and not np.isinf(ice_free_year) and ice_free_year >= 1979 else 'N/A'}**. Hal ini memberikan batas waktu krisis yang nyata dan mengubah pemanasan global dari masalah abstrak menjadi ancaman dengan *deadline* yang jelas.
    """)
    st.markdown("""
    **Rekomendas:** Pemerintah kota dan provinsi di wilayah pesisir yang rentan (seperti **Banjarmasin**, Semarang, Jakarta) harus **segera memprioritaskan anggaran dan mempercepat rencana adaptasi infrastruktur**. Proyeksi ini membuktikan bahwa ini bukan lagi masalah '100 tahun lagi', melainkan krisis mendesak yang diperkirakan terjadi dalam 20-30 tahun ke depan. Rencana tata ruang dan desain tanggul laut harus disesuaikan.
    """)

with col_insight2:
    st.subheader("Siklus Es & Konservasi Satwa Liar")
    st.markdown(f"""
    **Insight:** Analisis siklus musiman (Q2) secara konsisten menunjukkan luas es laut Arktik selalu berada pada titik terendahnya di bulan **{min_month['MonthName'] if 'min_month' in locals() else 'September'}** dan titik tertingginya di bulan **{peak_month['MonthName'] if 'peak_month' in locals() else 'Maret'}**. September adalah periode stres ekologis terbesar bagi satwa liar yang bergantung pada es.
    """)
    st.markdown("""
    **Rekomendasi:** Organisasi konservasi dan pemantau satwa liar (misal: WWF) harus **memfokuskan survei populasi tahunan mereka** dan upaya mitigasi konflik manusia-beruang pada **akhir musim panas (akhir Agu - awal Okt)**. Pada saat inilah es paling sedikit, sehingga beruang kutub paling terkonsentrasi di darat atau sisa es, memudahkan estimasi populasi dan pengelolaan interaksi dengan manusia.
    """)