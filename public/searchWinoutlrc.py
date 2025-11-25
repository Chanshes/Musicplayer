import os

# 设置music文件夹和lrc文件夹的路径
music_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'music')
lrc_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lrc')

# 获取music文件夹中所有的MP3文件
music_files = []
for file in os.listdir(music_folder):
    # 只处理MP3文件
    if file.lower().endswith('.mp3'):
        # 获取不带扩展名的文件名
        file_name_without_ext = os.path.splitext(file)[0]
        music_files.append(file_name_without_ext)

# 获取lrc文件夹中所有的歌词文件
lrc_files = []
for file in os.listdir(lrc_folder):
    # 只处理lrc文件
    if file.lower().endswith('.lrc'):
        # 获取不带扩展名的文件名
        file_name_without_ext = os.path.splitext(file)[0]
        lrc_files.append(file_name_without_ext)

# 找出没有对应歌词文件的歌曲
no_lrc_songs = []
for song in music_files:
    if song not in lrc_files:
        # 添加原始文件名（带.mp3扩展名）
        original_file_name = song + '.mp3'
        no_lrc_songs.append(original_file_name)

# 输出结果
print(f"总共有 {len(music_files)} 首MP3歌曲")
print(f"总共有 {len(lrc_files)} 个歌词文件")
print(f"没有对应歌词文件的歌曲有 {len(no_lrc_songs)} 首：")
for song in no_lrc_songs:
    print(f"- {song}")
