<template>
  <div class="music-player">
    <h2>本地音乐播放器</h2>

    <!-- 音乐列表 -->
    <div class="music-list">
      <div v-for="(artistSongs, artist) in songsByArtist" :key="artist" class="artist-section">
        <h3>{{ artist }}</h3>
        <ul class="songs-list">
          <li v-for="(song, idx) in artistSongs" :key="idx" class="song-item">
            <button class="button-bubble" :class="{
              'currently-playing': isCurrentlyPlaying(song),
              'in-playlist': isInPlaylist(song)
            }" :style="bubbleStyle(idx)" @click="handleSongClick(song)">
              {{ song.displayName }}
              <span v-if="isCurrentlyPlaying(song)" class="playing-indicator">♪</span>
            </button>
          </li>
        </ul>
      </div>
    </div>

    <!-- 空状态提示 -->
    <div v-if="Object.keys(songsByArtist).length === 0" class="empty-state">
      <p>暂无音乐文件</p>
      <p class="default-info">请添加音乐文件到 public/music 目录</p>
    </div>

    <!-- 歌词显示区域 -->
    <div v-if="lyrics" class="lyrics-container">
      <h3>歌词</h3>
      <pre>{{ lyrics }}</pre>
    </div>
  </div>
  <!-- 播放控制栏 -->
  <div class="player-bar" :class="{ closed: playerBarClosed }">
    <div class="player-header">
      <span>音乐控制</span>
      <button class="toggle-player-bar" @click="togglePlayerBar">
        {{ playerBarClosed ? '▲' : '▼' }}
      </button>
    </div>

    <transition name="player-bar-slide">
      <div v-show="!playerBarClosed" class="player-bar-content">
        <div class="player-controls">
          <div class="player-info">
            <span v-if="currentSong">当前播放: {{ currentSong.displayName }} - {{ currentSong.artist }}</span>
          </div>

          <div class="player-buttons">
            <button @click="playPrevious" class="player-btn prev-btn">◀◀</button>
            <button @click="togglePlayPause" class="player-btn play-btn">
              {{ isPlaying ? '⏸' : '▶' }}
            </button>
            <button @click="playNext" class="player-btn next-btn">▶▶</button>
          </div>

          <div class="progress-container">
            <span class="time">{{ currentTime.toFixed(1) }}s</span>
            <input type="range" min="0" :max="duration" v-model="progress" @input="seekTo" class="progress-bar" />
            <span class="time">{{ duration.toFixed(1) }}s</span>
          </div>
        </div>
      </div>
    </transition>
  </div>

  <!-- 播放列表 -->
  <div class="playlist-popup" :class="{ open: playlistOpen }"
    :style="{ transform: playlistOpen ? 'translateX(0)' : 'translateX(100%)' }">
    <div class="playlist-header">
      <span>播放列表</span>
      <button class="clear-btn" @click="clearPlaylist">清空列表</button>
    </div>

    <div class="play-modes">
      <button v-for="mode in playModes" :key="mode.value" :class="['mode-btn', { active: playMode === mode.value }]"
        @click="setPlayMode(mode.value)">
        {{ mode.label }}
      </button>
    </div>

    <div class="playlist-content">
      <ul>
        <li v-for="(song, idx) in playlist" :key="idx" class="playlist-li" @mouseenter="hoverIdx = idx"
          @mouseleave="hoverIdx = -1">
          <button class="playlist-item" :class="{ playing: idx === currentPlaylistIdx }" @click="playFromPlaylist(idx)">
            <span>{{ song.displayName }} - {{ song.artist }}</span>
            <span v-if="hoverIdx === idx" class="remove-btn" @click.stop="removeFromPlaylist(idx)">×</span>
          </button>
        </li>
      </ul>

      <!-- 空状态提示 -->
      <div v-if="playlist.length === 0" class="empty-playlist">
        播放列表为空，请添加歌曲
      </div>
    </div>
  </div>

  <!-- 播放列表切换按钮 - 固定在右侧中部 -->
  <button class="playlist-toggle" @click="togglePlaylist" :class="{ open: playlistOpen }">
    {{ playlistOpen ? '◀' : '▶' }}
  </button>

</template>

<script lang="ts">
import { defineComponent, ref, onMounted, onUnmounted, computed } from 'vue';

interface SongFile {
  name: string;
  url: string;
  displayName: string;
  artist: string;
}

export default defineComponent({
  name: 'MusicPlayer',
  setup() {
    // 状态管理
    const songs = ref<SongFile[]>([]);
    const audioRef = ref<HTMLAudioElement | null>(null);
    const audioUrl = ref<string | null>(null);
    const currentTime = ref(0);
    const duration = ref(0);
    const isPlaying = ref(false);
    const progress = ref(0);
    const lyrics = ref<string | null>(null);
    const playlist = ref<SongFile[]>([]);
    const playlistOpen = ref(false);
    const currentPlaylistIdx = ref(-1);
    const hoverIdx = ref(-1);
    const playerBarClosed = ref(false);
    const currentSong = ref<SongFile | null>(null);
    const playMode = ref<'single' | 'list' | 'random'>('list');

    // 播放模式
    const playModes = [
      { label: '单曲循环', value: 'single' as const },
      { label: '列表循环', value: 'list' as const },
      { label: '随机播放', value: 'random' as const }
    ];

    // 加载歌曲
    const loadSongs = async () => {
      try {
        const response = await fetch('/music/songs.json');
        if (!response.ok) {
          throw new Error(`网络请求失败: ${response.status}`);
        }

        const data = await response.json();
        songs.value = data.map((song: any) => ({
          name: song.name,
          url: `/music/${song.name}`,
          displayName: song.displayName,
          artist: song.artist
        }));

        console.log('成功加载歌曲数据:', songs.value);
      } catch (error) {
        console.error('加载歌曲数据失败:', error);
      }
    };

    // 播放控制
    const playSong = (song: SongFile) => {
      if (!audioRef.value) return;

      audioUrl.value = song.url;
      currentSong.value = song;
      isPlaying.value = true;

      // 尝试加载歌词
      lyrics.value = null;
      const lrcName = song.name.replace(/\.[^.]+$/, '.lrc');
      fetch(`/music/${lrcName}`)
        .then(response => response.text())
        .then(text => {
          lyrics.value = text;
        })
        .catch(() => {
          lyrics.value = null;
        });

      // 设置音频源并播放
      audioRef.value.src = song.url;
      audioRef.value.play().catch(e => console.error('播放失败:', e));
    };

    // 播放/暂停切换
    const togglePlayPause = () => {
      if (!audioRef.value) return;

      if (isPlaying.value) {
        audioRef.value.pause();
      } else {
        audioRef.value.play();
      }
      isPlaying.value = !isPlaying.value;
    };

    // 播放上一首
    const playPrevious = () => {
      if (!currentSong.value || playlist.value.length === 0) return;

      const currentIndex = playlist.value.findIndex(
        song => song.url === currentSong.value?.url
      );

      if (currentIndex <= 0) return;

      playSong(playlist.value[currentIndex - 1]);
    };

    // 播放下一首
    const playNext = () => {
      if (!currentSong.value || playlist.value.length === 0) return;

      const currentIndex = playlist.value.findIndex(
        song => song.url === currentSong.value?.url
      );

      if (currentIndex < 0 || currentIndex >= playlist.value.length - 1) {
        playSong(playlist.value[0]);
      } else {
        playSong(playlist.value[currentIndex + 1]);
      }
    };

    // 添加到播放列表
    const addToPlaylist = (song: SongFile) => {
      if (!playlist.value.find(s => s.url === song.url)) {
        playlist.value.push(song);
      }
      playSong(song);
    };

    // 从播放列表播放
    const playFromPlaylist = (idx: number) => {
      if (idx >= 0 && idx < playlist.value.length) {
        playSong(playlist.value[idx]);
        currentPlaylistIdx.value = idx;
      }
    };

    // 切换播放列表显示
    const togglePlaylist = () => {
      playlistOpen.value = !playlistOpen.value;
    };

    // 清空播放列表
    const clearPlaylist = () => {
      playlist.value = [];
      if (currentSong.value) {
        playSong(currentSong.value);
      }
      currentPlaylistIdx.value = -1;
    };

    // 从播放列表移除
    const removeFromPlaylist = (idx: number) => {
      playlist.value.splice(idx, 1);
      if (currentPlaylistIdx.value === idx) {
        if (playlist.value.length > 0) {
          playSong(playlist.value[Math.min(idx, playlist.value.length - 1)]);
        } else {
          audioUrl.value = null;
          currentSong.value = null;
          isPlaying.value = false;
        }
      } else if (currentPlaylistIdx.value > idx) {
        currentPlaylistIdx.value--;
      }
    };

    // 播放模式处理
    const setPlayMode = (mode: 'single' | 'list' | 'random') => {
      playMode.value = mode;
    };

    // 音频事件处理
    const handleAudioTimeUpdate = () => {
      if (!audioRef.value) return;

      currentTime.value = audioRef.value.currentTime;
      duration.value = audioRef.value.duration || 0;
      progress.value = duration.value > 0 ? (currentTime.value / duration.value) * 100 : 0;
    };

    const handleAudioEnded = () => {
      if (!currentSong.value || playlist.value.length === 0) return;

      if (playMode.value === 'single') {
        audioRef.value?.currentTime && (audioRef.value.currentTime = 0);
        audioRef.value?.play();
      } else if (playMode.value === 'list') {
        const currentIndex = playlist.value.findIndex(
          song => song.url === currentSong.value?.url
        );

        if (currentIndex < 0 || currentIndex >= playlist.value.length - 1) {
          playSong(playlist.value[0]);
        } else {
          playSong(playlist.value[currentIndex + 1]);
        }
      } else if (playMode.value === 'random') {
        const randomIndex = Math.floor(Math.random() * playlist.value.length);
        playSong(playlist.value[randomIndex]);
      }
    };

    // 跳转到指定时间
    const seekTo = (event: Event) => {
      if (!audioRef.value) return;
      const target = event.target as HTMLInputElement;
      const newTime = (parseFloat(target.value) / 100) * duration.value;
      audioRef.value.currentTime = newTime;
      currentTime.value = newTime;
      if (!isPlaying.value) {
        isPlaying.value = true;
        audioRef.value.play();
      }
    };

    // 气泡颜色
    const bubbleStyle = (idx: number) => {
      return {
        background: `hsl(${idx * 10}, 70%, 60%)`,
        animation: 'bubble-gradient 8s ease infinite',
        backgroundSize: '400% 400%'
      };
    };

    // 判断歌曲是否正在播放
    const isCurrentlyPlaying = (song: SongFile) => {
      return currentSong.value?.url === song.url && isPlaying.value;
    };

    // 判断歌曲是否在播放列表中
    const isInPlaylist = (song: SongFile) => {
      return playlist.value.some(s => s.url === song.url);
    };

    // 处理歌曲点击
    const handleSongClick = (song: SongFile) => {
      const playlistIndex = playlist.value.findIndex(s => s.url === song.url);
      if (playlistIndex >= 0) {
        playFromPlaylist(playlistIndex);
      } else {
        addToPlaylist(song);
      }
    };

    // 切换播放栏
    const togglePlayerBar = () => {
      playerBarClosed.value = !playerBarClosed.value;
    };

    // 组件挂载时加载数据
    onMounted(() => {
      loadSongs();

      // 添加全局音频元素
      const audioElement = document.createElement('audio');
      audioElement.id = 'global-audio';
      audioElement.style.display = 'none';
      document.body.appendChild(audioElement);
      audioRef.value = audioElement;

      // 添加事件监听器
      audioElement.addEventListener('timeupdate', handleAudioTimeUpdate);
      audioElement.addEventListener('ended', handleAudioEnded);
    });

    // 组件卸载时清理
    onUnmounted(() => {
      if (audioRef.value) {
        audioRef.value.pause();
        audioRef.value.remove();
        audioRef.value = null;
      }
    });

    return {
      songs,
      songsByArtist: computed(() => {
        const groups: Record<string, SongFile[]> = {};
        songs.value.forEach(song => {
          if (!groups[song.artist]) {
            groups[song.artist] = [];
          }
          groups[song.artist]?.push(song);
        });
        return groups;
      }),
      audioUrl,
      currentTime,
      duration,
      isPlaying,
      progress,
      lyrics,
      playlist,
      playlistOpen,
      togglePlaylist,
      playModes,
      playMode,
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
      bubbleStyle,
      currentSong,
      playSong,
      togglePlayPause,
      playPrevious,
      playNext,
      seekTo,
      setPlayMode
    };
  }
});
</script>

<style scoped>
/* 基础样式 */
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
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
  border-radius: 20px;
  overflow: hidden;
  position: relative;
}

h2 {
  text-align: center;
  margin-bottom: 25px;
  font-size: 2.2rem;
  text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
  color: #fff;
}

/* 空状态样式 */
.empty-state {
  text-align: center;
  padding: 40px 20px;
  color: #aaa;
}

.empty-state p {
  margin-bottom: 15px;
  font-size: 1.1rem;
}

.default-info {
  color: #ddd;
  font-size: 0.9rem;
}

/* 音乐列表样式 */
.music-list {
  margin-bottom: 30px;
  padding-bottom: 80px;
  /* 为底部控制栏留出空间 */
}

.artist-section {
  margin-bottom: 30px;
  padding: 15px;
  background: rgba(255, 255, 255, 0.08);
  border-radius: 15px;
  transition: all 0.3s ease;
}

.artist-section h3 {
  margin-bottom: 15px;
  padding-bottom: 8px;
  border-bottom: 2px solid rgba(255, 255, 255, 0.2);
  font-size: 1.5rem;
  color: #fff;
}

.songs-list {
  display: flex;
  flex-wrap: wrap;
  gap: 15px;
  list-style: none;
}

.song-item {
  flex: 1 0 calc(25% - 15px);
  min-width: 200px;
  margin: 0;
}

.button-bubble {
  padding: 12px 24px;
  border: none;
  border-radius: 50px;
  font-size: 1.25rem;
  color: #fff;
  font-weight: 700;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.12);
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
  background-size: 400% 400%;
  animation: bubble-gradient 8s ease infinite;
}

.button-bubble:hover {
  transform: scale(1.05);
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
  right: -5px;;
  background: #ffeb3b;
  color: #333;
  border-radius: 50%;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
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
    box-shadow: 0 0 10px rgba(255, 235, 59, 0.5);
  }

  100% {
    box-shadow: 0 0 30px rgba(255, 235, 59, 0.8);
  }
}

@keyframes bounce {

  0%,
  100% {
    transform: translateY(0);
  }

  50% {
    transform: translateY(-5px);
  }
}

@keyframes bubble-gradient {
  0% {
    background-position: 0% 50%;
  }

  50% {
    background-position: 100% 50%;
  }

  100% {
    background-position: 0% 50%;
  }
}

/* 播放控制栏 */
.player-bar {
  position: fixed;
  left:10%;
  bottom: 0;
  width: 80%;
  background: #2193b0;
  color: #fff;
  box-shadow: 0 -2px 12px rgba(0, 0, 0, 0.12);
  z-index: 999;
  transition: transform 0.3s ease;
}

.player-bar.closed {
  transform: translateY(calc(100% - 40px));
  /* 仅保留标题栏可见 */
}

.player-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 20px;
  background: rgba(0, 0, 0, 0.1);
  cursor: pointer;
}

.toggle-player-bar {
  background: rgba(255, 255, 255, 0.2);
  border: none;
  border-radius: 4px;
  color: #fff;
  font-size: 1.2rem;
  cursor: pointer;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s;
}

.toggle-player-bar:hover {
  background: rgba(255, 255, 255, 0.3);
}

.player-bar-content {
  padding: 15px 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
  background: #2193b0;
}

.player-controls {
  width: 100%;
  max-width: 800px;
}

.player-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
  font-size: 1.1rem;
}

.lyrics-tip {
  color: #ffeb3b;
  font-weight: 600;
  margin-left: 15px;
}

.player-buttons {
  display: flex;
  justify-content: center;
  gap: 20px;
  margin: 15px 0;
}

.player-btn {
  background: rgba(255, 255, 255, 0.2);
  border: none;
  border-radius: 50%;
  width: 50px;
  height: 50px;
  font-size: 1.5rem;
  color: #fff;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.player-btn:hover {
  background: rgba(255, 255, 255, 0.3);
  transform: scale(1.1);
}

.player-btn.play-btn {
  background: rgba(255, 255, 255, 0.3);
  font-size: 1.8rem;
}

.progress-container {
  display: flex;
  align-items: center;
  gap: 15px;
  width: 100%;
}

.time {
  font-size: 0.9rem;
  min-width: 40px;
}

.progress-bar {
  flex: 1;
  height: 8px;
  -webkit-appearance: none;
  appearance: none;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 4px;
  outline: none;
}

.progress-bar::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #fff;
  cursor: pointer;
}

/* 歌词显示区域 */
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
  color: #fff;
}

/* 播放列表样式 */
.playlist-popup {
  position: fixed;
  top: 20%;
  right: 0;
  width: 320px;
  background: #fff;
  box-shadow: -2px 0 16px rgba(0, 0, 0, 0.2);
  border-radius: 8px 0 0 8px;
  z-index: 1000;
  display: flex;
  flex-direction: column;
  background: #f5f7fa;
  color: #333;
  transition: transform 0.4s cubic-bezier(0.68, -0.55, 0.27, 1.55);
}

.playlist-popup.open {
  transform: translateY(-50%) translateX(0);
  border-left: 1px solid #e0e0e0;
}

.playlist-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #2173ee;
  color: white;
  border-radius: 8px 0 0 0;
}

.clear-btn {
  background: #6fc013;
  color: #f24444;
  border: none;
  border-radius: 4px;
  font-size: 0.9rem;
  font-weight: 700;
  padding: 4px 12px;
  cursor: pointer;
  transition: background 0.2s;
}

.clear-btn:hover {
  background: #c0392b;
}

.play-modes {
  display: flex;
  justify-content: center;
  gap: 12px;
  padding: 12px;
  background: #fff;
  border-bottom: 1px solid #eee;
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

.playlist-content {
  padding: 0 12px 12px;
  overflow-y: auto;
  height: 40vh;
}

.playlist-content ul {
  padding: 0;
  margin: 0;
  list-style: none;
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
  border-radius: 8px;
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
  transition: background 0.2s;
}

.remove-btn:hover {
  background: #e74c3c;
  color: #fff;
}

/* 播放列表空状态 */
.empty-playlist {
  text-align: center;
  padding: 20px;
  color: #666;
  font-style: italic;
}

/* 播放列表切换按钮 - 固定在右侧中部 */
.playlist-toggle {
  position: fixed;
  top: 50%;
  right: 0;
  transform: translate(40%, -40%);
  background: #a130d5;
  color: #36eb25;
  border: none;
  border-radius: 50% 0 0 50%;
  width: 40px;
  height: 40px;
  margin: 0;
  font-size: 1.2rem;
  cursor: pointer;
  z-index: 1001;
  transition: all 0.3s;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: -2px 0 8px rgba(0, 0, 0, 0.2);
}

.playlist-toggle.open {
  right: 320px;
  background: #2a54ec;
  border-radius: 50%;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .music-player {
    padding: 15px;
  }

  h2 {
    font-size: 1.8rem;
  }

  .song-item {
    flex: 1 0 calc(50% - 15px);
    min-width: 150px;
  }

  .button-bubble {
    padding: 10px 16px;
    font-size: 1rem;
  }

  .playlist-popup {
    width: 280px;
  }

  .playlist-toggle {
    width: 36px;
    height: 36px;
    font-size: 1rem;
  }

  .playlist-toggle.open {
    right: 280px;
  }

  .player-bar-arrow {
    right: 20px;
    bottom: 20px;
    width: 45px;
    height: 45px;
  }
}
</style>