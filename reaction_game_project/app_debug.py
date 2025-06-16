from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import os
import traceback

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
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime)
    total_rounds = db.Column(db.Integer, default=0)
    correct_responses = db.Column(db.Integer, default=0)
    average_reaction_time = db.Column(db.Float)

class GameRound(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('game_session.id'), nullable=False)
    round_number = db.Column(db.Integer, nullable=False)
    target_appear_time = db.Column(db.DateTime, nullable=False)
    response_time = db.Column(db.DateTime)
    reaction_time = db.Column(db.Integer)
    response_accuracy = db.Column(db.Boolean, default=False)

# ... 其他路由保持不變 ...

@app.route('/finish-game', methods=['POST'])
def finish_game():
    """完成遊戲 - 增強錯誤處理"""
    print(f"\n{'='*60}")
    print(f"🏁 完成遊戲請求 - {datetime.now()}")
    
    user_id = session.get('user_id')
    session_id = session.get('current_session_id')
    
    print(f"📊 會話信息:")
    print(f"   用戶ID: {user_id}")
    print(f"   會話ID: {session_id}")
    print(f"   所有會話鍵: {list(session.keys())}")
    
    if not user_id:
        print("❌ 用戶ID缺失")
        return jsonify({
            'error': 'User not logged in',
            'code': 'NO_USER_ID',
            'redirect': url_for('login')
        }), 401
    
    if not session_id:
        print("❌ 會話ID缺失")
        return jsonify({
            'error': 'Game session not found',
            'code': 'NO_SESSION_ID',
            'redirect': url_for('simple_reaction_game')
        }), 400
    
    try:
        # 查詢遊戲會話
        print(f"🔍 查詢遊戲會話: {session_id}")
        game_session = GameSession.query.get(session_id)
        
        if not game_session:
            print(f"❌ 找不到遊戲會話: {session_id}")
            # 列出該用戶的所有會話
            user_sessions = GameSession.query.filter_by(user_id=user_id).all()
            print(f"🔍 用戶 {user_id} 的所有會話: {[s.id for s in user_sessions]}")
            return jsonify({
                'error': 'Game session not found in database',
                'code': 'SESSION_NOT_FOUND',
                'redirect': url_for('game_menu')
            }), 404
        
        print(f"✅ 找到遊戲會話: ID={game_session.id}, 用戶ID={game_session.user_id}")
        
        # 驗證會話所有權
        if game_session.user_id != user_id:
            print(f"❌ 會話所有權不匹配: 會話用戶={game_session.user_id}, 當前用戶={user_id}")
            return jsonify({
                'error': 'Session ownership mismatch',
                'code': 'OWNERSHIP_MISMATCH',
                'redirect': url_for('game_menu')
            }), 403
        
        # 查詢回合記錄
        print(f"🔍 查詢回合記錄...")
        rounds = GameRound.query.filter_by(session_id=session_id).all()
        correct_rounds = [r for r in rounds if r.response_accuracy]
        
        print(f"📊 回合統計:")
        print(f"   總回合數: {len(rounds)}")
        print(f"   正確回合數: {len(correct_rounds)}")
        
        # 更新遊戲會話
        print(f"💾 更新遊戲會話統計...")
        game_session.end_time = datetime.utcnow()
        game_session.total_rounds = len(rounds)
        game_session.correct_responses = len(correct_rounds)
        
        if correct_rounds:
            reaction_times = [r.reaction_time for r in correct_rounds if r.reaction_time]
            if reaction_times:
                avg_reaction = sum(reaction_times) / len(reaction_times)
                game_session.average_reaction_time = avg_reaction
                print(f"   平均反應時間: {avg_reaction:.1f}ms")
            else:
                game_session.average_reaction_time = 0
                print(f"   平均反應時間: 無有效數據")
        else:
            game_session.average_reaction_time = 0
            print(f"   平均反應時間: 無正確回合")
        
        # 提交到資料庫
        db.session.commit()
        print(f"✅ 遊戲會話統計已保存")
        
        # 生成結果頁面URL
        results_url = url_for('show_results', session_id=session_id)
        print(f"🎯 結果頁面URL: {results_url}")
        
        return jsonify({
            'status': 'success',
            'message': 'Game completed successfully',
            'redirect': results_url,
            'session_id': session_id,
            'stats': {
                'total_rounds': len(rounds),
                'correct_responses': len(correct_rounds),
                'average_reaction_time': game_session.average_reaction_time
            }
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ 完成遊戲時發生錯誤:")
        print(f"   錯誤類型: {type(e).__name__}")
        print(f"   錯誤信息: {str(e)}")
        print(f"   完整追蹤:")
        traceback.print_exc()
        
        return jsonify({
            'error': f'Internal server error: {str(e)}',
            'code': 'INTERNAL_ERROR',
            'redirect': url_for('game_menu')
        }), 500

@app.route('/results/<int:session_id>')
def show_results(session_id):
    """顯示遊戲結果 - 增強錯誤處理"""
    print(f"\n{'='*60}")
    print(f"📊 顯示結果請求 - {datetime.now()}")
    print(f"   請求的會話ID: {session_id}")
    
    # 檢查用戶登入狀態
    user_id = session.get('user_id')
    username = session.get('username')
    
    print(f"📋 當前用戶信息:")
    print(f"   用戶ID: {user_id}")
    print(f"   用戶名: {username}")
    
    if not user_id:
        print("❌ 用戶未登入")
        flash('請先登入或註冊', 'error')
        return redirect(url_for('login'))
    
    try:
        # 查詢遊戲會話
        print(f"🔍 查詢遊戲會話: {session_id}")
        game_session = GameSession.query.get(session_id)
        
        if not game_session:
            print(f"❌ 找不到會話ID: {session_id}")
            # 列出該用戶的最近會話
            user_sessions = GameSession.query.filter_by(user_id=user_id).order_by(GameSession.id.desc()).limit(5).all()
            print(f"🔍 用戶 {user_id} 的最近會話: {[s.id for s in user_sessions]}")
            flash('找不到遊戲記錄', 'error')
            return redirect(url_for('game_menu'))
        
        print(f"✅ 找到遊戲會話:")
        print(f"   會話ID: {game_session.id}")
        print(f"   用戶ID: {game_session.user_id}")
        print(f"   開始時間: {game_session.start_time}")
        print(f"   結束時間: {game_session.end_time}")
        print(f"   總回合: {game_session.total_rounds}")
        print(f"   正確回合: {game_session.correct_responses}")
        print(f"   平均反應時間: {game_session.average_reaction_time}")
        
        # 驗證會話所有權
        if game_session.user_id != user_id:
            print(f"❌ 會話所有權不匹配:")
            print(f"   會話用戶: {game_session.user_id}")
            print(f"   當前用戶: {user_id}")
            flash('無權查看此結果', 'error')
            return redirect(url_for('game_menu'))
        
        # 查詢回合記錄
        print(f"🔍 查詢回合記錄...")
        rounds = GameRound.query.filter_by(session_id=session_id).order_by(GameRound.round_number).all()
        
        print(f"📊 回合記錄統計:")
        print(f"   回合數量: {len(rounds)}")
        if rounds:
            print(f"   回合範圍: {rounds[0].round_number} - {rounds[-1].round_number}")
            successful_rounds = [r for r in rounds if r.response_accuracy]
            print(f"   成功回合: {len(successful_rounds)}")
        
        # 檢查模板文件
        template_path = os.path.join('templates', 'game', 'results.html')
        if not os.path.exists(template_path):
            print(f"❌ 模板文件不存在: {template_path}")
            flash('結果頁面模板不存在', 'error')
            return redirect(url_for('game_menu'))
        
        print(f"✅ 模板文件存在: {template_path}")
        
        # 渲染模板
        print(f"🎨 渲染結果頁面...")
        return render_template('game/results.html', 
                             game_session=game_session,
                             rounds=rounds)
        
    except Exception as e:
        print(f"❌ 顯示結果時發生錯誤:")
        print(f"   錯誤類型: {type(e).__name__}")
        print(f"   錯誤信息: {str(e)}")
        print(f"   完整追蹤:")
        traceback.print_exc()
        
        flash('載入結果時發生錯誤', 'error')
        return redirect(url_for('game_menu'))

# ... 其他路由保持不變 ...

if __name__ == '__main__':
    print("🚀 啟動調試版本 Flask 應用...")
    app.run(debug=True, host='0.0.0.0', port=5000)