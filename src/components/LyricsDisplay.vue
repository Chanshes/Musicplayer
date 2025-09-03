<template>
  <div class="lyrics-display">
    <h2>歌词</h2>
    <pre>{{ lyrics }}</pre>
  </div>
</template>

<script lang="ts">
import { defineComponent, PropType } from 'vue';

export default defineComponent({
  name: 'LyricsDisplay',
  props: {
    lyrics: {
      type: String as PropType<string>,
      required: true
    }
  }
});
</script>

<style scoped>
.lyrics-display {
  padding: 20px;
  background-color: #f9f9f9;
  border: 1px solid #ddd;
  border-radius: 5px;
  max-height: 300px;
  overflow-y: auto;
}
</style>