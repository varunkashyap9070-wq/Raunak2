"""
=============================================================================
ChatIndia - Real-Time WhatsApp Clone with Phone Login & WebSockets (Python)
=============================================================================
Run with:
    pip install fastapi uvicorn python-multipart websockets
    python app.py
Open:
    http://localhost:8000
=============================================================================
"""

import os
import json
import time
import uuid
import sqlite3
from typing import Dict, List, Set
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn

app = FastAPI(title="ChatIndia Python")

# ---------------------------------------------------------------------------
# 1. डेटाबेस इनिशियलाइज़ेशन (SQLite)
# ---------------------------------------------------------------------------
DB_FILE = "chatindia.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # Users table
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        phone TEXT UNIQUE,
        name TEXT,
        about TEXT,
        avatar TEXT,
        created_at REAL
    )
    """)
    # Chats table
    c.execute("""
    CREATE TABLE IF NOT EXISTS chats (
        id TEXT PRIMARY KEY,
        name TEXT,
        is_group INTEGER,
        avatar TEXT,
        created_at REAL
    )
    """)
    # Chat Participants
    c.execute("""
    CREATE TABLE IF NOT EXISTS chat_participants (
        chat_id TEXT,
        user_id TEXT,
        PRIMARY KEY (chat_id, user_id)
    )
    """)
    # Messages table
    c.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id TEXT PRIMARY KEY,
        chat_id TEXT,
        sender_id TEXT,
        sender_name TEXT,
        text TEXT,
        msg_type TEXT,
        media_url TEXT,
        timestamp REAL,
        status TEXT,
        deleted_for_everyone INTEGER DEFAULT 0
    )
    """)
    
    # शुरुआती डेमो यूज़र्स यदि डेटाबेस खाली हो
    c.execute("SELECT COUNT(*) FROM users")
    if c.fetchone()[0] == 0:
        demo_users = [
            ("user_rahul", "+91 9876543210", "Rahul Sharma", "Coding in Bengaluru ☕ 💻", "https://api.dicebear.com/7.x/bottts/svg?seed=Rahul", time.time()),
            ("user_priya", "+91 9123456789", "Priya Patel", "Designing UI/UX • Mumbai 🎨 ✨", "https://api.dicebear.com/7.x/bottts/svg?seed=Priya", time.time()),
            ("user_amit", "+91 9456789012", "Amit Verma", "Exploring Himachal 🏔️", "https://api.dicebear.com/7.x/bottts/svg?seed=Amit", time.time())
        ]
        c.executemany("INSERT INTO users VALUES (?, ?, ?, ?, ?, ?)", demo_users)
        
        # डेमो ग्रुप चैट
        group_id = "group_tech_india"
        c.execute("INSERT INTO chats VALUES (?, ?, ?, ?, ?)", (group_id, "Tech India Devs 🚀🇮🇳", 1, "https://api.dicebear.com/7.x/identicon/svg?seed=TechIndia", time.time()))
        for u in demo_users:
            c.execute("INSERT INTO chat_participants VALUES (?, ?)", (group_id, u[0]))
            
        c.execute("""
        INSERT INTO messages VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            str(uuid.uuid4()), group_id, "user_rahul", "Rahul Sharma",
            "Namaste! Welcome to ChatIndia Python Edition 🇮🇳",
            "text", "", time.time(), "read", 0
        ))
        
    conn.commit()
    conn.close()

init_db()

# ---------------------------------------------------------------------------
# 2. WebSocket कनेक्शन मैनेजर (रियल-टाइम मल्टी-यूज़र सिंक)
# ---------------------------------------------------------------------------
class ConnectionManager:
    def __init__(self):
        # userId -> Set[WebSocket]
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, user_id: str, websocket: WebSocket):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(websocket)
        # ऑनलाइन स्टेटस ब्रॉडकास्ट
        await self.broadcast({
            "type": "USER_PRESENCE",
            "user_id": user_id,
            "is_online": True
        })

    async def disconnect(self, user_id: str, websocket: WebSocket):
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
                await self.broadcast({
                    "type": "USER_PRESENCE",
                    "user_id": user_id,
                    "is_online": False,
                    "last_seen": time.time()
                })

    async def broadcast(self, message: dict):
        payload = json.dumps(message)
        for user_conns in list(self.active_connections.values()):
            for conn in list(user_conns):
                try:
                    await conn.send_text(payload)
                except Exception:
                    pass

manager = ConnectionManager()

# ---------------------------------------------------------------------------
# 3. REST API रूट्स (Phone Login, Chats, Messages)
# ---------------------------------------------------------------------------
@app.post("/api/login")
def login(phone: str = Form(...), otp: str = Form(...), name: str = Form(""), about: str = Form("")):
    # 6 डिजिट OTP डेमो वेरिफिकेशन (जैसे 123456)
    if len(otp) != 6:
        return JSONResponse({"status": "error", "message": "Invalid OTP. Enter 6 digits."}, status_code=400)
    
    phone = phone.strip()
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, phone, name, about, avatar FROM users WHERE phone = ?", (phone,))
    row = c.fetchone()
    
    if row:
        user = {"id": row[0], "phone": row[1], "name": row[2], "about": row[3], "avatar": row[4]}
    else:
        user_id = "user_" + str(uuid.uuid4())[:8]
        user_name = name.strip() or f"User {phone[-4:]}"
        user_about = about.strip() or "Hey there! I am using ChatIndia 🇮🇳"
        avatar = f"https://api.dicebear.com/7.x/bottts/svg?seed={user_name}"
        c.execute("INSERT INTO users VALUES (?, ?, ?, ?, ?, ?)", (user_id, phone, user_name, user_about, avatar, time.time()))
        c.execute("INSERT OR IGNORE INTO chat_participants VALUES ('group_tech_india', ?)", (user_id,))
        conn.commit()
        user = {"id": user_id, "phone": phone, "name": user_name, "about": user_about, "avatar": avatar}
    
    conn.close()
    return {"status": "success", "user": user}

@app.get("/api/chats/{user_id}")
def get_user_chats(user_id: str):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
    SELECT c.id, c.name, c.is_group, c.avatar, c.created_at
    FROM chats c
    JOIN chat_participants cp ON c.id = cp.chat_id
    WHERE cp.user_id = ?
    ORDER BY c.created_at DESC
    """, (user_id,))
    
    chats = []
    for r in c.fetchall():
        chat_id = r[0]
        c.execute("""
        SELECT id, sender_id, sender_name, text, msg_type, timestamp, status, deleted_for_everyone
        FROM messages WHERE chat_id = ? ORDER BY timestamp DESC LIMIT 1
        """, (chat_id,))
        last_msg_row = c.fetchone()
        last_msg = None
        if last_msg_row:
            last_msg = {
                "id": last_msg_row[0],
                "senderId": last_msg_row[1],
                "senderName": last_msg_row[2],
                "text": last_msg_row[3],
                "type": last_msg_row[4],
                "timestamp": last_msg_row[5],
                "status": last_msg_row[6],
                "deletedForEveryone": bool(last_msg_row[7])
            }
            
        c.execute("SELECT user_id FROM chat_participants WHERE chat_id = ?", (chat_id,))
        participants = [p[0] for p in c.fetchall()]
        
        chats.append({
            "id": chat_id,
            "name": r[1],
            "isGroup": bool(r[2]),
            "avatar": r[3],
            "participants": participants,
            "lastMessage": last_msg
        })
        
    conn.close()
    return {"chats": chats}

@app.get("/api/messages/{chat_id}")
def get_messages(chat_id: str):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
    SELECT id, chat_id, sender_id, sender_name, text, msg_type, media_url, timestamp, status, deleted_for_everyone
    FROM messages WHERE chat_id = ? ORDER BY timestamp ASC
    """, (chat_id,))
    
    msgs = []
    for r in c.fetchall():
        msgs.append({
            "id": r[0],
            "chatId": r[1],
            "senderId": r[2],
            "senderName": r[3],
            "text": r[4],
            "type": r[5],
            "mediaUrl": r[6],
            "timestamp": r[7],
            "status": r[8],
            "deletedForEveryone": bool(r[9])
        })
    conn.close()
    return {"messages": msgs}

@app.get("/api/users")
def get_all_users():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, phone, name, about, avatar FROM users")
    users = [{"id": r[0], "phone": r[1], "name": r[2], "about": r[3], "avatar": r[4], "isOnline": r[0] in manager.active_connections} for r in c.fetchall()]
    conn.close()
    return {"users": users}

@app.post("/api/chats/create")
def create_chat(user_id: str = Form(...), target_id: str = Form(...), name: str = Form(""), is_group: bool = Form(False)):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    chat_id = "chat_" + str(uuid.uuid4())[:8] if not is_group else "group_" + str(uuid.uuid4())[:8]
    chat_name = name or "Direct Chat"
    avatar = f"https://api.dicebear.com/7.x/identicon/svg?seed={chat_name}"
    
    c.execute("INSERT INTO chats VALUES (?, ?, ?, ?, ?)", (chat_id, chat_name, int(is_group), avatar, time.time()))
    c.execute("INSERT INTO chat_participants VALUES (?, ?)", (chat_id, user_id))
    c.execute("INSERT INTO chat_participants VALUES (?, ?)", (chat_id, target_id))
    conn.commit()
    conn.close()
    return {"status": "success", "chat_id": chat_id}

# ---------------------------------------------------------------------------
# 4. WebSocket रियल-टाइम चैट एंडपॉइंट
# ---------------------------------------------------------------------------
@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await manager.connect(user_id, websocket)
    try:
        while True:
            raw_data = await websocket.receive_text()
            data = json.loads(raw_data)
            msg_type = data.get("type")
            
            if msg_type == "SEND_MESSAGE":
                msg_id = str(uuid.uuid4())
                chat_id = data["chatId"]
                text = data["text"]
                m_type = data.get("msgType", "text")
                now = time.time()
                
                conn = sqlite3.connect(DB_FILE)
                c = conn.cursor()
                c.execute("SELECT name FROM users WHERE id = ?", (user_id,))
                s_row = c.fetchone()
                sender_name = s_row[0] if s_row else "User"
                
                c.execute("""
                INSERT INTO messages VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (msg_id, chat_id, user_id, sender_name, text, m_type, "", now, "delivered", 0))
                conn.commit()
                conn.close()
                
                # सभी कनेक्टेड यूज़र्स को तुरंत मैसेज भेजें
                await manager.broadcast({
                    "type": "NEW_MESSAGE",
                    "message": {
                        "id": msg_id,
                        "chatId": chat_id,
                        "senderId": user_id,
                        "senderName": sender_name,
                        "text": text,
                        "type": m_type,
                        "timestamp": now,
                        "status": "delivered",
                        "deletedForEveryone": False
                    }
                })
                
            elif msg_type == "TYPING":
                await manager.broadcast({
                    "type": "USER_TYPING",
                    "userId": user_id,
                    "chatId": data["chatId"],
                    "isTyping": data["isTyping"]
                })
                
    except WebSocketDisconnect:
        await manager.disconnect(user_id, websocket)

# ---------------------------------------------------------------------------
# 5. फ्रंटएंड HTML + WhatsApp Dark UI (सिंगल-फाइल)
# ---------------------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
def index():
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ChatIndia - Python WebSockets</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        body { background: #0c1317; color: #e9edef; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; overflow: hidden; }
        ::-webkit-scrollbar { width: 5px; }
        ::-webkit-scrollbar-thumb { background: rgba(134,150,160,0.3); border-radius: 4px; }
        .bg-doodle { background-image: radial-gradient(#1f2c34 1px, transparent 1px); background-size: 20px 20px; }
    </style>
</head>
<body class="h-screen w-screen flex flex-col">

    <!-- LOGIN SCREEN -->
    <div id="loginScreen" class="fixed inset-0 z-50 bg-[#0c1317] flex items-center justify-center p-4">
        <div class="bg-[#111b21] border border-[#2a3942] rounded-2xl w-full max-w-md p-8 shadow-2xl">
            <div class="text-center mb-6">
                <div class="w-14 h-14 bg-[#00a884] rounded-2xl mx-auto flex items-center justify-center text-3xl shadow-lg mb-2">🇮🇳</div>
                <h1 class="text-2xl font-bold text-white">ChatIndia Python</h1>
                <p class="text-xs text-[#8696a0] mt-1">Real-Time WebSockets & Phone Login</p>
                <div class="mt-3 text-[11px] bg-[#1f2c34] text-[#f59e0b] px-3 py-1.5 rounded-full inline-block border border-[#2a3942]">
                    <i class="fa-solid fa-fire mr-1"></i> Demo: कोई भी 6 डिजिट OTP डालें (उदा. 123456)
                </div>
            </div>

            <form id="loginForm" class="space-y-4">
                <div>
                    <label class="block text-xs font-semibold text-[#8696a0] uppercase mb-1">Phone Number</label>
                    <div class="flex gap-2">
                        <span class="bg-[#202c33] border border-[#2a3942] text-white px-3 py-2.5 rounded-xl font-medium text-sm flex items-center">🇮🇳 +91</span>
                        <input type="tel" id="loginPhone" value="9876543210" placeholder="10-digit number" required class="flex-1 bg-[#202c33] border border-[#2a3942] text-white px-3 py-2.5 rounded-xl focus:outline-none focus:border-[#00a884]">
                    </div>
                </div>

                <div>
                    <label class="block text-xs font-semibold text-[#8696a0] uppercase mb-1">6-Digit OTP</label>
                    <input type="text" id="loginOtp" value="123456" maxlength="6" class="w-full bg-[#202c33] border border-[#2a3942] text-white text-center tracking-widest text-lg font-bold py-2.5 rounded-xl focus:outline-none focus:border-[#00a884]">
                </div>

                <div>
                    <label class="block text-xs font-semibold text-[#8696a0] uppercase mb-1">Your Name</label>
                    <input type="text" id="loginName" placeholder="e.g. Rahul Sharma" class="w-full bg-[#202c33] border border-[#2a3942] text-white px-3 py-2.5 rounded-xl focus:outline-none focus:border-[#00a884] text-sm">
                </div>

                <button type="submit" class="w-full py-3 bg-[#00a884] hover:bg-[#02906f] text-white font-bold rounded-xl shadow-lg transition mt-4 cursor-pointer">
                    Login with Phone
                </button>
            </form>
        </div>
    </div>

    <!-- MAIN CHAT APP -->
    <div id="mainApp" class="flex-1 flex overflow-hidden hidden">
        <!-- SIDEBAR -->
        <div class="w-full md:w-[380px] bg-[#111b21] border-r border-[#222e35] flex flex-col">
            <div class="h-16 px-4 bg-[#202c33] flex items-center justify-between border-b border-[#222e35]">
                <div class="flex items-center gap-3">
                    <img id="myAvatar" class="w-10 h-10 rounded-full ring-2 ring-[#00a884]" src="">
                    <div>
                        <div id="myName" class="font-bold text-sm text-white">My Name</div>
                        <div class="text-[11px] text-[#25d366]">● Online (WebSocket)</div>
                    </div>
                </div>
                <div class="flex gap-2">
                    <button onclick="window.open(window.location.href, '_blank')" class="text-xs px-2.5 py-1 bg-[#1f2c34] hover:bg-[#2a3942] text-[#25d366] rounded-lg border border-[#2a3942]">
                        <i class="fa-solid fa-up-right-from-square mr-1"></i> 2nd Tab
                    </button>
                </div>
            </div>
            <div id="chatList" class="flex-1 overflow-y-auto divide-y divide-[#222e35]/50"></div>
        </div>

        <!-- CHAT AREA -->
        <div class="flex-1 bg-[#0b141a] flex flex-col relative bg-doodle">
            <div class="h-16 px-4 bg-[#202c33] border-b border-[#222e35] flex items-center justify-between">
                <div class="flex items-center gap-3">
                    <img id="activeChatAvatar" class="w-10 h-10 rounded-full" src="">
                    <div>
                        <div id="activeChatName" class="font-bold text-sm text-white">Select a Chat</div>
                        <div id="activeChatStatus" class="text-xs text-[#8696a0]">ChatIndia Python</div>
                    </div>
                </div>
            </div>

            <div id="messagesContainer" class="flex-1 overflow-y-auto p-4 space-y-3"></div>

            <div class="bg-[#202c33] p-3 border-t border-[#222e35] flex items-center gap-3">
                <input id="messageInput" type="text" placeholder="Type a message..." class="flex-1 bg-[#2a3942] text-white px-4 py-2.5 rounded-xl border border-transparent focus:border-[#00a884] focus:outline-none text-sm">
                <button id="sendBtn" class="w-11 h-11 bg-[#00a884] hover:bg-[#02906f] text-white rounded-full flex items-center justify-center shadow-lg cursor-pointer">
                    <i class="fa-solid fa-paper-plane text-sm"></i>
                </button>
            </div>
        </div>
    </div>

    <script>
        let currentUser = null;
        let ws = null;
        let activeChatId = null;

        document.getElementById('loginForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const phone = '+91 ' + document.getElementById('loginPhone').value.trim();
            const otp = document.getElementById('loginOtp').value.trim();
            const name = document.getElementById('loginName').value.trim();

            const fd = new FormData();
            fd.append('phone', phone);
            fd.append('otp', otp);
            fd.append('name', name);

            const res = await fetch('/api/login', { method: 'POST', body: fd });
            const data = await res.json();

            if (data.status === 'success') {
                currentUser = data.user;
                document.getElementById('loginScreen').classList.add('hidden');
                document.getElementById('mainApp').classList.remove('hidden');
                document.getElementById('myName').innerText = currentUser.name;
                document.getElementById('myAvatar').src = currentUser.avatar;

                initWebSocket();
                loadChats();
            }
        });

        function initWebSocket() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            ws = new WebSocket(`${protocol}//${window.location.host}/ws/${currentUser.id}`);

            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                if (data.type === 'NEW_MESSAGE') {
                    if (data.message.chatId === activeChatId) {
                        appendMessage(data.message);
                    }
                    loadChats();
                }
            };
        }

        async function loadChats() {
            const res = await fetch(`/api/chats/${currentUser.id}`);
            const data = await res.json();
            const list = document.getElementById('chatList');
            list.innerHTML = '';

            data.chats.forEach(chat => {
                const div = document.createElement('div');
                div.className = `p-3.5 flex items-center gap-3 cursor-pointer hover:bg-[#202c33] transition ${activeChatId === chat.id ? 'bg-[#2a3942]' : ''}`;
                div.onclick = () => selectChat(chat);
                const lastTxt = chat.lastMessage ? chat.lastMessage.text : 'Tap to chat';
                div.innerHTML = `
                    <img class="w-12 h-12 rounded-full" src="${chat.avatar}">
                    <div class="flex-1 min-w-0">
                        <div class="flex justify-between items-center"><span class="font-bold text-sm text-white truncate">${chat.name}</span></div>
                        <p class="text-xs text-[#8696a0] truncate mt-0.5">${lastTxt}</p>
                    </div>
                `;
                list.appendChild(div);
            });

            if (!activeChatId && data.chats.length > 0) selectChat(data.chats[0]);
        }

        async function selectChat(chat) {
            activeChatId = chat.id;
            document.getElementById('activeChatName').innerText = chat.name;
            document.getElementById('activeChatAvatar').src = chat.avatar;

            const res = await fetch(`/api/messages/${chat.id}`);
            const data = await res.json();
            const container = document.getElementById('messagesContainer');
            container.innerHTML = '';
            data.messages.forEach(m => appendMessage(m));
        }

        function appendMessage(m) {
            const container = document.getElementById('messagesContainer');
            const isMe = m.senderId === currentUser.id;
            const bubble = document.createElement('div');
            bubble.className = `flex flex-col ${isMe ? 'items-end' : 'items-start'}`;
            const timeStr = new Date(m.timestamp * 1000).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
            bubble.innerHTML = `
                <div class="max-w-[70%] rounded-xl px-3.5 py-2 text-sm shadow ${isMe ? 'bg-[#005c4b] text-white rounded-tr-none' : 'bg-[#202c33] text-white rounded-tl-none'}">
                    ${!isMe ? `<div class="text-[11px] font-bold text-[#25d366] mb-0.5">${m.senderName}</div>` : ''}
                    <div>${m.text}</div>
                    <div class="text-[10px] text-[#8696a0] text-right mt-1">${timeStr} ${isMe ? '<i class="fa-solid fa-check-double text-[#53bdeb] ml-1"></i>' : ''}</div>
                </div>
            `;
            container.appendChild(bubble);
            container.scrollTop = container.scrollHeight;
        }

        document.getElementById('sendBtn').onclick = sendMessage;
        document.getElementById('messageInput').onkeydown = (e) => { if (e.key === 'Enter') sendMessage(); };

        function sendMessage() {
            const input = document.getElementById('messageInput');
            const text = input.value.trim();
            if (!text || !activeChatId || !ws) return;
            ws.send(JSON.stringify({ type: 'SEND_MESSAGE', chatId: activeChatId, text: text }));
            input.value = '';
        }
    </script>
</body>
</html>
    """

if __name__ == "__main__":
    print("Starting ChatIndia Python on http://localhost:8000 ...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
