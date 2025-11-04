import os
import requests
import time
from urllib.parse import quote

# 设置music文件夹和lrc文件夹的路径
music_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'music')
lrc_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lrc')

# 确保lrc文件夹存在
if not os.path.exists(lrc_folder):
    os.makedirs(lrc_folder)

# 获取music文件夹中所有的MP3文件和lrc文件夹中所有的歌词文件
def get_existing_files():
    music_files = []
    for file in os.listdir(music_folder):
        if file.lower().endswith('.mp3'):
            file_name_without_ext = os.path.splitext(file)[0]
            music_files.append((file_name_without_ext, file))
    
    lrc_files = []
    for file in os.listdir(lrc_folder):
        if file.lower().endswith('.lrc'):
            file_name_without_ext = os.path.splitext(file)[0]
            lrc_files.append(file_name_without_ext)
    
    return music_files, lrc_files

# 提取歌曲名和歌手（简单解析文件名）
def extract_song_info(file_name):
    # 尝试从文件名中提取歌曲名和歌手
    # 假设文件名格式为：歌曲名 - 歌手.mp3
    parts = file_name.split(' - ')
    if len(parts) == 2:
        song_name = parts[0].strip()
        artist = parts[1].strip()
    else:
        # 如果不符合预期格式，将整个文件名作为歌曲名
        song_name = file_name.strip()
        artist = ''
    return song_name, artist

# 搜索并下载歌词（使用歌词千寻作为示例，实际使用时可能需要调整）
def download_lyrics(song_name, artist, save_path):
    try:
        # 构建搜索URL（歌词千寻API示例）
        search_url = f"http://api.lrcgc.com/search?keyword={quote(song_name + ' ' + artist)}&limit=5"
        
        # 设置请求头模拟浏览器
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # 发送请求
        response = requests.get(search_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # 解析响应（这里假设返回的是JSON格式，实际格式可能不同）
        data = response.json()
        
        # 检查是否有搜索结果
        if data and 'data' in data and len(data['data']) > 0:
            # 获取第一个结果的歌词URL
            lyric_url = data['data'][0].get('lrcUrl')
            if lyric_url:
                # 下载歌词内容
                lyric_response = requests.get(lyric_url, headers=headers, timeout=10)
                lyric_response.raise_for_status()
                
                # 保存歌词到文件
                with open(save_path, 'w', encoding='utf-8') as f:
                    f.write(lyric_response.text)
                
                return True, f"成功下载歌词: {song_name} - {artist}"
            else:
                return False, f"未找到歌词URL: {song_name} - {artist}"
        else:
            return False, f"未找到匹配的歌词: {song_name} - {artist}"
            
    except Exception as e:
        return False, f"下载歌词时出错: {song_name} - {artist}, 错误信息: {str(e)}"

# 主函数
def main():
    music_files, lrc_files = get_existing_files()
    total_songs = len(music_files)
    existing_lyrics = len(lrc_files)
    
    print(f"总共有 {total_songs} 首MP3歌曲")
    print(f"总共有 {existing_lyrics} 个歌词文件")
    
    # 找出没有对应歌词文件的歌曲
    missing_lyrics_count = 0
    downloaded_count = 0
    failed_count = 0
    
    for file_name_without_ext, original_file_name in music_files:
        if file_name_without_ext not in lrc_files:
            missing_lyrics_count += 1
            song_name, artist = extract_song_info(file_name_without_ext)
            
            # 构建保存路径
            save_path = os.path.join(lrc_folder, file_name_without_ext + '.lrc')
            
            print(f"\n正在处理: {original_file_name}")
            print(f"搜索歌词: {song_name} - {artist}")
            
            # 下载歌词
            success, message = download_lyrics(song_name, artist, save_path)
            print(message)
            
            if success:
                downloaded_count += 1
            else:
                failed_count += 1
            
            # 添加延迟，避免请求过于频繁
            time.sleep(1)
    
    print(f"\n歌词下载完成！")
    print(f"共检测到 {missing_lyrics_count} 首歌曲缺少歌词")
    print(f"成功下载: {downloaded_count} 个歌词文件")
    print(f"下载失败: {failed_count} 个歌词文件")

if __name__ == "__main__":
    main()