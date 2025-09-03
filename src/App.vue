<template>
  <div id="app">
    <MusicPlayer />
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue';
import MusicPlayer from './views/MusicPlayer.vue';

export default defineComponent({
  name: 'App',
  components: {
    MusicPlayer
  }
});
</script>

<style>
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: #2c3e50;
  min-height: 100vh;
  background: linear-gradient(135deg, #1a2a6c, #b21f1f, #fdbb2d);
}
</style>
