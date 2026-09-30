// Purpose: reproducible React browser build; variables define the plugin and output configuration.
// Index: defineConfig@3, react@4
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
export default defineConfig({ plugins: [react()], build: { outDir: 'dist' }, server: { host: '127.0.0.1' } });
