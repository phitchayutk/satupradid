import streamlit as st
import pandas as pd
from datetime import date, timedelta
import io

# ── Page config ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ระบบตรวจสอบวิถีสา",
    page_icon="🙏",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@300;400;600;700&family=IBM+Plex+Sans+Thai:wght@400;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Sarabun', sans-serif; }
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 1.5rem; padding-bottom: 2rem; }

.app-header {
    background: linear-gradient(135deg, #1F3864 0%, #2E75B6 100%);
    border-radius: 16px; padding: 28px 36px; margin-bottom: 24px;
    display: flex; align-items: center; gap: 16px;
    box-shadow: 0 8px 32px rgba(31,56,100,0.25);
}
.app-header h1 {
    color: white; font-family: 'IBM Plex Sans Thai', sans-serif;
    font-size: 1.75rem; font-weight: 700; margin: 0; line-height: 1.2;
}
.app-header p { color: rgba(255,255,255,0.75); font-size: 0.9rem; margin: 4px 0 0 0; }

.kpi-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin-bottom: 24px; }
.kpi-card {
    border-radius: 12px; padding: 20px 16px; text-align: center;
    box-shadow: 0 2px 12px rgba(0,0,0,0.08); position: relative; overflow: hidden;
}
.kpi-card::before {
    content: ''; position: absolute; top: 0; left: 0; right: 0;
    height: 4px; border-radius: 12px 12px 0 0;
}
.kpi-card.navy  { background:#EEF3FB; } .kpi-card.navy::before  { background:#1F3864; }
.kpi-card.blue  { background:#E8F3FF; } .kpi-card.blue::before  { background:#2E75B6; }
.kpi-card.red   { background:#FFF0F0; } .kpi-card.red::before   { background:#C00000; }
.kpi-card.orange{ background:#FFF4EC; } .kpi-card.orange::before{ background:#C55A11; }
.kpi-label { font-size: 0.78rem; color: #666; font-weight: 600; letter-spacing: 0.02em; margin-bottom: 6px; }
.kpi-value { font-family: 'IBM Plex Sans Thai', sans-serif; font-size: 2rem; font-weight: 700; line-height: 1; }
.kpi-unit  { font-size: 0.8rem; color: #888; margin-top: 4px; }
.kpi-card.navy   .kpi-value { color: #1F3864; }
.kpi-card.blue   .kpi-value { color: #2E75B6; }
.kpi-card.red    .kpi-value { color: #C00000; }
.kpi-card.orange .kpi-value { color: #C55A11; }

.section-hdr {
    border-radius: 10px; padding: 12px 20px; margin: 20px 0 12px 0;
    font-family: 'IBM Plex Sans Thai', sans-serif; font-weight: 700;
    font-size: 1rem; color: white; display: flex; align-items: center; gap: 10px;
}
.section-hdr.red   { background: linear-gradient(90deg,#C00000,#E53935); }
.section-hdr.blue  { background: linear-gradient(90deg,#1F3864,#2E75B6); }
.section-hdr.green { background: linear-gradient(90deg,#1B5E20,#2E7D32); }

.info-banner {
    background: #E8F5E9; border-left: 4px solid #2E7D32;
    border-radius: 0 8px 8px 0; padding: 12px 16px; margin-bottom: 16px;
    font-size: 0.9rem; color: #1B5E20;
}
.warn-banner {
    background: #FFF8E1; border-left: 4px solid #F9A825;
    border-radius: 0 8px 8px 0; padding: 12px 16px; margin-bottom: 16px;
    font-size: 0.9rem; color: #795548;
}
.filter-bar {
    background: #F8FAFF; border: 1px solid #D0DEFF;
    border-radius: 10px; padding: 16px; margin-bottom: 16px;
}
</style>
""", unsafe_allow_html=True)

# ── Helper ─────────────────────────────────────────────────────────────────
def kpi_card(label, value, unit, cls):
    return f"""<div class="kpi-card {cls}">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        <div class="kpi-unit">{unit}</div>
    </div>"""

@st.cache_data(show_spinner=False)
def process_file(file_bytes: bytes):
    raw = pd.read_excel(io.BytesIO(file_bytes))
    col_ts, col_name, col_date, col_round = raw.columns[:4]

    raw[col_date] = pd.to_datetime(raw[col_date], errors='coerce')
    raw = raw.dropna(subset=[col_date])
    raw = raw[raw[col_date].dt.year.between(2020, 2035)].copy()
    raw[col_name] = raw[col_name].astype(str).str.strip()

    # วันที่แต่ละคนบันทึก (deduplicated per person-date)
    person_dates = (raw[[col_name, col_date]]
                    .drop_duplicates()
                    .assign(date=lambda df: df[col_date].dt.date)
                    [[col_name, 'date']]
                    .rename(columns={col_name: 'name'}))

    all_persons = sorted(person_dates['name'].unique())

    # ช่วงวันรวม: วันแรกถึงวันล่าสุดในไฟล์
    date_min = person_dates['date'].min()
    date_max = person_dates['date'].max()
    all_dates_range = [date_min + timedelta(days=i)
                       for i in range((date_max - date_min).days + 1)]

    # วันที่ขาด = วันที่อยู่ในช่วง date_min–date_max แต่ไม่มีบันทึกของคนนั้น
    miss_rows = []
    for person in all_persons:
        done_dates = set(person_dates[person_dates['name'] == person]['date'])
        for d in all_dates_range:
            if d not in done_dates:
                miss_rows.append({'ชื่อผู้ปฏิบัติ': person, 'วันที่ขาด': d})

    miss_df = (pd.DataFrame(miss_rows)
               .sort_values(['ชื่อผู้ปฏิบัติ', 'วันที่ขาด'])
               .reset_index(drop=True)
               if miss_rows
               else pd.DataFrame(columns=['ชื่อผู้ปฏิบัติ', 'วันที่ขาด']))

    # Summary per person
    total_days = len(all_dates_range)
    miss_count = miss_df.groupby('ชื่อผู้ปฏิบัติ').size().to_dict() if len(miss_df) else {}
    miss_dates_per = {}
    if len(miss_df):
        for p, grp in miss_df.groupby('ชื่อผู้ปฏิบัติ'):
            miss_dates_per[p] = sorted(grp['วันที่ขาด'].tolist())

    summary_rows = []
    for person in all_persons:
        md = miss_count.get(person, 0)
        ok = total_days - md
        pct = md / total_days if total_days > 0 else 0.0
        dates_list = miss_dates_per.get(person, [])
        dates_str = ',  '.join(d.strftime('%d/%m') for d in dates_list) if dates_list else '—'
        summary_rows.append({
            'ชื่อผู้ปฏิบัติ':         person,
            'วันทั้งหมด':              total_days,
            'วันที่ทำสมาธิ':           ok,
            'วันที่ขาด':               md,
            'อัตราขาด':               pct,
            'วันที่ขาด (ทั้งหมด)':    dates_str,
        })

    summary_df = pd.DataFrame(summary_rows)

    return raw, miss_df, summary_df, all_persons, date_min, date_max, total_days

def color_rate(val):
    if isinstance(val, float):
        if val >= 0.3:   return 'background-color:#FFD7D7; color:#C00000; font-weight:700'
        elif val > 0:    return 'background-color:#FFF2CC; color:#7F5000; font-weight:600'
        return 'background-color:#E2EFDA; color:#375623'
    return ''

# ── Header ─────────────────────────────────────────────────────────────────
st.markdown("""
<div class="app-header">
    <div style="font-size:2.5rem">🙏</div>
    <div>
        <h1>ระบบตรวจสอบการปฏิบัติวิถีสา</h1>
        <p>Upload ไฟล์ Google Form → ดูว่าวันไหนไม่ได้ทำสมาธิบ้าง</p>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Upload ─────────────────────────────────────────────────────────────────
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
    st.stop()

# ── Process ────────────────────────────────────────────────────────────────
with st.spinner("⏳  กำลังประมวลผล..."):
    try:
        raw, miss_df, summary_df, all_persons, date_min, date_max, total_days = process_file(uploaded.read())
    except Exception as e:
        st.error(f"❌  ไม่สามารถอ่านไฟล์ได้: {e}")
        st.stop()

st.markdown(f"""
<div class="info-banner">
✅  โหลดข้อมูลสำเร็จ — <strong>{len(all_persons)} คน</strong> |
ช่วงวันที่: <strong>{date_min.strftime('%d/%m/%Y')} – {date_max.strftime('%d/%m/%Y')}</strong> |
รวม <strong>{total_days} วัน</strong>
</div>
""", unsafe_allow_html=True)

# ── Tabs ───────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["📊  Dashboard", "📋  รายงานการขาด", "🔍  ค้นหารายบุคคล"])

# ══════════════════════════════════════════════════════════════════════════
# TAB 1: Dashboard
# ══════════════════════════════════════════════════════════════════════════
with tab1:
    total_persons = len(all_persons)
    total_miss_n  = len(miss_df)
    ppl_miss      = summary_df[summary_df['วันที่ขาด'] > 0].shape[0]
    ppl_perfect   = total_persons - ppl_miss

    st.markdown(f"""
    <div class="kpi-grid">
        {kpi_card("ผู้ปฏิบัติทั้งหมด", total_persons, "คน",  "navy")}
        {kpi_card("จำนวนวันในช่วง",    total_days,    "วัน", "blue")}
        {kpi_card("รวมวันที่ขาด",      total_miss_n,  "ครั้ง (คน×วัน)", "red")}
        {kpi_card("ทำครบทุกวัน",       ppl_perfect,   "คน",  "orange")}
    </div>
    """, unsafe_allow_html=True)

    col_l, col_r = st.columns(2)

    with col_l:
        st.markdown('<div class="section-hdr red">🔴  ผู้ขาดมากที่สุด (Top 10)</div>', unsafe_allow_html=True)
        top10 = summary_df.sort_values('วันที่ขาด', ascending=False).head(10).copy()
        top10.index = range(1, len(top10)+1)
        top10_show = top10[['ชื่อผู้ปฏิบัติ','วันที่ทำสมาธิ','วันที่ขาด','อัตราขาด']].copy()
        top10_show['อัตราขาด'] = top10_show['อัตราขาด'].map(lambda x: f"{x:.1%}")
        st.dataframe(top10_show, use_container_width=True, height=340)

    with col_r:
        st.markdown('<div class="section-hdr green">📅  วันที่มีคนขาดมากที่สุด (Top 10)</div>', unsafe_allow_html=True)
        if len(miss_df):
            date_miss = (miss_df.groupby('วันที่ขาด')
                         .agg(count=('ชื่อผู้ปฏิบัติ', 'nunique'),
                              names=('ชื่อผู้ปฏิบัติ',
                                lambda x: ', '.join(list(x.unique())[:3]) +
                                ('...' if x.nunique() > 3 else '')))
                         .rename(columns={'count': 'จำนวนคนขาด', 'names': 'ตัวอย่างรายชื่อ'})
                         .reset_index()
                         .sort_values('จำนวนคนขาด', ascending=False)
                         .head(10))
            date_miss['วันที่ขาด'] = date_miss['วันที่ขาด'].apply(lambda d: d.strftime('%d/%m/%Y'))
            date_miss.index = range(1, len(date_miss)+1)
            st.dataframe(date_miss, use_container_width=True, height=340)
        else:
            st.success("🎉  ไม่มีวันที่ขาดเลย!")

# ══════════════════════════════════════════════════════════════════════════
# TAB 2: รายงานการขาด
# ══════════════════════════════════════════════════════════════════════════
with tab2:

    # Filters
    fc1, fc2 = st.columns([2, 2])
    with fc1:
        sel_person = st.multiselect("👤  กรองตามชื่อ", all_persons, placeholder="ทุกคน")
    with fc2:
        date_range = st.date_input("📅  ช่วงวันที่",
            value=(date_min, date_max),
            min_value=date_min, max_value=date_max)

    # ── ส่วนที่ 1: รายการวันขาด ──
    st.markdown('<div class="section-hdr red">📋  ส่วนที่ 1 — รายการวันที่ไม่ได้ทำสมาธิ (รายแถว)</div>', unsafe_allow_html=True)

    filtered = miss_df.copy()
    if sel_person:
        filtered = filtered[filtered['ชื่อผู้ปฏิบัติ'].isin(sel_person)]
    if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
        d_start, d_end = date_range
        filtered = filtered[
            (filtered['วันที่ขาด'] >= d_start) &
            (filtered['วันที่ขาด'] <= d_end)
        ]

    filtered_show = filtered.copy()
    filtered_show['วันที่ขาด'] = filtered_show['วันที่ขาด'].apply(
        lambda d: d.strftime('%d/%m/%Y') if hasattr(d, 'strftime') else str(d))
    filtered_show['วัน'] = filtered.apply(
        lambda r: ['จันทร์','อังคาร','พุธ','พฤหัส','ศุกร์','เสาร์','อาทิตย์'][r['วันที่ขาด'].weekday()]
        if hasattr(r['วันที่ขาด'], 'weekday') else '', axis=1)
    filtered_show.insert(0, '#', range(1, len(filtered_show)+1))
    filtered_show = filtered_show[['#', 'ชื่อผู้ปฏิบัติ', 'วันที่ขาด', 'วัน']]

    if len(filtered_show):
        st.dataframe(filtered_show.set_index('#'), use_container_width=True, height=420)
        st.caption(f"แสดง {len(filtered_show):,} รายการ")

        buf = io.BytesIO()
        filtered_show.to_excel(buf, index=False, sheet_name='วันที่ขาด')
        st.download_button("⬇️  ดาวน์โหลด Excel",
            data=buf.getvalue(), file_name="วันที่ขาดสมาธิ.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    else:
        st.success("✅  ไม่มีวันที่ขาดตามเงื่อนไขที่เลือก")

    # ── ส่วนที่ 2: สรุปรายบุคคล ──
    st.markdown("---")
    st.markdown('<div class="section-hdr blue">📊  ส่วนที่ 2 — สรุปรายบุคคล</div>', unsafe_allow_html=True)

    sum_show = summary_df.copy()
    if sel_person:
        sum_show = sum_show[sum_show['ชื่อผู้ปฏิบัติ'].isin(sel_person)]
    sum_show.insert(0, '#', range(1, len(sum_show)+1))
    sum_show = sum_show[['#','ชื่อผู้ปฏิบัติ','วันทั้งหมด','วันที่ทำสมาธิ',
                          'วันที่ขาด','อัตราขาด','วันที่ขาด (ทั้งหมด)']]

    styled = (sum_show.set_index('#')
              .style
              .map(color_rate, subset=['อัตราขาด'])
              .format({'อัตราขาด': '{:.1%}'}))
    st.dataframe(styled, use_container_width=True, height=500)

    buf2 = io.BytesIO()
    export = sum_show.copy()
    export['อัตราขาด'] = export['อัตราขาด'].map(lambda x: f"{x:.1%}" if isinstance(x, float) else x)
    export.to_excel(buf2, index=False, sheet_name='สรุปรายบุคคล')
    st.download_button("⬇️  ดาวน์โหลด Excel (สรุปรายบุคคล)",
        data=buf2.getvalue(), file_name="สรุปรายบุคคล.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# ══════════════════════════════════════════════════════════════════════════
# TAB 3: ค้นหารายบุคคล
# ══════════════════════════════════════════════════════════════════════════
with tab3:
    sel = st.selectbox("🔍  เลือกผู้ปฏิบัติ", all_persons)
    if sel:
        p_sum  = summary_df[summary_df['ชื่อผู้ปฏิบัติ'] == sel].iloc[0]
        p_miss = miss_df[miss_df['ชื่อผู้ปฏิบัติ'] == sel].copy()

        td      = int(p_sum['วันทั้งหมด'])
        ok      = int(p_sum['วันที่ทำสมาธิ'])
        md      = int(p_sum['วันที่ขาด'])
        pct     = float(p_sum['อัตราขาด'])
        pct_str = f"{pct:.1%}"
        pct_cls = "red" if pct >= 0.3 else ("orange" if pct > 0 else "navy")

        st.markdown(f"""
        <div class="kpi-grid">
            {kpi_card("วันในช่วงทั้งหมด", td,       "วัน", "navy")}
            {kpi_card("วันที่ทำสมาธิ",    ok,       "วัน", "blue")}
            {kpi_card("วันที่ขาด",        md,       "วัน", "red")}
            {kpi_card("อัตราขาด",         pct_str,  "",    pct_cls)}
        </div>
        """, unsafe_allow_html=True)

        if md == 0:
            st.markdown(f"""
            <div class="info-banner">
            🎉  <strong>{sel}</strong> ทำสมาธิครบทุกวัน ตั้งแต่ {date_min.strftime('%d/%m/%Y')} ถึง {date_max.strftime('%d/%m/%Y')} — ไม่มีวันที่ขาดเลย!
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="section-hdr red">❌  วันที่ไม่ได้ทำสมาธิ ({md} วัน)</div>', unsafe_allow_html=True)

            p_show = p_miss.copy()
            p_show['วัน'] = p_show['วันที่ขาด'].apply(
                lambda d: ['จันทร์','อังคาร','พุธ','พฤหัส','ศุกร์','เสาร์','อาทิตย์'][d.weekday()])
            p_show['วันที่ขาด'] = p_show['วันที่ขาด'].apply(lambda d: d.strftime('%d/%m/%Y'))
            p_show.insert(0, '#', range(1, len(p_show)+1))
            p_show = p_show[['#', 'วันที่ขาด', 'วัน']]
            st.dataframe(p_show.set_index('#'), use_container_width=True,
                         height=min(500, 40 + 35 * len(p_show)))

# ── Footer ─────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption("🙏 ระบบตรวจสอบการปฏิบัติวิถีสา · อัปโหลดไฟล์ใหม่เพื่อรีเฟรชข้อมูล")
