import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import warnings
import os
warnings.filterwarnings('ignore')

# Use default English fonts
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Arial', 'Helvetica', 'DejaVu Sans']
plt.rcParams['font.size'] = 12
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['axes.titlesize'] = 16
plt.rcParams['axes.labelsize'] = 13
plt.rcParams['xtick.labelsize'] = 11
plt.rcParams['ytick.labelsize'] = 11
plt.rcParams['legend.fontsize'] = 11

# Set seaborn style
sns.set_style("whitegrid")
sns.set_palette("husl")

def check_and_load_data():
    """Check database structure and load data"""
    # Database paths
    db_paths = [
        '/Users/yangt-ccu/Desktop/reaction_game_project/instance/reaction_game.db',
        '/Users/yang/Desktop/reaction_game_project/instance/reaction_game.db',
        'instance/reaction_game.db',
        'reaction_game.db'
    ]
    
    db_path = None
    for path in db_paths:
        if os.path.exists(path):
            db_path = path
            break
    
    if not db_path:
        print("Database file not found")
        return None, None, None
    
    print(f"Using database path: {db_path}")
    
    conn = sqlite3.connect(db_path)
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [table[0] for table in cursor.fetchall()]
        
        print(f"Found tables: {tables}")
        
        if not tables:
            print("Database is empty!")
            return None, None, None
        
        # Detect table names
        user_table = next((t for t in tables if 'user' in t.lower()), None)
        session_table = next((t for t in tables if 'session' in t.lower()), None)
        round_table = next((t for t in tables if 'round' in t.lower()), None)
        
        print(f"Detected tables:")
        print(f"   User table: {user_table}")
        print(f"   Session table: {session_table}")
        print(f"   Round table: {round_table}")
        
        # Load data
        users_df = pd.DataFrame()
        sessions_df = pd.DataFrame()
        rounds_df = pd.DataFrame()
        
        if user_table:
            users_df = pd.read_sql_query(f"SELECT * FROM {user_table}", conn)
            print(f"Loaded user data: {len(users_df)} records")
        
        if session_table:
            if user_table:
                sessions_df = pd.read_sql_query(f"""
                    SELECT gs.*, u.username, u.age 
                    FROM {session_table} gs 
                    LEFT JOIN {user_table} u ON gs.user_id = u.id
                """, conn)
            else:
                sessions_df = pd.read_sql_query(f"SELECT * FROM {session_table}", conn)
            print(f"Loaded session data: {len(sessions_df)} records")
        
        if round_table:
            if session_table and user_table:
                rounds_df = pd.read_sql_query(f"""
                    SELECT gr.*, gs.user_id, u.username
                    FROM {round_table} gr
                    LEFT JOIN {session_table} gs ON gr.session_id = gs.id
                    LEFT JOIN {user_table} u ON gs.user_id = u.id
                """, conn)
            elif session_table:
                rounds_df = pd.read_sql_query(f"""
                    SELECT gr.*, gs.user_id
                    FROM {round_table} gr
                    LEFT JOIN {session_table} gs ON gr.session_id = gs.id
                """, conn)
            else:
                rounds_df = pd.read_sql_query(f"SELECT * FROM {round_table}", conn)
            print(f"Loaded round data: {len(rounds_df)} records")
        
        if not sessions_df.empty and 'start_time' in sessions_df.columns:
            sessions_df['start_time'] = pd.to_datetime(sessions_df['start_time'])
            if 'end_time' in sessions_df.columns:
                sessions_df['end_time'] = pd.to_datetime(sessions_df['end_time'])
        
        return users_df, sessions_df, rounds_df
        
    except Exception as e:
        print(f"Error loading data: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    finally:
        conn.close()

# Load data
users_df, sessions_df, rounds_df = check_and_load_data()

if users_df is None:
    exit()

print("\nData Overview:")
print(f"Number of users: {len(users_df)}")
print(f"Number of game sessions: {len(sessions_df)}")
print(f"Number of game rounds: {len(rounds_df)}")

# Create sample charts if no data
if rounds_df.empty:
    print("\nNo game data found, creating sample charts...")
    
    np.random.seed(42)
    sample_reactions = np.random.normal(350, 80, 100)
    sample_reactions = sample_reactions[sample_reactions > 150]
    sample_reactions = sample_reactions[sample_reactions < 800]
    
    fig = plt.figure(figsize=(18, 14))
    fig.suptitle('Reaction Time Test Data Analysis Report (Sample Data)', fontsize=20, fontweight='bold')
    
    gs = fig.add_gridspec(2, 2, hspace=0.35, wspace=0.3)
    
    # Sample chart 1
    ax1 = fig.add_subplot(gs[0, 0])
    sns.histplot(sample_reactions, bins=20, kde=True, alpha=0.7, color='skyblue', ax=ax1)
    ax1.axvline(np.mean(sample_reactions), color='red', linestyle='--', linewidth=2, 
               label=f'Mean: {np.mean(sample_reactions):.0f}ms')
    ax1.set_title('Reaction Time Distribution (Sample)', fontsize=14, fontweight='bold')
    ax1.set_xlabel('Reaction Time (ms)', fontsize=12)
    ax1.set_ylabel('Density', fontsize=12)
    ax1.legend()
    
    # Sample chart 2
    ax2 = fig.add_subplot(gs[0, 1])
    sample_accuracy = [85, 92, 78, 95, 88]
    accuracy_labels = ['User1', 'User2', 'User3', 'User4', 'User5']
    ax2.pie(sample_accuracy, labels=accuracy_labels, autopct='%1.1f%%', startangle=90)
    ax2.set_title('Accuracy Distribution (Sample)', fontsize=14, fontweight='bold')
    
    # Sample chart 3
    ax3 = fig.add_subplot(gs[1, 0])
    sample_heatmap = np.random.randint(0, 10, (6, 15))
    sns.heatmap(sample_heatmap, annot=True, fmt='d', cmap='YlOrRd', ax=ax3)
    ax3.set_title('Round vs Reaction Time Heatmap (Sample)', fontsize=14, fontweight='bold')
    ax3.set_xlabel('Round Number', fontsize=12)
    ax3.set_ylabel('Reaction Time Range', fontsize=12)
    
    # Sample chart 4
    ax4 = fig.add_subplot(gs[1, 1])
    sample_plays = [1, 2, 3, 4, 5]
    sample_avg_time = [380, 350, 330, 320, 310]
    ax4.scatter(sample_plays, sample_avg_time, s=120, alpha=0.7)
    ax4.plot(sample_plays, sample_avg_time, 'r--', alpha=0.8)
    ax4.set_title('Play Count vs Avg Reaction Time (Sample)', fontsize=14, fontweight='bold')
    ax4.set_xlabel('Number of Plays', fontsize=12)
    ax4.set_ylabel('Average Reaction Time (ms)', fontsize=12)
    
    plt.show()
    print("\nThis is a sample chart. Please run the game to generate real data!")
    exit()

print("\n" + "="*50 + "\n")

# Create real data charts
fig = plt.figure(figsize=(20, 15))
fig.suptitle('Reaction Time Test Data Analysis Report', fontsize=22, fontweight='bold')

gs = fig.add_gridspec(2, 2, hspace=0.4, wspace=0.3)

# Chart 1: Reaction Time Distribution
ax1 = fig.add_subplot(gs[0, 0])
if not rounds_df.empty and 'response_accuracy' in rounds_df.columns and 'reaction_time' in rounds_df.columns:
    successful_reactions = rounds_df[
        (rounds_df['response_accuracy'] == True) & 
        (rounds_df['reaction_time'] < 800)
    ]['reaction_time']
    
    if not successful_reactions.empty:
        sns.histplot(successful_reactions, bins=20, kde=True, alpha=0.7, 
                    color='skyblue', stat='density', ax=ax1)
        
        mean_time = successful_reactions.mean()
        median_time = successful_reactions.median()
        
        ax1.axvline(mean_time, color='red', linestyle='--', linewidth=2, 
                   label=f'Mean: {mean_time:.0f}ms')
        ax1.axvline(median_time, color='orange', linestyle='--', linewidth=2,
                   label=f'Median: {median_time:.0f}ms')
        
        ax1.set_title('Reaction Time Distribution', fontsize=16, fontweight='bold', pad=15)
        ax1.set_xlabel('Reaction Time (ms)', fontsize=13)
        ax1.set_ylabel('Density', fontsize=13)
        ax1.legend(fontsize=11)
        ax1.grid(True, alpha=0.3)
        
        # Statistics summary
        stats_text = (f'Statistics Summary:\n'
                     f'Sample Size: {len(successful_reactions)}\n'
                     f'Fastest: {successful_reactions.min():.0f}ms\n'
                     f'Slowest: {successful_reactions.max():.0f}ms\n'
                     f'Std Dev: {successful_reactions.std():.0f}ms')
        
        ax1.text(0.02, 0.98, stats_text, transform=ax1.transAxes, fontsize=10, 
                verticalalignment='top', 
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
    else:
        ax1.text(0.5, 0.5, 'No successful reaction data', ha='center', va='center', 
                transform=ax1.transAxes, fontsize=14)
        ax1.set_title('Reaction Time Distribution', fontsize=16, fontweight='bold', pad=15)
else:
    ax1.text(0.5, 0.5, 'No data available', ha='center', va='center', 
            transform=ax1.transAxes, fontsize=14)
    ax1.set_title('Reaction Time Distribution', fontsize=16, fontweight='bold', pad=15)

# Chart 2: Accuracy Distribution
ax2 = fig.add_subplot(gs[0, 1])
if not sessions_df.empty and not rounds_df.empty and 'response_accuracy' in rounds_df.columns:
    session_accuracy = []
    
    for session_id in sessions_df['id']:
        session_rounds = rounds_df[rounds_df['session_id'] == session_id]
        if not session_rounds.empty:
            accuracy = (session_rounds['response_accuracy'].sum() / len(session_rounds)) * 100
            session_accuracy.append(accuracy)
    
    if session_accuracy:
        accuracy_bins = [0, 40, 60, 80, 90, 100]
        accuracy_labels = ['0-40%', '41-60%', '61-80%', '81-90%', '91-100%']
        
        accuracy_counts = pd.cut(session_accuracy, bins=accuracy_bins, 
                               labels=accuracy_labels, include_lowest=True).value_counts()
        accuracy_counts = accuracy_counts[accuracy_counts > 0]
        
        if not accuracy_counts.empty:
            colors = ['#ff6b6b', '#ffa726', '#ffeb3b', '#66bb6a', '#42a5f5'][:len(accuracy_counts)]
            wedges, texts, autotexts = ax2.pie(accuracy_counts.values, 
                                              labels=accuracy_counts.index, 
                                              autopct='%1.1f%%', 
                                              startangle=90, 
                                              colors=colors)
            
            ax2.set_title('Accuracy Distribution', fontsize=16, fontweight='bold', pad=15)
            
            # Beautify text
            for text in texts:
                text.set_fontsize(10)
            for autotext in autotexts:
                autotext.set_color('black')
                autotext.set_fontweight('bold')
                autotext.set_fontsize(10)
            
            # Statistics
            mean_accuracy = np.mean(session_accuracy)
            stats_text = (f'Accuracy Statistics:\n'
                         f'Sessions: {len(session_accuracy)}\n'
                         f'Mean Accuracy: {mean_accuracy:.1f}%\n'
                         f'Max Accuracy: {max(session_accuracy):.1f}%\n'
                         f'Min Accuracy: {min(session_accuracy):.1f}%')
            
            ax2.text(1.3, 0.5, stats_text, transform=ax2.transAxes, fontsize=10, 
                    verticalalignment='center',
                    bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8))
        else:
            ax2.text(0.5, 0.5, 'Insufficient accuracy data', ha='center', va='center', 
                    transform=ax2.transAxes, fontsize=14)
            ax2.set_title('Accuracy Distribution', fontsize=16, fontweight='bold', pad=15)
    else:
        ax2.text(0.5, 0.5, 'No accuracy data', ha='center', va='center', 
                transform=ax2.transAxes, fontsize=14)
        ax2.set_title('Accuracy Distribution', fontsize=16, fontweight='bold', pad=15)
else:
    ax2.text(0.5, 0.5, 'No data available', ha='center', va='center', 
            transform=ax2.transAxes, fontsize=14)
    ax2.set_title('Accuracy Distribution', fontsize=16, fontweight='bold', pad=15)

# Chart 3: Round vs Reaction Time Heatmap/Bar Chart
ax3 = fig.add_subplot(gs[1, 0])
if not rounds_df.empty and 'response_accuracy' in rounds_df.columns and 'reaction_time' in rounds_df.columns:
    successful_rounds = rounds_df[
        (rounds_df['response_accuracy'] == True) & 
        (rounds_df['reaction_time'] < 800)
    ].copy()
    
    if not successful_rounds.empty and 'round_number' in successful_rounds.columns:
        reaction_bins = [0, 200, 300, 400, 500, 600, 800]
        reaction_labels = ['<200ms', '200-300ms', '300-400ms', '400-500ms', '500-600ms', '>600ms']
        
        successful_rounds['reaction_category'] = pd.cut(
            successful_rounds['reaction_time'], 
            bins=reaction_bins, 
            labels=reaction_labels, 
            include_lowest=True
        )
        
        heatmap_data = successful_rounds.groupby(['round_number', 'reaction_category']).size().unstack(fill_value=0)
        
        if not heatmap_data.empty and heatmap_data.shape[0] > 3 and heatmap_data.shape[1] > 2:
            # Draw heatmap
            sns.heatmap(heatmap_data.T, annot=True, fmt='d', cmap='YlOrRd', 
                       cbar_kws={'label': 'Reaction Count'}, ax=ax3)
            
            ax3.set_title('Round vs Reaction Time Heatmap', fontsize=16, fontweight='bold', pad=15)
            ax3.set_xlabel('Round Number', fontsize=13)
            ax3.set_ylabel('Reaction Time Range', fontsize=13)
            ax3.tick_params(axis='x', rotation=45, labelsize=10)
            ax3.tick_params(axis='y', rotation=0, labelsize=10)
        else:
            # Use bar chart when insufficient data
            reaction_counts = successful_rounds['reaction_category'].value_counts()
            if not reaction_counts.empty:
                bars = ax3.bar(range(len(reaction_counts)), reaction_counts.values, 
                              color='skyblue', alpha=0.7)
                ax3.set_xticks(range(len(reaction_counts)))
                ax3.set_xticklabels(reaction_counts.index, rotation=45)
                ax3.set_title('Reaction Time Distribution', fontsize=16, fontweight='bold', pad=15)
                ax3.set_xlabel('Reaction Time Range', fontsize=13)
                ax3.set_ylabel('Count', fontsize=13)
                
                # Add values on bars
                for bar in bars:
                    height = bar.get_height()
                    ax3.text(bar.get_x() + bar.get_width()/2., height,
                            f'{int(height)}', ha='center', va='bottom', fontsize=10)
            else:
                ax3.text(0.5, 0.5, 'Insufficient data for chart', ha='center', va='center', 
                        transform=ax3.transAxes, fontsize=14)
                ax3.set_title('Reaction Time Analysis', fontsize=16, fontweight='bold', pad=15)
    else:
        ax3.text(0.5, 0.5, 'No successful reaction data', ha='center', va='center', 
                transform=ax3.transAxes, fontsize=14)
        ax3.set_title('Round vs Reaction Time Heatmap', fontsize=16, fontweight='bold', pad=15)
else:
    ax3.text(0.5, 0.5, 'No data available', ha='center', va='center', 
            transform=ax3.transAxes, fontsize=14)
    ax3.set_title('Round vs Reaction Time Heatmap', fontsize=16, fontweight='bold', pad=15)

# Chart 4: Play Count vs Reaction Time Relationship (without user IDs)
ax4 = fig.add_subplot(gs[1, 1])
if not sessions_df.empty and not rounds_df.empty and not users_df.empty:
    user_stats = []
    
    for user_id in users_df['id']:
        user_sessions = sessions_df[sessions_df['user_id'] == user_id]
        play_count = len(user_sessions)
        
        user_rounds = rounds_df[
            (rounds_df['user_id'] == user_id) & 
            (rounds_df['response_accuracy'] == True) & 
            (rounds_df['reaction_time'] < 800)
        ]
        
        if not user_rounds.empty and play_count > 0:
            avg_reaction_time = user_rounds['reaction_time'].mean()
            user_stats.append({
                'play_count': play_count,
                'avg_reaction_time': avg_reaction_time,
                'total_rounds': len(user_rounds)
            })
    
    if user_stats:
        stats_df = pd.DataFrame(user_stats)
        
        # Draw scatter plot without user ID labels
        scatter = ax4.scatter(stats_df['play_count'], stats_df['avg_reaction_time'], 
                            s=stats_df['total_rounds']*8, alpha=0.7, 
                            c=range(len(stats_df)), cmap='viridis', 
                            edgecolors='black', linewidth=1)
        
        # Trend line
        if len(stats_df) > 1:
            z = np.polyfit(stats_df['play_count'], stats_df['avg_reaction_time'], 1)
            p = np.poly1d(z)
            ax4.plot(stats_df['play_count'], p(stats_df['play_count']), 
                    "r--", alpha=0.8, linewidth=2, 
                    label=f'Trend Line (slope: {z[0]:.1f})')
        
        ax4.set_title('Play Count vs Average Reaction Time', fontsize=16, fontweight='bold', pad=15)
        ax4.set_xlabel('Number of Plays', fontsize=13)
        ax4.set_ylabel('Average Reaction Time (ms)', fontsize=13)
        ax4.grid(True, alpha=0.3)
        
        if len(stats_df) > 1:
            ax4.legend(fontsize=10)
        
        # Info text without specific user count
        info_text = f'Info:\nBubble size = Total rounds\nData points: {len(stats_df)}'
        ax4.text(0.02, 0.98, info_text, transform=ax4.transAxes, fontsize=10, 
                verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.8))
    else:
        ax4.text(0.5, 0.5, 'No user statistics data', ha='center', va='center', 
                transform=ax4.transAxes, fontsize=14)
        ax4.set_title('Play Count vs Average Reaction Time', fontsize=16, fontweight='bold', pad=15)
else:
    ax4.text(0.5, 0.5, 'No data available', ha='center', va='center', 
            transform=ax4.transAxes, fontsize=14)
    ax4.set_title('Play Count vs Average Reaction Time', fontsize=16, fontweight='bold', pad=15)

# Show charts
plt.tight_layout()
plt.show()

# Print statistical report
print("\nDetailed Data Analysis Report:")
print("="*60)

if not rounds_df.empty and 'response_accuracy' in rounds_df.columns and 'reaction_time' in rounds_df.columns:
    successful_reactions = rounds_df[
        (rounds_df['response_accuracy'] == True) & 
        (rounds_df['reaction_time'] < 800)
    ]['reaction_time']
    
    if not successful_reactions.empty:
        print(f"Reaction Time Statistics:")
        print(f"   • Total successful reactions: {len(successful_reactions)}")
        print(f"   • Average reaction time: {successful_reactions.mean():.2f} ms")
        print(f"   • Median reaction time: {successful_reactions.median():.2f} ms")
        print(f"   • Fastest reaction time: {successful_reactions.min()} ms")
        print(f"   • Slowest reaction time: {successful_reactions.max()} ms")
        print(f"   • Standard deviation: {successful_reactions.std():.2f} ms")
        
        # Level analysis
        lightning = len(successful_reactions[successful_reactions < 200])
        excellent = len(successful_reactions[(successful_reactions >= 200) & (successful_reactions < 300)])
        good = len(successful_reactions[(successful_reactions >= 300) & (successful_reactions < 400)])
        average = len(successful_reactions[(successful_reactions >= 400) & (successful_reactions < 500)])
        slow = len(successful_reactions[successful_reactions >= 500])
        
        total = len(successful_reactions)
        print(f"\nReaction Level Distribution:")
        print(f"   • Lightning (<200ms): {lightning} times ({lightning/total*100:.1f}%)")
        print(f"   • Excellent (200-300ms): {excellent} times ({excellent/total*100:.1f}%)")
        print(f"   • Good (300-400ms): {good} times ({good/total*100:.1f}%)")
        print(f"   • Average (400-500ms): {average} times ({average/total*100:.1f}%)")
        print(f"   • Slow (>500ms): {slow} times ({slow/total*100:.1f}%)")

if not sessions_df.empty and not rounds_df.empty and 'response_accuracy' in rounds_df.columns:
    total_accuracy = (rounds_df['response_accuracy'].sum() / len(rounds_df)) * 100
    print(f"\nOverall Accuracy: {total_accuracy:.2f}%")
    print(f"Total Game Sessions: {len(sessions_df)}")
    print(f"Total Users: {len(users_df)}")

print("\n" + "="*60)
print("Analysis complete! Charts displayed.")