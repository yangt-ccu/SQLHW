import os
import sqlite3
from datetime import datetime

def check_database_content():
    """檢查資料庫內容"""
    db_path = os.path.join("instance", "reaction_game.db")
    
    if not os.path.exists(db_path):
        print("❌ 資料庫文件不存在")
        return
    
    print(f"✅ 資料庫文件存在: {db_path}")
    print(f"📊 文件大小: {os.path.getsize(db_path)} bytes")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 檢查表結構
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"📋 資料庫表: {[t[0] for t in tables]}")
        
        # 檢查用戶
        cursor.execute("SELECT id, username, created_at FROM user ORDER BY id DESC LIMIT 5;")
        users = cursor.fetchall()
        print(f"\n👥 最近用戶 (最多5個):")
        for user in users:
            print(f"  ID:{user[0]}, 用戶名:{user[1]}, 創建時間:{user[2]}")
        
        # 檢查遊戲會話
        cursor.execute("SELECT id, user_id, start_time, end_time, total_rounds FROM game_session ORDER BY id DESC LIMIT 10;")
        sessions = cursor.fetchall()
        print(f"\n🎮 最近遊戲會話 (最多10個):")
        for session in sessions:
            print(f"  會話ID:{session[0]}, 用戶ID:{session[1]}, 開始:{session[2]}, 結束:{session[3]}, 回合:{session[4]}")
        
        # 檢查回合記錄
        cursor.execute("SELECT session_id, COUNT(*) as round_count FROM game_round GROUP BY session_id ORDER BY session_id DESC LIMIT 5;")
        round_counts = cursor.fetchall()
        print(f"\n🎯 回合統計 (按會話):")
        for rc in round_counts:
            print(f"  會話ID:{rc[0]}, 回合數:{rc[1]}")
        
        # 檢查最近完成的遊戲
        cursor.execute("""
            SELECT gs.id, gs.user_id, u.username, gs.total_rounds, gs.correct_responses, gs.average_reaction_time
            FROM game_session gs 
            JOIN user u ON gs.user_id = u.id 
            WHERE gs.end_time IS NOT NULL 
            ORDER BY gs.id DESC LIMIT 5;
        """)
        completed_games = cursor.fetchall()
        print(f"\n🏁 最近完成的遊戲:")
        for game in completed_games:
            print(f"  會話ID:{game[0]}, 用戶:{game[2]}, 回合:{game[3]}, 正確:{game[4]}, 平均反應:{game[5]}ms")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 檢查資料庫時發生錯誤: {e}")

def check_template_files():
    """檢查模板文件"""
    templates = [
        "templates/base.html",
        "templates/game/results.html",
        "templates/game/menu.html",
        "templates/game/simple_reaction.html"
    ]
    
    print(f"\n📄 檢查模板文件:")
    for template in templates:
        if os.path.exists(template):
            size = os.path.getsize(template)
            print(f"  ✅ {template} ({size} bytes)")
        else:
            print(f"  ❌ {template} - 文件不存在")

if __name__ == "__main__":
    print("🔍 診斷結果頁面問題")
    print("=" * 50)
    print(f"⏰ 當前時間: {datetime.now()}")
    
    check_database_content()
    check_template_files()