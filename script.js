window.onload = loadPosts;

document.getElementById('imageInput').addEventListener('change', function(event) {
    const file = event.target.files[0];
    if (file) uploadFile(file);
});

function loadPosts() {
    fetch('/api/posts').then(r=>r.json()).then(data => {
        const container = document.querySelector('.feed-container');
        container.innerHTML = '';
        data.posts.forEach(post => {
            const mediaTag = post.type === 'video' 
                ? `<video src="images/uploads/${post.filename}" controls style="width:100%; display:block;"></video>` 
                : `<img src="images/uploads/${post.filename}" style="width:100%; display:block;">`;

            // Follow button logic
            let followBtn = (!post.is_mine && !post.is_following) 
                ? `<button onclick="follow('${post.username}')" style="color:blue; border:none; background:none; cursor:pointer;">Follow</button>` : '';
            
            // Delete button logic
            let delBtn = post.is_mine ? `<button onclick="del(${post.id}, '${post.type}')">🗑️</button>` : '';

            // Comments
            let comments = '';
            post.comments.forEach(c => comments += `<div><b>${c.username}</b>: ${c.text}</div>`);

            // Actions
            let actions = post.is_mine ? '' : `
                <button onclick="act('like', ${post.id}, '${post.type}')">❤️ ${post.likes}</button>
                <input type="text" id="c-${post.id}" placeholder="Comment...">
                <button onclick="act('comment', ${post.id}, '${post.type}')">Post</button>
            `;

            const html = `
                <div class="post-card" style="background:white; margin-bottom:20px; border:1px solid #ddd;">
                    <div style="padding:10px; display:flex; justify-content:space-between;">
                        <b><a href="/profile/${post.username}">${post.username}</a></b> ${followBtn} ${delBtn}
                    </div>
                    ${mediaTag}
                    <div style="padding:10px;">
                        <p>${post.caption}</p>
                        ${actions}
                        <div style="margin-top:10px; font-size:13px;">${comments}</div>
                    </div>
                </div>
            `;
            container.insertAdjacentHTML('beforeend', html);
        });
    });
}

function uploadFile(file) {
    const fd = new FormData(); fd.append('image', file);
    fetch('/api/upload', {method:'POST', body:fd}).then(r=>r.json()).then(d=>{ if(d.success) loadPosts(); });
}

function act(action, id, type) {
    let txt = null;
    if(action === 'comment') {
        txt = document.getElementById(`c-${id}`).value;
        if(!txt) return;
    }
    fetch('/api/action', {
        method:'POST', headers:{'Content-Type':'application/json'},
        body: JSON.stringify({action: action, id: id, type: type, text: txt})
    }).then(r=>r.json()).then(d=>{ if(d.success) loadPosts(); });
}

function del(id, type) {
    if(confirm('Delete?')) act('delete', id, type);
}

function follow(u) {
    fetch('/api/follow', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({username:u})})
    .then(r=>r.json()).then(d=>{ if(d.success) loadPosts(); });
}