import os
import datetime
from flask import Flask, send_from_directory, request, jsonify, session, redirect
from werkzeug.utils import secure_filename
import models

app = Flask(__name__)
app.secret_key = 'piklo_ultra_secure'

# --- Folder Setup ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_FOLDER = os.path.join(BASE_DIR, '..', 'frontend')
UPLOAD_FOLDER = os.path.join(FRONTEND_FOLDER, 'images', 'uploads')

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Database start karein
models.init_db()

# ===========================
#        PAGE ROUTES
# ===========================

@app.route('/')
def home():
    if 'username' not in session:
        return redirect('/login.html')
    return send_from_directory(FRONTEND_FOLDER, 'index.html')

@app.route('/<page>.html')
def pages(page):
    return send_from_directory(FRONTEND_FOLDER, f'{page}.html')

# Profile ke liye 2 routes (Ek khud ki, Ek doosron ki)
@app.route('/profile')
@app.route('/profile/<username>')
def profile(username=None):
    if 'username' not in session:
        return redirect('/login.html')
    return send_from_directory(FRONTEND_FOLDER, 'profile.html')

@app.route('/reels')
def reels():
    if 'username' not in session:
        return redirect('/login.html')
    return send_from_directory(FRONTEND_FOLDER, 'reels.html')

@app.route('/<path:filename>')
def static_files(filename):
    return send_from_directory(FRONTEND_FOLDER, filename)


# ===========================
#       API ENDPOINTS
# ===========================

@app.route('/api/signup', methods=['POST'])
def signup():
    success = models.create_user(request.json.get('username'), request.json.get('password'))
    return jsonify({'success': success})

@app.route('/api/login', methods=['POST'])
def login():
    if models.check_login(request.json.get('username'), request.json.get('password')):
        session['username'] = request.json.get('username')
        return jsonify({'success': True})
    return jsonify({'success': False})

@app.route('/api/logout')
def logout():
    session.pop('username', None)
    return redirect('/login.html')

@app.route('/api/posts', methods=['GET'])
def get_posts():
    if 'username' not in session:
        return jsonify({'posts': []})
    
    current_user = session['username']
    feed = models.get_feed_mixed()
    
    # Check karein follow status aur ownership
    for item in feed:
        item['is_following'] = models.is_following(current_user, item['username'])
        item['is_mine'] = (item['username'] == current_user)
        
    return jsonify({'posts': feed, 'current_user': current_user})

@app.route('/api/reels_scroll')
def get_reels_scroll():
    if 'username' not in session:
        return jsonify([])
    return jsonify(models.get_all_reels_scroll())

@app.route('/api/upload', methods=['POST'])
def upload():
    if 'username' not in session:
        return jsonify({'success': False})
    
    file = request.files.get('image') or request.files.get('video')
    is_video = request.files.get('video') is not None
    
    if file:
        filename = f"file_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}_{secure_filename(file.filename)}"
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        
        if is_video:
            models.create_reel(filename, session['username'], "Reel Upload")
        else:
            models.create_post(filename, session['username'], "Uploaded via Piklo")
            
        return jsonify({'success': True})
    return jsonify({'success': False})

@app.route('/api/action', methods=['POST'])
def action():
    if 'username' not in session:
        return jsonify({'success': False})
    
    data = request.json
    act = data.get('action')
    item_id = data.get('id')
    item_type = data.get('type')
    
    if act == 'like':
        models.like_item(item_id, item_type)
    elif act == 'comment':
        models.add_comment_mixed(item_id, item_type, session['username'], data.get('text'))
    elif act == 'delete':
        return jsonify({'success': models.delete_item(item_id, item_type, session['username'])})
        
    return jsonify({'success': True})

@app.route('/api/get_profile_data')
def get_profile_data():
    if 'username' not in session:
        return jsonify({'success': False})
    
    target_user = request.args.get('username') or session['username']
    if target_user == 'null':
        target_user = session['username']
    
    bio = models.get_user_info(target_user)
    if bio is None:
        return jsonify({'success': False})
    
    posts, reels = models.get_user_content(target_user)
    followers, following = models.get_follow_stats(target_user)
    
    return jsonify({
        'success': True,
        'username': target_user,
        'bio': bio,
        'posts': posts,
        'reels': reels,
        'followers': followers,
        'following': following,
        'is_me': (session['username'] == target_user),
        'is_following': models.is_following(session['username'], target_user)
    })

@app.route('/api/follow', methods=['POST'])
def follow():
    models.follow_user(session['username'], request.json.get('username'))
    return jsonify({'success': True})

@app.route('/api/unfollow', methods=['POST'])
def unfollow():
    models.unfollow_user(session['username'], request.json.get('username'))
    return jsonify({'success': True})

@app.route('/api/search')
def search():
    return jsonify(models.search_users(request.args.get('q', '')))

@app.route('/api/update_profile', methods=['POST'])
def update_profile():
    models.update_bio(session['username'], request.json.get('bio'))
    return jsonify({'success': True})

if __name__ == '__main__':
    print("Server Running on http://127.0.0.1:5000")
    app.run(debug=True)
