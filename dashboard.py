import streamlit as st
import pandas as pd
import plotly.express as px
import calendar
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv

load_dotenv()

# ── Konfigurasi Halaman ───────────────────────────────────────────────────────
st.set_page_config(
    page_title="Dashboard Review — Maribaya Glamping Tent",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Font & background */
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500&display=swap');

    html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }

    .main { background-color: #faf8f4; }

    /* Header utama */
    .dashboard-header {
        background: linear-gradient(160deg, #2d4a2d 0%, #3d5c3a 50%, #4a6b45 100%);
        padding: 28px 32px;
        border-radius: 12px;
        margin-bottom: 28px;
        color: white;
    }

    .dashboard-header h1 {
        font-size: 26px;
        font-weight: 300;
        margin: 0 0 4px 0;
        letter-spacing: 0.3px;
    }

    .dashboard-header p {
        font-size: 13px;
        opacity: 0.7;
        margin: 0;
    }

    /* Metric cards */
    [data-testid="metric-container"] {
        background: white;
        border: 1px solid #ddd8cf;
        border-radius: 10px;
        padding: 16px !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    }

    /* Section title */
    .section-title {
        font-size: 15px;
        font-weight: 500;
        color: #5a7a5a;
        letter-spacing: 0.5px;
        text-transform: uppercase;
        margin: 28px 0 12px 0;
        padding-bottom: 8px;
        border-bottom: 1px solid #ddd8cf;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #f0ede6;
    }
</style>
""", unsafe_allow_html=True)

# ── Koneksi Database ──────────────────────────────────────────────────────────
@st.cache_resource
def get_engine():
    return create_engine(os.getenv("DATABASE_URL"))

@st.cache_data(ttl=300)
def load_data():
    engine = get_engine()
    query = """
    SELECT
        submitted_at,
        nama,
        usia,
        jenis_kelamin,
        kota_asal,
        tujuan_menginap,
        kunjungan_pertama,
        tipe_kunjungan,
        sumber_informasi,
        rating_fasilitas,
        rating_kebersihan,
        rating_pelayanan_staff,
        rating_harga,
        rating_makanan,
        rating_lokasi,
        rating_aktivitas,
        rating_skor_keseluruhan,
        ulasan_teks,
        is_anomaly,
        anomaly_reason
    FROM reviews
    """

    df = pd.read_sql(query, engine)
    df["submitted_at"] = pd.to_datetime(df["submitted_at"])
    df["tahun"] = df["submitted_at"].dt.year
    df["bulan"] = df["submitted_at"].dt.month
    return df

# ── Warna Konsisten ───────────────────────────────────────────────────────────
PALETTE     = ["#5a7a5a", "#c9a96e", "#8b6f5a", "#7a9c7a", "#c4b8a8", "#3d5c3a", "#e8f0e8"]
RATING_COLS = [
    "rating_skor_keseluruhan",
    "rating_fasilitas",
    "rating_kebersihan",
    "rating_pelayanan_staff",
    "rating_harga",
    "rating_makanan",
    "rating_lokasi",
    "rating_aktivitas"
]
RATING_LABELS = {
    "rating_fasilitas":         "Fasilitas",
    "rating_kebersihan":        "Kebersihan",
    "rating_pelayanan_staff":   "Pelayanan & Staff",
    "rating_skor_keseluruhan":  "Skor Keseluruhan",
    "rating_harga":             "Harga & Value",
    "rating_makanan":           "Makanan & Minuman",
    "rating_aktivitas":         "Aktivitas",
    "rating_lokasi":            "Lokasi & Akses",
}

def make_pie(df, col, title):
    counts = df[col].value_counts().reset_index()
    counts.columns = [col, "Jumlah"]
    fig = px.pie(
        counts, names=col, values="Jumlah",
        color_discrete_sequence=PALETTE,
        hole=0.4,
    )
    fig.update_traces(textposition="outside", textinfo="percent+label")
    fig.update_layout(
        title=dict(text=title, font=dict(size=14, color="#2d2d2d")),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.3),
        margin=dict(t=48, b=48, l=12, r=12),
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(family="DM Sans"),
    )
    return fig

def make_bar_h(df, col, title, top_n=15):
    counts = df[col].value_counts().head(top_n).reset_index()
    counts.columns = [col, "Jumlah"]
    counts = counts.sort_values("Jumlah")
    fig = px.bar(
        counts, x="Jumlah", y=col, orientation="h",
        color_discrete_sequence=[PALETTE[0]],
        text="Jumlah",
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(
        title=dict(text=title, font=dict(size=14, color="#2d2d2d")),
        xaxis_title="Jumlah",
        yaxis_title="",
        margin=dict(t=48, b=24, l=12, r=48),
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(family="DM Sans"),
        yaxis=dict(gridcolor="#f0ece5"),
        xaxis=dict(gridcolor="#f0ece5"),
    )
    return fig

# ── Load Data ─────────────────────────────────────────────────────────────────
try:
    df_raw = load_data()
except Exception as e:
    st.error(f"Gagal terhubung ke database: {e}")
    st.stop()

# ── Sidebar Filters ───────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🔍 Filter Data")
    st.markdown("---")

    # Nama
    nama_sel = st.multiselect(
        "Nama",
        options=sorted(df_raw["nama"].dropna().unique().tolist()),
        default=[],
        placeholder="Semua"
    )

    # Usia
    if df_raw["usia"].notna().any():
        usia_min = int(df_raw["usia"].min())
        usia_max = int(df_raw["usia"].max())
        if usia_min == usia_max:
            st.caption(f"Usia: {usia_min} tahun (data belum bervariasi)")
            usia_range = (usia_min, usia_max)
        else:
            usia_range = st.slider("Rentang Usia", usia_min, usia_max, (usia_min, usia_max))
    else:
        usia_range = (0, 120)

    # Jenis Kelamin
    jk_sel = st.multiselect(
        "Jenis Kelamin",
        options=sorted(df_raw["jenis_kelamin"].dropna().unique().tolist()),
        default=[],
        placeholder="Semua"
    )

    # Kota Asal
    kota_sel = st.multiselect(
        "Kota Asal",
        options=sorted(df_raw["kota_asal"].dropna().unique().tolist()),
        default=[],
        placeholder="Semua"
    )
    tujuan_sel = st.multiselect(
        "Tujuan Menginap",
        options=sorted(df_raw["tujuan_menginap"].dropna().unique().tolist()),
        default=[],
        placeholder="Semua"
    )

    # Tipe Kunjungan
    tipe_sel = st.multiselect(
        "Tipe Kunjungan",
        options=sorted(df_raw["tipe_kunjungan"].dropna().unique().tolist()),
        default=[],
        placeholder="Semua"
    )

    # Kunjungan Pertama
    kp_sel = st.multiselect(
        "Kunjungan Pertama",
        options=["Ya, pertama kali", "Pernah sebelumnya"],
        default=[],
        placeholder="Semua"
    )

    # Sumber Informasi
    si_sel = st.multiselect(
        "Sumber Informasi",
        options=sorted(df_raw["sumber_informasi"].dropna().unique().tolist()),
        default=[],
        placeholder="Semua"
    )

    # Rentang Tanggal
    st.markdown("**Rentang Tanggal**")

    submitted_clean = df_raw["submitted_at"].dropna()

    if len(submitted_clean) > 0:
        min_date = pd.Timestamp(submitted_clean.min()).date()
        max_date = pd.Timestamp(submitted_clean.max()).date()

        if min_date == max_date:
            st.caption(f"Tanggal: {min_date} (data belum bervariasi)")
            tanggal_range = (min_date, max_date)
        else:
            tanggal_range = st.date_input(
                "Pilih Rentang Tanggal",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date,
            )
    else:
        tanggal_range = None

    # Rating per aspek
    st.markdown("**Rating per Aspek**")
    rating_filters = {}
    for col, label in RATING_LABELS.items():
        rating_filters[col] = st.multiselect(
            label,
            options=[1, 2, 3, 4, 5],
            default=[],
            placeholder="Semua"
        )

    # Ulasan Teks
    ulasan_sel = st.selectbox(
        "Ulasan Teks",
        options=["Semua", "Ada isi", "Kosong (null)"]
    )

    # Anomaly
    anomaly_sel = st.selectbox(
        "Status Anomali",
        options=["Semua", "Normal (False)", "Anomali (True)", "Belum Dicek (Null)"]
    )

    st.markdown("---")
    st.markdown("*Data diperbarui setiap 5 menit*")

# ── Terapkan Filter ───────────────────────────────────────────────────────────
df = df_raw.copy()

if nama_sel:  df = df[df["nama"].isin(nama_sel)]
if jk_sel:    df = df[df["jenis_kelamin"].isin(jk_sel)]
if kota_sel:  df = df[df["kota_asal"].isin(kota_sel)]
if tujuan_sel: df = df[df["tujuan_menginap"].isin(tujuan_sel)]
if tipe_sel:  df = df[df["tipe_kunjungan"].isin(tipe_sel)]
if si_sel:    df = df[df["sumber_informasi"].isin(si_sel)]

if df["usia"].notna().any():
    df = df[df["usia"].between(usia_range[0], usia_range[1])]

if kp_sel:
    kp_map    = {"Ya, pertama kali": True, "Pernah sebelumnya": False}
    kp_values = [kp_map[k] for k in kp_sel]
    df        = df[df["kunjungan_pertama"].isin(kp_values)]

if tanggal_range and isinstance(tanggal_range, tuple) and len(tanggal_range) == 2:
    df = df[
        (df["submitted_at"].dt.date >= tanggal_range[0]) &
        (df["submitted_at"].dt.date <= tanggal_range[1])
    ]

for col, selected in rating_filters.items():
    if selected:
        df = df[df[col].isin(selected)]

if ulasan_sel == "Ada isi":
    df = df[df["ulasan_teks"].notna() & (df["ulasan_teks"].str.strip() != "")]
elif ulasan_sel == "Kosong (null)":
    df = df[df["ulasan_teks"].isna() | (df["ulasan_teks"].str.strip() == "")]

if anomaly_sel == "Normal (False)":
    df = df[df["is_anomaly"] == False]
elif anomaly_sel == "Anomali (True)":
    df = df[df["is_anomaly"] == True]
elif anomaly_sel == "Belum Dicek (Null)":
    df = df[df["is_anomaly"].isna()]

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="dashboard-header">
    <h1>🌿 Dashboard Review Maribaya Glamping Tent</h1>
    <p>Analisis ulasan pengunjung untuk mendukung keputusan bisnis berbasis data</p>
</div>
""", unsafe_allow_html=True)

# ── Metric Summary ────────────────────────────────────────────────────────────
c1, c2, c3, c4, c5 = st.columns(5)

total                   = len(df)
avg_rating_overall      = df[RATING_COLS].stack().mean()
pct_pertama             = (df["kunjungan_pertama"] == True).sum() / total * 100 if total > 0 else 0
ada_ulasan              = df["ulasan_teks"].notna().sum()
kota_terbanyak          = df["kota_asal"].mode()[0] if df["kota_asal"].notna().any() else "-"

c1.metric("Total Review",       f"{total:,}")
c2.metric("Rata-rata Rating",   f"{avg_rating_overall:.2f} ⭐" if total > 0 else "-")
c3.metric("Kunjungan Pertama",  f"{pct_pertama:.0f}%" if total > 0 else "-")
c4.metric("Ada Ulasan Teks",    f"{ada_ulasan:,}")
c5.metric("Kota Terbanyak",     kota_terbanyak)

if total == 0:
    st.warning("Tidak ada data yang sesuai dengan filter yang dipilih.")
    st.stop()

# ── Seksi 1: Profil Pengunjung ────────────────────────────────────────────────
st.markdown('<div class="section-title">👤 Profil Pengunjung</div>', unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    st.plotly_chart(
        make_pie(df.dropna(subset=["jenis_kelamin"]), "jenis_kelamin", "Jenis Kelamin"),
        use_container_width=True
    )

with col2:
    st.plotly_chart(
        make_pie(df.dropna(subset=["tipe_kunjungan"]), "tipe_kunjungan", "Tipe Kunjungan"),
        use_container_width=True
    )

with col3:
    df_kp = df.dropna(subset=["kunjungan_pertama"]).copy()
    df_kp["kunjungan_pertama"] = df_kp["kunjungan_pertama"].map(
        {True: "Pertama kali", False: "Pernah sebelumnya"}
    )
    st.plotly_chart(
        make_pie(df_kp, "kunjungan_pertama", "Kunjungan Pertama"),
        use_container_width=True
    )

# Distribusi usia
if df["usia"].notna().any():
    fig_usia = px.histogram(
        df.dropna(subset=["usia"]), x="usia",
        nbins=20,
        color_discrete_sequence=[PALETTE[0]],
        title="Distribusi Usia Pengunjung",
        labels={"usia": "Usia", "count": "Jumlah"},
    )
    fig_usia.update_layout(
        paper_bgcolor="white", plot_bgcolor="white",
        font=dict(family="DM Sans"),
        yaxis=dict(gridcolor="#f0ece5"),
        margin=dict(t=48, b=24),
    )
    st.plotly_chart(fig_usia, use_container_width=True)

# ── Seksi 2: Sumber Informasi & Kota Asal ────────────────────────────────────
st.markdown('<div class="section-title">📍 Informasi, Asal, dan Tujuan Pengunjung</div>', unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    st.plotly_chart(
        make_bar_h(
            df.dropna(subset=["sumber_informasi"]),
            "sumber_informasi",
            "Sumber Informasi Pengunjung"
        ),
        use_container_width=True
    )

with col2:
    st.plotly_chart(
        make_bar_h(
            df.dropna(subset=["kota_asal"]),
            "kota_asal",
            "Top 15 Kota Asal Pengunjung",
            top_n=15
        ),
        use_container_width=True
    )
with col3:
    st.plotly_chart(
        make_bar_h(
            df.dropna(subset=["tujuan_menginap"]),
            "tujuan_menginap",
            "Tujuan Menginap"
        ),
        use_container_width=True
    )

# ── Seksi 3: Rating ───────────────────────────────────────────────────────────
st.markdown('<div class="section-title">⭐ Analisis Rating</div>', unsafe_allow_html=True)

# Rata-rata rating per aspek
avg_data = pd.DataFrame({
    "Aspek":[RATING_LABELS[c] for c in RATING_COLS],
    "Rata-rata":[df[c].mean() for c in RATING_COLS]
})

fig_avg = px.bar(
    avg_data, x="Rata-rata", y="Aspek", orientation="h",
    color="Rata-rata",
    color_continuous_scale=["#c4b8a8", "#7a9c7a", "#3d5c3a"],
    range_color=[1, 5],
    text=avg_data["Rata-rata"].round(2),
    title="Rata-rata Rating per Aspek",
)
fig_avg.update_traces(textposition="outside")
fig_avg.update_layout(
    xaxis=dict(range=[0, 5.5], gridcolor="#f0ece5"),
    yaxis=dict(gridcolor="#f0ece5"),
    paper_bgcolor="white", plot_bgcolor="white",
    font=dict(family="DM Sans"),
    coloraxis_showscale=False,
    margin=dict(t=48, b=24, r=64),
)
st.plotly_chart(fig_avg, use_container_width=True)

# Distribusi rating per aspek (heatmap)
dist_data = {}
for col in RATING_COLS:
    counts = df[col].value_counts().sort_index()
    dist_data[RATING_LABELS[col]] = [counts.get(i, 0) for i in range(1, 6)]

dist_df = pd.DataFrame(dist_data, index=["⭐1", "⭐2", "⭐3", "⭐4", "⭐5"]).T

fig_heat = px.imshow(
    dist_df,
    color_continuous_scale=["#f5f2ec", "#7a9c7a", "#2d4a2d"],
    aspect="auto",
    title="Distribusi Rating per Aspek (Heatmap)",
    text_auto=True,
    labels=dict(x="Bintang", y="Aspek", color="Jumlah"),
)
fig_heat.update_layout(
    paper_bgcolor="white",
    font=dict(family="DM Sans"),
    margin=dict(t=48, b=24),
    coloraxis_showscale=False,
)
st.plotly_chart(fig_heat, use_container_width=True)

avg_rating_df = pd.DataFrame({
    "Aspek":[RATING_LABELS[c] for c in RATING_COLS],
    "Rating":[df[c].mean() for c in RATING_COLS]
})

terbaik = avg_rating_df.loc[avg_rating_df["Rating"].idxmax()]
terburuk = avg_rating_df.loc[avg_rating_df["Rating"].idxmin()]

col1,col2=st.columns(2)

col1.success(
    f"🏆 Aspek Terbaik\n\n"
    f"**{terbaik['Aspek']}**\n\n"
    f"⭐ {terbaik['Rating']:.2f}"
)

col2.error(
    f"⚠ Aspek Terendah\n\n"
    f"**{terburuk['Aspek']}**\n\n"
    f"⭐ {terburuk['Rating']:.2f}"
)
st.markdown(
    '<div class="section-title">💬 Review Terbaru</div>',
    unsafe_allow_html=True
)

review = (
    df.sort_values("submitted_at", ascending=False)
    [["submitted_at","nama","rating_skor_keseluruhan","ulasan_teks"]]
    .head(10)
)

st.dataframe(
    review,
    hide_index=True,
    use_container_width=True
)

# ── Seksi 4: Tren Submission ──────────────────────────────────────────────────
st.markdown(
    '<div class="section-title">📅 Tren Pengunjung per Bulan</div>',
    unsafe_allow_html=True
)

col1, col2 = st.columns([6,1])

with col1:
    st.markdown("##### Trend Pengunjung Bulanan")

with col2:
    tahun_trend = st.selectbox(
        "Tahun",
        options=sorted(df["tahun"].unique()),
        key="trend_tahun"
    )

bulan_map = {
    i: calendar.month_name[i]
    for i in range(1,13)
}

trend_bulanan = (
    df[df["tahun"] == tahun_trend]
    .groupby("bulan")
    .size()
    .reindex(range(1,13), fill_value=0)
    .reset_index(name="Jumlah")
)

trend_bulanan["Bulan"] = trend_bulanan["bulan"].map(bulan_map)

fig_bulanan = px.line(
    trend_bulanan,
    x="Bulan",
    y="Jumlah",
    markers=True,
    title=f"Trend Pengunjung Tahun {tahun_trend}",
    color_discrete_sequence=[PALETTE[0]]
)

fig_bulanan.update_traces(
    line=dict(width=3),
    marker=dict(size=8)
)

fig_bulanan.update_layout(
    paper_bgcolor="white",
    plot_bgcolor="white",
    font=dict(family="DM Sans"),
    yaxis=dict(gridcolor="#f0ece5"),
    xaxis=dict(gridcolor="#f0ece5"),
    margin=dict(t=48,b=24)
)

st.plotly_chart(fig_bulanan, use_container_width=True)

# ── Seksi 6: Tabel Data & Download ───────────────────────────────────────────
st.markdown('<div class="section-title">📋 Data Lengkap</div>', unsafe_allow_html=True)

ROWS_PER_PAGE = 1000
df_tabel = df[
    [
        "submitted_at",
        "nama",
        "usia",
        "jenis_kelamin",
        "kota_asal",
        "tujuan_menginap",
        "rating_skor_keseluruhan",
        "is_anomaly",
        "anomaly_reason",
    ]
]
total_rows    = len(df_tabel)
total_pages   = max(1, (total_rows + ROWS_PER_PAGE - 1) // ROWS_PER_PAGE)

st.caption(
    f"Menampilkan {ROWS_PER_PAGE:,} baris per halaman untuk menjaga performa. "
    f"Total {total_pages} halaman."
)

# Inisialisasi dan validasi state halaman
if "tabel_halaman" not in st.session_state:
    st.session_state["tabel_halaman"] = 1
if st.session_state["tabel_halaman"] > total_pages:
    st.session_state["tabel_halaman"] = 1

# Navigasi halaman
col_nav1, col_nav2, col_nav3, col_nav4, col_nav5 = st.columns([1, 1, 2, 1, 1])

with col_nav1:
    if st.button("⏮ Pertama", use_container_width=True,
                 disabled=st.session_state["tabel_halaman"] == 1):
        st.session_state["tabel_halaman"] = 1

with col_nav2:
    if st.button("◀ Sebelum", use_container_width=True,
                 disabled=st.session_state["tabel_halaman"] == 1):
        st.session_state["tabel_halaman"] -= 1

with col_nav3:
    st.markdown(
        f"<div style='text-align:center; padding-top:8px;'>"
        f"Halaman <b>{st.session_state['tabel_halaman']}</b> "
        f"dari <b>{total_pages}</b></div>",
        unsafe_allow_html=True
    )

with col_nav4:
    if st.button("Sesudah ▶", use_container_width=True,
                 disabled=st.session_state["tabel_halaman"] == total_pages):
        st.session_state["tabel_halaman"] += 1

with col_nav5:
    if st.button("Terakhir ⏭", use_container_width=True,
                 disabled=st.session_state["tabel_halaman"] == total_pages):
        st.session_state["tabel_halaman"] = total_pages

# Slice data sesuai halaman aktif
halaman   = st.session_state["tabel_halaman"]
idx_awal  = (halaman - 1) * ROWS_PER_PAGE
idx_akhir = min(idx_awal + ROWS_PER_PAGE, total_rows)

st.caption(f"Baris {idx_awal + 1:,} – {idx_akhir:,} dari {total_rows:,}")
st.dataframe(
    df_tabel.iloc[idx_awal:idx_akhir],
    use_container_width=True,
    hide_index=True,
    height=420,
)

# Download seluruh data terfilter (tidak terbatas halaman)
csv = df_tabel.to_csv(
    index=False
).encode("utf-8-sig")

st.download_button(
    label=f"⬇️ Download Seluruh Data ({total_rows:,} baris) sebagai CSV",
    data=csv,
    file_name="glamping_reviews_filtered.csv",
    mime="text/csv",
    use_container_width=True,
)