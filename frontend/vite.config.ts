import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // host: true faz o Vite ouvir em todas as interfaces de rede (0.0.0.0),
    // para outros dispositivos na mesma rede poderem abrir o site pelo teu IP.
    host: true,
  },
})
