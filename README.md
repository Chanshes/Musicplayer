# Vue Music Player

这是一个使用Vue构建的音乐播放器项目，支持本地音乐播放，包含歌曲界面、歌词显示以及相关的播放操作。

## 项目结构

```
vue-music-player
├── src
│   ├── main.ts               # 应用程序的入口点
│   ├── App.vue               # 根组件
│   ├── components            # 组件目录
│   │   ├── SongList.vue      # 歌曲列表组件
│   │   ├── PlayerControls.vue # 播放控制组件
│   │   ├── LyricsDisplay.vue  # 歌词显示组件
│   │   └── SongInfo.vue      # 歌曲信息组件
│   ├── views                 # 视图目录
│   │   └── MusicPlayer.vue   # 音乐播放器视图
│   ├── assets                # 静态资源目录
│   ├── router                # 路由配置目录
│   │   └── index.ts          # Vue Router配置
│   ├── store                 # 状态管理目录
│   │   └── index.ts          # Vuex状态管理配置
│   └── types                 # 类型定义目录
│       └── index.ts          # TypeScript类型和接口
├── package.json              # npm配置文件
├── tsconfig.json             # TypeScript配置文件
└── README.md                 # 项目文档
```

## 功能特性

- **本地音乐播放**：支持从本地文件系统选择音乐文件进行播放。
- **歌曲列表**：显示可播放的歌曲列表，用户可以选择想要播放的歌曲。
- **播放控制**：提供播放、暂停、下一曲和上一曲等控制按钮。
- **歌词显示**：实时更新并显示当前播放歌曲的歌词。
<!-- - **歌曲信息**：显示当前播放歌曲的标题、艺术家和专辑封面。 -->

## 安装与运行

1. 克隆项目到本地：
   ```
   git clone <repository-url>
   ```

2. 进入项目目录：
   ```
   cd vue-music-player
   ```

3. 安装依赖：
   ```
   npm install
   ```

4. 启动开发服务器：
   ```
   npm run serve
   ```

5. 在浏览器中访问 `http://localhost:5173` 查看应用。

## 贡献

欢迎任何形式的贡献！请提交问题或拉取请求。

## 许可证

该项目遵循 MIT 许可证。