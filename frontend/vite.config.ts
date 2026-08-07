import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig(({ command }) => ({
  // Em produção o Django serve os assets do React através do WhiteNoise, sob
  // STATIC_URL = "/static/". Por isso o build tem de referenciar os ficheiros
  // em /static/assets/... (o collectstatic copia frontend/dist para aí). Em dev
  // (Vite) mantém-se "/" — o servidor Vite serve na raiz.
  base: command === "build" ? "/static/" : "/",
  plugins: [react()],
  server: {
    // host: true faz o Vite ouvir em todas as interfaces de rede (0.0.0.0),
    // para outros dispositivos na mesma rede poderem abrir o site pelo teu IP.
    host: true,
  },
}))
