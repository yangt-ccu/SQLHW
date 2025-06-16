from flask import Flask, session as flask_session, request
from flask_sqlalchemy import SQLAlchemy
import os

# 設定Flask應用進行測試
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here-change-in-production'
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "instance", "reaction_game.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    age = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

class GameSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    start_time = db.Column(db.DateTime, default=db.func.current_timestamp())
    end_time = db.Column(db.DateTime)
    total_rounds = db.Column(db.Integer, default=0)
    correct_responses = db.Column(db.Integer, default=0)
    average_reaction_time = db.Column(db.Float)

def simulate_game_flow():
    """模擬完整的遊戲流程"""
    with app.app_context():
        print("🧪 模擬遊戲流程測試")
        print("=" * 50)
        
        # 1. 檢查是否有用戶
        users = User.query.all()
        if not users:
            print("❌ 沒有用戶，請先註冊用戶")
            return
        
        test_user = users[0]
        print(f"✅ 使用測試用戶: {test_user.username} (ID: {test_user.id})")
        
        # 2. 模擬會話設置
        with app.test_request_context():
            flask_session['user_id'] = test_user.id
            flask_session['username'] = test_user.username
            flask_session.permanent = True
            
            print(f"✅ 設置Flask會話: user_id={flask_session.get('user_id')}")
            
            # 3. 創建遊戲會話
            try:
                game_session = GameSession(user_id=test_user.id)
                db.session.add(game_session)
                db.session.commit()
                db.session.refresh(game_session)
                
                flask_session['current_session_id'] = game_session.id
                
                print(f"✅ 創建遊戲會話成功: ID={game_session.id}")
                
                # 4. 驗證會話查詢
                retrieved_session = GameSession.query.get(game_session.id)
                if retrieved_session:
                    print(f"✅ 會話查詢成功: ID={retrieved_session.id}")
                else:
                    print("❌ 會話查詢失敗")
                    return
                
                # 5. 模擬提交數據
                from datetime import datetime
                
                print("🔄 模擬提交回合數據...")
                
                # 檢查會話狀態（模擬前端檢查）
                user_id = flask_session.get('user_id')
                session_id = flask_session.get('current_session_id')
                
                print(f"   檢查會話: user_id={user_id}, session_id={session_id}")
                
                if not user_id:
                    print("❌ 用戶ID缺失")
                    return
                
                if not session_id:
                    print("❌ 會話ID缺失") 
                    return
                
                # 驗證會話存在
                game_session_check = GameSession.query.get(session_id)
                if not game_session_check:
                    print(f"❌ 找不到會話ID {session_id}")
                    return
                
                if game_session_check.user_id != user_id:
                    print(f"❌ 會話所有權不匹配")
                    return
                
                print("✅ 所有檢查通過，模擬成功！")
                return True
                
            except Exception as e:
                print(f"❌ 創建遊戲會話失敗: {e}")
                db.session.rollback()
                return False

if __name__ == "__main__":
    simulate_game_flow()