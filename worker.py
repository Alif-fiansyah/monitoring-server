import db
import engine

def run():
    db.init_db()
    conn = db.get_connection()
    users = conn.cursor().execute("SELECT id, username FROM users").fetchall()
    conn.close()

    print(f"[*] Menjalankan Scheduled Health Check untuk {len(users)} pengguna...")
    for u in users:
        print(f" -> Memeriksa monitor milik user: {u['username']} (ID: {u['id']})")
        engine.run_health_check_for_user(u["id"])
    print("[✓] Pengecekan selesai.")

if __name__ == "__main__":
    run()
