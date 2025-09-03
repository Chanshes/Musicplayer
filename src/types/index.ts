interface Song {
  id: number;
  title: string;
  artist: string;
  album: string;
  duration: number; // duration in seconds
  file: string; // path to the local music file
}

interface Lyrics {
  songId: number;
  lines: Array<{
    time: number; // time in seconds
    text: string;
  }>;
}

interface PlayerState {
  currentSong: Song | null;
  isPlaying: boolean;
  currentTime: number; // current playback time in seconds
}

export type { Song, Lyrics, PlayerState };