import { defineConfig } from 'vite';
import { resolve, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));

export default defineConfig({
  build: {
    rollupOptions: {
      input: {
        main: resolve(__dirname, 'index.html'),
        admin: resolve(__dirname, 'pages/panel-admin.html'),
        conductor: resolve(__dirname, 'pages/panel-conductor.html'),
        perfil_conductor: resolve(__dirname, 'pages/perfil-conductor.html'),
        perfil: resolve(__dirname, 'pages/perfil.html'),
        registro_emergencias: resolve(__dirname, 'pages/registro-emergencias.html'),
        reportes: resolve(__dirname, 'pages/reportes.html')
      }
    }
  }
});
