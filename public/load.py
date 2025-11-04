import os
import json

# 设置music文件夹和songs.json文件的路径
music_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'music')
songs_json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'songs.json')

# 获取music文件夹中所有的MP3文件
song_files = []
for file in os.listdir(music_folder):
    # 只处理MP3文件（忽略mid等其他文件）
    if file.lower().endswith('.mp3'):
        song_files.append({'name': file})

# 将歌曲信息写入songs.json文件
with open(songs_json_path, 'w', encoding='utf-8') as f:
    json.dump(song_files, f, ensure_ascii=False, indent=2)

print(f"成功加载了{len(song_files)}首歌曲到songs.json文件中")