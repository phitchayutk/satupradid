import streamlit as st
import pandas as pd
from datetime import date
import io

# ── Page config ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ระบบตรวจสอบบันทึกวิทิสาแบบรายบุคคล",
    page_icon="🙏",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@300;400;600;700&family=IBM+Plex+Sans+Thai:wght@400;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Sarabun', sans-serif;
}

/* Hide default streamlit elements */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 1.5rem; padding-bottom: 2rem; }

/* ── App Header ── */
.app-header {
    background: linear-gradient(135deg, #1F3864 0%, #2E75B6 100%);
    border-radius: 16px;
    padding: 28px 36px;
    margin-bottom: 24px;
    display: flex;
    align-items: center;
    gap: 16px;
    box-shadow: 0 8px 32px rgba(31,56,100,0.25);
}
.app-header h1 {
    color: white;
    font-family: 'IBM Plex Sans Thai', sans-serif;
    font-size: 1.75rem;
    font-weight: 700;
    margin: 0;
    line-height: 1.2;
}
.app-header p {
    color: rgba(255,255,255,0.75);
    font-size: 0.9rem;
    margin: 4px 0 0 0;
}

/* ── Upload zone ── */
.upload-zone {
    background: #F0F6FF;
    border: 2px dashed #2E75B6;
    border-radius: 12px;
    padding: 32px;
    text-align: center;
    margin-bottom: 20px;
}

/* ── KPI Cards ── */
.kpi-grid {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 14px;
    margin-bottom: 24px;
}
.kpi-card {
    border-radius: 12px;
    padding: 20px 16px;
    text-align: center;
    box-shadow: 0 2px 12px rgba(0,0,0,0.08);
    position: relative;
    overflow: hidden;
}
.kpi-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 4px;
    border-radius: 12px 12px 0 0;
}
.kpi-card.navy  { background:#EEF3FB; } .kpi-card.navy::before  { background:#1F3864; }
.kpi-card.blue  { background:#E8F3FF; } .kpi-card.blue::before  { background:#2E75B6; }
.kpi-card.red   { background:#FFF0F0; } .kpi-card.red::before   { background:#C00000; }
.kpi-card.orange{ background:#FFF4EC; } .kpi-card.orange::before{ background:#C55A11; }
.kpi-card.brown { background:#FFF3E8; } .kpi-card.brown::before { background:#833C00; }
.kpi-label { font-size: 0.78rem; color: #666; font-weight: 600; letter-spacing: 0.02em; margin-bottom: 6px; }
.kpi-value { font-family: 'IBM Plex Sans Thai', sans-serif; font-size: 2rem; font-weight: 700; line-height: 1; }
.kpi-unit  { font-size: 0.8rem; color: #888; margin-top: 4px; }
.kpi-card.navy   .kpi-value { color: #1F3864; }
.kpi-card.blue   .kpi-value { color: #2E75B6; }
.kpi-card.red    .kpi-value { color: #C00000; }
.kpi-card.orange .kpi-value { color: #C55A11; }
.kpi-card.brown  .kpi-value { color: #833C00; }

/* ── Section headers ── */
.section-hdr {
    border-radius: 10px;
    padding: 12px 20px;
    margin: 20px 0 12px 0;
    font-family: 'IBM Plex Sans Thai', sans-serif;
    font-weight: 700;
    font-size: 1rem;
    color: white;
    display: flex;
    align-items: center;
    gap: 10px;
}
.section-hdr.red    { background: linear-gradient(90deg,#C00000,#E53935); }
.section-hdr.blue   { background: linear-gradient(90deg,#1F3864,#2E75B6); }
.section-hdr.green  { background: linear-gradient(90deg,#1B5E20,#2E7D32); }

/* ── Data tables ── */
.stDataFrame { border-radius: 10px; overflow: hidden; }
.stDataFrame table { font-family: 'Sarabun', sans-serif !important; }

/* ── Legend badges ── */
.legend-row { display: flex; gap: 12px; flex-wrap: wrap; margin: 8px 0 16px 0; }
.badge {
    display: inline-flex; align-items: center; gap: 6px;
    padding: 4px 12px; border-radius: 20px;
    font-size: 0.8rem; font-weight: 600;
}
.badge-red    { background:#FFD7D7; color:#C00000; }
.badge-yellow { background:#FFF2CC; color:#7F5000; }
.badge-light  { background:#FFFCE6; color:#7F6000; }
.badge-green  { background:#E2EFDA; color:#375623; }

/* ── Filter bar ── */
.filter-bar {
    background: #F8FAFF;
    border: 1px solid #D0DEFF;
    border-radius: 10px;
    padding: 16px;
    margin-bottom: 16px;
}

/* ── Info banner ── */
.info-banner {
    background: #E8F5E9;
    border-left: 4px solid #2E7D32;
    border-radius: 0 8px 8px 0;
    padding: 12px 16px;
    margin-bottom: 16px;
    font-size: 0.9rem;
    color: #1B5E20;
}
.warn-banner {
    background: #FFF8E1;
    border-left: 4px solid #F9A825;
    border-radius: 0 8px 8px 0;
    padding: 12px 16px;
    margin-bottom: 16px;
    font-size: 0.9rem;
    color: #795548;
}
</style>
""", unsafe_allow_html=True)

# ── Constants ──────────────────────────────────────────────────────────────
SESSIONS = ['เช้า', 'กลางวัน', 'เย็น']
SESSION_LABELS = {'เช้า': '🌅 เช้า', 'กลางวัน': '☀️ กลางวัน', 'เย็น': '🌆 เย็น'}

# ── Helper functions ───────────────────────────────────────────────────────
def parse_sessions(r: str) -> list[str]:
    s = []
    if 'เช้า' in r: s.append('เช้า')
    if 'กลางวัน' in r: s.append('กลางวัน')
    if 'เย็น' in r: s.append('เย็น')
    return s

@st.cache_data(show_spinner=False)
def process_file(file_bytes: bytes) -> tuple:
    raw = pd.read_excel(io.BytesIO(file_bytes))
    col_ts, col_name, col_date, col_round = raw.columns[:4]

    raw[col_date] = pd.to_datetime(raw[col_date], errors='coerce')
    raw = raw.dropna(subset=[col_date])
    raw = raw[raw[col_date].dt.year.between(2020, 2035)].copy()
    raw[col_name]  = raw[col_name].astype(str).str.strip()
    raw[col_round] = raw[col_round].astype(str).str.strip()

    # Flatten to person × date × session
    records = []
    for _, row in raw.iterrows():
        for s in parse_sessions(row[col_round]):
            records.append({
                'name': row[col_name],
                'date': row[col_date].date(),
                'session': s,
            })
    flat = pd.DataFrame(records).drop_duplicates()

    all_persons = sorted(flat['name'].unique())
    all_dates   = sorted(flat['date'].unique())

    # Missing records
    miss_rows = []
    for person in all_persons:
        pdata = flat[flat['name'] == person]
        for d in sorted(pdata['date'].unique()):
            done = set(pdata[pdata['date'] == d]['session'])
            miss = [s for s in SESSIONS if s not in done]
            if miss:
                miss_rows.append({
                    'ชื่อผู้ปฏิบัติ':   person,
                    'วันที่ขาด':        d,
                    'รอบที่ขาด':        ', '.join(miss),
                    'จำนวนรอบขาด':      len(miss),
                })

    miss_df = pd.DataFrame(miss_rows).sort_values(['ชื่อผู้ปฏิบัติ','วันที่ขาด']).reset_index(drop=True) if miss_rows else pd.DataFrame(columns=['ชื่อผู้ปฏิบัติ','วันที่ขาด','รอบที่ขาด','จำนวนรอบขาด'])

    # Summary per person
    person_days  = flat.groupby('name')['date'].nunique().to_dict()
    miss_per_per = miss_df.groupby('ชื่อผู้ปฏิบัติ')['วันที่ขาด'].nunique().to_dict() if len(miss_df) else {}
    miss_dates_per = {}
    if len(miss_df):
        for p, grp in miss_df.groupby('ชื่อผู้ปฏิบัติ'):
            miss_dates_per[p] = sorted(grp['วันที่ขาด'].unique())

    summary_rows = []
    for person in all_persons:
        td  = person_days.get(person, 0)
        md  = miss_per_per.get(person, 0)
        ok  = td - md
        pct = md / td if td > 0 else 0.0
        dates_list = miss_dates_per.get(person, [])
        dates_str  = ',  '.join(d.strftime('%d/%m') for d in dates_list) if dates_list else '—'
        summary_rows.append({
            'ชื่อผู้ปฏิบัติ':        person,
            'วันที่รายงาน':           td,
            'วันที่ขาดรอบ':           md,
            'วันที่ทำครบ':            ok,
            'อัตราขาด':              pct,
            'วันที่ขาด (ทั้งหมด)':   dates_str,
        })

    summary_df = pd.DataFrame(summary_rows)

    return raw, flat, miss_df, summary_df, all_persons, all_dates

def color_miss_count(val):
    if val == 3:   return 'background-color:#FFD7D7; color:#C00000; font-weight:600'
    elif val == 2: return 'background-color:#FFF2CC; color:#7F5000; font-weight:600'
    elif val == 1: return 'background-color:#FFFCE6; color:#7F6000'
    return ''

def color_rate(val):
    if isinstance(val, float):
        if val >= 0.3:   return 'background-color:#FFD7D7; color:#C00000; font-weight:700'
        elif val > 0:    return 'background-color:#FFF2CC; color:#7F5000; font-weight:600'
        return 'background-color:#E2EFDA; color:#375623'
    return ''

def kpi_card(label, value, unit, cls):
    return f"""<div class="kpi-card {cls}">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        <div class="kpi-unit">{unit}</div>
    </div>"""

# ── App Header ─────────────────────────────────────────────────────────────
st.markdown("""
<div class="app-header">
    <div style="font-size:2.5rem">🙏</div>
    <div>
        <h1>ระบบตรวจสอบการปฏิบัติวิถีสา</h1>
        <p>Upload ไฟล์ Google Form → ดูรายงานการขาดรอบทันที </p>
    </div>
</div>
""", unsafe_allow_html=True)

# ── File Upload ────────────────────────────────────────────────────────────
uploaded = st.file_uploader(
    "📂  อัปโหลดไฟล์ข้อมูล (Excel จาก Google Form)",
    type=["xlsx", "xls"],
    help="ไฟล์ต้องมีคอลัมน์: ประทับเวลา, ชื่อผู้ปฏิบัติ, วันที่ปฏิบัติ, รอบการปฏิบัติ"
)

if uploaded is None:
    st.markdown("""
    <div class="warn-banner">
    ⬆️  กรุณาอัปโหลดไฟล์ Excel ที่ Export จาก Google Form เพื่อเริ่มต้นใช้งาน
    </div>
    """, unsafe_allow_html=True)

    with st.expander("📋  รูปแบบไฟล์ที่รองรับ"):
        st.markdown("""
        ไฟล์ต้องมีคอลัมน์ตามลำดับ (4 คอลัมน์):
        | คอลัมน์ | ตัวอย่างข้อมูล |
        |---------|----------------|
        | ประทับเวลา | 5/4/2026 6:11:55 |
        | เลือกชื่อผู้ปฏิบัติ | 006 เทียมจันทร์ อูปคำ |
        | วันที่ปฏิบัติ | 5/4/2026 |
        | รอบการปฏิบัติ | เช้า 5 นาที, กลางวัน 5 นาที, เย็น 5 นาที |
        """)
    st.stop()

# ── Process ────────────────────────────────────────────────────────────────
with st.spinner("⏳  กำลังประมวลผล..."):
    try:
        raw, flat, miss_df, summary_df, all_persons, all_dates = process_file(uploaded.read())
    except Exception as e:
        st.error(f"❌  ไม่สามารถอ่านไฟล์ได้: {e}")
        st.stop()

st.markdown(f"""
<div class="info-banner">
✅  โหลดข้อมูลสำเร็จ — <strong>{len(raw):,} แถว</strong> | <strong>{len(all_persons)} คน</strong> | 
{all_dates[0].strftime('%d/%m/%Y')} – {all_dates[-1].strftime('%d/%m/%Y')}
</div>
""", unsafe_allow_html=True)

# ── Tabs ───────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["📊  Dashboard", "📋  รายงานการขาด", "🔍  ค้นหารายบุคคล"])

# ══════════════════════════════════════════════════════════════════════════
# TAB 1: Dashboard
# ══════════════════════════════════════════════════════════════════════════
with tab1:
    total_persons = len(all_persons)
    total_dates_n = len(all_dates)
    total_miss_n  = len(miss_df)
    ppl_miss      = summary_df[summary_df['วันที่ขาดรอบ'] > 0].shape[0]
    avg_rate      = (total_miss_n / total_persons / total_dates_n * 100) if total_persons and total_dates_n else 0

    st.markdown(f"""
    <div class="kpi-grid">
        {kpi_card("ผู้ปฏิบัติทั้งหมด",  total_persons,       "คน",    "navy")}
        {kpi_card("จำนวนวันข้อมูล",     total_dates_n,       "วัน",   "blue")}
        {kpi_card("วันที่ขาดรอบ",       total_miss_n,        "ครั้ง", "red")}
        {kpi_card("ผู้เคยขาดรอบ",       ppl_miss,            "คน",    "orange")}
        {kpi_card("อัตราขาดเฉลี่ย",     f"{avg_rate:.1f}%",  "",      "brown")}
    </div>
    """, unsafe_allow_html=True)

    col_l, col_r = st.columns(2)

    with col_l:
        st.markdown('<div class="section-hdr red">🔴  ผู้ขาดรอบมากที่สุด (Top 10)</div>', unsafe_allow_html=True)
        top10 = summary_df.sort_values('วันที่ขาดรอบ', ascending=False).head(10).copy()
        top10['อันดับ'] = range(1, len(top10)+1)
        top10_show = top10[['อันดับ','ชื่อผู้ปฏิบัติ','วันที่รายงาน','วันที่ขาดรอบ','อัตราขาด']].copy()
        top10_show['อัตราขาด'] = top10_show['อัตราขาด'].map(lambda x: f"{x:.1%}")
        st.dataframe(top10_show.set_index('อันดับ'), use_container_width=True, height=320)

    with col_r:
        st.markdown('<div class="section-hdr green">📅  วันที่มีผู้ขาดมากที่สุด (Top 10)</div>', unsafe_allow_html=True)
        if len(miss_df):
            date_miss = miss_df.groupby('วันที่ขาด').agg(
                คนขาดรอบ=('ชื่อผู้ปฏิบัติ','nunique'),
                ตัวอย่างรายชื่อ=('ชื่อผู้ปฏิบัติ', lambda x: ', '.join(list(x.unique())[:3]) + ('...' if x.nunique()>3 else ''))
            ).reset_index().sort_values('คนขาดรอบ', ascending=False).head(10)
            date_miss['วันที่ขาด'] = date_miss['วันที่ขาด'].apply(lambda d: d.strftime('%d/%m/%Y'))
            date_miss.index = range(1, len(date_miss)+1)
            st.dataframe(date_miss, use_container_width=True, height=320)
        else:
            st.success("🎉  ไม่มีวันที่ขาดรอบ!")

    # Missing by session type
    if len(miss_df):
        st.markdown('<div class="section-hdr blue">⏰  สรุปรอบที่ขาดบ่อยที่สุด</div>', unsafe_allow_html=True)
        sess_counts = {'เช้า': 0, 'กลางวัน': 0, 'เย็น': 0}
        for _, row in miss_df.iterrows():
            for s in SESSIONS:
                if s in row['รอบที่ขาด']:
                    sess_counts[s] += 1

        c1, c2, c3 = st.columns(3)
        for col, (sess, cnt) in zip([c1,c2,c3], sess_counts.items()):
            pct_s = cnt / total_miss_n * 100 if total_miss_n else 0
            with col:
                st.metric(SESSION_LABELS[sess], f"{cnt} ครั้ง", f"{pct_s:.1f}% ของทั้งหมด")

# ══════════════════════════════════════════════════════════════════════════
# TAB 2: รายงานการขาด
# ══════════════════════════════════════════════════════════════════════════
with tab2:

    # ── Filters ──────────────────────────────────────────────────────────
    with st.container():
        st.markdown('<div class="filter-bar">', unsafe_allow_html=True)
        fc1, fc2, fc3 = st.columns([2, 2, 1])
        with fc1:
            sel_person = st.multiselect("👤  กรองตามชื่อ", all_persons, placeholder="ทุกคน")
        with fc2:
            date_min = min(all_dates)
            date_max = max(all_dates)
            date_range = st.date_input("📅  ช่วงวันที่",
                value=(date_min, date_max),
                min_value=date_min, max_value=date_max)
        with fc3:
            sel_miss_count = st.selectbox("🔴  จำนวนรอบขาด", ["ทั้งหมด","1 รอบ","2 รอบ","3 รอบ"])
        st.markdown('</div>', unsafe_allow_html=True)

    # Apply filters to miss_df
    filtered = miss_df.copy()
    if sel_person:
        filtered = filtered[filtered['ชื่อผู้ปฏิบัติ'].isin(sel_person)]
    if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
        d_start, d_end = date_range
        filtered = filtered[
            (filtered['วันที่ขาด'] >= d_start) &
            (filtered['วันที่ขาด'] <= d_end)
        ]
    if sel_miss_count != "ทั้งหมด":
        n = int(sel_miss_count[0])
        filtered = filtered[filtered['จำนวนรอบขาด'] == n]

    filtered_show = filtered.copy()
    filtered_show['#'] = range(1, len(filtered_show)+1)
    filtered_show['วันที่ขาด'] = filtered_show['วันที่ขาด'].apply(lambda d: d.strftime('%d/%m/%Y') if hasattr(d, 'strftime') else str(d))
    filtered_show = filtered_show[['#','ชื่อผู้ปฏิบัติ','วันที่ขาด','รอบที่ขาด','จำนวนรอบขาด']]

    st.markdown('<div class="section-hdr red">📋  ส่วนที่ 1 — รายการวันที่ขาดรอบ</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="legend-row">
        <span class="badge badge-red">🔴 ขาดทั้ง 3 รอบ</span>
        <span class="badge badge-yellow">🟡 ขาด 2 รอบ</span>
        <span class="badge badge-light">🟨 ขาด 1 รอบ</span>
    </div>
    """, unsafe_allow_html=True)

    if len(filtered_show):
        styled = (filtered_show.set_index('#')
            .style
            .map(color_miss_count, subset=['จำนวนรอบขาด'])
        )
        st.dataframe(styled, use_container_width=True, height=420)
        st.caption(f"แสดง {len(filtered_show)} รายการ")
    else:
        st.success("✅  ไม่มีรายการขาดตามเงื่อนไขที่เลือก")

    # Export button
    if len(filtered_show):
        buf = io.BytesIO()
        filtered_show.to_excel(buf, index=False, sheet_name='รายการขาด')
        st.download_button(
            "⬇️  ดาวน์โหลด Excel (ส่วนที่ 1)",
            data=buf.getvalue(),
            file_name="รายการขาดรอบ.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    st.markdown("---")
    st.markdown('<div class="section-hdr blue">📊  ส่วนที่ 2 — สรุปรายบุคคล</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="legend-row">
        <span class="badge badge-red">🔴 อัตราขาด ≥ 30%</span>
        <span class="badge badge-yellow">🟡 อัตราขาด > 0%</span>
        <span class="badge badge-green">🟢 ไม่เคยขาด</span>
    </div>
    """, unsafe_allow_html=True)

    # Apply person filter to summary too
    sum_filtered = summary_df.copy()
    if sel_person:
        sum_filtered = sum_filtered[sum_filtered['ชื่อผู้ปฏิบัติ'].isin(sel_person)]

    sum_show = sum_filtered.copy()
    sum_show['#'] = range(1, len(sum_show)+1)
    sum_show = sum_show[['#','ชื่อผู้ปฏิบัติ','วันที่รายงาน','วันที่ขาดรอบ','วันที่ทำครบ','อัตราขาด','วันที่ขาด (ทั้งหมด)']]

    styled2 = (sum_show.set_index('#')
        .style
        .map(color_rate, subset=['อัตราขาด'])
        .format({'อัตราขาด': '{:.1%}'})
    )
    st.dataframe(styled2, use_container_width=True, height=480)

    buf2 = io.BytesIO()
    sum_filtered_export = sum_filtered.copy()
    sum_filtered_export['อัตราขาด'] = sum_filtered_export['อัตราขาด'].map(lambda x: f"{x:.1%}")
    sum_filtered_export.to_excel(buf2, index=False, sheet_name='สรุปรายบุคคล')
    st.download_button(
        "⬇️  ดาวน์โหลด Excel (ส่วนที่ 2)",
        data=buf2.getvalue(),
        file_name="สรุปรายบุคคล.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

# ══════════════════════════════════════════════════════════════════════════
# TAB 3: ค้นหารายบุคคล
# ══════════════════════════════════════════════════════════════════════════
with tab3:
    sel = st.selectbox("🔍  เลือกผู้ปฏิบัติ", all_persons)
    if sel:
        p_miss = miss_df[miss_df['ชื่อผู้ปฏิบัติ'] == sel].copy()
        p_sum  = summary_df[summary_df['ชื่อผู้ปฏิบัติ'] == sel].iloc[0]
        p_flat = flat[flat['name'] == sel].copy()

        # Personal KPIs
        td  = int(p_sum['วันที่รายงาน'])
        md  = int(p_sum['วันที่ขาดรอบ'])
        ok  = int(p_sum['วันที่ทำครบ'])
        pct = float(p_sum['อัตราขาด'])
        pct_str = f"{pct:.1%}"

        pct_color = "red" if pct >= 0.3 else ("orange" if pct > 0 else "navy")

        st.markdown(f"""
        <div class="kpi-grid" style="grid-template-columns:repeat(4,1fr)">
            {kpi_card("วันที่มีบันทึก",    td,       "วัน",   "navy")}
            {kpi_card("วันที่ทำครบ",      ok,       "วัน",   "blue")}
            {kpi_card("วันที่ขาดรอบ",     md,       "วัน",   "red")}
            {kpi_card("อัตราขาด",         pct_str,  "",      pct_color)}
        </div>
        """, unsafe_allow_html=True)

        if len(p_miss):
            st.markdown('<div class="section-hdr red">🔴  วันที่ขาดรอบ — ทั้งหมด</div>', unsafe_allow_html=True)
            p_miss_show = p_miss.copy()
            p_miss_show['#'] = range(1, len(p_miss_show)+1)
            p_miss_show['วันที่ขาด'] = p_miss_show['วันที่ขาด'].apply(
                lambda d: d.strftime('%d/%m/%Y') if hasattr(d, 'strftime') else str(d))
            p_miss_show = p_miss_show[['#','วันที่ขาด','รอบที่ขาด','จำนวนรอบขาด']]
            styled3 = (p_miss_show.set_index('#')
                .style
                .map(color_miss_count, subset=['จำนวนรอบขาด'])
            )
            st.dataframe(styled3, use_container_width=True, height=min(420, 40 + 35*len(p_miss_show)))

            # Calendar-style heatmap of missing days
            st.markdown('<div class="section-hdr blue">📅  ปฏิทินการปฏิบัติ</div>', unsafe_allow_html=True)

            p_dates = p_flat['date'].unique()
            miss_dates_set = set(p_miss['วันที่ขาด'])

            # Build mini calendar table
            cal_data = []
            for d in sorted(p_dates):
                status = "❌ ขาดรอบ" if d in miss_dates_set else "✅ ครบ"
                p_day_miss = p_miss[p_miss['วันที่ขาด'] == d]
                miss_detail = p_day_miss['รอบที่ขาด'].values[0] if len(p_day_miss) else "—"
                cal_data.append({
                    'วันที่': d.strftime('%d/%m/%Y'),
                    'วันในสัปดาห์': ['จ','อ','พ','พฤ','ศ','ส','อา'][d.weekday()],
                    'สถานะ': status,
                    'รอบที่ขาด': miss_detail,
                })

            cal_df = pd.DataFrame(cal_data)
            st.dataframe(cal_df, use_container_width=True, height=min(600, 40+35*len(cal_df)))
        else:
            st.markdown(f"""
            <div class="info-banner">
            🎉  <strong>{sel}</strong> ปฏิบัติครบทุกรอบทุกวัน — ไม่มีรายการขาดเลย!
            </div>
            """, unsafe_allow_html=True)

# ── Footer ─────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption("🏥 ระบบตรวจสอบการปฏิบัติวิถีสา · อัปโหลดไฟล์ใหม่เพื่อรีเฟรชข้อมูล")
