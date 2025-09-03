<template>
  <div class="song-info">
    <img :src="song.cover" alt="Album Cover" class="album-cover" />
    <h2 class="song-title">{{ song.title }}</h2>
    <h3 class="song-artist">{{ song.artist }}</h3>
    <h4 class="song-album">{{ song.album }}</h4>
  </div>
</template>

<script lang="ts">
import { defineComponent, PropType } from 'vue';

interface Song {
  title: string;
  artist: string;
  album: string;
  cover: string;
}

export default defineComponent({
  name: 'SongInfo',
  props: {
    song: {
      type: Object as PropType<Song>,
      required: true
    }
  }
});
</script>

<style scoped>
.song-info {
  text-align: center;
  margin: 20px;
}

.album-cover {
  width: 150px;
  height: 150px;
  border-radius: 10px;
}

.song-title {
  font-size: 1.5em;
  margin: 10px 0;
}

.song-artist,
.song-album {
  font-size: 1.2em;
  color: #666;
}
</style>