import sqlite3

DB_NAME = "piklo.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # 1. Users
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL, password TEXT NOT NULL, bio TEXT DEFAULT 'Hello! I am using Piklo.'
    )''')
    # 2. Posts (Images)
    cursor.execute('''CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT, filename TEXT NOT NULL, username TEXT NOT NULL, caption TEXT, likes INTEGER DEFAULT 0, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')
    # 3. Reels (Videos)
    cursor.execute('''CREATE TABLE IF NOT EXISTS reels (
        id INTEGER PRIMARY KEY AUTOINCREMENT, filename TEXT NOT NULL, username TEXT NOT NULL, caption TEXT, likes INTEGER DEFAULT 0, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')
    # 4. Comments
    cursor.execute('''CREATE TABLE IF NOT EXISTS comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT, post_id INTEGER, username TEXT, text TEXT, FOREIGN KEY(post_id) REFERENCES posts(id)
    )''')
    # 5. Reel Comments
    cursor.execute('''CREATE TABLE IF NOT EXISTS reel_comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT, reel_id INTEGER, username TEXT, text TEXT, FOREIGN KEY(reel_id) REFERENCES reels(id)
    )''')
    # 6. Followers
    cursor.execute('''CREATE TABLE IF NOT EXISTS followers (
        id INTEGER PRIMARY KEY AUTOINCREMENT, follower TEXT, followed TEXT, UNIQUE(follower, followed)
    )''')
    
    conn.commit()
    conn.close()

# --- Common Helpers ---
def create_user(u, p):
    try: conn=sqlite3.connect(DB_NAME); conn.cursor().execute("INSERT INTO users (username, password) VALUES (?, ?)", (u, p)); conn.commit(); conn.close(); return True
    except: return False
def check_login(u, p): conn=sqlite3.connect(DB_NAME); c=conn.cursor(); c.execute("SELECT * FROM users WHERE username=? AND password=?", (u,p)); r=c.fetchone(); conn.close(); return r
def get_user_info(u): conn=sqlite3.connect(DB_NAME); c=conn.cursor(); c.execute("SELECT bio FROM users WHERE username=?", (u,)); r=c.fetchone(); conn.close(); return r[0] if r else None
def update_bio(u, b): conn=sqlite3.connect(DB_NAME); conn.cursor().execute("UPDATE users SET bio=? WHERE username=?", (b, u)); conn.commit(); conn.close()
def follow_user(fr, fd): 
    if fr==fd: return False
    try: conn=sqlite3.connect(DB_NAME); conn.cursor().execute("INSERT INTO followers (follower, followed) VALUES (?, ?)", (fr, fd)); conn.commit(); conn.close(); return True
    except: return False
def unfollow_user(fr, fd): conn=sqlite3.connect(DB_NAME); conn.cursor().execute("DELETE FROM followers WHERE follower=? AND followed=?", (fr, fd)); conn.commit(); conn.close()
def get_follow_stats(u): 
    conn=sqlite3.connect(DB_NAME); c=conn.cursor()
    c.execute("SELECT COUNT(*) FROM followers WHERE followed=?", (u,)); fr=c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM followers WHERE follower=?", (u,)); fg=c.fetchone()[0]; conn.close(); return fr, fg
def is_following(fr, fd): conn=sqlite3.connect(DB_NAME); c=conn.cursor(); c.execute("SELECT * FROM followers WHERE follower=? AND followed=?", (fr, fd)); r=c.fetchone(); conn.close(); return True if r else False
def search_users(q): conn=sqlite3.connect(DB_NAME); c=conn.cursor(); c.execute("SELECT username FROM users WHERE username LIKE ? LIMIT 5", ('%'+q+'%',)); r=[x[0] for x in c.fetchall()]; conn.close(); return r

# --- CONTENT LOGIC ---

def create_post(f, u, c=""):
    conn=sqlite3.connect(DB_NAME); conn.cursor().execute("INSERT INTO posts (filename, username, caption, likes) VALUES (?, ?, ?, 0)", (f, u, c)); conn.commit(); conn.close()

def create_reel(f, u, c=""):
    conn=sqlite3.connect(DB_NAME); conn.cursor().execute("INSERT INTO reels (filename, username, caption, likes) VALUES (?, ?, ?, 0)", (f, u, c)); conn.commit(); conn.close()

def get_feed_mixed():
    conn = sqlite3.connect(DB_NAME); c = conn.cursor()
    c.execute("SELECT id, filename, username, caption, likes, timestamp, 'image' as type FROM posts")
    posts = c.fetchall()
    c.execute("SELECT id, filename, username, caption, likes, timestamp, 'video' as type FROM reels")
    reels = c.fetchall()
    
    all_items = posts + reels
    all_items.sort(key=lambda x: x[5], reverse=True)
    
    final = []
    for item in all_items:
        table = "comments" if item[6] == 'image' else "reel_comments"
        col = "post_id" if item[6] == 'image' else "reel_id"
        c.execute(f"SELECT username, text FROM {table} WHERE {col} = ?", (item[0],))
        comments = [{'username': x[0], 'text': x[1]} for x in c.fetchall()]
        
        final.append({
            'id': item[0], 'filename': item[1], 'username': item[2], 'caption': item[3],
            'likes': item[4], 'timestamp': item[5], 'type': item[6], 'comments': comments
        })
    conn.close()
    return final

def get_all_reels_scroll():
    conn = sqlite3.connect(DB_NAME); c = conn.cursor()
    c.execute("SELECT id, filename, username, caption, likes FROM reels ORDER BY RANDOM()")
    reels = []
    for r in c.fetchall():
        c.execute("SELECT username, text FROM reel_comments WHERE reel_id=?", (r[0],))
        coms = [{'username':x[0], 'text':x[1]} for x in c.fetchall()]
        reels.append({'id':r[0], 'filename':r[1], 'username':r[2], 'caption':r[3], 'likes':r[4], 'comments':coms})
    conn.close()
    return reels

def get_user_content(u):
    conn = sqlite3.connect(DB_NAME); c = conn.cursor()
    c.execute("SELECT filename FROM posts WHERE username=? ORDER BY id DESC", (u,)); posts=[x[0] for x in c.fetchall()]
    c.execute("SELECT filename FROM reels WHERE username=? ORDER BY id DESC", (u,)); reels=[x[0] for x in c.fetchall()]
    conn.close()
    return posts, reels

def like_item(id, type):
    table = "posts" if type == 'image' else "reels"
    conn=sqlite3.connect(DB_NAME); conn.cursor().execute(f"UPDATE {table} SET likes=likes+1 WHERE id=?", (id,)); conn.commit(); conn.close()

def add_comment_mixed(id, type, u, text):
    table = "comments" if type == 'image' else "reel_comments"
    col = "post_id" if type == 'image' else "reel_id"
    conn=sqlite3.connect(DB_NAME); conn.cursor().execute(f"INSERT INTO {table} ({col}, username, text) VALUES (?, ?, ?)", (id, u, text)); conn.commit(); conn.close()

def delete_item(id, type, u):
    ptable = "posts" if type == 'image' else "reels"
    ctable = "comments" if type == 'image' else "reel_comments"
    col = "post_id" if type == 'image' else "reel_id"
    conn=sqlite3.connect(DB_NAME); c=conn.cursor()
    c.execute(f"SELECT * FROM {ptable} WHERE id=? AND username=?", (id, u))
    if c.fetchone():
        c.exe
