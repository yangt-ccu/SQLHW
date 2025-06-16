import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
import seaborn as sns
from datetime import datetime
import warnings
import os
import io
import base64
warnings.filterwarnings('ignore')

# 設置中文字體
def setup_chinese_font():
    """設置中文字體"""
    chinese_fonts = ['Heiti TC', 'Arial Unicode MS', 'PingFang SC', 'STHeiti', 'SimHei']
    
    import matplotlib.font_manager as fm
    available_fonts = [f.name for f in fm.fontManager.ttflist]
    
    for font in chinese_fonts:
        if font in available_fonts:
            plt.rcParams['font.sans-serif'] = [font]
            plt.rcParams['axes.unicode_minus'] = False
            return font
    
    plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False
    return 'DejaVu Sans'

def get_session_data(session_id):
    """獲取指定會話的數據"""
    project_root = os.path.dirname(os.path.dirname(__file__))
    db_path = os.path.join(project_root, 'instance', 'reaction_game.db')
    
    if not os.path.exists(db_path):
        # 嘗試其他路徑
        alt_path = os.path.join(project_root, 'reaction_game.db')
        if os.path.exists(alt_path):
            db_path = alt_path
        else:
            return None, None, None
    
    conn = sqlite3.connect(db_path)
    
    try:
        # 獲取會話信息
        session_query = """
        SELECT gs.*, u.username, u.age
        FROM game_session gs
        JOIN user u ON gs.user_id = u.id
        WHERE gs.id = ?
        """
        session_df = pd.read_sql_query(session_query, conn, params=[session_id])
        
        # 獲取回合數據
        rounds_query = """
        SELECT * FROM game_round
        WHERE session_id = ?
        ORDER BY round_number
        """
        rounds_df = pd.read_sql_query(rounds_query, conn, params=[session_id])
        
        # 獲取所有用戶的反應時間數據（用於比較）
        all_rounds_query = """
        SELECT gr.reaction_time, gr.response_accuracy
        FROM game_round gr
        JOIN game_session gs ON gr.session_id = gs.id
        WHERE gr.response_accuracy = 1
        """
        all_rounds_df = pd.read_sql_query(all_rounds_query, conn)
        
    except Exception as e:
        print(f"數據庫錯誤: {e}")
        return None, None, None
    finally:
        conn.close()
    
    return session_df, rounds_df, all_rounds_df

def create_heatmap_chart(rounds_df):
    """創建反應時間熱圖"""
    if rounds_df.empty:
        return None
    
    # 準備熱圖數據 - 將15回合分成3x5網格
    rounds_per_row = 5
    rows = 3
    
    # 創建3x5的矩陣
    heatmap_data = np.full((rows, rounds_per_row), np.nan)
    
    for _, row in rounds_df.iterrows():
        round_num = row['round_number'] - 1  # 轉為0基索引
        if round_num < 15:  # 確保在範圍內
            grid_row = round_num // rounds_per_row
            grid_col = round_num % rounds_per_row
            
            if row['response_accuracy']:
                heatmap_data[grid_row, grid_col] = row['reaction_time']
            else:
                heatmap_data[grid_row, grid_col] = 1000  # 失敗標記為1000ms
    
    # 創建熱圖
    fig, ax = plt.subplots(figsize=(8, 6))
    
    # 使用自定義顏色映射
    cmap = plt.cm.RdYlGn_r  # 紅到綠反轉
    
    # 創建熱圖
    im = ax.imshow(heatmap_data, cmap=cmap, aspect='auto', vmin=200, vmax=800)
    
    # 添加數值標籤
    for i in range(rows):
        for j in range(rounds_per_row):
            round_num = i * rounds_per_row + j + 1
            if round_num <= 15:
                value = heatmap_data[i, j]
                if not np.isnan(value):
                    if value >= 1000:
                        text = 'MISS'
                        color = 'white'
                    else:
                        text = f'{int(value)}ms'
                        color = 'white' if value > 500 else 'black'
                    
                    ax.text(j, i, text, ha='center', va='center', 
                           color=color, fontweight='bold', fontsize=10)
    
    # 設置標籤
    ax.set_xticks(range(rounds_per_row))
    ax.set_xticklabels([f'第{i+1}回合' for i in range(rounds_per_row)])
    ax.set_yticks(range(rows))
    ax.set_yticklabels([f'第{i*5+1}-{(i+1)*5}回合' for i in range(rows)])
    
    ax.set_title('反應時間熱圖分佈', fontsize=14, fontweight='bold', pad=20)
    
    # 添加顏色條
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label('反應時間 (ms)', fontsize=12)
    
    plt.tight_layout()
    return fig

def create_radar_chart(session_data, all_rounds_df):
    """創建雷達圖"""
    if session_data.empty:
        return None
    
    session = session_data.iloc[0]
    
    # 計算指標
    avg_reaction = session['average_reaction_time']
    accuracy = (session['correct_responses'] / session['total_rounds']) * 100
    
    # 計算最快反應時間（需要從rounds數據獲取）
    project_root = os.path.dirname(os.path.dirname(__file__))
    db_path = os.path.join(project_root, 'instance', 'reaction_game.db')
    
    if not os.path.exists(db_path):
        alt_path = os.path.join(project_root, 'reaction_game.db')
        if os.path.exists(alt_path):
            db_path = alt_path
    
    conn = sqlite3.connect(db_path)
    best_reaction_query = """
    SELECT MIN(reaction_time) as best_time 
    FROM game_round 
    WHERE session_id = ? AND response_accuracy = 1
    """
    best_result = pd.read_sql_query(best_reaction_query, conn, params=[session['id']])
    conn.close()
    
    best_reaction = best_result['best_time'].iloc[0] if not best_result.empty else avg_reaction
    
    # 標準化分數（0-100），分數越高越好
    def normalize_reaction_time(time_ms, max_time=600):
        return max(0, min(100, (max_time - time_ms) / max_time * 100))
    
    scores = {
        '平均反應時間': normalize_reaction_time(avg_reaction),
        '準確率': accuracy,
        '最快反應時間': normalize_reaction_time(best_reaction),
        '穩定性': normalize_reaction_time(session['average_reaction_time'], 500),  # 簡化計算
        '專注度': accuracy * 0.8 + normalize_reaction_time(avg_reaction) * 0.2  # 綜合指標
    }
    
    # 創建雷達圖
    categories = list(scores.keys())
    values = list(scores.values())
    
    # 計算角度
    angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
    values += values[:1]  # 閉合圖形
    angles += angles[:1]
    
    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(projection='polar'))
    
    # 繪製雷達圖
    ax.plot(angles, values, 'o-', linewidth=2, color='#1f77b4', label='你的表現')
    ax.fill(angles, values, alpha=0.25, color='#1f77b4')
    
    # 添加參考線
    perfect_scores = [100] * (len(categories) + 1)
    ax.plot(angles, perfect_scores, '--', alpha=0.5, color='red', label='完美表現')
    
    # 設置標籤
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories, fontsize=11)
    ax.set_ylim(0, 100)
    
    # 添加網格標籤
    ax.set_yticks([20, 40, 60, 80, 100])
    ax.set_yticklabels(['20', '40', '60', '80', '100'], fontsize=9)
    ax.grid(True, alpha=0.3)
    
    ax.set_title('個人表現雷達圖', fontsize=14, fontweight='bold', pad=30)
    ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.0))
    
    plt.tight_layout()
    return fig

def create_personal_distribution(rounds_df):
    """創建個人反應時間分布圖"""
    if rounds_df.empty:
        return None
    
    successful_rounds = rounds_df[rounds_df['response_accuracy'] == True]
    if successful_rounds.empty:
        return None
    
    reaction_times = successful_rounds['reaction_time']
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # 創建直方圖
    n, bins, patches = ax.hist(reaction_times, bins=15, alpha=0.7, color='skyblue', 
                              edgecolor='navy', linewidth=1)
    
    # 添加統計線
    mean_time = reaction_times.mean()
    median_time = reaction_times.median()
    
    ax.axvline(mean_time, color='red', linestyle='--', linewidth=2, 
               label=f'平均: {mean_time:.1f}ms')
    ax.axvline(median_time, color='orange', linestyle='--', linewidth=2, 
               label=f'中位數: {median_time:.1f}ms')
    
    # 標記最佳表現
    best_time = reaction_times.min()
    ax.axvline(best_time, color='green', linestyle='-', linewidth=2, 
               label=f'最佳: {best_time}ms')
    
    # 設置標籤和標題
    ax.set_xlabel('反應時間 (ms)', fontsize=12, fontweight='bold')
    ax.set_ylabel('次數', fontsize=12, fontweight='bold')
    ax.set_title('個人反應時間分布', fontsize=14, fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # 添加統計信息文本框
    stats_text = f"""統計摘要:
樣本數: {len(reaction_times)}
平均: {mean_time:.1f}ms
標準差: {reaction_times.std():.1f}ms
範圍: {reaction_times.min()}-{reaction_times.max()}ms"""
    
    ax.text(0.75, 0.75, stats_text, transform=ax.transAxes, 
            bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgray", alpha=0.8),
            fontsize=10, verticalalignment='top')
    
    plt.tight_layout()
    return fig

def create_population_comparison(session_data, all_rounds_df):
    """創建與總體人群的比較圖"""
    if session_data.empty or all_rounds_df.empty:
        return None
    
    session = session_data.iloc[0]
    user_avg = session['average_reaction_time']
    
    # 獲取所有用戶的反應時間
    population_times = all_rounds_df['reaction_time']
    
    if population_times.empty:
        return None
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # 創建人群分布直方圖
    n, bins, patches = ax.hist(population_times, bins=50, alpha=0.6, color='lightgray', 
                              edgecolor='gray', density=True, label='所有用戶分布')
    
    # 添加常態分布擬合
    mu = population_times.mean()
    sigma = population_times.std()
    x = np.linspace(population_times.min(), population_times.max(), 100)
    y = ((1 / (sigma * np.sqrt(2 * np.pi))) * 
         np.exp(-0.5 * ((x - mu) / sigma) ** 2))
    
    ax.plot(x, y, 'b-', linewidth=2, label=f'常態分布擬合\n(μ={mu:.1f}ms, σ={sigma:.1f}ms)')
    
    # 標記當前用戶位置
    ax.axvline(user_avg, color='red', linestyle='-', linewidth=3, 
               label=f'你的平均反應時間: {user_avg:.1f}ms')
    
    # 計算百分位排名
    percentile = (population_times < user_avg).mean() * 100
    
    # 添加陰影區域顯示比你慢的人
    if percentile > 50:
        ax.axvspan(user_avg, population_times.max(), alpha=0.2, color='green', 
                   label=f'比你慢的用戶: {100-percentile:.1f}%')
    else:
        ax.axvspan(population_times.min(), user_avg, alpha=0.2, color='orange',
                   label=f'比你快的用戶: {percentile:.1f}%')
    
    # 設置標籤和標題
    ax.set_xlabel('反應時間 (ms)', fontsize=12, fontweight='bold')
    ax.set_ylabel('密度', fontsize=12, fontweight='bold')
    ax.set_title('你的表現 vs 所有用戶', fontsize=14, fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # 添加排名信息
    rank_text = f"""你的排名:
平均反應時間: {user_avg:.1f}ms
超越了 {percentile:.1f}% 的用戶
{get_performance_level(percentile)}"""
    
    ax.text(0.02, 0.98, rank_text, transform=ax.transAxes, 
            bbox=dict(boxstyle="round,pad=0.3", facecolor="lightyellow", alpha=0.9),
            fontsize=11, verticalalignment='top')
    
    plt.tight_layout()
    return fig

def get_performance_level(percentile):
    """根據百分位獲取表現等級"""
    if percentile >= 90:
        return "🏆 頂級表現！"
    elif percentile >= 75:
        return "🥇 優秀表現！"
    elif percentile >= 50:
        return "🥈 良好表現！"
    elif percentile >= 25:
        return "🥉 一般表現"
    else:
        return "💪 還有進步空間"

def generate_result_charts(session_id):
    """生成結果頁面的所有圖表"""
    setup_chinese_font()
    
    # 獲取數據
    session_df, rounds_df, all_rounds_df = get_session_data(session_id)
    
    if session_df is None or session_df.empty:
        return None
    
    charts = {}
    
    try:
        # 1. 熱圖
        fig1 = create_heatmap_chart(rounds_df)
        if fig1:
            charts['heatmap'] = fig_to_base64(fig1)
            plt.close(fig1)
        
        # 2. 雷達圖
        fig2 = create_radar_chart(session_df, all_rounds_df)
        if fig2:
            charts['radar'] = fig_to_base64(fig2)
            plt.close(fig2)
        
        # 3. 個人分布圖
        fig3 = create_personal_distribution(rounds_df)
        if fig3:
            charts['personal_dist'] = fig_to_base64(fig3)
            plt.close(fig3)
        
        # 4. 人群比較圖
        fig4 = create_population_comparison(session_df, all_rounds_df)
        if fig4:
            charts['population_comparison'] = fig_to_base64(fig4)
            plt.close(fig4)
        
    except Exception as e:
        print(f"生成圖表時發生錯誤: {e}")
        return None
    
    return charts

def fig_to_base64(fig):
    """將matplotlib圖表轉換為base64字符串"""
    img_buffer = io.BytesIO()
    fig.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight', 
                facecolor='white', edgecolor='none')
    img_buffer.seek(0)
    img_string = base64.b64encode(img_buffer.read()).decode()
    img_buffer.close()
    return img_string

if __name__ == "__main__":
    # 測試函數
    charts = generate_result_charts(19)  # 使用你的session_id
    if charts:
        print(f"成功生成 {len(charts)} 個圖表")
        for chart_name in charts.keys():
            print(f"✅ {chart_name}")
    else:
        print("❌ 圖表生成失敗")