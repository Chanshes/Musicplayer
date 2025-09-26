<template>
  <div class="music-player">
    <h2>本地音乐播放器</h2>

    <!-- 音乐列表 -->
    <div class="music-list">
      <div v-for="(artistSongs, artist) in songsByArtist" :key="artist" class="artist-section">
        <h3>{{ artist }}</h3>
        <ul class="songs-list">
          <li v-for="(song, idx) in artistSongs" :key="idx" class="song-item" @mouseenter="setHoveredSong(song)"
            @mouseleave="hoveredSong = null">
            <button class="button-bubble" :class="{
              'currently-playing': isCurrentlyPlaying(song),
              'in-playlist': isInPlaylist(song)
            }" @click="handleSongClick($event, song)">
              {{ song.displayName }}
              <span v-if="isCurrentlyPlaying(song)" class="playing-indicator">♪</span>
            </button>

            <!-- 添加到播放列表按钮 -->
            <button v-if="hoveredSong === song && !isInPlaylist(song)" class="add-to-playlist-btn"
              @click="addToPlaylistEnd(song, $event)">
              +
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
            <span class="time">{{ formatTime(currentTime) }}</span>
            <input type="range" min="0" :max="duration" v-model="currentTime" @input="handleSeek"
              class="progress-bar" />
            <span class="time">{{ formatTime(duration) }}</span>
          </div>
        </div>
      </div>
    </transition>
  </div>

  <!-- 播放列表 -->
  <div class="playlist-popup" :class="{ open: playlistOpen }"
    :style="{ transform: playlistOpen ? 'translateX(0)' : 'translateX(100%)' }" ref="playlistContainer">
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

  <!-- 播放列表切换按钮 -->
  <button class="playlist-toggle" @click="togglePlaylist" :class="{ open: playlistOpen }">
    {{ playlistOpen ? '◀' : '▶' }}
  </button>
</template>

<script lang="ts">
import { defineComponent, ref, onMounted, onUnmounted, nextTick, computed, PropType } from 'vue';

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
    const lyrics = ref<string | null>(null);
    const songs = ref<SongFile[]>([]);
    const audioRef = ref<HTMLAudioElement | null>(null);
    const audioUrl = ref<string | null>(null);
    const currentTime = ref(0);
    const duration = ref(0);
    const isPlaying = ref(false);
    const playlist = ref<SongFile[]>([]);
    const playlistOpen = ref(false);
    const currentPlaylistIdx = ref(-1);
    const hoverIdx = ref(-1);
    const playerBarClosed = ref(false);
    const currentSong = ref<SongFile | null>(null);
    const playModes = [
      { label: '单曲循环', value: 'single' as const },
      { label: '列表循环', value: 'list' as const },
      { label: '随机播放', value: 'random' as const }
    ];
    const playMode = ref<'single' | 'list' | 'random'>('list');
    const hoveredSong = ref<SongFile | null>(null);
    const playlistContainer = ref<Element | null>(null);
    const noteElement = ref<HTMLElement | null>(null);
    const targetElement = ref<HTMLElement | null>(null);

    // 加载歌曲
    const loadSongs = async () => {
      try {
        const response = await fetch('/music/songs.json');
        if (!response.ok) {
          throw new Error(`网络请求失败: ${response.status}`);
        }

        const data = await response.json();
        songs.value = data.map((song: any) => {
          const name = song.name;
          const lastDashIndex = name.lastIndexOf('-');
          let displayName, artist;

          if (lastDashIndex !== -1) {
            displayName = name.substring(0, lastDashIndex).trim();
            artist = name.substring(lastDashIndex + 1).trim();
          } else {
            displayName = name;
            artist = '未知艺术家';
          }

          return {
            name,
            url: `/music/${name}`,
            displayName,
            artist
          };
        });

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
      currentPlaylistIdx.value = playlist.value.findIndex(s => s.url === song.url);

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

      if (currentIndex > 0) {
        playSong(playlist.value[currentIndex - 1]);
      } else {
        playSong(playlist.value[playlist.value.length - 1]);
      }
    };

    // 播放下一首
    const playNext = () => {
      if (!currentSong.value || playlist.value.length === 0) return;

      const currentIndex = playlist.value.findIndex(
        song => song.url === currentSong.value?.url
      );

      if (currentIndex < playlist.value.length - 1) {
        playSong(playlist.value[currentIndex + 1]);
      } else {
        playSong(playlist.value[0]);
      }
    };

    // 添加到播放列表
    const addToPlaylist = (song: SongFile) => {
      if (!playlist.value.find(s => s.url === song.url)) {
        playlist.value.push(song);
      }
      playSong(song);
    };

    // 添加到播放列表末尾（不影响当前播放）
    const addToPlaylistEnd = (song: SongFile, event?: MouseEvent) => {
      // 创建音符动画
      if (event) {
        createNoteAnimation(event, song);
      }
    
      // 添加到播放列表
      if (!playlist.value.find(s => s.url === song.url)) {
        playlist.value.push(song);
      }
    };

    // 创建音符动画
    const createNoteAnimation = (event: MouseEvent, song: SongFile) => {
      // 确保event存在
      if (!event || !event.target) {
        console.warn('Event or event.target is undefined');
        return;
      }
    
      // 创建音符元素
      noteElement.value = document.createElement('div');
      noteElement.value.className = 'animated-note';
      noteElement.value.innerHTML = '♪';
      document.body.appendChild(noteElement.value);

      // 设置初始位置（随机在屏幕上半部分）
      const bubble = event.target as HTMLElement;
      const bubbleRect = bubble.getBoundingClientRect();
      noteElement.value.style.left = (bubbleRect.right - 20) + 'px';
      noteElement.value.style.top = (bubbleRect.top + window.scrollY + 10) + 'px';

      // 触发重绘
      noteElement.value.offsetHeight;

      // 设置目标位置（播放列表图标附近）
      targetElement.value = document.querySelector('.playlist-toggle');
      if (targetElement.value) {
        const targetRect = targetElement.value.getBoundingClientRect();
        noteElement.value.style.setProperty('--target-x', targetRect.left + 'px');
        noteElement.value.style.setProperty('--target-y', (targetRect.top + window.scrollY + targetRect.height/2) + 'px');
      }

      // 添加动画类
      noteElement.value.classList.add('animate');
    
      // 动画结束后移除元素
      setTimeout(() => {
        if (noteElement.value && noteElement.value.parentNode) {
          noteElement.value.parentNode.removeChild(noteElement.value);
          noteElement.value = null;
        }
      }, 1000);
    };

    // 从播放列表播放
    const playFromPlaylist = (idx: number) => {
      if (idx >= 0 && idx < playlist.value.length) {
        playSong(playlist.value[idx]);
      }
    };

    // 切换播放列表显示
    const togglePlaylist = () => {
      playlistOpen.value = !playlistOpen.value;
    };

    // 清空播放列表
    const clearPlaylist = () => {
      if (audioRef.value) {
        audioRef.value.pause();
        audioRef.value.currentTime = 0;
      }
      isPlaying.value = false;
      playlist.value = [];
      currentPlaylistIdx.value = -1;
    };

    // 从播放列表移除
    const removeFromPlaylist = (idx: number) => {
      if (idx < 0 || idx >= playlist.value.length) return;

      const newPlaylist = [...playlist.value];
      const removedSong = newPlaylist.splice(idx, 1)[0];
      playlist.value = newPlaylist;

      if (currentPlaylistIdx.value === idx) {
        if (playlist.value.length > 0) {
          if (idx >= playlist.value.length) {
            playSong(playlist.value[playlist.value.length - 1]);
          } else {
            playSong(playlist.value[idx]);
          }
        } else {
          if (audioRef.value) {
            audioRef.value.pause();
            audioRef.value.currentTime = 0;
          }
          isPlaying.value = false;
          currentSong.value = null;
          currentPlaylistIdx.value = -1;
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
    };

    const handleAudioEnded = () => {
      if (!currentSong.value || playlist.value.length === 0) return;

      if (playMode.value === 'single') {
        if (audioRef.value) {
          audioRef.value.currentTime = 0;
          audioRef.value.play();
        }
      } else if (playMode.value === 'list') {
        playNext();
      } else if (playMode.value === 'random') {
        const randomIndex = Math.floor(Math.random() * playlist.value.length);
        playSong(playlist.value[randomIndex]);
      }
    };

    // 跳转到指定时间
    const handleSeek = (event: Event) => {
      if (!audioRef.value) return;
      const target = event.target as HTMLInputElement;
      const newTime = parseFloat(target.value);

      if (newTime <= duration.value) {
        audioRef.value.currentTime = newTime;
        currentTime.value = newTime;
      } else {
        audioRef.value.currentTime = duration.value;
        currentTime.value = duration.value;
      }

      if (!isPlaying.value) {
        isPlaying.value = true;
        audioRef.value.play();
      }
    };

    // 时间格式化
    const formatTime = (seconds: number) => {
      if (isNaN(seconds) || seconds === 0) return '0:00';
      const mins = Math.floor(seconds / 60);
      const secs = Math.floor(seconds % 60);
      return `${mins}:${secs < 10 ? '0' : ''}${secs}`;
    };

    // 气泡样式
    const bubbleStyle = (idx: number) => {
      const hue = (idx * 25) % 360; // 调整色相变化
      return {
        'background': `linear-gradient(135deg, hsl(${hue}, 70%, 55%), hsl(${(hue + 30) % 360}, 70%, 45%))`,
        'box-shadow': '0 4px 15px rgba(0, 0, 0, 0.2)',
        'transition': 'all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275)',
        'width': '100%' // 确保宽度填满容器
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
    const handleSongClick = (event: MouseEvent, song: SongFile) => {
      const playlistIndex = playlist.value.findIndex(s => s.url === song.url);
      if (playlistIndex >= 0) {
        playFromPlaylist(playlistIndex);
      } else {
        addToPlaylist(song);
      }
    };

    // 设置悬停歌曲
    const setHoveredSong = (song: SongFile) => {
      hoveredSong.value = song;
    };

    // 滚动到当前播放的歌曲
    const scrollToCurrentSong = () => {
      if (!playlistOpen.value || !playlistContainer.value) return;

      nextTick(() => {
        const currentItem = document.querySelector(`.playlist-li:nth-child(${currentPlaylistIdx.value + 1})`);
        if (currentItem) {
          currentItem.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
        }
      });
    };

    // 切换播放栏
    const togglePlayerBar = () => {
      playerBarClosed.value = !playerBarClosed.value;
    };

    // 组件挂载时加载数据
    onMounted(() => {
      loadSongs().then(() => {
        // 不再自动收集气泡元素
      });

      const audioElement = document.createElement('audio');
      audioElement.id = 'global-audio';
      audioElement.style.display = 'none';
      document.body.appendChild(audioElement);
      audioRef.value = audioElement;

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

      if (noteElement.value && noteElement.value.parentNode) {
        noteElement.value.parentNode.removeChild(noteElement.value);
      }
    });

    // 计算属性
    const songsByArtist = computed(() => {
      const groups: Record<string, SongFile[]> = {};
      songs.value.forEach(song => {
        if (!groups[song.artist]) {
          groups[song.artist] = [];
        }
        groups[song.artist]?.push(song);
      });
      return groups;
    });

    return {
      lyrics,
      songs,
      songsByArtist,
      audioUrl,
      currentTime,
      duration,
      isPlaying,
      playlist,
      playlistOpen,
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
      handleSeek,
      playModes,
      playMode,
      hoveredSong,
      setHoveredSong,
      addToPlaylistEnd,
      formatTime,
      playlistContainer,
      scrollToCurrentSong,
      playFromPlaylist,
      togglePlaylist,
      setPlayMode
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
  background: linear-gradient(135deg, #f5f7fa 0%, #e4e7f0 100%);
  border-radius: 20px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.08);
  color: #333;
  position: relative;
  overflow: hidden;
}

.music-player::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: radial-gradient(circle at top right, rgba(106, 27, 154, 0.05), transparent 40%);
  pointer-events: none;
  z-index: -1;
}

h2 {
  text-align: center;
  margin-bottom: 25px;
  font-size: 2.2rem;
  color: #2c3e50;
  position: relative;
  padding-bottom: 10px;
}

h2::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 25%;
  right: 25%;
  height: 3px;
  background: linear-gradient(90deg, #7e57c2, #5e35b1);
  border-radius: 3px;
}

.empty-state {
  text-align: center;
  padding: 40px 20px;
  color: #7e57c2;
  background: rgba(126, 87, 194, 0.05);
  border-radius: 15px;
  margin: 20px 0;
  box-shadow: inset 0 0 10px rgba(0, 0, 0, 0.05);
}

.empty-state p {
  margin-bottom: 15px;
  font-size: 1.1rem;
}

.default-info {
  color: #9575cd;
  font-size: 0.9rem;
}

.music-list {
  margin-bottom: 30px;
  padding: 0 10px;
}

.artist-section {
  margin-bottom: 30px;
  padding: 15px;
  background: rgba(255, 255, 255, 0.8);
  border-radius: 15px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
}

.artist-section h3 {
  margin-bottom: 15px;
  padding-bottom: 8px;
  color: #5e35b1;
  border-bottom: 2px solid rgba(126, 87, 194, 0.2);
}

.songs-list {
  display: flex;
  flex-wrap: wrap;
  gap: 15px;
}

.song-item {
  flex: 1 0 calc(25% - 15px);
  min-width: 200px;
  position: relative;
  display: flex;
  align-items: center;
  width: 100%; /* 确保宽度填满容器 */
}

.button-bubble {
  padding: 12px 24px;
  border: none;
  border-radius: 50px;
  font-size: 1.25rem;
  font-weight: 700;
  cursor: pointer;
  color: white;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
  width: 100%; /* 确保宽度填满容器 */
  text-align: center;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.15);
  background: linear-gradient(135deg, #7e57c2 0%, #5e35b1 100%);
}

.button-bubble:hover {
  transform: scale(1.05);
  box-shadow: 0 6px 20px rgba(126, 87, 194, 0.3);
  background: linear-gradient(135deg, #9575cd 0%, #7e57c2 100%);
}

.button-bubble.currently-playing {
  position: relative;
  animation: pulse 2s infinite;
  box-shadow: 0 0 20px rgba(126, 87, 194, 0.4);
}

.button-bubble.currently-playing::after {
  content: '♪';
  position: absolute;
  top: -15px;
  right: 15px;
  background: linear-gradient(135deg, #ffeb3b, #ff9800);
  color: #333;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  font-weight: bold;
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
  animation: bounce 1.5s ease-in-out infinite;
}

@keyframes bounce {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-10px);
  }
}

@keyframes pulse {
  0% {
    box-shadow: 0 0 5px rgba(126, 87, 194, 0.6);
  }
  50% {
    box-shadow: 0 0 20px rgba(126, 87, 194, 0.8);
  }
  100% {
    box-shadow: 0 0 5px rgba(126, 87, 194, 0.6);
  }
}

.add-to-playlist-btn {
  position: absolute;
  right: 15px;
  top: 50%;
  transform: translateY(-50%);
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: linear-gradient(135deg, #4caf50, #2e7d32);
  color: white;
  border: none;
  font-size: 1.5rem;
  font-weight: bold;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 5;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
  right: 10px; /* 调整位置 */
}

.add-to-playlist-btn:hover {
  background: linear-gradient(135deg, #66bb6a, #388e3c);
  transform: translateY(-50%) scale(1.1);
}

.player-bar {
  position: fixed;
  left: 10%;
  bottom: 0;
  width: 80%;
  background: linear-gradient(135deg, #5e35b1, #4527a0);
  color: #fff;
  box-shadow: 0 -2px 12px rgba(0, 0, 0, 0.15);
  z-index: 999;
  transition: transform 0.3s ease;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 20px 20px 0 0;
}

.player-bar.closed {
  transform: translateY(calc(100% - 40px));
}

.player-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 20px;
  cursor: pointer;
}

.toggle-player-bar {
  background: rgba(255, 255, 255, 0.15);
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
  background: rgba(255, 255, 255, 0.25);
}

.player-bar-content {
  padding: 15px 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
  background: rgba(0, 0, 0, 0.1);
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
  width: 100%;
  color: #e0e0ff;
}

.player-buttons {
  display: flex;
  justify-content: center;
  gap: 20px;
  margin: 15px 0;
}

.player-btn {
  background: rgba(255, 255, 255, 0.15);
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
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}

.player-btn:hover {
  background: rgba(255, 255, 255, 0.25);
  transform: scale(1.1);
}

.player-btn.play-btn {
  background: rgba(255, 255, 255, 0.25);
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
  min-width: 50px;
  text-align: center;
  font-variant-numeric: tabular-nums;
  color: #e0e0ff;
}

.progress-bar {
  flex: 1;
  height: 8px;
  -webkit-appearance: none;
  appearance: none;
  background: rgba(255, 255, 255, 0.15);
  border-radius: 4px;
  outline: none;
  overflow: hidden;
}

.progress-bar::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #ffeb3b;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.3);
  border: 2px solid white;
}

.progress-bar::-webkit-slider-thumb:hover {
  transform: scale(1.2);
  background: #ffc107;
}

.lyrics-container {
  margin-top: 20px;
  padding: 15px;
  background: rgba(255, 255, 255, 0.8);
  border-radius: 15px;
  max-height: 300px;
  overflow-y: auto;
  box-shadow: inset 0 0 10px rgba(0, 0, 0, 0.05);
}

.lyrics-container h3 {
  margin-bottom: 10px;
  color: #5e35b1;
  text-align: center;
  font-size: 1.4rem;
  padding-bottom: 10px;
  border-bottom: 1px solid rgba(126, 87, 194, 0.2);
}

.lyrics-container pre {
  white-space: pre-wrap;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  line-height: 1.6;
  color: #333;
  text-align: center;
  font-size: 1.1rem;
}

.playlist-popup {
  position: fixed;
  top: 20%;
  right: 0;
  width: 320px;
  background: white;
  box-shadow: -2px 0 16px rgba(0, 0, 0, 0.2);
  border-radius: 8px 0 0 8px;
  z-index: 1000;
  display: flex;
  flex-direction: column;
  transform: translateX(100%);
  transition: transform 0.4s cubic-bezier(0.68, -0.55, 0.27, 1.155);
  border: 1px solid #e0e0e0;
}

.playlist-popup.open {
  transform: translateX(0);
  box-shadow: -2px 0 20px rgba(0, 0, 0, 0.3);
}

.playlist-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #f5f5f5;
  border-bottom: 1px solid #e0e0e0;
}

.clear-btn {
  background: linear-gradient(135deg, #ff5252, #d32f2f);
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 0.9rem;
  font-weight: 700;
  padding: 4px 12px;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
}

.clear-btn:hover {
  background: linear-gradient(135deg, #ff6b6b, #e53935);
}

.play-modes {
  display: flex;
  justify-content: center;
  gap: 12px;
  padding: 12px;
  background: #f9f9f9;
  border-bottom: 1px solid #e0e0e0;
}

.mode-btn {
  padding: 6px 18px;
  border-radius: 20px;
  border: none;
  background: #e0e0e0;
  color: #555;
  font-size: 1rem;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
}

.mode-btn.active {
  background: linear-gradient(135deg, #7e57c2, #5e35b1);
  color: white;
  box-shadow: 0 0 10px rgba(126, 87, 194, 0.3);
}

.playlist-content {
  padding: 0 12px 12px;
  overflow-y: auto;
  max-height: 50vh;
  min-height: 25vh;
  background: white;
  border-radius: 0 0 8px 8px;
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
  transition: background 0.3s ease;
}

.playlist-item {
  width: 100%;
  text-align: left;
  padding: 12px 50px 12px 16px;
  border: none;
  border-radius: 8px;
  background: #f9f9f9;
  color: #333;
  font-size: 1.1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.playlist-item:hover {
  background: #f0f0f0;
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.playlist-item.playing {
  background: linear-gradient(135deg, rgba(126, 87, 194, 0.1), rgba(94, 53, 177, 0.1));
  color: #5e35b1;
  font-weight: 700;
  box-shadow: 0 0 15px rgba(126, 87, 194, 0.2);
}

.playlist-item.playing::after {
  content: '▶';
  position: absolute;
  right: 16px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 14px;
  color: #5e35b1;
  background: rgba(255, 255, 255, 0.7);
  width: 30px;
  height: 30px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.remove-btn {
  position: absolute;
  right: 16px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 1.5rem;
  color: #d32f2f;
  background: transparent;
  border: none;
  cursor: pointer;
  padding: 0;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: all 0.2s;
  z-index: 3;
}

.remove-btn:hover {
  background: rgba(211, 47, 47, 0.1);
  transform: translateY(-50%) scale(1.1);
}

.empty-playlist {
  text-align: center;
  padding: 20px;
  color: #757575;
  font-style: italic;
  background: #f5f5f5;
  border-radius: 8px;
  margin-top: 10px;
}

.playlist-toggle {
  position: fixed;
  top: 50%;
  right: 0;
  transform: translateY(-50%);
  background: linear-gradient(135deg, #7e57c2, #5e35b1);
  color: white;
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
  background: linear-gradient(135deg, #9575cd, #7e57c2);
  border-radius: 50%;
  transform: translateY(-50%) rotate(180deg);
}

/* 音符动画样式 */
.animated-note {
  position: fixed;
  font-size: 24px;
  color: #ffeb3b;
  z-index: 1000;
  pointer-events: none;
  opacity: 1;
  transition: all 0.8s cubic-bezier(0.175, 0.885, 0.32, 1.275);
  background: rgba(0, 0, 0, 0.3);
  padding: 5px 10px;
  border-radius: 20px;
  font-weight: bold;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
  white-space: nowrap;
}

.animated-note.animate {
  animation: noteMove 1s forwards, fadeOut 0.5s forwards 0.8s;
}

@keyframes noteMove {
  0% {
    transform: translate(var(--start-x, 0), var(--start-y, 0)) scale(1);
    opacity: 1;
  }
  100% {
    transform: translate(var(--target-x, 0), var(--target-y, 0)) scale(0.8);
    opacity: 0.3;
  }
}

@keyframes fadeOut {
  0% {
    opacity: 1;
  }
  100% {
    opacity: 0;
  }
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

  .playlist-popup {
    width: 280px;
  }

  .player-btn {
    width: 40px;
    height: 40px;
    font-size: 1.2rem;
  }

  .player-btn.play-btn {
    width: 45px;
    height: 45px;
  }

  .playlist-toggle {
    width: 36px;
    height: 36px;
    font-size: 1rem;
  }

  .playlist-toggle.open {
    right: 280px;
  }

  .player-bar {
    left: 5%;
    bottom: 0;
    width: 90%;
  }
}

@media (max-width: 480px) {
  .music-player {
    padding: 10px;
  }

  h2 {
    font-size: 1.5rem;
  }

  .song-item {
    flex: 1 0 calc(100% - 15px);
  }

  .playlist-popup {
    width: 90%;
    right: 5%;
    transform: translateX(105%);
  }

  .playlist-popup.open {
    transform: translateX(5%);
  }

  .playlist-toggle {
    display: none;
  }
}
</style>