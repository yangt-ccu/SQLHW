from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta

# 創建 Flask 應用
app = Flask(__name__)

# 配置
app.config['SECRET_KEY'] = 'reaction-game-secret-key-2025-very-secure'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///reaction_game.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SESSION_COOKIE_SECURE'] = False
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=2)

db = SQLAlchemy(app)

# 模型定義
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    age = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<User {self.username}>'

class GameSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime)
    total_rounds = db.Column(db.Integer, default=0)
    correct_responses = db.Column(db.Integer, default=0)
    average_reaction_time = db.Column(db.Float)
    
    user = db.relationship('User', backref=db.backref('sessions', lazy=True))
    
    def __repr__(self):
        return f'<GameSession {self.id}>'

class GameRound(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('game_session.id'), nullable=False)
    round_number = db.Column(db.Integer, nullable=False)
    stimulus_color = db.Column(db.String(20))
    reaction_time = db.Column(db.Integer)
    response_accuracy = db.Column(db.Boolean, default=False)
    
    session = db.relationship('GameSession', backref=db.backref('rounds', lazy=True))
    
    def __repr__(self):
        return f'<GameRound {self.round_number}>'

# 路由
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        age = request.form.get('age', type=int)
        
        if not username:
            flash('請輸入用戶名！', 'error')
            return render_template('register.html')
        
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('用戶名已存在！', 'error')
            return render_template('register.html')
        
        try:
            user = User(username=username, age=age)
            db.session.add(user)
            db.session.commit()
            
            session.permanent = True
            session['user_id'] = user.id
            session['username'] = user.username
            session['login_time'] = datetime.now().isoformat()
            
            flash('註冊成功！', 'success')
            return redirect(url_for('game_menu'))
            
        except Exception as e:
            db.session.rollback()
            flash('註冊時發生錯誤，請重試！', 'error')
            return render_template('register.html')
    
    return render_template('register.html')

@app.route('/game_menu')
def game_menu():
    if 'user_id' not in session:
        flash('請先註冊！', 'error')
        return redirect(url_for('register'))
    
    return render_template('game/menu.html')

@app.route('/simple_reaction_game')
def simple_reaction_game():
    if 'user_id' not in session:
        flash('請先註冊！', 'error')
        return redirect(url_for('register'))
    
    try:
        game_session = GameSession(user_id=session['user_id'])
        db.session.add(game_session)
        db.session.commit()
        
        session['session_id'] = game_session.id
        session['game_start_time'] = datetime.now().isoformat()
        
        return render_template('game/simple_reaction.html', session_id=game_session.id)
        
    except Exception as e:
        db.session.rollback()
        flash('創建遊戲會話失敗，請重試！', 'error')
        return redirect(url_for('game_menu'))

@app.route('/api/record_round', methods=['POST'])
def record_round():
    if 'session_id' not in session:
        return jsonify({'success': False, 'error': 'No game session'})
    
    session_id = session['session_id']
    data = request.json or {}
    
    try:
        game_round = GameRound(
            session_id=session_id,
            round_number=data.get('round_number', 0),
            stimulus_color=data.get('stimulus_color', 'red'),
            reaction_time=data.get('reaction_time', 0),
            response_accuracy=data.get('response_accuracy', False)
        )
        
        db.session.add(game_round)
        db.session.commit()
        
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/end_session', methods=['POST'])
def end_session():
    if 'session_id' not in session:
        return jsonify({'success': False, 'error': 'No game session'})
    
    session_id = session['session_id']
    
    try:
        game_session = db.session.get(GameSession, session_id)
        if not game_session:
            return jsonify({'success': False, 'error': 'Session not found'})
        
        game_session.end_time = datetime.utcnow()
        
        rounds = GameRound.query.filter_by(session_id=session_id).all()
        game_session.total_rounds = len(rounds)
        game_session.correct_responses = sum(1 for r in rounds if r.response_accuracy)
        
        reaction_times = [r.reaction_time for r in rounds if r.response_accuracy]
        if reaction_times:
            game_session.average_reaction_time = sum(reaction_times) / len(reaction_times)
        else:
            game_session.average_reaction_time = 0
        
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'session_id': session_id,
            'total_rounds': game_session.total_rounds,
            'correct_responses': game_session.correct_responses
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/results/<int:session_id>')
def results(session_id):
    try:
        game_session = db.session.get(GameSession, session_id)
        if not game_session:
            flash('找不到測試結果', 'error')
            return redirect(url_for('game_menu'))
        
        rounds = GameRound.query.filter_by(session_id=session_id).order_by(GameRound.round_number).all()
        
        return render_template('game/results.html', session=game_session, rounds=rounds)
    
    except Exception as e:
        flash('載入結果時發生錯誤', 'error')
        return redirect(url_for('game_menu'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    
    app.run(debug=True, host='0.0.0.0', port=5000)