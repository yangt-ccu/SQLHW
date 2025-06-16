import sqlite3
import os
from datetime import datetime

def create_fresh_database():
    """創建全新的資料庫"""
    db_path = "/Users/yang/Desktop/reaction_game_project/instance/reaction_game.db"
    
    # 備份舊資料庫
    if os.path.exists(db_path):
        backup_path = f"{db_path}.old_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        os.rename(db_path, backup_path)
        print(f"✅ 舊資料庫已備份至: {backup_path}")
    
    # 創建新資料庫
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 創建用戶表
        cursor.execute('''
        CREATE TABLE user (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            age INTEGER,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        ''')
        
        # 創建遊戲會話表
        cursor.execute('''
        CREATE TABLE game_session (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            start_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            end_time DATETIME,
            total_rounds INTEGER DEFAULT 0,
            correct_responses INTEGER DEFAULT 0,
            average_reaction_time REAL,
            FOREIGN KEY (user_id) REFERENCES user (id)
        );
        ''')
        
        # 創建遊戲回合表
        cursor.execute('''
        CREATE TABLE game_round (
            id INTEGER PRIMARY KEY,
            session_id INTEGER NOT NULL,
            round_number INTEGER NOT NULL,
            target_appear_time DATETIME NOT NULL,
            response_time DATETIME,
            reaction_time INTEGER,
            response_accuracy BOOLEAN DEFAULT 0,
            FOREIGN KEY (session_id) REFERENCES game_session (id)
        );
        ''')
        
        conn.commit()
        print("✅ 新資料庫創建成功")
        
        # 驗證結構
        tables = ['user', 'game_session', 'game_round']
        for table in tables:
            cursor.execute(f"PRAGMA table_info({table});")
            columns = cursor.fetchall()
            print(f"\n{table} 表結構:")
            for col in columns:
                print(f"  {col[1]} | {col[2]}")
        
        return True
        
    except Exception as e:
        print(f"❌ 創建新資料庫失敗: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    print("🆕 創建全新資料庫")
    print("=" * 30)
    
    if create_fresh_database():
        print("\n🎉 全新資料庫創建完成！")
        print("⚠️ 所有舊資料已備份，但無法在新系統中使用")
        print("💡 建議重新註冊用戶並開始新的測試")
    else:
        print("\n💥 創建失敗")