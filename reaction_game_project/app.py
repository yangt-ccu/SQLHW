from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import os
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here-change-in-production'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=2)

# 資料庫配置
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "instance", "reaction_game.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 確保 instance 目錄存在
instance_dir = os.path.join(basedir, 'instance')
if not os.path.exists(instance_dir):
    os.makedirs(instance_dir)

db = SQLAlchemy(app)

# 資料庫模型
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    age = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class GameSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    difficulty = db.Column(db.String(20), default='normal')
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime)
    total_rounds = db.Column(db.Integer, default=0)
    correct_responses = db.Column(db.Integer, default=0)
    average_reaction_time = db.Column(db.Float)
    best_reaction_time = db.Column(db.Integer)

class GameRound(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('game_session.id'), nullable=False)
    round_number = db.Column(db.Integer, nullable=False)
    target_appear_time = db.Column(db.DateTime, nullable=False)
    response_time = db.Column(db.DateTime)
    reaction_time = db.Column(db.Integer)
    response_accuracy = db.Column(db.Boolean, default=False)
    target_size = db.Column(db.Integer, default=80)
    target_duration = db.Column(db.Integer, default=3000)

# 遊戲難度配置
DIFFICULTY_CONFIG = {
    'easy': {
        'name': '簡單',
        'description': '較大的目標，較長的顯示時間',
        'target_size_range': (100, 120),
        'delay_range': (2000, 4000),
        'display_duration': 4000,
        'rounds': 10,
        'color': 'success',
        'icon': '🟢'
    },
    'normal': {
        'name': '普通',
        'description': '標準的目標大小和顯示時間',
        'target_size_range': (80, 100),
        'delay_range': (1500, 3500),
        'display_duration': 3000,
        'rounds': 15,
        'color': 'warning',
        'icon': '🟡'
    },
    'hard': {
        'name': '困難',
        'description': '較小的目標，較短的顯示時間',
        'target_size_range': (60, 80),
        'delay_range': (1000, 3000),
        'display_duration': 2000,
        'rounds': 20,
        'color': 'danger',
        'icon': '🔴'
    },
    'expert': {
        'name': '專家',
        'description': '極小目標，極短顯示時間',
        'target_size_range': (40, 60),
        'delay_range': (800, 2500),
        'display_duration': 1500,
        'rounds': 25,
        'color': 'dark',
        'icon': '⚫'
    }
}

# ==================== 路由 ====================

@app.route('/')
def index():
    """首頁"""
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """用戶註冊"""
    if request.method == 'POST':
        username = request.form['username']
        age = request.form.get('age')
        
        # 檢查用戶是否已存在
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('用戶名已存在，請選擇其他用戶名', 'error')
            return render_template('register.html')
        
        # 處理年齡
        age_int = None
        if age:
            try:
                age_int = int(age)
                if age_int < 5 or age_int > 120:
                    flash('請輸入有效的年齡 (5-120)', 'error')
                    return render_template('register.html')
            except ValueError:
                flash('年齡必須是數字', 'error')
                return render_template('register.html')
        
        # 創建新用戶
        try:
            user = User(username=username, age=age_int)
            db.session.add(user)
            db.session.commit()
            
            # 設置會話
            session.clear()
            session.permanent = True
            session['user_id'] = user.id
            session['username'] = user.username
            
            flash(f'歡迎 {user.username}！註冊成功！', 'success')
            return redirect(url_for('game_menu'))
            
        except Exception as e:
            db.session.rollback()
            flash('註冊時發生錯誤，請重試', 'error')
            return render_template('register.html')
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """用戶登入"""
    if request.method == 'POST':
        username = request.form['username']
        
        user = User.query.filter_by(username=username).first()
        if user:
            session.clear()
            session.permanent = True
            session['user_id'] = user.id
            session['username'] = user.username
            
            flash(f'歡迎回來，{user.username}！', 'success')
            return redirect(url_for('game_menu'))
        else:
            flash('用戶名不存在，請先註冊', 'error')
            return render_template('login.html')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """用戶登出"""
    username = session.get('username', '用戶')
    session.clear()
    flash(f'再見，{username}！', 'info')
    return redirect(url_for('index'))

@app.route('/game-menu')
def game_menu():
    """遊戲選單"""
    if 'user_id' not in session:
        flash('請先登入或註冊', 'warning')
        return redirect(url_for('login'))
    
    # 獲取用戶統計
    user_id = session['user_id']
    total_games = GameSession.query.filter_by(user_id=user_id).filter(GameSession.end_time.isnot(None)).count()
    
    best_time = db.session.query(db.func.min(GameSession.average_reaction_time)).filter_by(user_id=user_id).scalar()
    
    user_stats = {
        'total_games': total_games,
        'best_average_time': best_time
    }
    
    return render_template('game/menu.html', 
                         difficulty_config=DIFFICULTY_CONFIG,
                         user_stats=user_stats)

@app.route('/simple-reaction-game')
@app.route('/simple-reaction-game/<difficulty>')
def simple_reaction_game(difficulty='normal'):
    """簡單反應時間遊戲"""
    if 'user_id' not in session:
        flash('請先登入或註冊', 'warning')
        return redirect(url_for('login'))
    
    if difficulty not in DIFFICULTY_CONFIG:
        difficulty = 'normal'
    
    try:
        user_id = session['user_id']
        
        # 創建新的遊戲會話
        game_session = GameSession(user_id=user_id, difficulty=difficulty)
        db.session.add(game_session)
        db.session.commit()
        db.session.refresh(game_session)
        
        # 設置會話ID
        session['current_session_id'] = game_session.id
        session['current_difficulty'] = difficulty
        
        return render_template('game/simple_reaction.html', 
                             difficulty=difficulty,
                             config=DIFFICULTY_CONFIG[difficulty])
        
    except Exception as e:
        db.session.rollback()
        flash('初始化遊戲時發生錯誤，請重試', 'error')
        return redirect(url_for('game_menu'))

@app.route('/submit-reaction', methods=['POST'])
def submit_reaction():
    """提交反應數據"""
    user_id = session.get('user_id')
    session_id = session.get('current_session_id')
    
    if not user_id or not session_id:
        return jsonify({'error': 'Invalid session'}), 400
    
    try:
        game_session = GameSession.query.get(session_id)
        if not game_session or game_session.user_id != user_id:
            return jsonify({'error': 'Session not found or invalid'}), 404
        
        data = request.get_json()
        
        game_round = GameRound(
            session_id=session_id,
            round_number=data['round'],
            target_appear_time=datetime.fromtimestamp(data['targetTime'] / 1000),
            response_time=datetime.fromtimestamp(data['responseTime'] / 1000) if data.get('responseTime') else None,
            reaction_time=data.get('reactionTime'),
            response_accuracy=data['accuracy'],
            target_size=data.get('targetSize', 80),
            target_duration=data.get('targetDuration', 3000)
        )
        
        db.session.add(game_round)
        db.session.commit()
        
        return jsonify({'status': 'success'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/finish-game', methods=['POST'])
def finish_game():
    """完成遊戲"""
    user_id = session.get('user_id')
    session_id = session.get('current_session_id')
    
    if not user_id or not session_id:
        return jsonify({'error': 'Invalid session'}), 400
    
    try:
        game_session = GameSession.query.get(session_id)
        if not game_session:
            return jsonify({'error': 'Session not found'}), 404
        
        # 計算統計信息
        rounds = GameRound.query.filter_by(session_id=session_id).all()
        correct_rounds = [r for r in rounds if r.response_accuracy]
        
        game_session.end_time = datetime.utcnow()
        game_session.total_rounds = len(rounds)
        game_session.correct_responses = len(correct_rounds)
        
        if correct_rounds:
            reaction_times = [r.reaction_time for r in correct_rounds if r.reaction_time]
            if reaction_times:
                avg_reaction = sum(reaction_times) / len(reaction_times)
                game_session.average_reaction_time = avg_reaction
                game_session.best_reaction_time = min(reaction_times)
        else:
            game_session.average_reaction_time = 0
            game_session.best_reaction_time = 0
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'redirect': url_for('show_results', session_id=session_id)
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/results/<int:session_id>')
def show_results(session_id):
    """顯示遊戲結果"""
    if 'user_id' not in session:
        flash('請先登入或註冊', 'warning')
        return redirect(url_for('login'))
    
    try:
        game_session = GameSession.query.get_or_404(session_id)
        
        # 驗證會話所有權
        if game_session.user_id != session['user_id']:
            flash('無權查看此結果', 'error')
            return redirect(url_for('game_menu'))
        
        rounds = GameRound.query.filter_by(session_id=session_id).order_by(GameRound.round_number).all()
        
        # 獲取難度配置
        difficulty_info = DIFFICULTY_CONFIG.get(game_session.difficulty, DIFFICULTY_CONFIG['normal'])
        
        return render_template('game/results.html', 
                             game_session=game_session, 
                             rounds=rounds,
                             difficulty_info=difficulty_info)
        
    except Exception as e:
        flash('載入結果時發生錯誤', 'error')
        return redirect(url_for('game_menu'))

@app.route('/api/difficulty-config')
def get_difficulty_config():
    """獲取難度配置API"""
    return jsonify(DIFFICULTY_CONFIG)

# 創建資料庫表
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)