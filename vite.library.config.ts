import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
// the standalone site of the library (library.html -> dist-library/index.html); see scripts/build_library_site.mjs
export default defineConfig({ base: './', plugins: [react()], build: { outDir: 'dist-library', emptyOutDir: true, assetsInlineLimit: 0, target: 'es2022', rollupOptions: { input: 'library.html' } } });
