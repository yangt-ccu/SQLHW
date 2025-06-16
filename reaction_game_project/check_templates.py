import os
import re

def check_template_urls():
    """檢查模板中的URL引用"""
    template_dir = "templates"
    url_for_pattern = r"url_for\(['\"]([^'\"]+)['\"]\)"
    
    issues = []
    
    for root, dirs, files in os.walk(template_dir):
        for file in files:
            if file.endswith('.html'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    matches = re.findall(url_for_pattern, content)
                    if matches:
                        print(f"\n📄 {file_path}:")
                        for match in matches:
                            print(f"  url_for('{match}')")
                            
                            # 檢查常見問題
                            if match == 'game_menu':
                                issues.append(f"{file_path}: url_for('game_menu') 應該是 url_for('game_menu')")
                            elif '_' in match and '-' not in match:
                                # 檢查是否應該使用連字符
                                potential_fix = match.replace('_', '-')
                                issues.append(f"{file_path}: url_for('{match}') 可能應該是 url_for('{potential_fix}')")
                                
                except Exception as e:
                    print(f"❌ 讀取文件失敗 {file_path}: {e}")
    
    if issues:
        print(f"\n⚠️ 發現 {len(issues)} 個潛在問題:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("\n✅ 沒有發現明顯的URL問題")

if __name__ == "__main__":
    check_template_urls()