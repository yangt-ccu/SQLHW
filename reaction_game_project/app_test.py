from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import os

# 創建 Flask 應用
app = Flask(__name__)

# 強制設置 SECRET_KEY
app.config['SECRET_KEY'] = 'test-secret-key-for-reaction-game-2025'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test_reaction_game.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Session 配置
app.config['SESSION_COOKIE_SECURE'] = False
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=2)

print(f"🔑 SECRET_KEY 設置為: {app.config['SECRET_KEY']}")
print(f"🗄️  資料庫路徑: {app.config['SQLALCHEMY_DATABASE_URI']}")

db = SQLAlchemy(app)

# 簡化的模型
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    age = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class GameSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime)
    total_rounds = db.Column(db.Integer, default=0)
    correct_responses = db.Column(db.Integer, default=0)
    average_reaction_time = db.Column(db.Float)
    
    user = db.relationship('User', backref=db.backref('sessions', lazy=True))

class GameRound(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('game_session.id'), nullable=False)
    round_number = db.Column(db.Integer, nullable=False)
    stimulus_color = db.Column(db.String(20))
    reaction_time = db.Column(db.Integer)
    response_accuracy = db.Column(db.Boolean, default=False)
    
    session = db.relationship('GameSession', backref=db.backref('rounds', lazy=True))

# 測試路由
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/test_session')
def test_session():
    # 測試 session 設置
    session['test_key'] = 'test_value'
    session['timestamp'] = datetime.now().isoformat()
    session.permanent = True
    
    return jsonify({
        'message': 'Session 測試',
        'session_set': dict(session),
        'secret_key_exists': bool(app.config.get('SECRET_KEY')),
        'secret_key_length': len(app.config.get('SECRET_KEY', ''))
    })

@app.route('/debug_session')
def debug_session():
    return jsonify({
        'session': dict(session),
        'session_keys': list(session.keys()),
        'has_session_id': 'session_id' in session,
        'session_id_value': session.get('session_id'),
        'session_id_type': str(type(session.get('session_id'))),
        'secret_key_configured': bool(app.config.get('SECRET_KEY')),
        'app_config_keys': list(app.config.keys())
    })

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        age = request.form.get('age', type=int)
        
        print(f"📝 註冊請求 - 用戶名: {username}, 年齡: {age}")
        
        if not username:
            flash('請輸入用戶名！', 'error')
            return render_template('register.html')
        
        # 檢查用戶是否存在
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('用戶名已存在！', 'error')
            return render_template('register.html')
        
        try:
            # 創建新用戶
            user = User(username=username, age=age)
            db.session.add(user)
            db.session.commit()
            
            # 設置 session
            session.permanent = True
            session['user_id'] = user.id
            session['username'] = user.username
            session['login_time'] = datetime.now().isoformat()
            
            print(f"✅ 用戶創建成功，ID: {user.id}")
            print(f"✅ Session 設置: {dict(session)}")
            
            flash('註冊成功！', 'success')
            return redirect(url_for('game_menu'))
            
        except Exception as e:
            print(f"❌ 註冊錯誤: {str(e)}")
            db.session.rollback()
            flash('註冊時發生錯誤，請重試！', 'error')
            return render_template('register.html')
    
    return render_template('register.html')

@app.route('/game_menu')
def game_menu():
    print(f"🎮 遊戲選單 - 當前 session: {dict(session)}")
    
    if 'user_id' not in session:
        print("❌ 用戶未登入")
        flash('請先註冊！', 'error')
        return redirect(url_for('register'))
    
    return render_template('game/menu.html')

@app.route('/simple_reaction_game')
def simple_reaction_game():
    print(f"🎯 反應遊戲 - 當前 session: {dict(session)}")
    
    if 'user_id' not in session:
        print("❌ 用戶未登入")
        flash('請先註冊！', 'error')
        return redirect(url_for('register'))
    
    try:
        # 創建遊戲會話
        game_session = GameSession(user_id=session['user_id'])
        db.session.add(game_session)
        db.session.commit()
        
        # 更新 session
        session['session_id'] = game_session.id
        session['game_start_time'] = datetime.now().isoformat()
        
        print(f"✅ 遊戲會話創建，ID: {game_session.id}")
        print(f"✅ 更新 session: {dict(session)}")
        
        return render_template('game/simple_reaction.html', session_id=game_session.id)
        
    except Exception as e:
        print(f"❌ 創建遊戲會話錯誤: {str(e)}")
        db.session.rollback()
        flash('無法創建遊戲會話！', 'error')
        return redirect(url_for('game_menu'))

@app.route('/api/record_round', methods=['POST'])
def record_round():
    print(f"📝 記錄回合 - Session: {dict(session)}")
    
    if 'session_id' not in session:
        print("❌ 沒有遊戲會話")
        return jsonify({'success': False, 'error': 'No game session'})
    
    data = request.json or {}
    session_id = session['session_id']
    
    print(f"📝 使用 session_id: {session_id}, 數據: {data}")
    
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
        
        print(f"✅ 回合記錄成功")
        return jsonify({'success': True})
        
    except Exception as e:
        print(f"❌ 記錄回合錯誤: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/end_session', methods=['POST'])
def end_session():
    print(f"🏁 結束會話 - Session: {dict(session)}")
    
    if 'session_id' not in session:
        print("❌ 沒有遊戲會話")
        return jsonify({'success': False, 'error': 'No game session'})
    
    session_id = session['session_id']
    
    try:
        game_session = db.session.get(GameSession, session_id)
        if not game_session:
            print(f"❌ 找不到會話 {session_id}")
            return jsonify({'success': False, 'error': 'Session not found'})
        
        # 結束會話
        game_session.end_time = datetime.utcnow()
        
        # 計算統計
        rounds = GameRound.query.filter_by(session_id=session_id).all()
        game_session.total_rounds = len(rounds)
        game_session.correct_responses = sum(1 for r in rounds if r.response_accuracy)
        
        reaction_times = [r.reaction_time for r in rounds if r.response_accuracy]
        if reaction_times:
            game_session.average_reaction_time = sum(reaction_times) / len(reaction_times)
        
        db.session.commit()
        
        print(f"✅ 會話結束，共 {len(rounds)} 回合")
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'total_rounds': game_session.total_rounds,
            'correct_responses': game_session.correct_responses
        })
        
    except Exception as e:
        print(f"❌ 結束會話錯誤: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/results/<int:session_id>')
def results(session_id):
    print(f"📊 結果頁面 - 會話 ID: {session_id}")
    
    try:
        game_session = db.session.get(GameSession, session_id)
        if not game_session:
            flash('找不到測試結果！', 'error')
            return redirect(url_for('game_menu'))
        
        rounds = GameRound.query.filter_by(session_id=session_id).order_by(GameRound.round_number).all()
        
        print(f"✅ 載入結果，{len(rounds)} 回合")
        
        return render_template('game/results.html', session=game_session, rounds=rounds)
        
    except Exception as e:
        print(f"❌ 載入結果錯誤: {str(e)}")
        flash('載入結果失敗！', 'error')
        return redirect(url_for('game_menu'))

if __name__ == '__main__':
    # 刪除舊資料庫
    if os.path.exists('test_reaction_game.db'):
        os.remove('test_reaction_game.db')
        print("🗑️  刪除舊資料庫")
    
    with app.app_context():
        print("🔄 創建資料庫...")
        db.create_all()
        print("✅ 資料庫創建完成")
    
    print("🚀 啟動測試應用...")
    app.run(debug=True, host='0.0.0.0', port=5001)  # 使用不同的端口