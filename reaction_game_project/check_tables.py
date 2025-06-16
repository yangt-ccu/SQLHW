import sqlite3

def check_database_structure():
    """檢查資料庫結構"""
    try:
        conn = sqlite3.connect('reaction_game.db')
        cursor = conn.cursor()
        
        # 檢查所有表格
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print("📊 資料庫中的表格:")
        if tables:
            for table in tables:
                table_name = table[0]
                print(f"   • {table_name}")
                
                # 檢查每個表格的結構
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()
                print(f"     欄位: {[col[1] for col in columns]}")
                
                # 檢查記錄數
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                print(f"     記錄數: {count}")
                print()
        else:
            print("   資料庫是空的！")
        
        conn.close()
        return [table[0] for table in tables]
        
    except Exception as e:
        print(f"❌ 檢查資料庫時發生錯誤: {e}")
        return []

# 執行檢查
table_names = check_database_structure()