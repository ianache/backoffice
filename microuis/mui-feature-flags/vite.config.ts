import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import federation from '@originjs/vite-plugin-federation'

export default defineConfig({
  base: 'http://localhost:5178/',
  plugins: [
    vue(),
    federation({
      name: 'mui-feature-flags',
      filename: 'remoteEntry.js',
      remotes: {
        shell: 'http://localhost:5173/assets/remoteEntry.js',
      },
      exposes: {
        './routes': './src/routes.ts',
      },
      shared: {
        vue:          { singleton: true, requiredVersion: false },
        pinia:        { singleton: true, requiredVersion: false },
        'vue-router': { singleton: true, requiredVersion: false },
        axios:        { singleton: true, requiredVersion: false },
      },
    }),
  ],
  build: {
    target: 'esnext',
    minify: false,
    outDir: 'dist',
  },
  preview: {
    port: 5178,
    strictPort: true,
    cors: true,
  },
})
