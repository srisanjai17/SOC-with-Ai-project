import { defineConfig } from 'vite';

// Build is handled by build.mjs (vanilla IIFE concatenation + esbuild minify).
// This config only sets up `vite preview` for testing the built output.

export default defineConfig({
  root: 'dist',
  preview: {
    port: 4173,
    proxy: {
      '/api': 'http://127.0.0.1:8002',
    },
  },
});
