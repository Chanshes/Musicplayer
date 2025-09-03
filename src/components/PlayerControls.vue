<template>
  <div class="player-controls">
    <button @click="play" :disabled="isPlaying">Play</button>
    <button @click="pause" :disabled="!isPlaying">Pause</button>
    <button @click="next">Next</button>
    <button @click="prev">Previous</button>
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue';

export default defineComponent({
  name: 'PlayerControls',
  props: {
    isPlaying: {
      type: Boolean,
      required: true
    },
    onPlay: {
      type: Function,
      required: true
    },
    onPause: {
      type: Function,
      required: true
    },
    onNext: {
      type: Function,
      required: true
    },
    onPrev: {
      type: Function,
      required: true
    }
  },
  methods: {
    play() {
      this.onPlay();
    },
    pause() {
      this.onPause();
    },
    next() {
      this.onNext();
    },
    prev() {
      this.onPrev();
    }
  }
});
</script>

<style scoped>
.player-controls {
  display: flex;
  justify-content: center;
  gap: 10px;
}
</style>