import streamlit as st
import pandas as pd
from datetime import date, timedelta
import io

# ── Page config ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ระบบตรวจสอบการปฏิบัติวิทิสาสมาธิ โครงการปฏิบัติวิทิสาสมาธิ ๔๙ ล้านนาที",
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

    # ── Streak แบบ 1: มีบันทึกวันนั้น (ไม่สนใจกี่รอบ) ─────────────────
    def calc_streaks(date_list, label):
        rows = []
        if not date_list:
            return rows
        start = date_list[0]
        prev  = date_list[0]
        for d in date_list[1:]:
            if (d - prev).days == 1:
                prev = d
            else:
                rows.append({'เริ่ม': start, 'สิ้นสุด': prev,
                             'จำนวนวัน': (prev - start).days + 1, 'ประเภท': label})
                start = d; prev = d
        rows.append({'เริ่ม': start, 'สิ้นสุด': prev,
                     'จำนวนวัน': (prev - start).days + 1, 'ประเภท': label})
        return rows

    # วันที่ทำครบ 3 รอบ (เช้า กลางวัน เย็น)
    # รองรับทั้งแบบส่งครั้งเดียว "เช้า, กลางวัน, เย็น"
    # และแบบส่งแยก 3 แถว — group by คน+วัน แล้วรวม session
    raw[col_round] = raw[col_round].astype(str).str.strip()

    session_rows = []
    for _, row in raw.iterrows():
        r = str(row[col_round])
        d = row[col_date].date()
        n = row[col_name]
        if 'เช้า'     in r: session_rows.append({'name': n, 'date': d, 'session': 'เช้า'})
        if 'กลางวัน' in r: session_rows.append({'name': n, 'date': d, 'session': 'กลางวัน'})
        if 'เย็น'     in r: session_rows.append({'name': n, 'date': d, 'session': 'เย็น'})

    session_flat = pd.DataFrame(session_rows).drop_duplicates() if session_rows else pd.DataFrame(columns=['name','date','session'])

    # วันที่มีครบทั้ง 3 session
    if len(session_flat):
        sess_count = (session_flat.groupby(['name','date'])['session']
                      .nunique().reset_index(name='n_sessions'))
        full_days = sess_count[sess_count['n_sessions'] == 3][['name','date']].copy()
    else:
        full_days = pd.DataFrame(columns=['name','date'])

    streak_rows      = []
    full_streak_rows = []

    for person in all_persons:
        # streak ทั่วไป (มีบันทึก)
        done = sorted(person_dates[person_dates['name'] == person]['date'])
        for r in calc_streaks(done, 'any'):
            r['ชื่อผู้ปฏิบัติ'] = person
            streak_rows.append(r)

        # streak ครบ 3 รอบ
        full = sorted(full_days[full_days['name'] == person]['date'].unique())
        for r in calc_streaks(full, 'full'):
            r['ชื่อผู้ปฏิบัติ'] = person
            full_streak_rows.append(r)

    streak_df = (pd.DataFrame(streak_rows)[['ชื่อผู้ปฏิบัติ','เริ่ม','สิ้นสุด','จำนวนวัน']]
                 .sort_values(['ชื่อผู้ปฏิบัติ','เริ่ม']).reset_index(drop=True)
                 if streak_rows
                 else pd.DataFrame(columns=['ชื่อผู้ปฏิบัติ','เริ่ม','สิ้นสุด','จำนวนวัน']))

    full_streak_df = (pd.DataFrame(full_streak_rows)[['ชื่อผู้ปฏิบัติ','เริ่ม','สิ้นสุด','จำนวนวัน']]
                      .sort_values(['ชื่อผู้ปฏิบัติ','เริ่ม']).reset_index(drop=True)
                      if full_streak_rows
                      else pd.DataFrame(columns=['ชื่อผู้ปฏิบัติ','เริ่ม','สิ้นสุด','จำนวนวัน']))

    if len(streak_df):
        best_streak = streak_df.groupby('ชื่อผู้ปฏิบัติ')['จำนวนวัน'].max().to_dict()
        summary_df['ต่อเนื่องสูงสุด (วัน)'] = summary_df['ชื่อผู้ปฏิบัติ'].map(lambda p: best_streak.get(p, 0))
    else:
        summary_df['ต่อเนื่องสูงสุด (วัน)'] = 0

    if len(full_streak_df):
        best_full = full_streak_df.groupby('ชื่อผู้ปฏิบัติ')['จำนวนวัน'].max().to_dict()
        summary_df['ต่อเนื่องครบ3รอบ (วัน)'] = summary_df['ชื่อผู้ปฏิบัติ'].map(lambda p: best_full.get(p, 0))
    else:
        summary_df['ต่อเนื่องครบ3รอบ (วัน)'] = 0

    return raw, miss_df, summary_df, streak_df, full_streak_df, all_persons, date_min, date_max, total_days

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
        <h1>ระบบตรวจสอบการปฏิบัติวิถีสาสมาธิ โครงการปฏิบัติวิถีสาสมาธิ ๔๙ ล้านนาที</h1>
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
        raw, miss_df, summary_df, streak_df, full_streak_df, all_persons, date_min, date_max, total_days = process_file(uploaded.read())
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

    # ── Top 10 ครบ 3 รอบต่อเนื่องยาวสุด ─────────────────────────────────
    st.markdown(
        '<div class="section-hdr blue">🏆  Top 10 — ทำครบ 3 รอบ (เช้า กลางวัน เย็น) ต่อเนื่องยาวสุด</div>',
        unsafe_allow_html=True)

    if len(full_streak_df):
        best_full = (full_streak_df
                     .loc[full_streak_df.groupby('ชื่อผู้ปฏิบัติ')['จำนวนวัน'].idxmax()]
                     .sort_values('จำนวนวัน', ascending=False)
                     .head(10)
                     .copy())
        best_full['เริ่ม']   = best_full['เริ่ม'].apply(lambda d: d.strftime('%d/%m/%Y'))
        best_full['สิ้นสุด'] = best_full['สิ้นสุด'].apply(lambda d: d.strftime('%d/%m/%Y'))
        best_full = best_full.rename(columns={'จำนวนวัน': 'วันต่อเนื่องครบ 3 รอบ'})
        best_full.insert(0, 'อันดับ', range(1, len(best_full)+1))
        best_full = best_full[['อันดับ','ชื่อผู้ปฏิบัติ','วันต่อเนื่องครบ 3 รอบ','เริ่ม','สิ้นสุด']]

        def color_full_streak(val):
            if not isinstance(val, (int, float)): return ''
            if val >= 30: return 'background-color:#D5F5E3;color:#145A32;font-weight:700'
            if val >= 14: return 'background-color:#D6EAF8;color:#1A5276;font-weight:700'
            if val >= 7:  return 'background-color:#FEF9E7;color:#7D6608;font-weight:600'
            return ''

        styled_top = (best_full.set_index('อันดับ')
                      .style.map(color_full_streak, subset=['วันต่อเนื่องครบ 3 รอบ']))
        st.dataframe(styled_top, use_container_width=True,
                     height=min(380, 40+35*len(best_full)))
        st.markdown(
            '<div style="font-size:0.82rem;margin-top:6px">'
            '<span style="background:#D5F5E3;color:#145A32;padding:3px 10px;border-radius:12px;font-weight:600;margin-right:8px">🥇 ≥ 30 วัน</span>'
            '<span style="background:#D6EAF8;color:#1A5276;padding:3px 10px;border-radius:12px;font-weight:600;margin-right:8px">🥈 ≥ 14 วัน</span>'
            '<span style="background:#FEF9E7;color:#7D6608;padding:3px 10px;border-radius:12px;font-weight:600">🥉 ≥ 7 วัน</span>'
            '</div>',
            unsafe_allow_html=True)
    else:
        st.info("ยังไม่มีข้อมูลการทำครบ 3 รอบต่อเนื่อง")

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
                          'วันที่ขาด','อัตราขาด','ต่อเนื่องสูงสุด (วัน)','วันที่ขาด (ทั้งหมด)']]

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
        p_sum    = summary_df[summary_df['ชื่อผู้ปฏิบัติ'] == sel].iloc[0]
        p_miss   = miss_df[miss_df['ชื่อผู้ปฏิบัติ'] == sel].copy()
        p_streak = streak_df[streak_df['ชื่อผู้ปฏิบัติ'] == sel].copy()

        td      = int(p_sum['วันทั้งหมด'])
        ok      = int(p_sum['วันที่ทำสมาธิ'])
        md      = int(p_sum['วันที่ขาด'])
        pct     = float(p_sum['อัตราขาด'])
        best_s  = int(p_sum.get('ต่อเนื่องสูงสุด (วัน)', 0))
        best_fs = int(p_sum.get('ต่อเนื่องครบ3รอบ (วัน)', 0))
        pct_str = f"{pct:.1%}"
        pct_cls = "red" if pct >= 0.3 else ("orange" if pct > 0 else "navy")

        st.markdown(f"""
        <div class="kpi-grid" style="grid-template-columns:repeat(5,1fr)">
            {kpi_card("วันในช่วงทั้งหมด", td,      "วัน",             "navy")}
            {kpi_card("วันที่ทำสมาธิ",    ok,      "วัน",             "blue")}
            {kpi_card("วันที่ขาด",        md,      "วัน",             "red")}
            {kpi_card("อัตราขาด",         pct_str, "",                pct_cls)}
            {kpi_card("Streak สูงสุด",    best_s,  "วันติดต่อกัน",    "orange")}
        </div>
        """, unsafe_allow_html=True)

        # ── ตารางช่วงต่อเนื่อง ──────────────────────────────────────────
        st.markdown('<div class="section-hdr blue">🔥  ช่วงที่ทำสมาธิต่อเนื่อง (เรียงจากยาวสุด)</div>', unsafe_allow_html=True)

        if len(p_streak):
            def color_streak(val):
                if isinstance(val, (int, float)) and val == best_s and best_s > 1:
                    return 'background-color:#D6EAF8; color:#1A5276; font-weight:700'
                return ''

            s_show = p_streak.copy()
            s_show['เริ่ม']   = s_show['เริ่ม'].apply(lambda d: d.strftime('%d/%m/%Y'))
            s_show['สิ้นสุด'] = s_show['สิ้นสุด'].apply(lambda d: d.strftime('%d/%m/%Y'))
            s_show = (s_show[['เริ่ม','สิ้นสุด','จำนวนวัน']]
                      .sort_values('จำนวนวัน', ascending=False)
                      .reset_index(drop=True))
            s_show.insert(0, '#', range(1, len(s_show)+1))
            styled_s = s_show.set_index('#').style.map(color_streak, subset=['จำนวนวัน'])
            st.dataframe(styled_s, use_container_width=True,
                         height=min(420, 40 + 35*len(s_show)))
        else:
            st.info("ไม่มีข้อมูล streak")

        # ── วันที่ขาด ───────────────────────────────────────────────────
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
                         height=min(400, 40 + 35*len(p_show)))

# ── Footer ─────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption("🙏 ระบบตรวจสอบการปฏิบัติวิถีสาสมาธิ โครงการปฏิบัติวิถีสาสมาธิ ๔๙ ล้านนาที · อัปโหลดไฟล์ใหม่เพื่อรีเฟรชข้อมูล")
