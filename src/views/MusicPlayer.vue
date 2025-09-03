<template>
  <div class="music-player">
    <h2>本地音乐播放器</h2>
    <div class="folder-input">
      <label for="folder-upload">
        <i class="fas fa-folder-open"></i> 选择音乐文件夹
      </label>
      <input id="folder-upload" type="file" webkitdirectory @change="onFolderChange" />
    </div>
    
    <div v-for="(artistSongs, artist) in songsByArtist" :key="artist" class="artist-section">
      <h3>{{ artist }}</h3>
      <ul class="songs-list">
        <li v-for="(song, idx) in artistSongs" :key="idx" class="song-item">
          <button
            class="button-bubble"
            :class="{ 
              'currently-playing': isCurrentlyPlaying(song),
              'in-playlist': isInPlaylist(song)
            }"
            :style="bubbleStyle(idx)"
            @click="handleSongClick(song)"
          >
            {{ song.displayName }}
            <span v-if="isCurrentlyPlaying(song)" class="playing-indicator">♪</span>
          </button>
        </li>
      </ul>
    </div>
  </div>
      <!-- 歌词显示区域 -->
    <div v-if="lyrics" class="lyrics-container">
      <h3>歌词</h3>
      <pre>{{ lyrics }}</pre>
    </div>
    
    <!-- 悬浮底部播放栏 -->
    <div v-if="audioUrl" class="player-bar" :class="{ closed: playerBarClosed }">
      <transition name="player-bar-slide">
        <div v-show="!playerBarClosed" class="player-bar-content">
          <audio
            ref="audio"
            :src="audioUrl"
            controls
            @ended="onEnded"
            @timeupdate="updateTime"
          ></audio>
          <div class="player-info">
            <span>当前时间：{{ currentTime.toFixed(1) }} 秒</span>
            <span v-if="lyrics" class="lyrics-tip">歌词已加载</span>
          </div>
        </div>
      </transition>
    </div>
    
    <!-- 播放列表弹窗 -->
    <div class="playlist-popup" :class="{ open: playlistOpen }">
      <div class="playlist-header">
        <span>播放列表</span>
        <button class="clear-btn" @click="clearPlaylist">清空列表</button>
      </div>
      <div class="play-modes">
        <button
          v-for="mode in playModes"
          :key="mode.value"
          :class="['mode-btn', { active: playMode === mode.value }]"
          @click="setPlayMode(mode.value)"
        >
          {{ mode.label }}
        </button>
      </div>
      <ul>
        <li
          v-for="(song, idx) in playlist"
          :key="idx"
          class="playlist-li"
          @mouseenter="hoverIdx = idx"
          @mouseleave="hoverIdx = -1"
        >
          <button
            class="playlist-item"
            :class="{ playing: idx === currentPlaylistIdx }"
            @click="playFromPlaylist(idx)"
          >
            <span>{{ song.displayName }} - {{ song.artist }}</span>
            <span
              v-if="hoverIdx === idx"
              class="remove-btn"
              @click.stop="removeFromPlaylist(idx)"
            >×</span>
          </button>
        </li>
      </ul>
    </div>
    
    <!-- 播放列表收纳按钮（悬浮在右侧） -->
    <button class="playlist-arrow" @click="togglePlaylist">
      <span v-if="playlistOpen">→</span>
      <span v-else>←</span>
    </button>
    
    <!-- 固定在右下角的播放栏收纳按钮 -->
    <button v-if="audioUrl" class="player-bar-arrow" @click="togglePlayerBar">
      <span v-if="playerBarClosed">↑</span>
      <span v-else>↓</span>
    </button>
    
</template>

<script lang="ts">
import { defineComponent, ref, computed } from 'vue';

interface SongFile {
  name: string;
  url: string;
  file: File;
  displayName: string;
  artist: string;
}

export default defineComponent({
  name: 'MusicPlayer',
  setup() {
    const songs = ref<SongFile[]>([]);
    const audioUrl = ref<string | null>(null);
    const currentTime = ref(0);
    const lyrics = ref<string | null>(null);

    // 歌曲分组
    const onFolderChange = (e: Event) => {
      const files = (e.target as HTMLInputElement).files;
      if (files) {
        songs.value = [];
        for (const file of Array.from(files)) {
          if (file.type.startsWith('audio/')) {
            const baseName = file.name.replace(/\.[^.]+$/, '');
            const [songName, artistName] = baseName.split('-');
            songs.value.push({
              name: file.name,
              url: URL.createObjectURL(file),
              file,
              displayName: songName ? songName.trim() : file.name,
              artist: artistName ? artistName.trim() : '未知歌手'
            });
          }
        }
      }
    };

    const songsByArtist = computed(() => {
      const groups: Record<string, SongFile[]> = {};
      for (const song of songs.value) {
        if (!groups[song.artist]) groups[song.artist] = [];
        groups[song.artist].push(song);
      }
      return groups;
    });

    // 播放列表相关
    const playlist = ref<SongFile[]>([]);
    const playlistOpen = ref(false);
    const currentPlaylistIdx = ref(-1);
    const hoverIdx = ref(-1);

    function addToPlaylist(song: SongFile) {
      // 防止重复添加
      if (!playlist.value.find(s => s.url === song.url)) {
        playlist.value.push(song);
      }
      // 自动播放刚添加的歌曲
      playFromPlaylist(playlist.value.length - 1);
    }

    function playFromPlaylist(idx: number) {
      const song = playlist.value[idx];
      if (!song) return;
      audioUrl.value = song.url;
      currentPlaylistIdx.value = idx;
      // 查找同名歌词文件
      lyrics.value = null;
      const lrcName = song.name.replace(/\.[^.]+$/, '.lrc');
      const lrcFile = songs.value.find(f => f.name === lrcName);
      if (lrcFile) {
        const reader = new FileReader();
        reader.onload = () => {
          lyrics.value = reader.result as string;
        };
        reader.readAsText(lrcFile.file);
      }
      setTimeout(() => {
        const audio = document.querySelector('audio');
        if (audio) audio.play();
      }, 100);
    }

    function togglePlaylist() {
      playlistOpen.value = !playlistOpen.value;
    }

    function clearPlaylist() {
      playlist.value = [];
      audioUrl.value = null;
      currentPlaylistIdx.value = -1;
    }

    function removeFromPlaylist(idx: number) {
      playlist.value.splice(idx, 1);
      // 如果移除的是当前播放，停止播放或播放下一首
      if (currentPlaylistIdx.value === idx) {
        if (playlist.value.length === 0) {
          audioUrl.value = null;
          currentPlaylistIdx.value = -1;
        } else {
          let nextIdx = idx;
          if (nextIdx >= playlist.value.length) nextIdx = playlist.value.length - 1;
          playFromPlaylist(nextIdx);
        }
      } else if (currentPlaylistIdx.value > idx) {
        currentPlaylistIdx.value -= 1;
      }
    }

    // 播放模式
    const playModes = [
      { label: '单曲循环', value: 'single' },
      { label: '列表循环', value: 'list' },
      { label: '随机播放', value: 'random' }
    ];
    const playMode = ref<'single' | 'list' | 'random'>('list');

    function setPlayMode(mode: string) {
      if (mode === 'single' || mode === 'list' || mode === 'random') {
        playMode.value = mode;
      }
    }

    // 播放结束时根据模式切换下一首
    function onEnded() {
      if (playlist.value.length === 0) return;
      if (playMode.value === 'single') {
        // 单曲循环
        setTimeout(() => {
          const audio = document.querySelector('audio');
          if (audio) audio.currentTime = 0;
          if (audio) audio.play();
        }, 100);
      } else if (playMode.value === 'list') {
        // 列表循环
        let nextIdx = currentPlaylistIdx.value + 1;
        if (nextIdx >= playlist.value.length) nextIdx = 0;
        playFromPlaylist(nextIdx);
      } else if (playMode.value === 'random') {
        // 随机播放
        let nextIdx = Math.floor(Math.random() * playlist.value.length);
        playFromPlaylist(nextIdx);
      }
    }

    const updateTime = (e: Event) => {
      const audio = e.target as HTMLAudioElement;
      currentTime.value = audio.currentTime;
    };

    // 气泡颜色
    const gradients = [
      'linear-gradient(135deg, #ff7e5f, #feb47b)',
      'linear-gradient(135deg, #6dd5ed, #2193b0)',
      'linear-gradient(135deg, #cc2b5e, #753a88)',
      'linear-gradient(135deg, #43cea2, #185a9d)',
      'linear-gradient(135deg, #f7971e, #ffd200)',
      'linear-gradient(135deg, #ee9ca7, #ffdde1)',
      'linear-gradient(135deg, #f953c6, #b91d73)',
      'linear-gradient(135deg, #30cfd0, #330867)',
      'linear-gradient(135deg, #5f2c82, #49a09d)',
      'linear-gradient(135deg, #a8ff78, #78ffd6)',
      'linear-gradient(135deg, #fcb69f, #ffecd2)',
      'linear-gradient(135deg, #c471f5, #fa71cd)'
    ];

    function bubbleStyle(idx: number) {
      return {
        background: gradients[idx % gradients.length],
        animation: 'bubble-gradient 8s ease infinite',
        backgroundSize: '400% 400%'
      };
    }

    const playerBarClosed = ref(false);
    function togglePlayerBar() {
      playerBarClosed.value = !playerBarClosed.value;
    }

    // 判断歌曲是否正在播放
    function isCurrentlyPlaying(song: SongFile) {
      return audioUrl.value === song.url && currentPlaylistIdx.value >= 0;
    }

    // 判断歌曲是否在播放列表中
    function isInPlaylist(song: SongFile) {
      return playlist.value.some(s => s.url === song.url);
    }

    // 处理歌曲点击
    function handleSongClick(song: SongFile) {
      const playlistIndex = playlist.value.findIndex(s => s.url === song.url);
      
      if (playlistIndex >= 0) {
        // 如果歌曲已在播放列表中，直接播放
        playFromPlaylist(playlistIndex);
      } else {
        // 如果歌曲不在播放列表中，添加到播放列表并播放
        addToPlaylist(song);
      }
    }

    return {
      songsByArtist,
      audioUrl,
      currentTime,
      lyrics,
      onFolderChange,
      addToPlaylist,
      updateTime,
      bubbleStyle,
      playlist,
      playlistOpen,
      togglePlaylist,
      playModes,
      playMode,
      setPlayMode,
      onEnded,
      playFromPlaylist,
      currentPlaylistIdx,
      clearPlaylist,
      removeFromPlaylist,
      hoverIdx,
      playerBarClosed,
      togglePlayerBar,
      isCurrentlyPlaying,
      isInPlaylist,
      handleSongClick,
    };
  }
});
</script>

<style scoped>
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

.music-player {
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
    background: rgba(255, 255, 255, 0.1);
    backdrop-filter: blur(10px);
    border-radius: 20px;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
}

h2 {
    text-align: center;
    margin-bottom: 25px;
    font-size: 2.2rem;
    text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
}

.folder-input {
    text-align: center;
    margin-bottom: 30px;
}

.folder-input label {
    display: inline-block;
    padding: 12px 25px;
    background: linear-gradient(135deg, #6a11cb 0%, #2575fc 100%);
    color: white;
    border-radius: 50px;
    cursor: pointer;
    transition: all 0.3s;
    font-weight: 600;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
}

.folder-input label:hover {
    transform: translateY(-3px);
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.3);
}

.folder-input input {
    display: none;
}

.artist-section {
    margin-bottom: 30px;
    padding: 15px;
    background: rgba(255, 255, 255, 0.08);
    border-radius: 15px;
}

.artist-section h3 {
    margin-bottom: 15px;
    padding-bottom: 8px;
    border-bottom: 2px solid rgba(255, 255, 255, 0.2);
    font-size: 1.5rem;
}

.songs-list {
    display: flex;
    flex-wrap: wrap;
    gap: 15px;
    list-style: none;
}

.song-item {
    margin: 0;
}

.button-bubble {
    padding: 12px 24px;
    border: none;
    border-radius: 24px;
    font-size: 1.25rem;
    color: #fff;
    font-weight: 700;
    cursor: pointer;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.12);
    transition: transform 0.2s;
    min-width: 160px;
}

.button-bubble:hover {
    transform: scale(1.08);
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.18);
}

/* 当前播放歌曲的样式 */
.button-bubble.currently-playing {
    position: relative;
    border: 3px solid #ffeb3b;
    box-shadow: 0 0 20px rgba(255, 235, 59, 0.5);
    animation: pulse-glow 2s ease-in-out infinite alternate;
}

.button-bubble.currently-playing .playing-indicator {
    position: absolute;
    top: -5px;
    right: -5px;
    background: #ffeb3b;
    color: #333;
    border-radius: 50%;
    width: 24px;
    height: 24px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 14px;
    font-weight: bold;
    animation: bounce 1s ease-in-out infinite;
}

/* 已在播放列表中的歌曲样式 */
.button-bubble.in-playlist:not(.currently-playing) {
    border: 2px solid rgba(255, 255, 255, 0.6);
    box-shadow: 0 0 10px rgba(255, 255, 255, 0.3);
}

/* 动画效果 */
@keyframes pulse-glow {
    0% {
        box-shadow: 0 0 20px rgba(255, 235, 59, 0.5);
    }
    100% {
        box-shadow: 0 0 30px rgba(255, 235, 59, 0.8);
    }
}

@keyframes bounce {
    0%, 100% {
        transform: translateY(0);
    }
    50% {
        transform: translateY(-3px);
    }
}

/* 播放栏样式 */
.player-bar {
    position: fixed;
    border-radius: 24px 24px 0 0;
    left: 50%;
    transform: translate(-50%, 0);
    bottom: 0;
    width: 90vw;
    background: #2193b0;
    color: #fff;
    box-shadow: 0 -2px 12px rgba(0, 0, 0, 0.12);
    z-index: 999;
    transition: transform 0.3s ease;
}

.player-bar.closed {
    transform: translateY(100%);
}

.player-bar-content {
    padding: 15px 20px;
    display: flex;
    flex-direction: column;
    align-items: center;
    max-width: 1000px;
    margin: 0 auto;
}

.player-bar audio {
    width: 100%;
    margin-bottom: 10px;
}

.player-info {
    display: flex;
    justify-content: space-between;
    width: 100%;
    font-size: 0.9rem;
}

.lyrics-tip {
    color: #ffeb3b;
    font-weight: 600;
}


/* 播放列表样式 */
.playlist-popup {
    position: fixed;
    top: 60px;
    right: 0;
    width: 320px;
    max-width: 40vw;
    height: 70vh;
    background: #fff;
    box-shadow: -2px 0 16px rgba(0, 0, 0, 0.12);
    border-radius: 16px 0 0 16px;
    transform: translateX(100%);
    transition: transform 0.3s;
    z-index: 100;
    display: flex;
    flex-direction: column;
    padding: 16px;
    color: #333;
}

.playlist-popup.open {
    transform: translateX(0);
}

.playlist-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-weight: bold;
    font-size: 1.2rem;
    margin-bottom: 8px;
    color: #2193b0;
}

.clear-btn {
    background: #e74c3c;
    color: #fff;
    border: none;
    border-radius: 8px;
    font-size: 0.95rem;
    font-weight: 700;
    padding: 4px 12px;
    cursor: pointer;
    transition: background 0.2s;
}

.clear-btn:hover {
    background: #c0392b;
}

.play-modes {
    margin: 12px 0;
    display: flex;
    gap: 12px;
    justify-content: center;
}

.mode-btn {
    padding: 6px 18px;
    border-radius: 18px;
    border: none;
    background: #eee;
    color: #333;
    font-size: 1rem;
    font-weight: 700;
    cursor: pointer;
    transition: background 0.2s;
}

.mode-btn.active {
    background: #2193b0;
    color: #fff;
}

.playlist-popup ul {
    flex: 1;
    overflow-y: auto;
    max-height: 50vh;
    margin: 0;
    padding: 0;
}

.playlist-li {
    position: relative;
    list-style: none;
    margin-bottom: 8px;
}

.playlist-item {
    width: 100%;
    text-align: left;
    padding: 8px 16px;
    border: none;
    border-radius: 12px;
    background: #f5f5f5;
    color: #333;
    font-size: 1.1rem;
    font-weight: 600;
    cursor: pointer;
    transition: background 0.2s;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.playlist-item.playing {
    background: #2193b0;
    color: #fff;
}

.remove-btn {
    font-size: 1.5rem;
    color: #e74c3c;
    background: transparent;
    border: none;
    cursor: pointer;
    padding: 0;
    width: 24px;
    height: 24px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 50%;
}

.remove-btn:hover {
    background: #e74c3c;
    color: #fff;
}

.playlist-arrow {
    position: fixed;
    top: 50%;
    right: 0;
    transform: translateY(-50%);
    background: #2193b0;
    color: #fff;
    border: none;
    border-radius: 16px 0 0 16px;
    font-size: 1.5rem;
    padding: 8px 12px;
    cursor: pointer;
    z-index: 101;
    transition: all 0.3s;
}

.playlist-arrow:hover {
    background: #17627a;
}

.lyrics-container {
    margin-top: 20px;
    padding: 15px;
    background: rgba(255, 255, 255, 0.08);
    border-radius: 15px;
    max-height: 300px;
    overflow-y: auto;
}

.lyrics-container h3 {
    margin-bottom: 10px;
    color: #ffeb3b;
}

.lyrics-container pre {
    white-space: pre-wrap;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    line-height: 1.6;
}

/* 动画效果 */
.player-bar-slide-enter-active,
.player-bar-slide-leave-active {
    transition: opacity 0.3s, transform 0.3s;
}

.player-bar-slide-enter-from,
.player-bar-slide-leave-to {
    opacity: 0;
    transform: translateY(30px);
}

@keyframes bubble-gradient {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}

/* 固定在右下角的收纳按钮 */
.player-bar-arrow {
    position: fixed;
    right: 30px;
    bottom: 30px;
    background: #17627a;
    color: #fff;
    border: none;
    border-radius: 50%;
    font-size: 1.3rem;
    width: 50px;
    height: 50px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
    cursor: pointer;
    transition: all 0.3s;
    z-index: 1000;
    display: flex;
    align-items: center;
    justify-content: center;
}

.player-bar-arrow:hover {
    background: #2193b0;
    transform: scale(1.1);
}

/* 响应式设计 */
@media (max-width: 768px) {
    .music-player {
        padding: 15px;
    }
    
    h2 {
        font-size: 1.8rem;
    }
    
    .button-bubble {
        font-size: 1rem;
        padding: 10px 20px;
        min-width: 140px;
    }
    
    .player-bar-content {
        padding: 10px 15px;
    }
    
    .playlist-popup {
        width: 280px;
    }
    
    .player-bar-arrow {
        right: 20px;
        bottom: 20px;
        width: 45px;
        height: 45px;
    }
}
</style>
