import httpx
import time
import socket
import ssl
from urllib.parse import urlparse
from datetime import datetime
import db

def get_ssl_expiry_days(url: str):
    try:
        parsed = urlparse(url)
        if parsed.scheme != "https":
            return None
        hostname = parsed.hostname
        port = parsed.port or 443
        
        ctx = ssl.create_default_context()
        with socket.create_connection((hostname, port), timeout=4.0) as sock:
            with ctx.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert = ssock.getpeercert()
                expire_date = datetime.strptime(cert['notAfter'], "%b %d %H:%M:%S %Y %Z")
                remaining_days = (expire_date - datetime.utcnow()).days
                return remaining_days
    except Exception:
        return None

def ping_target(url: str, timeout: float = 6.0):
    start = time.perf_counter()
    try:
        headers = {"User-Agent": "PulseWatch-Observability-Agent/1.0"}
        with httpx.Client(timeout=timeout, follow_redirects=True, headers=headers) as client:
            resp = client.get(url)
            latency = int((time.perf_counter() - start) * 1000)
            is_up = 200 <= resp.status_code < 400
            
            # Ekstraksi Metadata Server Header
            server = resp.headers.get("server", "Cloud/Unknown")
            content_type = resp.headers.get("content-type", "-").split(";")[0]
            size_kb = round(len(resp.content) / 1024, 2)
            
            meta = {
                "server": server,
                "content_type": content_type,
                "size_kb": size_kb
            }
            return is_up, resp.status_code, latency, meta, None
    except httpx.TimeoutException:
        latency = int((time.perf_counter() - start) * 1000)
        return False, 0, latency, {}, "Connection Timeout (> 6s)"
    except Exception as e:
        latency = int((time.perf_counter() - start) * 1000)
        return False, 0, latency, {}, str(e)

def run_health_check_for_user(user_id: int):
    monitors = db.get_user_monitors(user_id)
    conn = db.get_connection()
    c = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for mon in monitors:
        mon_id = mon["id"]
        is_up, status_code, latency, meta, err = ping_target(mon["url"])
        new_status = "UP" if is_up else "DOWN"
        ssl_days = get_ssl_expiry_days(mon["url"])
        
        srv = meta.get("server", "-")
        ctype = meta.get("content_type", "-")
        sz = meta.get("size_kb", 0.0)

        # 1. Catat ke ping_logs
        c.execute("""
            INSERT INTO ping_logs (monitor_id, status_code, latency_ms, is_up, checked_at)
            VALUES (?, ?, ?, ?, ?)
        """, (mon_id, status_code, latency, 1 if is_up else 0, now_str))

        # 2. Update metadata lengkap monitor
        c.execute("""
            UPDATE monitors 
            SET status = ?, last_latency_ms = ?, ssl_days_left = ?, 
                server_header = ?, content_type = ?, response_size_kb = ?,
                last_checked_at = ?
            WHERE id = ?
        """, (new_status, latency, ssl_days, srv, ctype, sz, now_str, mon_id))

        # 3. Logika Insiden
        active_inc = c.execute(
            "SELECT id, started_at FROM incidents WHERE monitor_id = ? AND status = 'OPEN'",
            (mon_id,)
        ).fetchone()

        if not is_up and not active_inc:
            c.execute("""
                INSERT INTO incidents (monitor_id, error_message, started_at, status)
                VALUES (?, ?, ?, 'OPEN')
            """, (mon_id, err or f"HTTP Status {status_code}", now_str))

        elif is_up and active_inc:
            inc_id = active_inc["id"]
            start_dt = datetime.strptime(active_inc["started_at"], "%Y-%m-%d %H:%M:%S")
            now_dt = datetime.strptime(now_str, "%Y-%m-%d %H:%M:%S")
            duration = max(1, int((now_dt - start_dt).total_seconds() / 60))

            c.execute("""
                UPDATE incidents 
                SET resolved_at = ?, duration_minutes = ?, status = 'RESOLVED'
                WHERE id = ?
            """, (now_str, duration, inc_id))

    conn.commit()
    conn.close()
