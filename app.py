from flask import Flask, request, jsonify, session, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from datetime import timedelta
import os
from models import db, bcrypt, User, Story, Comment, Like, WritingPrompt

app = Flask(__name__, static_folder='.', static_url_path='')

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///inkpage.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-key-change-me')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)

# Initialize extensions
db.init_app(app)
bcrypt.init_app(app)
jwt = JWTManager(app)
CORS(app, origins=["http://localhost:5000", "http://127.0.0.1:5000", "http://localhost:5001", "http://127.0.0.1:5001"], supports_credentials=True)

# Create tables
with app.app_context():
    db.create_all()
    # Seed initial writing prompts if none exist
    if WritingPrompt.query.count() == 0:
        initial_prompts = [
            "Write about a letter that arrives 10 years too late, carrying a forgotten promise.",
            "Describe a bookstore where every book writes itself as you read it.",
            "Write a story where the main character discovers they're a character in someone else's novel.",
            "The old library had a secret door behind the poetry section...",
            "Write about the scent of old books and the secret found between page 42 and 43."
        ]
        for prompt in initial_prompts:
            db.session.add(WritingPrompt(prompt=prompt, category='creative'))
        db.session.commit()

# ==================== SERVE FRONTEND ====================

@app.route('/')
def serve_index():
    """Serve the main HTML file"""
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def serve_static_files(path):
    """Serve any static files (CSS, JS, HTML pages)"""
    if os.path.exists(path):
        return send_from_directory('.', path)
    return jsonify({'error': 'File not found'}), 404

# ==================== AUTHENTICATION ROUTES ====================

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    
    # Validate input
    if not data.get('username') or not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Username, email and password are required'}), 400
    
    # Check if user exists
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already registered'}), 400
    
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Username already taken'}), 400
    
    # Create new user
    user = User(
        username=data['username'],
        email=data['email'],
        avatar=data.get('avatar', '📖'),
        bio=data.get('bio', 'Book lover and storyteller')
    )
    user.set_password(data['password'])
    
    db.session.add(user)
    db.session.commit()
    
    # Create access token
    access_token = create_access_token(identity=user.id)
    
    return jsonify({
        'message': 'Registration successful',
        'access_token': access_token,
        'user': user.to_dict()
    }), 201


@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Email and password required'}), 400
    
    # Find user by email
    user = User.query.filter_by(email=data['email']).first()
    
    if not user or not user.check_password(data['password']):
        return jsonify({'error': 'Invalid email or password'}), 401
    
    # Create access token
    access_token = create_access_token(identity=user.id)
    
    return jsonify({
        'message': 'Login successful',
        'access_token': access_token,
        'user': user.to_dict()
    }), 200


@app.route('/api/me', methods=['GET'])
@jwt_required()
def get_current_user():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify({'user': user.to_dict()}), 200


# ==================== STORIES ROUTES ====================

@app.route('/api/stories', methods=['GET'])
def get_stories():
    """Get all published stories (for library)"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 12, type=int)
    genre = request.args.get('genre')
    search = request.args.get('search')
    
    query = Story.query.filter_by(is_published=True)
    
    if genre:
        query = query.filter_by(genre=genre)
    
    if search:
        query = query.filter(
            db.or_(
                Story.title.ilike(f'%{search}%'),
                Story.content.ilike(f'%{search}%'),
                Story.author.has(User.username.ilike(f'%{search}%'))
            )
        )
    
    stories = query.order_by(Story.created_at.desc()).paginate(page=page, per_page=per_page)
    
    return jsonify({
        'stories': [story.to_dict() for story in stories.items],
        'total': stories.total,
        'page': stories.page,
        'pages': stories.pages
    }), 200


@app.route('/api/stories/featured', methods=['GET'])
def get_featured_stories():
    """Get featured stories (most liked/recent)"""
    featured = Story.query.filter_by(is_published=True)\
        .order_by(Story.view_count.desc(), Story.created_at.desc())\
        .limit(6).all()
    
    return jsonify({'stories': [story.to_dict() for story in featured]}), 200


@app.route('/api/stories/<int:story_id>', methods=['GET'])
def get_story(story_id):
    """Get single story by ID"""
    story = Story.query.get_or_404(story_id)
    
    if not story.is_published:
        return jsonify({'error': 'Story not available'}), 404
    
    # Increment view count
    story.view_count += 1
    db.session.commit()
    
    return jsonify({'story': story.to_dict(include_content=True)}), 200


@app.route('/api/stories', methods=['POST'])
@jwt_required()
def create_story():
    """Create a new story"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data.get('title') or not data.get('content'):
        return jsonify({'error': 'Title and content are required'}), 400
    
    story = Story(
        title=data['title'],
        content=data['content'],
        preview=data.get('preview', data['content'][:150] + '...'),
        genre=data.get('genre', 'Fiction'),
        cover_emoji=data.get('cover_emoji', '📖'),
        author_id=user_id,
        is_published=data.get('is_published', True)
    )
    
    db.session.add(story)
    db.session.commit()
    
    return jsonify({
        'message': 'Story created successfully',
        'story': story.to_dict()
    }), 201


@app.route('/api/stories/<int:story_id>', methods=['PUT'])
@jwt_required()
def update_story(story_id):
    """Update user's own story"""
    user_id = get_jwt_identity()
    story = Story.query.get_or_404(story_id)
    
    if story.author_id != user_id:
        return jsonify({'error': 'Permission denied'}), 403
    
    data = request.get_json()
    
    if 'title' in data:
        story.title = data['title']
    if 'content' in data:
        story.content = data['content']
        story.preview = data['content'][:150] + '...'
    if 'genre' in data:
        story.genre = data['genre']
    if 'cover_emoji' in data:
        story.cover_emoji = data['cover_emoji']
    
    db.session.commit()
    
    return jsonify({
        'message': 'Story updated successfully',
        'story': story.to_dict()
    }), 200


@app.route('/api/stories/<int:story_id>', methods=['DELETE'])
@jwt_required()
def delete_story(story_id):
    """Delete user's own story"""
    user_id = get_jwt_identity()
    story = Story.query.get_or_404(story_id)
    
    if story.author_id != user_id:
        return jsonify({'error': 'Permission denied'}), 403
    
    db.session.delete(story)
    db.session.commit()
    
    return jsonify({'message': 'Story deleted successfully'}), 200


@app.route('/api/my-stories', methods=['GET'])
@jwt_required()
def get_my_stories():
    """Get current user's stories"""
    user_id = get_jwt_identity()
    stories = Story.query.filter_by(author_id=user_id).order_by(Story.created_at.desc()).all()
    
    return jsonify({'stories': [story.to_dict() for story in stories]}), 200


# ==================== COMMENTS ROUTES ====================

@app.route('/api/stories/<int:story_id>/comments', methods=['GET'])
def get_comments(story_id):
    """Get comments for a story"""
    comments = Comment.query.filter_by(story_id=story_id)\
        .order_by(Comment.created_at.desc()).all()
    
    return jsonify({'comments': [comment.to_dict() for comment in comments]}), 200


@app.route('/api/stories/<int:story_id>/comments', methods=['POST'])
@jwt_required()
def add_comment(story_id):
    """Add comment to a story"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data.get('content'):
        return jsonify({'error': 'Comment content required'}), 400
    
    comment = Comment(
        content=data['content'],
        story_id=story_id,
        user_id=user_id
    )
    
    db.session.add(comment)
    db.session.commit()
    
    return jsonify({
        'message': 'Comment added',
        'comment': comment.to_dict()
    }), 201


@app.route('/api/comments/<int:comment_id>', methods=['DELETE'])
@jwt_required()
def delete_comment(comment_id):
    """Delete user's own comment"""
    user_id = get_jwt_identity()
    comment = Comment.query.get_or_404(comment_id)
    
    if comment.user_id != user_id:
        return jsonify({'error': 'Permission denied'}), 403
    
    db.session.delete(comment)
    db.session.commit()
    
    return jsonify({'message': 'Comment deleted'}), 200


# ==================== LIKES ROUTES ====================

@app.route('/api/stories/<int:story_id>/like', methods=['POST'])
@jwt_required()
def like_story(story_id):
    """Like a story"""
    user_id = get_jwt_identity()
    
    existing_like = Like.query.filter_by(story_id=story_id, user_id=user_id).first()
    
    if existing_like:
        return jsonify({'message': 'Already liked'}), 400
    
    like = Like(story_id=story_id, user_id=user_id)
    db.session.add(like)
    db.session.commit()
    
    return jsonify({'message': 'Story liked', 'like_count': len(Like.query.filter_by(story_id=story_id).all())}), 201


@app.route('/api/stories/<int:story_id>/like', methods=['DELETE'])
@jwt_required()
def unlike_story(story_id):
    """Unlike a story"""
    user_id = get_jwt_identity()
    
    like = Like.query.filter_by(story_id=story_id, user_id=user_id).first()
    
    if not like:
        return jsonify({'message': 'Not liked yet'}), 400
    
    db.session.delete(like)
    db.session.commit()
    
    return jsonify({'message': 'Story unliked', 'like_count': len(Like.query.filter_by(story_id=story_id).all())}), 200


# ==================== WRITING PROMPTS ====================

@app.route('/api/prompts', methods=['GET'])
def get_writing_prompts():
    """Get random writing prompts"""
    limit = request.args.get('limit', 3, type=int)
    prompts = WritingPrompt.query.order_by(db.func.random()).limit(limit).all()
    
    return jsonify({'prompts': [prompt.to_dict() for prompt in prompts]}), 200


@app.route('/api/prompts/today', methods=['GET'])
def get_today_prompt():
    """Get today's featured writing prompt"""
    prompt = WritingPrompt.query.order_by(db.func.random()).first()
    
    return jsonify({'prompt': prompt.to_dict() if prompt else {'prompt': 'Write about a journey that changed everything.'}}), 200


# ==================== USER ROUTES ====================

@app.route('/api/users/<int:user_id>', methods=['GET'])
def get_user_profile(user_id):
    """Get user profile with their stories"""
    user = User.query.get_or_404(user_id)
    stories = Story.query.filter_by(author_id=user_id, is_published=True)\
        .order_by(Story.created_at.desc()).limit(10).all()
    
    return jsonify({
        'user': user.to_dict(),
        'stories': [story.to_dict() for story in stories]
    }), 200


@app.route('/api/users/<int:user_id>', methods=['PUT'])
@jwt_required()
def update_user_profile(user_id):
    """Update user profile"""
    current_user_id = get_jwt_identity()
    
    if current_user_id != user_id:
        return jsonify({'error': 'Permission denied'}), 403
    
    user = User.query.get_or_404(user_id)
    data = request.get_json()
    
    if 'bio' in data:
        user.bio = data['bio']
    if 'avatar' in data:
        user.avatar = data['avatar']
    if 'username' in data:
        existing = User.query.filter_by(username=data['username']).first()
        if existing and existing.id != user_id:
            return jsonify({'error': 'Username taken'}), 400
        user.username = data['username']
    
    db.session.commit()
    
    return jsonify({
        'message': 'Profile updated',
        'user': user.to_dict()
    }), 200


# ==================== DASHBOARD STATS ====================

@app.route('/api/dashboard/stats', methods=['GET'])
@jwt_required()
def get_dashboard_stats():
    """Get user's writing statistics"""
    user_id = get_jwt_identity()
    
    user_stories = Story.query.filter_by(author_id=user_id).all()
    total_views = sum(story.view_count for story in user_stories)
    total_likes = sum(len(story.likes) for story in user_stories)
    total_comments = sum(len(story.comments) for story in user_stories)
    
    return jsonify({
        'total_stories': len(user_stories),
        'total_views': total_views,
        'total_likes': total_likes,
        'total_comments': total_comments
    }), 200


# ==================== HEALTH CHECK ====================

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'message': 'Ink & Page API is running'}), 200


if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)