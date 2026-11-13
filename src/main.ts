import icon0 from 'lucide-static/icons/scan-line.svg?raw';
import icon1 from 'lucide-static/icons/panels-top-left.svg?raw';
import icon2 from 'lucide-static/icons/images.svg?raw';
import icon3 from 'lucide-static/icons/settings-2.svg?raw';
import icon4 from 'lucide-static/icons/folder-open.svg?raw';
import icon5 from 'lucide-static/icons/scan.svg?raw';
import icon6 from 'lucide-static/icons/minus.svg?raw';
import icon7 from 'lucide-static/icons/plus.svg?raw';
import icon8 from 'lucide-static/icons/image-plus.svg?raw';
import icon9 from 'lucide-static/icons/arrow-up-right.svg?raw';
import icon10 from 'lucide-static/icons/copy.svg?raw';
import icon11 from 'lucide-static/icons/sliders-horizontal.svg?raw';
import icon12 from 'lucide-static/icons/rotate-ccw.svg?raw';
import icon13 from 'lucide-static/icons/palette.svg?raw';
import icon14 from 'lucide-static/icons/scan-face.svg?raw';
import icon15 from 'lucide-static/icons/sparkles.svg?raw';
import icon16 from 'lucide-static/icons/download.svg?raw';
import icon17 from 'lucide-static/icons/bookmark.svg?raw';
import icon18 from 'lucide-static/icons/trash-2.svg?raw';
import { invoke } from '@tauri-apps/api/core';
import { save } from '@tauri-apps/plugin-dialog';
import { writeFile } from '@tauri-apps/plugin-fs';
import { writeText } from '@tauri-apps/plugin-clipboard-manager';
import '@fontsource/space-grotesk/latin-400.css';
import '@fontsource/space-grotesk/latin-500.css';
import '@fontsource/space-grotesk/latin-700.css';
import '@fontsource/ibm-plex-mono/latin-400.css';
import './style.css';

type Options = {
  mode: 'ultra_detail' | 'rgb_photo' | 'portrait';
  palette: 'truecolor' | 'grayscale' | 'mono_green' | 'mono_amber';
  width: number;
  contrast: number;
  brightness: number;
  invert: boolean;
};
type Preview = {
  source: string; art: string; text: string; width: number; height: number;
  originalWidth: number; originalHeight: number;
};
type Project = { id: string; name: string; created: number; file: Blob; options: Options; thumb: string };
type Preferences = { autoRender: boolean; reduceMotion: boolean; defaults: Options };
type ExportFormat = 'png' | 'html' | 'txt' | 'comparison';
type View = 'studio' | 'gallery' | 'settings';

const defaults: Options = {
  mode: 'ultra_detail', palette: 'truecolor', width: 150,
  contrast: 1, brightness: 1, invert: false,
};
const initialPreferences: Preferences = { autoRender: true, reduceMotion: false, defaults };
const modes: Record<Options['mode'], string> = { ultra_detail: 'Ultra detail', rgb_photo: 'RGB photo', portrait: 'Portrait' };
const palettes: Record<Options['palette'], string> = {
  truecolor: 'True color', grayscale: 'Grayscale', mono_green: 'Matrix green', mono_amber: 'Amber',
};
const samples = [
  { file: 'landscape_sunset.jpg', title: 'Sunset ridge' },
  { file: 'portrait_hd.jpg', title: 'Studio portrait' },
  { file: 'vivid_colors.jpg', title: 'Color study' },
];
const formats: Record<ExportFormat, [string, string]> = {
  png: ['PNG artwork', 'png'], html: ['Interactive HTML', 'html'],
  txt: ['Plain text', 'txt'], comparison: ['Before / after PNG', 'png'],
};

const icons: Record<string, string> = {
  'scan-line': icon0,
  'panels-top-left': icon1,
  'images': icon2,
  'settings-2': icon3,
  'folder-open': icon4,
  'scan': icon5,
  'minus': icon6,
  'plus': icon7,
  'image-plus': icon8,
  'arrow-up-right': icon9,
  'copy': icon10,
  'sliders-horizontal': icon11,
  'rotate-ccw': icon12,
  'palette': icon13,
  'scan-face': icon14,
  'sparkles': icon15,
  'download': icon16,
  'bookmark': icon17,
  'trash-2': icon18,
};
function icon(name: string) { return icons[name] ?? ''; }
function el<T extends HTMLElement>(id: string): T {
  return document.getElementById(id) as T;
}

function readPreferences(): Preferences {
  try {
    const saved = JSON.parse(localStorage.getItem('nebula.preferences') ?? 'null');
    if (saved && typeof saved === 'object') {
      return { ...initialPreferences, ...saved, defaults: { ...defaults, ...saved.defaults } };
    }
  } catch { /* Invalid preferences fall back to the factory values. */ }
  return { ...initialPreferences, defaults: { ...defaults } };
}
let preferences = readPreferences();
let options = { ...preferences.defaults };
let project: { id?: string; name: string; file: Blob } | undefined;
let preview: Preview | undefined;
let renderedOptions: Options | undefined;
let view: View = 'studio';
let zoom = 100;
let dirty = false;
let busy = false;
let transfer = false;
let renderQueued = false;
let renderTimer: number | undefined;
let toastTimer: number | undefined;
let inputRequest = 0;
let galleryRequest = 0;

const app = el('app');
app.innerHTML = `
  <header class="topbar">
    <button class="brand" id="brand" aria-label="Nebula Studio home">
      <span class="brand-icon">${icon('scan-line')}</span><span>Nebula<span class="brand-muted"> / Studio</span></span>
    </button>
    <nav aria-label="Workspace">
      <button data-view="studio">${icon('panels-top-left')}<span>Studio</span></button>
      <button data-view="gallery">${icon('images')}<span>Gallery</span></button>
      <button data-view="settings">${icon('settings-2')}<span>Settings</span></button>
    </nav>
    <div class="local"><i></i> Local workspace</div>
  </header>
  <main class="shell">
    <section id="studio" class="page">
      <div class="page-title">
        <div><p class="eyebrow">IMAGE TO ASCII</p><h1>Conversion studio</h1></div>
        <button class="button primary" id="choose">${icon('folder-open')} Open image</button>
      </div>
      <input id="file" type="file" hidden accept=".jpg,.jpeg,.png,.webp,.bmp,.tiff,.tif,image/jpeg,image/png,image/webp,image/bmp,image/tiff">
      <div class="workspace">
        <div class="viewer panel">
          <div class="panel-header">
            <span class="section-title">${icon('scan')} Preview</span>
            <div class="preview-tools" id="preview-tools" hidden>
              <button id="zoom-out" class="icon-button" aria-label="Zoom out">${icon('minus')}</button>
              <button id="zoom-label" class="zoom-label" aria-label="Reset zoom">100%</button>
              <button id="zoom-in" class="icon-button" aria-label="Zoom in">${icon('plus')}</button>
            </div>
          </div>
          <div id="empty" class="drop-zone">
            <div class="star-field" aria-hidden="true"></div>
            <div class="drop-symbol">${icon('image-plus')}</div>
            <h2>Drop a photo here</h2>
            <p>JPG, PNG, WebP, BMP or TIFF · up to 24 MB</p>
            <button id="browse" class="button secondary">Browse files ${icon('arrow-up-right')}</button>
          </div>
          <div id="result" class="result" hidden>
            <div class="image-pane"><div class="image-label"><span>Original</span><small id="original-size"></small></div><div class="image-scroll"><img id="original" alt="Original photograph"></div></div>
            <div class="image-pane art-pane"><div class="image-label"><span>ASCII art</span><small id="grid-size"></small></div><div class="image-scroll"><img id="art" alt="Photo reconstructed with ASCII characters"></div></div>
          </div>
          <div class="viewer-footer">
            <span id="work-status" role="status">Waiting for an image</span>
            <button class="text-button" id="copy" disabled>${icon('copy')} Copy text</button>
          </div>
        </div>
        <aside class="panel controls">
          <div class="panel-header"><span class="section-title">${icon('sliders-horizontal')} Render settings</span><button id="reset" class="icon-button" title="Reset controls" aria-label="Reset controls">${icon('rotate-ccw')}</button></div>
          <div class="controls-body">
            <fieldset><legend>Render mode</legend><div class="mode-grid">${Object.entries(modes).map(([key, title], i) => `<button class="mode" data-mode="${key}" aria-pressed="false">${icon(['scan-line','palette','scan-face'][i])}<span>${title}</span></button>`).join('')}</div></fieldset>
            <label class="field">Palette<select id="palette">${Object.entries(palettes).map(([key, title]) => `<option value="${key}">${title}</option>`).join('')}</select></label>
            <label class="field range"><span>Columns <output id="width-value"></output></span><input id="width" type="range" min="40" max="500" step="1"></label>
            <label class="field range"><span>Contrast <output id="contrast-value"></output></span><input id="contrast" type="range" min="50" max="200" step="1"></label>
            <label class="field range"><span>Brightness <output id="brightness-value"></output></span><input id="brightness" type="range" min="50" max="150" step="1"></label>
            <label class="toggle"><span>Invert character density</span><input id="invert" type="checkbox"></label>
            <button class="button primary convert" id="convert" disabled>${icon('sparkles')} Convert image</button>
          </div>
        </aside>
        <section class="panel samples" id="samples"><div class="panel-header"><span class="section-title">${icon('images')} Try a sample</span></div><div class="sample-list">
          ${samples.map((sample, i) => `<button class="sample" data-sample="${i}"><img src="/samples/${sample.file}" alt=""><span>${sample.title}</span>${icon('arrow-up-right')}</button>`).join('')}
        </div></section>
        <section class="panel export"><div class="panel-header"><span class="section-title">${icon('download')} Export</span></div><div class="export-body">
          <label class="field">File format<select id="format">${Object.entries(formats).map(([key,[title]]) => `<option value="${key}">${title}</option>`).join('')}</select></label>
          <button class="button primary" id="export" disabled>${icon('download')} Save file</button>
          <button class="button secondary" id="save-project" disabled>${icon('bookmark')} Save to gallery</button>
        </div></section>
      </div>
    </section>
    <section id="gallery" class="page" hidden>
      <div class="page-title"><div><p class="eyebrow">LOCAL WORKSPACE</p><h1>Gallery</h1></div><button class="button primary" id="new-conversion">${icon('plus')} Open image</button></div>
      <div class="gallery-grid" id="gallery-grid"></div>
    </section>
    <section id="settings" class="page" hidden>
      <div class="page-title"><div><p class="eyebrow">LOCAL WORKSPACE</p><h1>Settings</h1></div></div>
      <div class="settings-grid">
        <section class="panel">
          <div class="panel-header"><span class="section-title">${icon('settings-2')} Workspace</span></div>
          <div class="preferences">
            <label class="toggle"><span><strong>Live preview</strong><small>Render again when you adjust a setting.</small></span><input id="auto-render" type="checkbox"></label>
            <label class="toggle"><span><strong>Reduce motion</strong><small>Use fewer animations in the studio.</small></span><input id="reduce-motion" type="checkbox"></label>
          </div>
        </section>
        <section class="panel">
          <div class="panel-header"><span class="section-title">${icon('sliders-horizontal')} New image defaults</span></div>
          <div class="preferences">
            <p id="default-summary"></p>
            <button class="button primary" id="save-defaults">${icon('bookmark')} Use current render settings</button>
            <button class="button secondary" id="reset-defaults">${icon('rotate-ccw')} Restore factory defaults</button>
          </div>
        </section>
      </div>
    </section>
  </main>
  <div id="toast" class="toast" role="status" hidden></div>
  <dialog id="delete-dialog"><form method="dialog"><h2>Remove from gallery?</h2><p>The saved project will be removed from this device.</p><div><button class="button secondary" value="cancel" autofocus>Cancel</button><button class="button danger" value="delete">Remove</button></div></form></dialog>
`;

const fileInput = el<HTMLInputElement>('file');
const palette = el<HTMLSelectElement>('palette');
const invert = el<HTMLInputElement>('invert');
const autoRender = el<HTMLInputElement>('auto-render');
const reduceMotion = el<HTMLInputElement>('reduce-motion');

function toast(message: string, error = false) {
  const element = el('toast');
  element.textContent = message;
  element.classList.toggle('error', error);
  element.hidden = false;
  clearTimeout(toastTimer);
  toastTimer = window.setTimeout(() => { element.hidden = true; }, 4900);
}

function errorText(error: unknown) {
  return error instanceof Error ? error.message : String(error);
}

function show(viewName: View) {
  view = viewName;
  for (const page of ['studio', 'gallery', 'settings']) el(page).hidden = page !== view;
  document.querySelectorAll<HTMLButtonElement>('[data-view]').forEach(button => {
    button.setAttribute('aria-current', button.dataset.view === view ? 'page' : 'false');
  });
  if (view === 'gallery') void populateGallery();
  if (view === 'settings') syncPreferences();
}

function syncControls() {
  document.querySelectorAll<HTMLButtonElement>('[data-mode]').forEach(button => {
    button.setAttribute('aria-pressed', String(button.dataset.mode === options.mode));
  });
  palette.value = options.palette;
  invert.checked = options.invert;
  for (const key of ['width', 'contrast', 'brightness'] as const) {
    const value = key === 'width' ? options[key] : Math.round(options[key] * 100);
    el<HTMLInputElement>(key).value = String(value);
    el(key + '-value').textContent = value + (key === 'width' ? ' col' : '%');
  }
}

function syncPreferences() {
  autoRender.checked = preferences.autoRender;
  reduceMotion.checked = preferences.reduceMotion;
  document.documentElement.classList.toggle('reduced-motion', preferences.reduceMotion);
  const d = preferences.defaults;
  el('default-summary').textContent = modes[d.mode] + ' · ' + palettes[d.palette] + ' · ' + d.width + ' columns';
}

function persistPreferences() {
  try { localStorage.setItem('nebula.preferences', JSON.stringify(preferences)); }
  catch (error) { toast('Could not save preferences: ' + errorText(error), true); }
  syncPreferences();
}

function syncActions() {
  el<HTMLButtonElement>('convert').disabled = !project || busy || transfer;
  el<HTMLButtonElement>('copy').disabled = !preview || busy;
  el<HTMLButtonElement>('export').disabled = !preview || busy || transfer || dirty;
  el<HTMLButtonElement>('save-project').disabled = !preview || busy || transfer || dirty;
  el('result').hidden = !preview;
  el('empty').hidden = !!preview;
  el('preview-tools').hidden = !preview;
  el('work-status').textContent = busy ? 'Converting image…' :
    project ? project.name + (dirty ? ' · Ready to convert' : '') : 'Waiting for an image';
  el('work-status').classList.toggle('processing', busy);
}

function optionsChanged() {
  syncControls();
  dirty = !!project;
  syncActions();
  clearTimeout(renderTimer);
  if (project && preferences.autoRender) renderTimer = window.setTimeout(() => { void convert(); }, 320);
}

function readImage(file: Blob): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onerror = () => reject(new Error('The image could not be read.'));
    reader.onload = () => resolve(String(reader.result).split(',', 2)[1]);
    reader.readAsDataURL(file);
  });
}

async function openImage(file: Blob, name: string, saved?: Project) {
  if (!file.size || file.size > 24 * 1024 * 1024) {
    toast('Choose a non-empty image under 24 MB.', true);
    return;
  }
  clearTimeout(renderTimer);
  project = { id: saved?.id, file, name };
  options = { ...(saved?.options ?? preferences.defaults) };
  dirty = true;
  preview = undefined;
  zoom = 100;
  syncControls();
  syncActions();
  show('studio');
  await convert();
}

async function convert() {
  if (!project) return;
  if (busy || transfer) { renderQueued = true; return; }
  const current = project;
  const selected = { ...options };
  busy = true;
  syncActions();
  try {
    const encoded = await readImage(current.file);
    const next = await invoke<Preview>('convert', { encoded, name: current.name, options: selected });
    if (project !== current) return;
    preview = next;
    renderedOptions = selected;
    dirty = JSON.stringify(selected) !== JSON.stringify(options);
    el<HTMLImageElement>('original').src = 'data:image/jpeg;base64,' + next.source;
    el<HTMLImageElement>('art').src = 'data:image/png;base64,' + next.art;
    el('original-size').textContent = next.originalWidth + ' × ' + next.originalHeight;
    el('grid-size').textContent = next.width + ' × ' + next.height + ' glyphs';
    setZoom(zoom);
  } catch (error) {
    if (project === current) toast(errorText(error), true);
  } finally {
    busy = false;
    syncActions();
    if (renderQueued) { renderQueued = false; void convert(); }
  }
}

function setZoom(value: number) {
  zoom = Math.max(75, Math.min(250, value));
  el('zoom-label').textContent = zoom + '%';
  for (const id of ['original', 'art']) el(id).style.setProperty('--zoom', zoom + '%');
}

async function transferArt(format: ExportFormat) {
  if (!project || !preview || dirty || busy || transfer) return;
  const stem = project.name.replace(/\.[^.]+$/, '').replace(/[<>:"/\\|?*]/g, '_') || 'nebula';
  const [label, ext] = formats[format];
  transfer = true;
  syncActions();
  try {
    const path = await save({ defaultPath: stem + (format === 'comparison' ? '-comparison.' : '-ascii.') + ext, filters: [{ name: label, extensions: [ext] }] });
    if (!path) return;
    const result = await invoke<ArrayBuffer | number[]>('export_art', { format });
    await writeFile(path, new Uint8Array(result));
    toast(label + ' saved.');
  } catch (error) {
    if (!/cancelled|canceled/i.test(errorText(error))) toast('Could not save: ' + errorText(error), true);
  } finally {
    transfer = false;
    syncActions();
    if (renderQueued) { renderQueued = false; void convert(); }
  }
}

let database: Promise<IDBDatabase> | undefined;
function db() {
  if (!database) {
    database = new Promise<IDBDatabase>((resolve, reject) => {
      const request = indexedDB.open('nebula-studio', 1);
      request.onupgradeneeded = () => request.result.createObjectStore('projects', { keyPath: 'id' });
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    }).catch(error => { database = undefined; throw error; });
  }
  return database;
}
async function galleryOperation<T>(mode: IDBTransactionMode, operation: (store: IDBObjectStore) => IDBRequest<T>) {
  const connection = await db();
  return new Promise<T>((resolve, reject) => {
    const tx = connection.transaction('projects', mode);
    const request = operation(tx.objectStore('projects'));
    tx.oncomplete = () => resolve(request.result);
    tx.onerror = tx.onabort = () => reject(tx.error ?? request.error);
  });
}

async function saveProject() {
  if (!project || !preview || !renderedOptions || dirty) return;
  const current = project;
  const id = current.id ?? crypto.randomUUID();
  const savedOptions = renderedOptions;
  const thumbnail = 'data:image/png;base64,' + preview.art;
  transfer = true;
  syncActions();
  try {
    await galleryOperation('readwrite', store => store.put({
      id, name: current.name, file: current.file, options: savedOptions, created: Date.now(),
      thumb: thumbnail,
    } satisfies Project));
    current.id = id;
    toast('Project saved to the gallery.');
    if (view === 'gallery') void populateGallery();
  } catch (error) { toast('Could not save project: ' + errorText(error), true); }
  finally {
    transfer = false;
    syncActions();
    if (renderQueued) { renderQueued = false; void convert(); }
  }
}

async function populateGallery() {
  const request = ++galleryRequest;
  const grid = el('gallery-grid');
  grid.innerHTML = '<p class="empty-gallery">Loading saved projects…</p>';
  try {
    const entries = await galleryOperation<Project[]>('readonly', store => store.getAll());
    if (request !== galleryRequest || view !== 'gallery') return;
    grid.replaceChildren();
    if (!entries.length) {
      grid.innerHTML = '<div class="panel empty-gallery"><h2>No saved projects yet</h2><p>Convert an image and select Save to gallery to find it here again.</p></div>';
    }
    for (const entry of entries.sort((a, b) => b.created - a.created)) {
      const card = document.createElement('article');
      card.className = 'panel gallery-card';
      card.innerHTML = `<button class="gallery-open"><img alt=""><span></span></button><div class="gallery-meta"><time></time><button class="icon-button gallery-delete" aria-label="Remove project" title="Remove project">${icon('trash-2')}</button></div>`;
      card.querySelector('img')!.src = entry.thumb;
      card.querySelector('span')!.textContent = entry.name;
      const time = card.querySelector('time')!;
      time.dateTime = new Date(entry.created).toISOString();
      time.textContent = new Date(entry.created).toLocaleDateString();
      card.querySelector('button')!.onclick = () => { ++inputRequest; void openImage(entry.file, entry.name, entry); };
      card.querySelector<HTMLButtonElement>('.gallery-delete')!.onclick = () => {
        const dialog = el<HTMLDialogElement>('delete-dialog');
        dialog.returnValue = '';
        dialog.addEventListener('close', async () => {
          if (dialog.returnValue !== 'delete') return;
          try {
            await galleryOperation('readwrite', store => store.delete(entry.id));
            if (project?.id === entry.id) project.id = undefined;
            await populateGallery();
            toast('Project removed.');
          } catch (error) { toast(errorText(error), true); }
        }, { once: true });
        dialog.showModal();
      };
      grid.append(card);
    }
  } catch (error) {
    grid.textContent = 'Could not open gallery: ' + errorText(error);
  }
}

async function loadSample(index: number) {
  const request = ++inputRequest;
  const sample = samples[index];
  try {
    const response = await fetch('/samples/' + sample.file);
    if (!response.ok) throw new Error('Sample unavailable.');
    const file = await response.blob();
    if (request === inputRequest) await openImage(file, sample.file);
  } catch (error) { toast(errorText(error), true); }
}

for (const id of ['choose', 'browse', 'new-conversion']) el(id).onclick = () => fileInput.click();
el('brand').onclick = () => show('studio');
fileInput.onchange = () => {
  const file = fileInput.files?.[0];
  fileInput.value = '';
  if (file) { ++inputRequest; void openImage(file, file.name); }
};
document.querySelectorAll<HTMLButtonElement>('[data-view]').forEach(button => {
  button.onclick = () => show(button.dataset.view as View);
});
document.querySelectorAll<HTMLButtonElement>('[data-sample]').forEach(button => {
  button.onclick = () => void loadSample(Number(button.dataset.sample));
});
document.querySelectorAll<HTMLButtonElement>('[data-mode]').forEach(button => {
  button.onclick = () => { options.mode = button.dataset.mode as Options['mode']; optionsChanged(); };
});
palette.onchange = () => { options.palette = palette.value as Options['palette']; optionsChanged(); };
invert.onchange = () => { options.invert = invert.checked; optionsChanged(); };
for (const key of ['width', 'contrast', 'brightness'] as const) {
  const input = el<HTMLInputElement>(key);
  input.oninput = () => { options[key] = Number(input.value) / (key === 'width' ? 1 : 100); optionsChanged(); };
}
el('reset').onclick = () => { options = { ...preferences.defaults }; optionsChanged(); };
el('convert').onclick = () => { clearTimeout(renderTimer); void convert(); };
el('zoom-in').onclick = () => setZoom(zoom + 25);
el('zoom-out').onclick = () => setZoom(zoom - 25);
el('zoom-label').onclick = () => setZoom(100);
el('copy').onclick = async () => {
  if (!preview) return;
  try { await writeText(preview.text); toast('ASCII text copied.'); }
  catch (error) { toast(errorText(error), true); }
};
el('export').onclick = () => void transferArt(el<HTMLSelectElement>('format').value as ExportFormat);
el('save-project').onclick = () => void saveProject();
autoRender.onchange = () => {
  preferences.autoRender = autoRender.checked;
  clearTimeout(renderTimer);
  persistPreferences();
  if (preferences.autoRender && dirty) void convert();
};
reduceMotion.onchange = () => { preferences.reduceMotion = reduceMotion.checked; persistPreferences(); };
el('save-defaults').onclick = () => { preferences.defaults = { ...options }; persistPreferences(); toast('Render defaults saved.'); };
el('reset-defaults').onclick = () => { preferences.defaults = { ...defaults }; persistPreferences(); toast('Factory defaults restored.'); };

const dropZone = el('empty');
window.addEventListener('dragover', event => {
  if (!event.dataTransfer?.types.includes('Files')) return;
  event.preventDefault();
  dropZone.classList.add('dragging');
});
window.addEventListener('dragleave', event => {
  if (!event.relatedTarget) dropZone.classList.remove('dragging');
});
window.addEventListener('drop', event => {
  event.preventDefault();
  dropZone.classList.remove('dragging');
  const file = event.dataTransfer?.files[0];
  if (file) { ++inputRequest; void openImage(file, file.name); }
});
window.addEventListener('keydown', event => {
  if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'o') {
    event.preventDefault(); fileInput.click();
  }
});

syncControls();
syncPreferences();
syncActions();
show('studio');
