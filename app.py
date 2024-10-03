import pandas as pd
import streamlit as st
import seaborn as sns
import matplotlib.pyplot as plt
from datetime import datetime

# Fungsi yang digunakan untuk menormalisasikan atau mengembalikan data agar lebih umum dan dapat diapahami
def normalize_df(df):
    df["temp"] = df["temp"] * 41
    df["atemp"] = df["atemp"] * 50
    df["hum"] = df["hum"] * 100
    df["windspeed"] = df["windspeed"] * 67
    return df 

# Membuat daily report dimaan didalamnya terdapat user aktifiti, temperatur, kelembaban
def create_daily_report_df(df):
    daily_report_df = df.resample(rule="D", on="dteday").agg({
        "casual": "sum",
        "temp": "mean",
        "hum": "mean",
        "windspeed": "mean"
    })
    daily_report_df = daily_report_df.reset_index()
    daily_report_df.rename(columns={
        "casual": "user_active",
        "temp": "temperature",
        "hum": "humidity",
    }, inplace=True)

    return daily_report_df

# Mencari hubungan pengaruh musim dengan user yang aktif menyewa sepeda
def create_user_on_season(df):
    user_on_season = df.groupby('season').agg({
        "casual": "sum",
        "registered": "sum",
        "cnt": "sum"
    }).reset_index()

    season_mapping = {
        1: 'Spring',
        2: 'Summer',
        3: 'Fall',
        4: 'Winter'
    }
    user_on_season['season_desc'] = user_on_season['season'].map(season_mapping)

    return user_on_season

# Membuat perhitungan untuk analsis RFM
def calculate_rfm(df, reference_date):
    # Menghitung Recency, Frequency, dan Monetary
    rfm_df = df.groupby('instant').agg({
        'dteday': lambda x: (reference_date - x.max()).days,  # Recency
        'cnt': 'count',  # Frequency (jumlah hari penyewaan)
        'casual': 'sum',  # Monetary 1: total penyewaan casual
        'registered': 'sum'  # Monetary 2: total penyewaan registered
    }).reset_index()

    # Ganti nama kolom agar sesuai dengan analisis RFM
    rfm_df.rename(columns={
        'dteday': 'recency',
        'cnt': 'frequency',
        'casual': 'monetary_casual',
        'registered': 'monetary_registered'
    }, inplace=True)
    
    # Periksa nilai unik dalam kolom, jika sama, beri penanganan khusus
    if rfm_df['recency'].nunique() > 1:
        rfm_df['R_Score'] = pd.qcut(rfm_df['recency'], 5, labels=[5, 4, 3, 2, 1])
    else:
        rfm_df['R_Score'] = 3  # Misalnya beri nilai tetap jika semua recency sama
    
    if rfm_df['frequency'].nunique() > 1:
        rfm_df['F_Score'] = pd.qcut(rfm_df['frequency'], 5, labels=[1, 2, 3, 4, 5])
    else:
        rfm_df['F_Score'] = 3  # Nilai tetap jika frequency sama

    if rfm_df['monetary_casual'].nunique() > 1:
        rfm_df['M_Casual_Score'] = pd.qcut(rfm_df['monetary_casual'], 5, labels=[1, 2, 3, 4, 5])
    else:
        rfm_df['M_Casual_Score'] = 3  # Nilai tetap jika monetary casual sama

    if rfm_df['monetary_registered'].nunique() > 1:
        rfm_df['M_Registered_Score'] = pd.qcut(rfm_df['monetary_registered'], 5, labels=[1, 2, 3, 4, 5])
    else:
        rfm_df['M_Registered_Score'] = 3  # Nilai tetap jika monetary registered sama

    # Menggabungkan skor RFM ke satu string
    rfm_df['RFM_Score'] = rfm_df['R_Score'].astype(str) + rfm_df['F_Score'].astype(str) + rfm_df['M_Casual_Score'].astype(str)

    return rfm_df

# Fungsi untuk menentukan segmentasi RFM
def segment_rfm(df):
    if df['RFM_Score'] == '555':
        return 'Champions'
    elif df['R_Score'] == 1:
        return 'At Risk'
    elif df['F_Score'] == 1:
        return 'Hibernating'
    else:
        return 'Other'
# code digunakan untuk menentukan segmen pelanggan berdasarkan nilai RFM (Recency, Frequency, Monetary) yang telah dihitung.
# Segmentasi ini dilakukan untuk mempermudah pemahaman perilaku pelanggan dan memprioritaskan tindakan bisnis yang berbeda untuk tiap kelompok pelanggan.

# Load dataset yang akan di olah
day_df = pd.read_csv("dataset/day.csv")

# Ubah tipedata untuk columns dteday ke dalam datetime
day_df["dteday"] = pd.to_datetime(day_df["dteday"])

day_df = normalize_df(day_df)

min_date = day_df["dteday"].min()
max_date = day_df["dteday"].max()

# Membuat sidebar untuk mengakses tanggal yang ingin di liat datanya
with st.sidebar:
    start_date, end_date = st.date_input(
        label="Rentang Waktu", min_value=min_date,
        max_value=max_date,
        value=[min_date, max_date]
    )

# Filter dataset berdasarkan rentang waktu
main_df = day_df[(day_df["dteday"] >= str(start_date)) & (day_df["dteday"] <= str(end_date))]

# Tentukan reference_date sebagai tanggal terakhir di rentang waktu
reference_date = main_df['dteday'].max()
rfm_df = calculate_rfm(main_df, reference_date)
daily_report_df = create_daily_report_df(main_df)
user_on_season = create_user_on_season(main_df)

rfm_df['Segment'] = rfm_df.apply(segment_rfm, axis=1)

st.header("Penyewaan Sepeda Pak Vincent, dua lah!")
st.subheader("Daily Reports")

# Kolom untuk menampilkan metrik pengguna aktif dan suhu rata-rata
col1, col2 = st.columns(2)

with col1:
    total_user = daily_report_df["user_active"].sum()  # Corrected sum for user_active
    st.metric("Total User Active", value=total_user)

with col2:
    temp = daily_report_df["temperature"].mean()  # Corrected temperature
    st.metric("Average Tempareture", value=f"{int(temp)}°C")  # Showing temperature with two decimals

# Kolom untuk menampilkan kelembapan rata-rata
col3 = st.columns(1)
with col3[0]:  # Make sure it's col3[0] since st.columns returns a list of columns
    hum = daily_report_df["humidity"].mean()  # Corrected humidity
    st.metric("Average Humidity", value=f"{hum:.2f}%")  # Showing humidity with two decimals

fig, ax = plt.subplots(figsize=(16, 8))
ax.plot(
    daily_report_df["dteday"],
    daily_report_df["user_active"],
    marker="o",
    linewidth=2,
    color="#90CAF9"
)
ax.tick_params(axis="y", labelsize=20)
ax.tick_params(axis="x", labelsize=15)

st.pyplot(fig)

# Plot bar untuk total penyewaan berdasarkan musim
st.subheader("Pengaruh Musim dalam jumlah total penyewaan sepeda")
plt.figure(figsize=(10, 6))
sns.barplot(x='season_desc', y='casual', data=user_on_season, palette='coolwarm_r')
plt.title('Total Rental Bikes by Season')
plt.xlabel('Total Season')
plt.ylabel('Total Rental Bikes')
st.pyplot(plt)

# Tampilkan tabel RFM dan distribusi segmen
st.subheader("Summary of RFM Segments")
st.write(rfm_df.head())

# Kolom untuk menampilkan total pelanggan, rata-rata recency, dan rata-rata frequency
st.subheader("Distribusi Segmen Berdasarkan RFM Analysis")
fig, ax = plt.subplots(figsize=(10,6))
sns.countplot(data=rfm_df, x='Segment', palette='coolwarm', ax=ax)
st.pyplot(fig)

col1, col2, col3 = st.columns(3)

with col1:
    total_customers = rfm_df.shape[0]
    st.metric("Total Customers", value=total_customers)

with col2:
    avg_recency = rfm_df['recency'].mean()
    st.metric("Average Recency", value=round(avg_recency, 2))

with col3:
    avg_frequency = rfm_df['frequency'].mean()
    st.metric("Average Frequency", value=round(avg_frequency, 2))