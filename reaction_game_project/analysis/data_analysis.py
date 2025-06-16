import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import seaborn as sns
import numpy as np
from datetime import datetime
import warnings
import os
warnings.filterwarnings('ignore')

# 修正中文字體設置
def setup_chinese_font():
    """設置中文字體"""
    # 嘗試多個中文字體
    chinese_fonts = [
        'Heiti TC',           # macOS 黑體
        'Arial Unicode MS',   # macOS
        'PingFang SC',        # macOS 蘋方
        'STHeiti',           # macOS 華文黑體
        'SimHei',            # Windows 黑體
        'Microsoft YaHei',   # Windows 微軟雅黑
        'WenQuanYi Micro Hei', # Linux
        'DejaVu Sans'        # 備用
    ]
    
    available_fonts = [f.name for f in fm.fontManager.ttflist]
    
    for font in chinese_fonts:
        if font in available_fonts:
            print(f"✅ 使用字體: {font}")
            plt.rcParams['font.sans-serif'] = [font] + plt.rcParams['font.sans-serif']
            plt.rcParams['axes.unicode_minus'] = False
            return font
    
    print("⚠️ 未找到理想的中文字體，使用預設字體")
    plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False
    return 'DejaVu Sans'

# 修正資料庫路徑 - 指向 instance 目錄
PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
DB_PATH = os.path.join(PROJECT_ROOT, 'instance', 'reaction_game.db')
REPORTS_PATH = os.path.join(os.path.dirname(__file__), 'reports')

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

def load_data():
    """載入資料庫數據"""
    db_path = check_database_exists()
    
    if not db_path:
        print("❌ 無法找到資料庫檔案")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    
    # 如果 check_database_exists 返回的是路徑字符串，使用它；否則使用預設路徑
    if isinstance(db_path, str):
        actual_db_path = db_path
    else:
        actual_db_path = DB_PATH
    
    print(f"📂 使用資料庫: {actual_db_path}")
    
    conn = sqlite3.connect(actual_db_path)
    
    try:
        # 檢查資料庫中的表
        tables_query = "SELECT name FROM sqlite_master WHERE type='table';"
        tables = pd.read_sql_query(tables_query, conn)
        print(f"📋 資料庫中的表: {tables['name'].tolist()}")
        
        # 載入用戶數據
        users_df = pd.read_sql_query("""
            SELECT id, username, age, created_at
            FROM user
        """, conn)
        print(f"👥 載入用戶數據: {len(users_df)} 筆")
        
        # 載入遊戲會話數據
        sessions_df = pd.read_sql_query("""
            SELECT gs.*, u.username, u.age
            FROM game_session gs
            JOIN user u ON gs.user_id = u.id
            WHERE gs.end_time IS NOT NULL
        """, conn)
        print(f"🎮 載入會話數據: {len(sessions_df)} 筆")
        
        # 載入詳細回合數據
        rounds_df = pd.read_sql_query("""
            SELECT gr.*, gs.user_id, u.username, u.age
            FROM game_round gr
            JOIN game_session gs ON gr.session_id = gs.id
            JOIN user u ON gs.user_id = u.id
        """, conn)
        print(f"🔄 載入回合數據: {len(rounds_df)} 筆")
        
    except Exception as e:
        print(f"❌ 讀取資料庫時發生錯誤: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    finally:
        conn.close()
    
    # 轉換時間格式
    if not sessions_df.empty:
        sessions_df['start_time'] = pd.to_datetime(sessions_df['start_time'])
        sessions_df['end_time'] = pd.to_datetime(sessions_df['end_time'])
    
    return users_df, sessions_df, rounds_df

def basic_statistics():
    """基本統計分析"""
    users_df, sessions_df, rounds_df = load_data()
    
    print("\n" + "=" * 60)
    print("🎮 反應時間測試遊戲 - 數據分析報告")
    print("=" * 60)
    print(f"📅 分析時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📂 資料庫路徑: {DB_PATH}")
    print()
    
    if users_df.empty and sessions_df.empty and rounds_df.empty:
        print("❌ 沒有找到任何數據，請確認：")
        print("   1. 資料庫檔案位置是否正確")
        print("   2. 是否已經進行過測試")
        print("   3. 資料庫檔案是否有讀取權限")
        return users_df, sessions_df, rounds_df
    
    print("📊 基本統計:")
    print(f"👥 總註冊用戶數: {len(users_df)}")
    print(f"🎯 完成的測試會話: {len(sessions_df)}")
    print(f"🔄 總測試回合數: {len(rounds_df)}")
    
    if not sessions_df.empty:
        print(f"⚡ 平均每次測試回合數: {sessions_df['total_rounds'].mean():.1f}")
        print(f"🎯 平均準確率: {(sessions_df['correct_responses'].sum() / sessions_df['total_rounds'].sum() * 100):.1f}%")
        print(f"⏱️  整體平均反應時間: {sessions_df['average_reaction_time'].mean():.1f}ms")
    
    print()
    return users_df, sessions_df, rounds_df

def reaction_time_analysis(rounds_df):
    """反應時間詳細分析"""
    if rounds_df.empty:
        print("❌ 沒有反應時間數據可供分析")
        return
    
    # 只分析成功的反應
    successful_rounds = rounds_df[rounds_df['response_accuracy'] == True].copy()
    
    if successful_rounds.empty:
        print("❌ 沒有成功的反應時間記錄")
        return
    
    print("⚡ 反應時間分析:")
    print("-" * 40)
    
    reaction_times = successful_rounds['reaction_time']
    
    print(f"📊 統計摘要:")
    print(f"   • 樣本數量: {len(reaction_times)}")
    print(f"   • 平均反應時間: {reaction_times.mean():.1f}ms")
    print(f"   • 中位數反應時間: {reaction_times.median():.1f}ms")
    print(f"   • 標準差: {reaction_times.std():.1f}ms")
    print(f"   • 最快反應: {reaction_times.min()}ms")
    print(f"   • 最慢反應: {reaction_times.max()}ms")
    
    # 反應時間分級
    lightning = len(reaction_times[reaction_times < 200])
    excellent = len(reaction_times[(reaction_times >= 200) & (reaction_times < 300)])
    good = len(reaction_times[(reaction_times >= 300) & (reaction_times < 400)])
    average = len(reaction_times[(reaction_times >= 400) & (reaction_times < 500)])
    slow = len(reaction_times[reaction_times >= 500])
    
    print(f"\n🏆 反應速度分級:")
    print(f"   ⚡ 閃電級 (<200ms): {lightning} 次 ({lightning/len(reaction_times)*100:.1f}%)")
    print(f"   🎯 優秀級 (200-299ms): {excellent} 次 ({excellent/len(reaction_times)*100:.1f}%)")
    print(f"   👍 良好級 (300-399ms): {good} 次 ({good/len(reaction_times)*100:.1f}%)")
    print(f"   📊 一般級 (400-499ms): {average} 次 ({average/len(reaction_times)*100:.1f}%)")
    print(f"   🐌 偏慢級 (≥500ms): {slow} 次 ({slow/len(reaction_times)*100:.1f}%)")
    
    print()

def create_visualizations(users_df, sessions_df, rounds_df):
    """創建數據可視化圖表"""
    if rounds_df.empty:
        print("❌ 沒有數據可供可視化")
        return
    
    # 設置中文字體
    font_name = setup_chinese_font()
    
    # 確保報告目錄存在
    os.makedirs(REPORTS_PATH, exist_ok=True)
    
    # 使用非互動式後端，避免顯示問題
    import matplotlib
    matplotlib.use('Agg')  # 非互動式後端
    
    # 創建更大的圖表，提供更多空間
    fig = plt.figure(figsize=(20, 14))
    fig.patch.set_facecolor('white')
    
    # 調整子圖間距
    plt.subplots_adjust(left=0.08, bottom=0.1, right=0.95, top=0.92, wspace=0.25, hspace=0.35)
    
    # 1. 反應時間分布直方圖
    plt.subplot(2, 3, 1)
    successful_rounds = rounds_df[rounds_df['response_accuracy'] == True]
    if not successful_rounds.empty:
        plt.hist(successful_rounds['reaction_time'], bins=25, alpha=0.8, color='skyblue', 
                edgecolor='navy', linewidth=0.8)
        mean_time = successful_rounds['reaction_time'].mean()
        plt.axvline(mean_time, color='red', linestyle='--', linewidth=2,
                   label=f'平均: {mean_time:.1f}ms')
        plt.xlabel('反應時間 (ms)', fontsize=12, fontweight='bold')
        plt.ylabel('頻率', fontsize=12, fontweight='bold')
        plt.title('反應時間分布', fontsize=14, fontweight='bold', pad=20)
        plt.legend(fontsize=10)
        plt.grid(True, alpha=0.3)
    
    # 2. 準確率分析
    plt.subplot(2, 3, 2)
    if not sessions_df.empty:
        accuracy_rates = (sessions_df['correct_responses'] / sessions_df['total_rounds'] * 100)
        plt.hist(accuracy_rates, bins=12, alpha=0.8, color='lightgreen', 
                edgecolor='darkgreen', linewidth=0.8)
        mean_accuracy = accuracy_rates.mean()
        plt.axvline(mean_accuracy, color='red', linestyle='--', linewidth=2,
                   label=f'平均: {mean_accuracy:.1f}%')
        plt.xlabel('準確率 (%)', fontsize=12, fontweight='bold')
        plt.ylabel('頻率', fontsize=12, fontweight='bold')
        plt.title('測試準確率分布', fontsize=14, fontweight='bold', pad=20)
        plt.legend(fontsize=10)
        plt.grid(True, alpha=0.3)
    
    # 3. 反應時間等級分布（餅圖）
    plt.subplot(2, 3, 3)
    if not successful_rounds.empty:
        reaction_times = successful_rounds['reaction_time']
        categories = ['閃電級\n<200ms', '優秀級\n200-299ms', '良好級\n300-399ms', 
                     '一般級\n400-499ms', '偏慢級\n≥500ms']
        counts = [
            len(reaction_times[reaction_times < 200]),
            len(reaction_times[(reaction_times >= 200) & (reaction_times < 300)]),
            len(reaction_times[(reaction_times >= 300) & (reaction_times < 400)]),
            len(reaction_times[(reaction_times >= 400) & (reaction_times < 500)]),
            len(reaction_times[reaction_times >= 500])
        ]
        
        # 只顯示非零的類別
        non_zero_categories = []
        non_zero_counts = []
        colors = ['#FFD700', '#32CD32', '#FF8C00', '#87CEEB', '#F08080']  # 修正顏色代碼
        non_zero_colors = []
        
        for i, count in enumerate(counts):
            if count > 0:
                non_zero_categories.append(categories[i])
                non_zero_counts.append(count)
                non_zero_colors.append(colors[i])
        
        if non_zero_counts:
            wedges, texts, autotexts = plt.pie(non_zero_counts, labels=non_zero_categories, 
                                              autopct='%1.1f%%', colors=non_zero_colors, 
                                              startangle=90, textprops={'fontsize': 10})
            # 調整百分比文字
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontweight('bold')
                autotext.set_fontsize(11)
        
        plt.title('反應速度等級分布', fontsize=14, fontweight='bold', pad=20)
    
    # 4. 用戶年齡 vs 平均反應時間
    plt.subplot(2, 3, 4)
    if not sessions_df.empty and 'age' in sessions_df.columns:
        sessions_with_age = sessions_df.dropna(subset=['age'])
        if not sessions_with_age.empty:
            age_reaction = sessions_with_age.groupby('age')['average_reaction_time'].mean()
            if not age_reaction.empty:
                # 修正顏色名稱
                plt.scatter(age_reaction.index, age_reaction.values, alpha=0.7, 
                          color='purple', s=120, edgecolors='indigo', linewidth=1.5)
                plt.xlabel('年齡', fontsize=12, fontweight='bold')
                plt.ylabel('平均反應時間 (ms)', fontsize=12, fontweight='bold')
                plt.title('年齡 vs 平均反應時間', fontsize=14, fontweight='bold', pad=20)
                plt.grid(True, alpha=0.3)
                
                # 添加趨勢線
                if len(age_reaction) > 1:
                    z = np.polyfit(age_reaction.index, age_reaction.values, 1)
                    p = np.poly1d(z)
                    plt.plot(age_reaction.index, p(age_reaction.index), "r--", alpha=0.8, linewidth=2)
            else:
                plt.text(0.5, 0.5, '暫無年齡數據', transform=plt.gca().transAxes, 
                        fontsize=14, ha='center', va='center')
                plt.title('年齡 vs 平均反應時間', fontsize=14, fontweight='bold', pad=20)
    
    # 5. 測試進度中的反應時間變化
    plt.subplot(2, 3, 5)
    if not rounds_df.empty:
        round_performance = rounds_df.groupby('round_number').agg({
            'reaction_time': 'mean',
            'response_accuracy': 'mean'
        }).reset_index()
        
        plt.plot(round_performance['round_number'], round_performance['reaction_time'], 
                marker='o', color='blue', linewidth=2.5, markersize=6, 
                markerfacecolor='lightblue', markeredgecolor='navy', markeredgewidth=1,
                label='平均反應時間')
        plt.xlabel('回合數', fontsize=12, fontweight='bold')
        plt.ylabel('平均反應時間 (ms)', fontsize=12, fontweight='bold')
        plt.title('測試進度中的反應時間變化', fontsize=14, fontweight='bold', pad=20)
        plt.legend(fontsize=10)
        plt.grid(True, alpha=0.3)
        
        # 設置 x 軸刻度
        max_round = int(round_performance['round_number'].max())
        plt.xticks(range(1, max_round + 1, max(1, max_round // 10)))
    
    # 6. 每日測試活動
    plt.subplot(2, 3, 6)
    if not sessions_df.empty:
        sessions_df['date'] = sessions_df['start_time'].dt.date
        daily_tests = sessions_df.groupby('date').size()
        
        plt.plot(daily_tests.index, daily_tests.values, marker='o', color='green', 
                linewidth=2.5, markersize=8, markerfacecolor='lightgreen', 
                markeredgecolor='darkgreen', markeredgewidth=1.5)
        plt.xlabel('日期', fontsize=12, fontweight='bold')
        plt.ylabel('測試次數', fontsize=12, fontweight='bold')
        plt.title('每日測試活動', fontsize=14, fontweight='bold', pad=20)
        plt.grid(True, alpha=0.3)
        
        # 旋轉日期標籤以避免重疊
        plt.xticks(rotation=45, ha='right')
    
    # 設置總標題
    fig.suptitle('🎮 反應時間測試遊戲 - 數據分析圖表', fontsize=18, fontweight='bold', y=0.98)
    
    # 保存到 reports 目錄
    output_path = os.path.join(REPORTS_PATH, 'reaction_time_analysis.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    
    print(f"📊 圖表已保存為 '{output_path}'")
    print(f"🎨 使用字體: {font_name}")
    
    # 嘗試顯示圖表（如果在支援的環境中）
    try:
        plt.show()
    except:
        print("💡 圖表已保存，請在檔案管理器中查看 PNG 圖片")
    
    plt.close()  # 關閉圖表以釋放記憶體

def advanced_analysis(sessions_df, rounds_df):
    """進階分析"""
    print("🔬 進階分析:")
    print("-" * 40)
    
    if rounds_df.empty:
        print("❌ 沒有數據可供進階分析")
        return
    
    # 學習效果分析
    if len(rounds_df) > 0:
        # 分析前半段 vs 後半段的表現
        total_rounds = rounds_df['round_number'].max()
        first_half = rounds_df[rounds_df['round_number'] <= total_rounds/2]
        second_half = rounds_df[rounds_df['round_number'] > total_rounds/2]
        
        first_half_success = first_half[first_half['response_accuracy'] == True]
        second_half_success = second_half[second_half['response_accuracy'] == True]
        
        if not first_half_success.empty and not second_half_success.empty:
            print(f"📈 學習效果分析:")
            print(f"   • 前半段平均反應時間: {first_half_success['reaction_time'].mean():.1f}ms")
            print(f"   • 後半段平均反應時間: {second_half_success['reaction_time'].mean():.1f}ms")
            improvement = first_half_success['reaction_time'].mean() - second_half_success['reaction_time'].mean()
            print(f"   • 改進幅度: {improvement:.1f}ms ({improvement/first_half_success['reaction_time'].mean()*100:.1f}%)")
    
    # 一致性分析
    if not sessions_df.empty:
        reaction_std = sessions_df['average_reaction_time'].std()
        print(f"\n📊 表現一致性:")
        print(f"   • 不同會話間反應時間標準差: {reaction_std:.1f}ms")
        if reaction_std < 50:
            print(f"   • 評價: 表現非常一致 ⭐⭐⭐")
        elif reaction_std < 100:
            print(f"   • 評價: 表現較為一致 ⭐⭐")
        else:
            print(f"   • 評價: 表現變化較大 ⭐")

def generate_report():
    """生成完整分析報告"""
    print("🚀 開始生成數據分析報告...")
    print(f"📂 項目根目錄: {PROJECT_ROOT}")
    print(f"🗄️ 資料庫路徑: {DB_PATH}")
    
    users_df, sessions_df, rounds_df = basic_statistics()
    
    if users_df.empty and sessions_df.empty and rounds_df.empty:
        print("\n❌ 沒有數據可供分析，請先進行一些測試！")
        return
    
    reaction_time_analysis(rounds_df)
    advanced_analysis(sessions_df, rounds_df)
    
    print("\n" + "="*60)
    print("📋 建議與總結:")
    print("="*60)
    
    if not rounds_df.empty:
        successful_rounds = rounds_df[rounds_df['response_accuracy'] == True]
        if not successful_rounds.empty:
            avg_reaction = successful_rounds['reaction_time'].mean()
            
            if avg_reaction < 250:
                print("🎉 恭喜！您的反應速度非常優秀！")
            elif avg_reaction < 350:
                print("👍 您的反應速度良好，還有提升空間。")
            else:
                print("💪 建議多加練習以提升反應速度。")
            
            print(f"\n💡 個人化建議:")
            print(f"   • 您的平均反應時間為 {avg_reaction:.1f}ms")
            
            if avg_reaction > 300:
                print(f"   • 建議：定期練習可以提升反應速度")
                print(f"   • 目標：嘗試將反應時間降至 250ms 以下")
    
    print(f"\n🎯 系統統計:")
    if not sessions_df.empty:
        print(f"   • 總測試次數: {len(sessions_df)}")
        print(f"   • 平均完成率: {(sessions_df['total_rounds'].mean()/15*100):.1f}%")
    
    create_visualizations(users_df, sessions_df, rounds_df)

if __name__ == "__main__":
    generate_report()