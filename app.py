import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh
import db
import engine
import ui_helpers

st.set_page_config(
    page_title="PulseWatch",
    page_icon="⚡",
    layout="wide"
)

# Inisialisasi Database & Assets
db.init_db()
ui_helpers.load_css()

if "current_user" not in st.session_state:
    st.session_state.current_user = None

# ================= AUTH VIEW =================
if not st.session_state.current_user:
    _, center_box, _ = st.columns([1, 1.2, 1])
    with center_box:
        st.write("")
        st.write("")
        st.markdown("### PulseWatch")
        st.caption("Masuk ke dashboard monitoring sistem")
        
        t_login, t_reg = st.tabs(["Login", "Buat Akun"])
        with t_login:
            with st.form("form_login"):
                u = st.text_input("Username").strip()
                p = st.text_input("Password", type="password")
                if st.form_submit_button("Masuk", use_container_width=True, type="primary"):
                    auth = db.authenticate_user(u, p)
                    if auth:
                        st.session_state.current_user = auth
                        st.rerun()
                    else:
                        st.error("Username atau password salah")
        with t_reg:
            with st.form("form_reg"):
                ru = st.text_input("Username").strip()
                rp = st.text_input("Password", type="password")
                if st.form_submit_button("Daftar", use_container_width=True):
                    if ru and rp and db.create_user(ru, rp):
                        st.success("Akun berhasil dibuat. Silakan login.")
                    else:
                        st.error("Gagal membuat akun")
    st.stop()

# ================= DASHBOARD UTAMA =================
user = st.session_state.current_user
user_id = user["id"]
monitors = db.get_user_monitors(user_id)
tot_monitors = len(monitors)

# --- SIDEBAR ---
with st.sidebar:
    username = user['username']
    initial = (username[:2] if len(username) >= 2 else username).upper()
    
    st.markdown(
        ui_helpers.render_template("profile_card", initial=initial, username=username),
        unsafe_allow_html=True
    )
    
    if st.button("Keluar Sesi", use_container_width=True):
        st.session_state.current_user = None
        st.rerun()
        
    st.write("")
    
    presets_data = ui_helpers.load_presets()
    preset_labels = [p["label"] for p in presets_data]
    
    st.markdown(f"**TAMBAH ENDPOINT** ({tot_monitors} Aktif)")
    selected_label = st.selectbox(
        "Gunakan Preset Contoh",
        options=preset_labels,
        index=0,
        label_visibility="collapsed"
    )
    
    selected_preset = next(p for p in presets_data if p["label"] == selected_label)
    
    with st.form("form_add", clear_on_submit=True):
        name_in = st.text_input("Nama Layanan", value=selected_preset["name"], placeholder="Production API")
        url_in = st.text_input("URL Target", value=selected_preset["url"], placeholder="https://api.domain.com")
        
        if st.form_submit_button("Simpan Target", use_container_width=True, type="primary"):
            if name_in and url_in.startswith("http"):
                db.add_monitor(user_id, name_in, url_in)
                st.rerun()
            else:
                st.error("Nama wajib diisi dan URL harus diawali http/https.")

# --- TOP HEADER & CONTROLS ---
c_head, c_refresh_opt, c_btn = st.columns([0.62, 0.22, 0.16])
with c_head:
    st.markdown("### Status Infrastruktur")
    st.caption("Pemeriksaan ketersediaan endpoint, latensi HTTP, SSL, dan Server Header Inspector")

with c_refresh_opt:
    refresh_rate = st.selectbox(
        "Interval Auto-Refresh",
        options=["Off (Manual)", "Setiap 30 Detik", "Setiap 1 Menit", "Setiap 5 Menit"],
        index=0,
        label_visibility="collapsed"
    )

with c_btn:
    manual_check = st.button("Check Now", use_container_width=True)

# Logika Interval Auto-Refresh
refresh_ms_map = {
    "Off (Manual)": 0,
    "Setiap 30 Detik": 30 * 1000,
    "Setiap 1 Menit": 60 * 1000,
    "Setiap 5 Menit": 300 * 1000
}
chosen_interval = refresh_ms_map.get(refresh_rate, 0)

if chosen_interval > 0:
    # Trigger refresh timer
    refresh_count = st_autorefresh(interval=chosen_interval, limit=None, key="uptime_autorefresh")
    if refresh_count > 0:
        engine.run_health_check_for_user(user_id)

if manual_check:
    with st.spinner("Pinging & inspecting headers..."):
        engine.run_health_check_for_user(user_id)
        st.rerun()

if not monitors:
    st.info("Belum ada endpoint yang dipantau. Tambahkan target baru melalui menu di sidebar sebelah kiri.")
    st.stop()

# --- KPI METRICS ---
tot = len(monitors)
up = sum(1 for m in monitors if m["status"] == "UP")
down = tot - up
avg_l = int(sum(m["last_latency_ms"] for m in monitors) / tot) if tot > 0 else 0
uptime_val = round((up / tot) * 100, 1)

with st.container():
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(
            ui_helpers.render_template(
                "kpi_card", 
                label="Sistem Global", 
                value="Operational" if down == 0 else f"{down} Down", 
                color="#22c55e" if down == 0 else "#ef4444"
            ), 
            unsafe_allow_html=True
        )
    with k2:
        st.markdown(
            ui_helpers.render_template(
                "kpi_card", 
                label="Endpoint Aktif", 
                value=f'{up} <span style="font-size:14px;color:#64748b">/ {tot}</span>', 
                color="#f8fafc"
            ), 
            unsafe_allow_html=True
        )
    with k3:
        st.markdown(
            ui_helpers.render_template(
                "kpi_card", 
                label="Rata-rata Latensi", 
                value=f"{avg_l} ms", 
                color="#38bdf8"
            ), 
            unsafe_allow_html=True
        )
    with k4:
        st.markdown(
            ui_helpers.render_template(
                "kpi_card", 
                label="Uptime Saat Ini", 
                value=f"{uptime_val}%", 
                color="#a78bfa"
            ), 
            unsafe_allow_html=True
        )

st.write("")
st.divider()

# --- TABS KONTEN ---
t_list, t_logs = st.tabs(["Endpoints & Latensi", "Catatan Insiden"])

with t_list:
    for mon in monitors:
        pings = db.get_ping_logs(mon["id"], limit=35)
        is_up = mon["status"] == "UP"
        
        ssl_days = mon.get("ssl_days_left")
        if ssl_days is not None:
            if ssl_days > 30:
                ssl_badge = f'<span class="badge-ssl-ok">SSL {ssl_days}d</span>'
            elif ssl_days > 7:
                ssl_badge = f'<span class="badge-ssl-warn">SSL {ssl_days}d exp</span>'
            else:
                ssl_badge = f'<span class="badge-ssl-err">SSL {ssl_days}d exp</span>'
        else:
            ssl_badge = '<span style="color:#64748b; font-size:11px; font-family:monospace;">NO SSL</span>'

        status_badge = '<span class="badge-ok">UP 200</span>' if is_up else '<span class="badge-fail">DOWN</span>'

        with st.container():
            c_info, c_spark, c_del = st.columns([0.48, 0.44, 0.08])
            
            with c_info:
                st.markdown(
                    ui_helpers.render_template(
                        "endpoint_card",
                        name=mon["name"],
                        status_badge=status_badge,
                        ssl_badge=ssl_badge,
                        url=mon["url"],
                        server=mon.get("server_header") or "-",
                        size_kb=mon.get("response_size_kb") or 0.0,
                        content_type=mon.get("content_type") or "-",
                        latency=mon["last_latency_ms"],
                        last_checked=mon["last_checked_at"] or "-"
                    ),
                    unsafe_allow_html=True
                )
                
                if pings:
                    bars_tags = "".join([f'<div class="{"bar-pill-up" if p["is_up"] else "bar-pill-down"}"></div>' for p in pings[-20:]])
                    st.markdown(ui_helpers.render_template("strip_bar", bars=bars_tags), unsafe_allow_html=True)

            with c_spark:
                if pings:
                    df = pd.DataFrame(pings)
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=df["checked_at"],
                        y=df["latency_ms"],
                        mode="lines",
                        line=dict(color="#38bdf8", width=1.5),
                        fill="tozeroy",
                        fillcolor="rgba(56, 189, 248, 0.05)"
                    ))
                    fig.update_layout(
                        height=90,
                        margin=dict(l=0, r=0, t=10, b=0),
                        plot_bgcolor="rgba(0,0,0,0)",
                        paper_bgcolor="rgba(0,0,0,0)",
                        xaxis=dict(showgrid=False, showticklabels=False),
                        yaxis=dict(showgrid=True, gridcolor="#1e293b", tickfont=dict(size=9, color="#64748b")),
                    )
                    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

            with c_del:
                st.write("")
                if st.button("Hapus", key=f"d_{mon['id']}"):
                    db.delete_monitor(mon["id"], user_id)
                    st.rerun()

            st.write("")

with t_logs:
    incidents = db.get_incidents(user_id)
    if not incidents:
        st.caption("Belum ada rekaman downtime pada endpoint yang terdaftar.")
    else:
        df_inc = pd.DataFrame(incidents)[["monitor_name", "url", "error_message", "started_at", "resolved_at", "duration_minutes", "status"]]
        df_inc.columns = ["Endpoint", "URL", "Penyebab Error", "Mulai Down", "Waktu Pulih", "Durasi (m)", "Status"]
        st.dataframe(df_inc, use_container_width=True, hide_index=True)
