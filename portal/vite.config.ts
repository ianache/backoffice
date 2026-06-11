import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import federation from '@originjs/vite-plugin-federation'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const remotes: Record<string, string> = {}
  
  // Remote Discovery
  remotes['mui-stub'] = env.VITE_REMOTE_STUB 
    ? `${env.VITE_REMOTE_STUB}/assets/remoteEntry.js` 
    : 'http://localhost:5175/assets/remoteEntry.js'

  remotes['mui-security'] = env.VITE_REMOTE_SECURITY
    ? `${env.VITE_REMOTE_SECURITY}/assets/remoteEntry.js`
    : 'http://localhost:5174/assets/remoteEntry.js'

  remotes['mui-tenants'] = env.VITE_REMOTE_TENANTS
    ? `${env.VITE_REMOTE_TENANTS}/assets/remoteEntry.js`
    : 'http://localhost:5176/assets/remoteEntry.js'

  remotes['mui-feature-flags'] = env.VITE_REMOTE_FEATURE_FLAGS
    ? `${env.VITE_REMOTE_FEATURE_FLAGS}/assets/remoteEntry.js`
    : 'http://localhost:5178/assets/remoteEntry.js'

  console.log('--- Vite Config Remotes ---', remotes)

  return {
    plugins: [
      vue({
        template: {
          compilerOptions: {
            isCustomElement: (tag) => tag.startsWith('md-')
          }
        }
      }),
      federation({
        name: 'shell',
        remotes,
        exposes: {
          './StitchButton': './src/components/ui/StitchButton.vue',
          './StitchTextField': './src/components/ui/StitchTextField.vue',
          './toastStore': './src/stores/toast.ts',
          './api': './src/services/api.ts',
          './boFlags': './src/composables/useBoFlags.ts',
        },
        shared: {
          vue: {
            singleton: true,
            requiredVersion: false
          },
          pinia: {
            singleton: true,
            requiredVersion: false
          },
          'vue-router': {
            singleton: true,
            requiredVersion: false
          },
          axios: {
            singleton: true,
            requiredVersion: false
          }
        }
      })
    ],
    resolve: {
      alias: {
        '@': fileURLToPath(new URL('./src', import.meta.url)),
      },
    },
    build: {
      target: 'esnext',
      minify: false,
      cssCodeSplit: false
    },
    server: {
      port: 5173,
      strictPort: true,
    },
    preview: {
      port: 5173,
      strictPort: true,
      cors: true,
    },
  }
})
