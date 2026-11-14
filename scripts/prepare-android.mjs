import { copyFileSync, readdirSync } from 'node:fs';

const generated = new URL('../src-tauri/gen/android/app/src/main/java/', import.meta.url);
const activities = readdirSync(generated, { recursive: true }).filter(path => /(^|[/\\])MainActivity\.kt$/.test(path));
if (activities.length !== 1) {
  throw new Error('Expected one generated MainActivity.kt. Run the Tauri Android initializer first.');
}
copyFileSync(new URL('../src-tauri/android/MainActivity.kt', import.meta.url), new URL(activities[0].replaceAll('\\', '/'), generated));
