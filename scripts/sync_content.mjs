// Copies content/ (the single source of truth for the app's data) into public/content/ so it is bundled into the web build and the Android app.
import { cpSync, rmSync, mkdirSync } from 'node:fs';
rmSync('public/content', { recursive: true, force: true }); mkdirSync('public/content', { recursive: true });
cpSync('content', 'public/content', { recursive: true, filter: (s) => !s.endsWith('.md') });
console.log('content synced to public/content');
