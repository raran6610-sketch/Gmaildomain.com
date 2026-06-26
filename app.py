import random
import string
import time
import json
import re
import sqlite3
from datetime import datetime, timedelta
from flask import Flask, render_template_string, jsonify, request
import threading
import asyncio
import aiohttp

app = Flask(__name__)
DB_FILE = "raps_tempgbox_premium.db"

class RapsTempGBoxPremium:
    def __init__(self):
        self.init_db()
        self.inboxes = {}
        print("🚀 Raps TempGBox PREMIUM GOD MODE ACTIVATED")

    def init_db(self):
        conn = sqlite3.connect(DB_FILE)
        conn.execute('''CREATE TABLE IF NOT EXISTS emails (
            email TEXT PRIMARY KEY,
            created_at TEXT,
            expires_at TEXT,
            messages TEXT DEFAULT '[]'
        )''')
        conn.commit()
        conn.close()

    def generate_premium_email(self):
        username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=12))
        domains = ["@tempgbox.net", "@gmailnator.com", "@smail.pro", "@1secmail.com"]
        email = f"{username}{random.randint(100,999)}{random.choice(domains)}"
        
        expires = (datetime.now() + timedelta(hours=24)).isoformat()
        conn = sqlite3.connect(DB_FILE)
        conn.execute("INSERT OR REPLACE INTO emails VALUES (?, ?, ?, ?)", 
                    (email, datetime.now().isoformat(), expires, json.dumps([])))
        conn.commit()
        conn.close()
        
        self.inboxes[email] = []
        return email

    async def fetch_inbox(self, email):
        try:
            if '@1secmail' in email or any(d in email for d in ['temp', 'smail', 'gbox']):
                login, domain = email.split('@')
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"https://www.1secmail.com/api/v1/?action=getMessages&login={login}&domain={domain}") as resp:
                        msgs = await resp.json()
                        for msg in msgs:
                            async with session.get(f"https://www.1secmail.com/api/v1/?action=readMessage&login={login}&domain={domain}&id={msg['id']}") as d:
                                detail = await d.json()
                                body = detail.get('body', '')
                                code = re.search(r'(\d{6})', body)
                                message = {
                                    "from": detail.get('from', 'Anthropic'),
                                    "subject": detail.get('subject', 'Verification'),
                                    "body": body[:800],
                                    "code": code.group(1) if code else None,
                                    "time": datetime.now().isoformat()
                                }
                                # Save to DB
                                conn = sqlite3.connect(DB_FILE)
                                conn.execute("UPDATE emails SET messages = ? WHERE email = ?", 
                                           (json.dumps([message]), email))
                                conn.commit()
                                conn.close()
        except:
            pass

    def get_emails(self):
        conn = sqlite3.connect(DB_FILE)
        cur = conn.execute("SELECT email, expires_at FROM emails WHERE expires_at > ?", (datetime.now().isoformat(),))
        emails = cur.fetchall()
        conn.close()
        return [{"email": e[0], "expires": e[1]} for e in emails]

    def cleanup_expired(self):
        conn = sqlite3.connect(DB_FILE)
        conn.execute("DELETE FROM emails WHERE expires_at < ?", (datetime.now().isoformat(),))
        conn.commit()
        conn.close()

@app.route('/')
def index():
    god = RapsTempGBoxPremium()
    god.cleanup_expired()
    emails = god.get_emails()
    html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Raps TempGBox Premium</title>
        <meta charset="utf-8">
        <style>
            body {{ background: #0a0a0a; color: #00ff9d; font-family: monospace; margin: 0; padding: 20px; }}
            .container {{ max-width: 900px; margin: auto; }}
            button {{ background: #00ff9d; color: #000; border: none; padding: 12px 24px; font-size: 16px; cursor: pointer; margin: 10px 0; }}
            button:hover {{ background: #00cc7a; }}
            .email-list {{ list-style: none; padding: 0; }}
            .email-item {{ background: #1a1a1a; padding: 15px; margin: 10px 0; border-radius: 8px; }}
            .code {{ color: #ffff00; font-weight: bold; }}
            .refresh {{ color: #ff00ff; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 Raps TempGBox PREMIUM</h1>
            <button onclick="generateEmail()">GENERATE NEW EMAIL</button>
            <ul class="email-list" id="emailList"></ul>
        </div>

        <script>
            let currentEmail = null;
            async function generateEmail() {{
                const res = await fetch('/generate', {{method: 'POST'}});
                const data = await res.json();
                currentEmail = data.email;
                loadEmails();
            }}

            async function loadEmails() {{
                const res = await fetch('/emails');
                const emails = await res.json();
                let html = '';
                emails.forEach(e => {{
                    html += `<li class="email-item">
                        <strong>${{e.email}}</strong> (exp: ${{e.expires}})
                        <button onclick="monitor('${{e.email}}')">Monitor Inbox</button>
                    </li>`;
                }});
                document.getElementById('emailList').innerHTML = html;
            }}

            async function monitor(email) {{
                currentEmail = email;
                alert('Monitoring ' + email + ' setiap 0.4 detik... Cek console untuk kode!');
                setInterval(async () => {{
                    const res = await fetch(`/inbox?email=${{encodeURIComponent(email)}}`);
                    const data = await res.json();
                    if (data.messages && data.messages.length > 0) {{
                        data.messages.forEach(m => {{
                            if (m.code) console.log('%c🔥 KODE: ' + m.code, 'color:yellow;font-size:18px');
                        }});
                    }}
                }}, 400); // 0.4 detik
            }}

            loadEmails();
            setInterval(loadEmails, 5000);
        </script>
    </body>
    </html>'''
    return html

@app.route('/generate', methods=['POST'])
def generate():
    god = RapsTempGBoxPremium()
    email = god.generate_premium_email()
    return jsonify({"email": email})

@app.route('/emails')
def emails():
    god = RapsTempGBoxPremium()
    return jsonify(god.get_emails())

@app.route('/inbox')
def inbox():
    email = request.args.get('email')
    god = RapsTempGBoxPremium()
    # Trigger async fetch
    asyncio.run(god.fetch_inbox(email))
    conn = sqlite3.connect(DB_FILE)
    cur = conn.execute("SELECT messages FROM emails WHERE email=?", (email,))
    row = cur.fetchone()
    conn.close()
    messages = json.loads(row[0]) if row else []
    return jsonify({"messages": messages})

if __name__ == "__main__":
    # Background cleanup
    def cleaner():
        while True:
            RapsTempGBoxPremium().cleanup_expired()
            time.sleep(300)
    threading.Thread(target=cleaner, daemon=True).start()
    
    print("🌐 Server running at http://127.0.0.1:6969")
    print("ITU YANG SEDANG TERJADI bos Raps! Premium version siap publish.")
    app.run(host='0.0.0.0', port=6969, debug=False)
