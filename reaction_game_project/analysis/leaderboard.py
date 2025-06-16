import sqlite3
import pandas as pd
from datetime import datetime
import os

# 修正資料庫路徑 - 指向 instance 目錄
PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
DB_PATH = os.path.join(PROJECT_ROOT, 'instance', 'reaction_game.db')

def check_database_exists():
    """檢查資料庫是否存在"""
    if os.path.exists(DB_PATH):
        print(f"✅ 找到資料庫: {DB_PATH}")
        return True
    else:
        print(f"❌ 找不到資料庫: {DB_PATH}")
        
        # 嘗試尋找其他可能的位置
        possible_paths = [
            os.path.join(PROJECT_ROOT, 'reaction_game.db'),
            os.path.join(PROJECT_ROOT, 'instance', 'reaction_game.db'),
            '/Users/yang/Desktop/reaction_game_project/reaction_game.db',
            '/Users/yang/Desktop/reaction_game_project/instance/reaction_game.db'
        ]
        
        print("🔍 嘗試尋找資料庫檔案...")
        for path in possible_paths:
            if os.path.exists(path):
                print(f"✅ 找到資料庫: {path}")
                return path
        
        print("❌ 找不到任何資料庫檔案")
        return False

def create_leaderboard():
    """創建排行榜"""
    db_path = check_database_exists()
    
    if not db_path:
        print("❌ 無法找到資料庫檔案")
        return
    
    # 如果 check_database_exists 返回的是路徑字符串，使用它；否則使用預設路徑
    if isinstance(db_path, str):
        actual_db_path = db_path
    else:
        actual_db_path = DB_PATH
    
    print(f"📂 使用資料庫: {actual_db_path}")
    
    conn = sqlite3.connect(actual_db_path)
    
    try:
        # 獲取用戶最佳表現
        query = """
        SELECT 
            u.username,
            u.age,
            COUNT(gs.id) as total_sessions,
            MIN(gs.average_reaction_time) as best_avg_reaction,
            MAX(gs.correct_responses) as best_accuracy,
            AVG(gs.average_reaction_time) as overall_avg_reaction
        FROM user u
        LEFT JOIN game_session gs ON u.id = gs.user_id 
        WHERE gs.end_time IS NOT NULL
        GROUP BY u.id, u.username, u.age
        ORDER BY best_avg_reaction ASC
        """
        
        df = pd.read_sql_query(query, conn)
        print(f"📊 載入排行榜數據: {len(df)} 位用戶")
        
    except Exception as e:
        print(f"❌ 讀取資料庫時發生錯誤: {e}")
        return
    finally:
        conn.close()
    
    print("\n🏆 反應時間排行榜")
    print("=" * 60)
    
    if df.empty:
        print("❌ 暫無排行榜數據")
        return
    
    for i, row in df.iterrows():
        rank = i + 1
        medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else f"{rank:2d}."
        
        age_str = f"({int(row['age'])}歲)" if pd.notna(row['age']) else ""
        
        print(f"{medal} {row['username']:15s} {age_str:8s} | "
              f"最佳: {row['best_avg_reaction']:6.1f}ms | "
              f"平均: {row['overall_avg_reaction']:6.1f}ms | "
              f"測試次數: {row['total_sessions']:2d}")

if __name__ == "__main__":
    create_leaderboard()