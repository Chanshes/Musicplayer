import { createStore } from 'vuex';

export default createStore({
  state: {
    currentSong: null,
    isPlaying: false,
    songList: [],
    currentLyrics: ''
  },
  mutations: {
    setCurrentSong(state, song) {
      state.currentSong = song;
    },
    setIsPlaying(state, isPlaying) {
      state.isPlaying = isPlaying;
    },
    setSongList(state, songs) {
      state.songList = songs;
    },
    setCurrentLyrics(state, lyrics) {
      state.currentLyrics = lyrics;
    }
  },
  actions: {
    playSong({ commit }, song) {
      commit('setCurrentSong', song);
      commit('setIsPlaying', true);
      // Additional logic to handle playing the song can be added here
    },
    pauseSong({ commit }) {
      commit('setIsPlaying', false);
      // Additional logic to handle pausing the song can be added here
    },
    loadSongs({ commit }, songs) {
      commit('setSongList', songs);
    },
    updateLyrics({ commit }, lyrics) {
      commit('setCurrentLyrics', lyrics);
    }
  },
  getters: {
    currentSong: state => state.currentSong,
    isPlaying: state => state.isPlaying,
    songList: state => state.songList,
    currentLyrics: state => state.currentLyrics
  }
});