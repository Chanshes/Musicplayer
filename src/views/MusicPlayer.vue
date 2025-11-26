<!-- 模板部分 -->
<template>
  <div class="music-player">
    <h2>Music Club</h2>

    <!-- 分类模式切换 -->
    <div class="category-controls">
      <button 
        class="category-btn" 
        :class="{ active: categoryMode === 'artist' }"
        @click="toggleCategoryMode"
      >
        按歌手分类
      </button>
      <button 
        class="category-btn" 
        :class="{ active: categoryMode === 'firstLetter' }"
        @click="toggleCategoryMode"
      >
        按首字母分类
      </button>
      <button 
        class="sort-btn" 
        :class="{ active: sortOrder === 'desc' }"
        @click="toggleSortOrder"
        title="点击切换排序方向"
      >
        {{ sortOrder === 'asc' ? 'A→Z' : 'Z→A' }}
      </button>
    </div>

    <!-- 音乐列表 -->
    <div class="music-list">
      <!-- 按歌手分类显示 -->
      <div v-if="categoryMode === 'artist'">
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
      
      <!-- 按首字母分类显示 -->
      <div v-else-if="categoryMode === 'firstLetter'">
        <div v-for="(letterSongs, letter) in songsByFirstLetter" :key="letter" class="artist-section">
          <h3>{{ letter }}</h3>
          <ul class="songs-list">
            <li v-for="(song, idx) in letterSongs" :key="idx" class="song-item" @mouseenter="setHoveredSong(song)"
              @mouseleave="hoveredSong = null">
              <button class="button-bubble" :class="{
                'currently-playing': isCurrentlyPlaying(song),
                'in-playlist': isInPlaylist(song)
              }" @click="handleSongClick($event, song)">
                {{ song.displayName }} - {{ song.artist }}
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
    </div>

    <!-- 空状态提示 -->
    <div v-if="Object.keys(songsByArtist).length === 0" class="empty-state">
      <p>暂无音乐文件</p>
      <p class="default-info">请添加音乐文件到 public/music 目录</p>
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
            <!-- QQ音乐风格歌词按钮 -->
            <button class="lyrics-toggle-btn" :class="{ 'has-lyrics': showLyricsPanel && currentSong?.lrcLines && currentSong.lrcLines.length > 0 }" 
                    @click="toggleLyricsDisplay" 
                    :title="showLyricsPanel ? '隐藏歌词' : '显示歌词'">
              词
              <span v-if="showLyricsPanel && currentSong?.lrcLines && currentSong.lrcLines.length > 0" class="lyrics-checkmark">✓</span>
            </button>
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

  <!-- 歌词面板（可拖动与设置） -->
  <div
    class="lyrics-panel"
    :class="{ open: showLyricsPanel }"
    :style="{
      transform: showLyricsPanel ? 'translateX(0)' : 'translateX(' + hiddenTranslateX + ')',
      top: panelPosition.top + 'px',
      left: panelPosition.left + 'px',
      width: lyricsSettings.width + 'px'
    }"
    ref="lyricsPanelRef"
  >
    <div class="lyrics-panel-header" @mousedown="startDrag" :style="{ background: `rgba(245,245,245,${lyricsSettings.opacity})` }">
      <span>歌词 - {{ currentSong?.displayName || '' }}</span>
      <div class="lyrics-header-actions">
        <button class="settings-btn" @click.stop="toggleLyricsSettings" title="设置">⚙</button>
        <button class="close-lyrics-btn" @click="toggleLyricsDisplay">×</button>
      </div>
    </div>

    <div v-if="showLyricsSettings" class="lyrics-settings">
      <div class="setting-item">
        <label>长度</label>
        <input type="range" min="240" max="640" v-model.number="lyricsSettings.width" @input="persistLyricsSettings" />
      </div>
      <div class="setting-item">
        <label>颜色</label>
        <input type="color" v-model="lyricsSettings.textColor" @input="persistLyricsSettings" />
      </div>
      <div class="setting-item">
        <label>透明度</label>
        <input type="range" min="0.3" max="1" step="0.05" v-model.number="lyricsSettings.opacity" @input="persistLyricsSettings" />
      </div>
    </div>

    <div class="lyrics-panel-content">
      <div v-if="!currentSong?.lrcLines || currentSong.lrcLines.length === 0" class="no-lyrics">
        暂无歌词
      </div>
      <div v-else class="lyrics-lines" :style="{ background: `rgba(255,255,255,${lyricsSettings.opacity})` }">
        <div
          v-for="(line, index) in getCurrentLyrics()"
          :key="index"
          :class="['lyrics-line', { current: line.isCurrent }]"
          :style="{ color: lyricsSettings.textColor }"
        >
          {{ line.text }}
        </div>
      </div>
    </div>
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

interface LrcLine {
  time: number; // 秒
  text: string;
}

interface SongFile {
  name: string;
  url: string;
  displayName: string;
  artist: string;
  lrcLines?: LrcLine[]; // 解析后的歌词行
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
    
    // 歌词相关状态
    const currentLrcIndex = ref(-1);
    const showLyricsPanel = ref(false);
    const lyricsPanelRef = ref<HTMLElement | null>(null);
    const dragging = ref(false);
    const dragOffset = ref({ x: 0, y: 0 });
    const panelPosition = ref({ top: Math.round(window.innerHeight * 0.2), left: 0 });
    const showLyricsSettings = ref(false);
    const lyricsSettings = ref({ width: 320, textColor: '#5e35b1', opacity: 1 });
    
    // 分类模式状态
    const categoryMode = ref<'artist' | 'firstLetter'>('artist');
    
    // 排序方向状态 (asc: 升序, desc: 降序)
    const sortOrder = ref<'asc' | 'desc'>('asc');

    // 文件名解析函数
    const parseFileName = (fileName: string) => {
      // 移除文件扩展名
      const nameWithoutExt = fileName.replace(/\.(mp3|wav|flac|aac)$/i, '');
      
      // 使用破折号分割（格式：歌曲名-艺术家）
      const parts = nameWithoutExt.split('-');
      
      if (parts.length >= 2) {
        // 最后一个部分是艺术家，前面的是歌曲名
        const artist = parts.pop()?.trim() || '未知艺术家';
        const displayName = parts.join('-').trim();
        
        return {
          displayName: displayName || nameWithoutExt,
          artist: artist || '未知艺术家'
        };
      }
      
      // 如果没有破折号，整个文件名作为歌曲名
      return {
        displayName: nameWithoutExt,
        artist: '未知艺术家'
      };
    };

    // 加载歌曲
    const loadSongs = async () => {
      try {
        const response = await fetch('/songs.json');
        if (!response.ok) {
          throw new Error(`网络请求失败: ${response.status}`);
        }

        const data = await response.json();
        songs.value = data.map((song: any) => {
          const { displayName, artist } = parseFileName(song.name);
          
          return {
            name: song.name,
            url: `/music/${song.name}`,
            displayName,
            artist
          };
        });

        console.log('成功加载歌曲数据:', songs.value);
      } catch (error) {
        console.error('加载歌曲数据失败:', error);
      }
    };

    // 歌词解析函数
    const parseLrcText = (lrcText: string): LrcLine[] => {
      if (!lrcText) return [];
      
      const lines = lrcText.split('\n');
      const lrcLines: LrcLine[] = [];
      
      lines.forEach(line => {
        // 匹配时间标签 [mm:ss.xx] 或 [mm:ss]
        const timeMatch = line.match(/\[(\d+):(\d+)\.?(\d*)\]/);
        if (timeMatch) {
          const minutes = parseInt(timeMatch[1]);
          const seconds = parseInt(timeMatch[2]);
          const milliseconds = timeMatch[3] ? parseInt(timeMatch[3].padEnd(3, '0')) : 0;
          const time = minutes * 60 + seconds + milliseconds / 1000;
          
          // 提取歌词文本（去除时间标签）
          const text = line.replace(/\[\d+:\d+\.?\d*\]/g, '').trim();
          
          if (text) {
            lrcLines.push({ time, text });
          }
        }
      });
      
      // 按时间排序
      lrcLines.sort((a, b) => a.time - b.time);
      return lrcLines;
    };

    // 播放控制
    const playSong = (song: SongFile) => {
      if (!audioRef.value) return;

      audioUrl.value = song.url;
      currentSong.value = song;
      isPlaying.value = true;
      currentPlaylistIdx.value = playlist.value.findIndex(s => s.url === song.url);

      // 重置歌词状态
      currentLrcIndex.value = -1;
      
      // 尝试加载并解析歌词
      const lrcName = song.name.replace(/\.[^.]+$/, '.lrc');
      fetch(`/lrc/${lrcName}`)
        .then(response => {
          if (response.ok) return response.text();
          throw new Error('歌词文件不存在');
        })
        .then(text => {
          // 解析歌词
          song.lrcLines = parseLrcText(text);
        })
        .catch(() => {
          song.lrcLines = [];
        });

      audioRef.value.src = song.url;
      audioRef.value.play().catch(e => console.error('播放失败:', e));
    };

    // 歌词时间轴更新方法
    const updateLyricsDisplay = () => {
      if (!currentSong.value || !currentSong.value.lrcLines || !audioRef.value) {
        currentLrcIndex.value = -1;
        return;
      }
      
      const currentTime = audioRef.value.currentTime;
      const lrcLines = currentSong.value.lrcLines;
      
      // 提前50毫秒显示下一句
      const adjustedTime = currentTime + 0.1;
      
      // 找到当前应该显示的歌词行
      let newIndex = -1;
      for (let i = lrcLines.length - 1; i >= 0; i--) {
        if (adjustedTime >= lrcLines[i].time) {
          newIndex = i;
          break;
        }
      }
      
      if (newIndex !== currentLrcIndex.value) {
        currentLrcIndex.value = newIndex;
      }
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
      
      // 更新歌词显示
      updateLyricsDisplay();
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

    // 获取当前显示的歌词
    const getCurrentLyrics = () => {
      if (!currentSong.value || !currentSong.value.lrcLines || currentLrcIndex.value === -1) {
        return [];
      }
      
      const lrcLines = currentSong.value.lrcLines;
      const startIndex = Math.max(0, currentLrcIndex.value - 2);
      const endIndex = Math.min(lrcLines.length - 1, currentLrcIndex.value + 2);
      
      return lrcLines.slice(startIndex, endIndex + 1).map((line, index) => ({
        ...line,
        isCurrent: startIndex + index === currentLrcIndex.value
      }));
    };

    // 歌词显示/隐藏切换
    const toggleLyricsDisplay = () => {
      showLyricsPanel.value = !showLyricsPanel.value;
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

    const startDrag = (e: MouseEvent) => {
      if (!lyricsPanelRef.value) return;
      dragging.value = true;
      const rect = lyricsPanelRef.value.getBoundingClientRect();
      dragOffset.value = { x: e.clientX - rect.left, y: e.clientY - rect.top };
      e.preventDefault();
    };

    const onDrag = (e: MouseEvent) => {
      if (!dragging.value) return;
      const newLeft = Math.min(Math.max(e.clientX - dragOffset.value.x, 0), window.innerWidth - lyricsSettings.value.width);
      const newTop = Math.min(Math.max(e.clientY - dragOffset.value.y, 0), window.innerHeight - 120);
      panelPosition.value = { top: Math.round(newTop), left: Math.round(newLeft) };
    };

    const endDrag = () => {
      if (!dragging.value) return;
      dragging.value = false;
      localStorage.setItem('lyricsPanelPos', JSON.stringify(panelPosition.value));
    };

    const toggleLyricsSettings = () => {
      showLyricsSettings.value = !showLyricsSettings.value;
    };

    const persistLyricsSettings = () => {
      localStorage.setItem('lyricsSettings', JSON.stringify(lyricsSettings.value));
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
      try {
        const saved = localStorage.getItem('lyricsSettings');
        if (saved) {
          const parsed = JSON.parse(saved);
          lyricsSettings.value = {
            width: Math.min(Math.max(parsed.width ?? 320, 240), 640),
            textColor: parsed.textColor ?? '#5e35b1',
            opacity: typeof parsed.opacity === 'number' ? Math.min(Math.max(parsed.opacity, 0.3), 1) : 1
          };
        }
        const savedPos = localStorage.getItem('lyricsPanelPos');
        if (savedPos) {
          const pos = JSON.parse(savedPos);
          panelPosition.value = {
            top: Math.min(Math.max(pos.top ?? panelPosition.value.top, 0), window.innerHeight - 120),
            left: Math.min(Math.max(pos.left ?? panelPosition.value.left, 0), window.innerWidth - lyricsSettings.value.width)
          };
        }
      } catch {}

      window.addEventListener('mousemove', onDrag);
      window.addEventListener('mouseup', endDrag);
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
      window.removeEventListener('mousemove', onDrag);
      window.removeEventListener('mouseup', endDrag);
    });

    // 获取歌曲名称的首字母
    const getFirstLetter = (text: string): string => {
      if (!text || text.length === 0) {
        return '#'; // 其他
      }
      
      const firstChar = text.charAt(0);
      
      // 检查是否为中文
      if (/[\u4e00-\u9fa5]/.test(firstChar)) {
        // 使用Unicode范围判断中文拼音首字母
        const code = firstChar.charCodeAt(0);
        
        // 简单的拼音首字母判断逻辑
        if (code >= 0x4e00 && code < 0x54c0) return 'A';
        if (code >= 0x54c0 && code < 0x5c30) return 'B';
        if (code >= 0x5c30 && code < 0x6558) return 'C';
        if (code >= 0x6558 && code < 0x7000) return 'D';
        if (code >= 0x7000 && code < 0x7730) return 'E';
        if (code >= 0x7730 && code < 0x7a60) return 'F';
        if (code >= 0x7a60 && code < 0x8400) return 'G';
        if (code >= 0x8400 && code < 0x8c00) return 'H';
        if (code >= 0x8c00 && code < 0x9600) return 'J';
        if (code >= 0x9600 && code < 0x9ea0) return 'K';
        if (code >= 0x9ea0 && code < 0xa8c0) return 'L';
        if (code >= 0xa8c0 && code < 0xb580) return 'M';
        if (code >= 0xb580 && code < 0xbdc0) return 'N';
        if (code >= 0xbdc0 && code < 0xc0b0) return 'O';
        if (code >= 0xc0b0 && code < 0xc9c0) return 'P';
        if (code >= 0xc9c0 && code < 0xd4c0) return 'Q';
        if (code >= 0xd4c0 && code < 0xd8c0) return 'R';
        if (code >= 0xd8c0 && code < 0xe4c0) return 'S';
        if (code >= 0xe4c0 && code < 0xe8c0) return 'T';
        if (code >= 0xe8c0 && code < 0xf0c0) return 'W';
        if (code >= 0xf0c0 && code < 0xf900) return 'X';
        if (code >= 0xf900 && code <= 0x9fa5) return 'Y';
        if (code >= 0x3400 && code <= 0x4db5) return 'Z'; // 扩展汉字
        
        return '#'; // 其他汉字
      }
      
      // 检查是否为英文
      if (/[a-zA-Z]/.test(firstChar)) {
        return firstChar.toUpperCase();
      }
      
      // 其他字符归为'其'
      return '#';
    };

    // 计算属性：按歌手分类
    const songsByArtist = computed(() => {
      const groups: Record<string, SongFile[]> = {};
      songs.value.forEach(song => {
        if (!groups[song.artist]) {
          groups[song.artist] = [];
        }
        groups[song.artist]?.push(song);
      });
      
      // 根据排序方向对分组进行排序
      const sortedGroups: Record<string, SongFile[]> = {};
      const sortedKeys = Object.keys(groups).sort((a, b) => {
        if (sortOrder.value === 'asc') {
          return a.localeCompare(b);
        } else {
          return b.localeCompare(a);
        }
      });
      
      sortedKeys.forEach(key => {
        sortedGroups[key] = groups[key];
      });
      
      return sortedGroups;
    });

    // 计算属性：按首字母分类
    const songsByFirstLetter = computed(() => {
      const groups: Record<string, SongFile[]> = {};
      songs.value.forEach(song => {
        const firstLetter = getFirstLetter(song.displayName);
        if (!groups[firstLetter]) {
          groups[firstLetter] = [];
        }
        groups[firstLetter]?.push(song);
      });
      
      // 根据排序方向对分组进行排序
      const sortedGroups: Record<string, SongFile[]> = {};
      const sortedKeys = Object.keys(groups).sort((a, b) => {
        // 特殊处理 '#' 分组，将其放在最后
        if (a === '#') return 1;
        if (b === '#') return -1;
        
        if (sortOrder.value === 'asc') {
          return a.localeCompare(b);
        } else {
          return b.localeCompare(a);
        }
      });
      
      sortedKeys.forEach(key => {
        sortedGroups[key] = groups[key];
      });
      
      return sortedGroups;
    });

    // 切换分类模式
    const toggleCategoryMode = () => {
      categoryMode.value = categoryMode.value === 'artist' ? 'firstLetter' : 'artist';
    };
    
    // 切换排序方向
    const toggleSortOrder = () => {
      sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc';
    };
    const hiddenTranslateX = computed(() => {
      return `-${panelPosition.value.left + lyricsSettings.value.width + 40}px`;
    });

    return {
      songs,
      songsByArtist,
      songsByFirstLetter,
      categoryMode,
      sortOrder,
      toggleSortOrder,
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
      setPlayMode,
      showLyricsPanel,
      toggleLyricsDisplay,
      getCurrentLyrics,
      toggleCategoryMode,
      lyricsPanelRef,
      panelPosition,
      startDrag,
      onDrag,
      endDrag,
      showLyricsSettings,
      toggleLyricsSettings,
      lyricsSettings,
      persistLyricsSettings,
      hiddenTranslateX
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
  overflow: visible;
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

/* 分类控制按钮样式 */
.category-controls {
  display: flex;
  justify-content: center;
  gap: 15px;
  margin-bottom: 30px;
}

.category-btn, .sort-btn {
  padding: 12px 24px;
  border: none;
  border-radius: 25px;
  background-color: rgba(255, 255, 255, 0.8);
  color: #5e35b1;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
}

.category-btn:hover, .sort-btn:hover {
  background-color: rgba(255, 255, 255, 1);
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.08);
}

.category-btn.active {
  background-color: #7e57c2;
  color: white;
  box-shadow: 0 4px 15px rgba(126, 87, 194, 0.3);
}

.sort-btn {
  background-color: rgba(33, 150, 243, 0.8);
  color: white;
}

.sort-btn:hover {
  background-color: #2196F3;
}

.sort-btn.active {
    background-color: #FF9800;
    box-shadow: 0 4px 15px rgba(255, 152, 0, 0.3);
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
  margin-bottom: 28px;
  padding: 16px;
  background: linear-gradient(135deg, rgba(255,255,255,0.65), rgba(255,255,255,0.5));
  border-radius: 18px;
  box-shadow: 0 12px 26px rgba(94, 53, 177, 0.12);
  transition: all 0.25s ease;
  border: 1px solid rgba(126, 87, 194, 0.15);
  backdrop-filter: blur(10px);
}

.artist-section h3 {
  margin-bottom: 12px;
  padding-bottom: 6px;
  color: #5e35b1;
  border-bottom: 2px solid rgba(126, 87, 194, 0.22);
}

.songs-list {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.song-item {
  flex: 1 0 calc(25% - 15px);
  min-width: 200px;
  position: relative;
  display: flex;
  align-items: center;
  width: 100%;
}

.button-bubble {
  padding: 12px 18px;
  border: 1px solid rgba(126, 87, 194, 0.25);
  border-radius: 14px;
  font-size: 1.05rem;
  font-weight: 700;
  cursor: pointer;
  color: #fff;
  transition: all 0.2s ease;
  position: relative;
  overflow: visible;
  width: 100%;
  text-align: center;
  box-shadow: 0 10px 20px rgba(94, 53, 177, 0.18);
  background: linear-gradient(135deg, rgba(126, 87, 194, 0.9), rgba(94, 53, 177, 0.9));
}

.button-bubble:hover {
  transform: translateY(-1px);
  box-shadow: 0 16px 28px rgba(94, 53, 177, 0.28);
  background: linear-gradient(135deg, rgba(149, 117, 205, 0.95), rgba(126, 87, 194, 0.95));
}

.button-bubble.currently-playing {
  position: relative;
  animation: pulse 2s infinite;
  box-shadow: 0 0 20px rgba(126, 87, 194, 0.45);
  z-index: 2;
}

.button-bubble.currently-playing::after {
  content: '♪';
  position: absolute;
  top: -12px;
  right: 12px;
  background: linear-gradient(135deg, #ffeb3b, #ffc107);
  color: #333;
  border-radius: 10px;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  font-weight: bold;
  box-shadow: 0 8px 16px rgba(94, 53, 177, 0.25);
  animation: bounce 1.5s ease-in-out infinite;
  z-index: 3;
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
  right: 10px;
  top: 50%;
  transform: translateY(-50%);
  width: 34px;
  height: 34px;
  border-radius: 12px;
  background: linear-gradient(135deg, rgba(76,175,80,0.85), rgba(46,125,50,0.85));
  color: white;
  border: 1px solid rgba(255,255,255,0.25);
  font-size: 1.2rem;
  font-weight: 700;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 5;
  transition: all 0.2s ease;
  box-shadow: 0 6px 12px rgba(46, 125, 50, 0.35);
}

.add-to-playlist-btn:hover {
  background: linear-gradient(135deg, rgba(102,187,106,0.95), rgba(56,142,60,0.95));
  transform: translateY(-50%) translateY(-1px) scale(1.05);
}

.player-bar {
  position: fixed;
  left: 10%;
  bottom: 16px;
  width: 80%;
  background: linear-gradient(135deg, rgba(126, 87, 194, 0.24), rgba(94, 53, 177, 0.18));
  color: #fff;
  box-shadow: 0 20px 40px rgba(94, 53, 177, 0.25);
  z-index: 999;
  transition: transform 0.3s ease, box-shadow 0.3s ease, background 0.3s ease;
  border: 1px solid rgba(255, 255, 255, 0.18);
  border-radius: 16px;
  backdrop-filter: blur(12px) saturate(120%);
}

.player-bar.closed {
  transform: translateY(calc(100% - 40px));
}

.player-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 18px;
  z-index: 1000;
}

.toggle-player-bar {
  background: rgba(255, 255, 255, 0.18);
  border: 1px solid rgba(255, 255, 255, 0.25);
  border-radius: 10px;
  color: #fff;
  font-size: 1rem;
  cursor: pointer;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  z-index: 1001;
}

.toggle-player-bar:hover {
  background: rgba(255, 255, 255, 0.28);
  transform: translateY(-1px);
}

.player-bar-content {
  padding: 12px 18px 16px 18px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  z-index: 999;
}

.player-controls {
  width: 100%;
  max-width: 800px;
  z-index: 1000;
}

.player-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
  font-size: 1.1rem;
  width: 100%;
  color: #e0e0ff;
  z-index: 999;
  flex-wrap: wrap;
  gap: 10px;
}

.player-buttons {
  display: flex;
  justify-content: center;
  gap: 12px;
  margin: 6px 0 12px 0;
  z-index: 1000;
}

.player-btn {
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.16), rgba(255, 255, 255, 0.12));
  border: 1px solid rgba(255, 255, 255, 0.25);
  border-radius: 14px;
  width: 44px;
  height: 44px;
  font-size: 1.2rem;
  color: #fff;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  box-shadow: 0 8px 18px rgba(94, 53, 177, 0.25);
  z-index: 1001;
}

.player-btn:hover {
  background: rgba(255, 255, 255, 0.28);
  transform: translateY(-1px) scale(1.05);
}

.player-btn.play-btn {
  background: linear-gradient(135deg, rgba(126, 87, 194, 0.35), rgba(94, 53, 177, 0.35));
  border: 1px solid rgba(255, 255, 255, 0.35);
  font-size: 1.4rem;
  z-index: 1001;
}

.progress-container {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  z-index: 999;
}

.time {
  font-size: 0.85rem;
  min-width: 44px;
  text-align: center;
  font-variant-numeric: tabular-nums;
  color: #e0e0ff;
  z-index: 1000;
}

.progress-bar {
  flex: 1;
  height: 10px;
  -webkit-appearance: none;
  appearance: none;
  background: linear-gradient(90deg, rgba(126, 87, 194, 0.25), rgba(94, 53, 177, 0.25));
  border-radius: 8px;
  outline: none;
  overflow: hidden;
  z-index: 999;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.progress-bar::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 16px;
  height: 16px;
  border-radius: 8px;
  background: linear-gradient(135deg, #ffeb3b, #ffc107);
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 6px 12px rgba(94, 53, 177, 0.35);
  border: 2px solid rgba(255, 255, 255, 0.85);
  z-index: 1000;
}

.progress-bar::-webkit-slider-thumb:hover {
  transform: scale(1.08);
}

.player-bar-slide-enter-active,
.player-bar-slide-leave-active {
  transition: opacity 0.25s ease, transform 0.25s ease;
}
.player-bar-slide-enter-from,
.player-bar-slide-leave-to {
  opacity: 0;
  transform: translateY(8px);
}

/* QQ音乐风格歌词按钮样式 */
.lyrics-toggle-btn {
  position: relative;
  background: rgba(255, 255, 255, 0.15);
  border: none;
  border-radius: 50%;
  width: 36px;
  height: 36px;
  color: #e0e0ff;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-left: 10px;
}

.lyrics-toggle-btn:hover {
  background: rgba(255, 255, 255, 0.25);
  transform: scale(1.1);
}

.lyrics-toggle-btn.has-lyrics {
  background: rgba(76, 175, 80, 0.2);
  border: 1px solid rgba(76, 175, 80, 0.5);
}

.lyrics-toggle-btn.has-lyrics:hover {
  background: rgba(76, 175, 80, 0.3);
}

.lyrics-checkmark {
  position: absolute;
  top: -2px;
  right: -2px;
  background: #4caf50;
  color: white;
  border-radius: 50%;
  width: 14px;
  height: 14px;
  font-size: 10px;
  font-weight: bold;
  display: flex;
  align-items: center;
  justify-content: center;
  line-height: 1;
  animation: checkmarkPop 0.3s ease-out;
}

@keyframes checkmarkPop {
  0% {
    transform: scale(0);
    opacity: 0;
  }
  70% {
    transform: scale(1.2);
  }
  100% {
    transform: scale(1);
    opacity: 1;
  }
}

/* 歌词面板样式（左侧，与播放列表对称） */
.lyrics-panel {
  position: fixed;
  top: 20%;
  left: 0;
  width: 320px;
  background: transparent;
  z-index: 1000;
  display: flex;
  flex-direction: column;
  transform: translateX(-100%);
  transition: transform 0.4s cubic-bezier(0.68, -0.55, 0.27, 1.155);
}

.lyrics-panel.open {
  transform: translateX(0);
  z-index: 1001;
}

.lyrics-panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: rgba(245, 245, 245, 0.9);
  border-bottom: 1px solid rgba(224, 224, 224, 0.8);
  border-radius: 8px 0 0 0;
  backdrop-filter: blur(10px);
  z-index: 10;
}

.lyrics-header-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.settings-btn {
  background: rgba(255, 255, 255, 0.3);
  border: none;
  border-radius: 50%;
  width: 24px;
  height: 24px;
  color: #666;
  font-size: 14px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.settings-btn:hover {
  background: rgba(255, 255, 255, 0.5);
  color: #333;
}

.lyrics-panel-header span {
  font-weight: 600;
  color: #333;
}

.close-lyrics-btn {
  background: rgba(255, 255, 255, 0.3);
  border: none;
  border-radius: 50%;
  width: 24px;
  height: 24px;
  color: #666;
  font-size: 1.2rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.close-lyrics-btn:hover {
  background: rgba(255, 255, 255, 0.5);
  color: #333;
}

.lyrics-panel-content {
  padding: 12px;
  overflow-y: auto;
  max-height: 50vh;
  min-height: 25vh;
  background: transparent;
  border-radius: 0 0 0 8px;
  z-index: 9;
}

.lyrics-settings {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 10px 12px;
  background: rgba(255, 255, 255, 0.85);
  border: 1px solid #e0e0e0;
  border-radius: 0 0 0 8px;
  width: 100%;
  box-sizing: border-box;
}

.setting-item {
  display: grid;
  grid-template-columns: 48px 1fr;
  align-items: center;
  width: 100%;
  box-sizing: border-box;
}

.setting-item input[type="range"] {
  width: 100%;
}

.setting-item input[type="color"] {
  width: 48px;
  height: 24px;
  padding: 0;
}

.no-lyrics {
  text-align: center;
  padding: 40px 20px;
  color: #999;
  font-style: italic;
  background: rgba(255, 255, 255, 0.7);
  border-radius: 8px;
  backdrop-filter: blur(5px);
}

.lyrics-lines {
  background: rgba(255, 255, 255, 0.7);
  border-radius: 8px;
  padding: 15px;
  backdrop-filter: blur(5px);
}

.lyrics-line {
  font-size: 1.1rem;
  line-height: 1.6;
  margin: 10px 0;
  color: rgba(0, 0, 0, 0.6);
  transition: all 0.3s ease;
  text-align: center;
}

.lyrics-line.current {
  color: #5e35b1;
  font-size: 1.3rem;
  font-weight: 600;
  transform: scale(1.05);
  text-shadow: 0 2px 4px rgba(94, 53, 177, 0.3);
}

.playlist-popup {
  position: fixed;
  top: 20%;
  right: 0;
  width: 320px;
  background: linear-gradient(135deg, rgba(255,255,255,0.75), rgba(255,255,255,0.6));
  box-shadow: -2px 10px 24px rgba(94, 53, 177, 0.18);
  border-radius: 12px 0 0 12px;
  z-index: 1000;
  display: flex;
  flex-direction: column;
  transform: translateX(100%);
  transition: transform 0.4s cubic-bezier(0.68, -0.55, 0.27, 1.155);
  border: 1px solid rgba(126,87,194,0.2);
  backdrop-filter: blur(10px);
}

.playlist-popup.open {
  transform: translateX(0);
  box-shadow: -2px 0 24px rgba(94, 53, 177, 0.28);
  z-index: 1001;
}

.playlist-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: rgba(245,245,245,0.9);
  border-bottom: 1px solid rgba(126,87,194,0.15);
  z-index: 10;
}

.clear-btn {
  background: linear-gradient(135deg, rgba(255,82,82,0.9), rgba(211,47,47,0.9));
  color: white;
  border: 1px solid rgba(255,255,255,0.3);
  border-radius: 8px;
  font-size: 0.9rem;
  font-weight: 700;
  padding: 4px 12px;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 8px 14px rgba(211, 47, 47, 0.25);
  z-index: 11;
}

.clear-btn:hover {
  background: linear-gradient(135deg, rgba(255,107,107,0.95), rgba(229,57,53,0.95));
  z-index: 12;
}

.play-modes {
  display: flex;
  justify-content: center;
  gap: 10px;
  padding: 10px;
  background: rgba(249,249,249,0.9);
  border-bottom: 1px solid rgba(126,87,194,0.15);
  z-index: 10;
}

.mode-btn {
  padding: 6px 16px;
  border-radius: 14px;
  border: 1px solid rgba(126,87,194,0.25);
  background: linear-gradient(135deg, rgba(224,224,224,0.9), rgba(240,240,240,0.9));
  color: #555;
  font-size: 0.95rem;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 8px 14px rgba(94, 53, 177, 0.1);
  z-index: 11;
}

.mode-btn.active {
  background: linear-gradient(135deg, rgba(126, 87, 194, 0.9), rgba(94, 53, 177, 0.9));
  color: white;
  box-shadow: 0 0 12px rgba(126, 87, 194, 0.35);
  z-index: 12;
}

.playlist-content {
  padding: 0 12px 12px;
  overflow-y: auto;
  max-height: 50vh;
  min-height: 25vh;
  background: transparent;
  border-radius: 0 0 12px 12px;
  z-index: 9;
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
  z-index: 10;
}

.playlist-item {
  width: 100%;
  text-align: left;
  padding: 12px 50px 12px 16px;
  border: 1px solid rgba(126,87,194,0.18);
  border-radius: 12px;
  background: linear-gradient(135deg, rgba(249,249,249,0.95), rgba(240,240,240,0.95));
  color: #333;
  font-size: 1.05rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  position: relative;
  overflow: hidden;
  z-index: 11;
  box-shadow: 0 8px 14px rgba(94, 53, 177, 0.08);
}

.playlist-item:hover {
  background: linear-gradient(135deg, rgba(245,245,245,0.95), rgba(234,234,234,0.95));
  transform: translateY(-1px);
  box-shadow: 0 12px 20px rgba(94, 53, 177, 0.14);
  z-index: 12;
}

.playlist-item.playing {
  background: linear-gradient(135deg, rgba(126, 87, 194, 0.12), rgba(94, 53, 177, 0.12));
  color: #5e35b1;
  font-weight: 700;
  box-shadow: 0 0 16px rgba(126, 87, 194, 0.28);
  z-index: 13;
  border-color: rgba(126,87,194,0.35);
}

.playlist-item.playing::after {
  content: '▶';
  position: absolute;
  right: 16px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 14px;
  color: #5e35b1;
  background: linear-gradient(135deg, rgba(255,255,255,0.8), rgba(255,255,255,0.65));
  width: 30px;
  height: 30px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 14;
  border: 1px solid rgba(126,87,194,0.2);
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
  z-index: 15;
}

.remove-btn:hover {
  background: rgba(211, 47, 47, 0.12);
  transform: translateY(-50%) translateY(-1px) scale(1.05);
  z-index: 16;
}

.empty-playlist {
  text-align: center;
  padding: 20px;
  color: #757575;
  font-style: italic;
  background: #f5f5f5;
  border-radius: 8px;
  margin-top: 10px;
  z-index: 10;
}

.playlist-toggle {
  position: fixed;
  top: 50%;
  right: 0;
  transform: translateY(-50%);
  background: linear-gradient(135deg, rgba(126,87,194,0.95), rgba(94,53,177,0.95));
  color: white;
  border: 1px solid rgba(255,255,255,0.3);
  border-radius: 50% 0 0 50%;
  width: 40px;
  height: 40px;
  margin: 0;
  font-size: 1.2rem;
  cursor: pointer;
  z-index: 1001;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: -2px 10px 18px rgba(94, 53, 177, 0.2);
}

.playlist-toggle.open {
  right: 305px;
  background: linear-gradient(135deg, rgba(149,117,205,0.95), rgba(126,87,194,0.95));
  border-radius: 50%;
  transform: translateY(-50%) rotate(180deg);
  z-index: 1002;
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
  z-index: 1000;
}

.animated-note.animate {
  animation: noteMove 1s forwards, fadeOut 0.5s forwards 0.8s;
  z-index: 1000;
}

@keyframes noteMove {
  0% {
    transform: translate(var(--start-x, 0), var(--start-y, 0)) scale(1);
    opacity: 1;
    z-index: 1000;
  }
  100% {
    transform: translate(var(--target-x, 0), var(--target-y, 0)) scale(0.8);
    opacity: 0.3;
    z-index: 1000;
  }
}

@keyframes fadeOut {
  0% {
    opacity: 1;
    z-index: 1000;
  }
  100% {
    opacity: 0;
    z-index: 1000;
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

  .playlist-popup,
  .lyrics-panel {
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

  .lyrics-line {
    font-size: 1rem;
  }
  
  .lyrics-line.current {
    font-size: 1.2rem;
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

  .playlist-popup,
  .lyrics-panel {
    width: 90%;
    right: 5%;
    transform: translateX(105%);
  }

  .playlist-popup.open,
  .lyrics-panel.open {
    transform: translateX(5%);
  }

  .playlist-toggle {
    display: none;
  }

  .player-info {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
  
  .lyrics-toggle-btn {
    margin-left: 0;
    align-self: flex-end;
  }

  .lyrics-line {
    font-size: 0.9rem;
  }
  
  .lyrics-line.current {
    font-size: 1.1rem;
  }
}
</style>
