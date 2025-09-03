import { createRouter, createWebHistory } from 'vue-router';
import MusicPlayer from '../views/MusicPlayer.vue';

const routes = [
  {
    path: '/',
    name: 'MusicPlayer',
    component: MusicPlayer
  }
];

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes
});

export default router;