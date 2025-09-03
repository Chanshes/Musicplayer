<template>
  <div class="song-list">
    <h2>可播放的歌曲列表</h2>
    <ul>
      <li v-for="(song, index) in songs" :key="index" @click="selectSong(song)">
        {{ song.title }} - {{ song.artist }}
      </li>
    </ul>
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue';

export default defineComponent({
  name: 'SongList',
  props: {
    songs: {
      type: Array,
      required: true
    }
  },
  methods: {
    selectSong(song: { title: string; artist: string }) {
      this.$emit('song-selected', song);
    }
  }
});
</script>

<style scoped>
.song-list {
  padding: 20px;
}

.song-list h2 {
  margin-bottom: 10px;
}

.song-list ul {
  list-style-type: none;
  padding: 0;
}

.song-list li {
  cursor: pointer;
  padding: 5px;
  transition: background-color 0.3s;
}

.song-list li:hover {
  background-color: #f0f0f0;
}
</style>