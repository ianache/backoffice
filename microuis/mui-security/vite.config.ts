import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import federation from '@originjs/vite-plugin-federation'

export default defineConfig({
  plugins: [
    vue(),
    federation({
      name: 'mui-security',
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
    port: 5174,
    strictPort: true,
    cors: true,
  },
})
