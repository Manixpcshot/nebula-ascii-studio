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
import languagesIcon from 'lucide-static/icons/languages.svg?raw';
import photoIcon from 'lucide-static/icons/image.svg?raw';
import gridIcon from 'lucide-static/icons/grid-3x3.svg?raw';
import { messages, type Locale, type Message } from './i18n';
import { invoke } from '@tauri-apps/api/core';
import { save } from '@tauri-apps/plugin-dialog';
import { writeFile } from '@tauri-apps/plugin-fs';
import { writeText } from '@tauri-apps/plugin-clipboard-manager';
import '@fontsource/space-grotesk/latin-400.css';
import '@fontsource/space-grotesk/latin-500.css';
import '@fontsource/space-grotesk/latin-700.css';
import '@fontsource/ibm-plex-mono/latin-400.css';
import '@fontsource-variable/vazirmatn';
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
type Preferences = { language: Locale; autoRender: boolean; reduceMotion: boolean; defaults: Options };
type ExportFormat = 'png' | 'html' | 'txt' | 'comparison';
type View = 'studio' | 'gallery' | 'settings';

const defaults: Options = {
  mode: 'ultra_detail', palette: 'truecolor', width: 150,
  contrast: 1, brightness: 1, invert: false,
};
const initialPreferences: Preferences = { language: 'fa', autoRender: true, reduceMotion: false, defaults };
const modes: Record<Options['mode'], Message> = { ultra_detail: 'ultraDetail', rgb_photo: 'rgbPhoto', portrait: 'portrait' };
const palettes: Record<Options['palette'], Message> = {
  truecolor: 'truecolor', grayscale: 'grayscale', mono_green: 'monoGreen', mono_amber: 'monoAmber',
};
const featured = { file: 'caracal-twilight.png', title: 'caracal' } as const;
const samples = [
  { file: 'landscape_sunset.jpg', title: 'sunset' },
  { file: 'portrait_hd.jpg', title: 'portraitSample' },
  { file: 'vivid_colors.jpg', title: 'colorStudy' },
] as const;
const formats: Record<ExportFormat, [Message, string]> = {
  png: ['png', 'png'], html: ['html', 'html'],
  txt: ['txt', 'txt'], comparison: ['comparison', 'png'],
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
      return { ...initialPreferences, ...saved, language: saved.language === 'en' ? 'en' : 'fa', defaults: { ...defaults, ...saved.defaults } };
    }
  } catch { /* Invalid preferences fall back to the factory values. */ }
  return { ...initialPreferences, defaults: { ...defaults } };
}
let preferences = readPreferences();
const t = (key: Message) => messages[preferences.language][key];
const tr = (key: Message) => `<span data-message="${key}">${t(key)}</span>`;
const number = (value: number) => new Intl.NumberFormat(preferences.language).format(value);
const percent = (value: number) => new Intl.NumberFormat(preferences.language, { style: 'percent' }).format(value / 100);
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
    <button class="brand" id="brand" data-aria="brandHome">
      <img class="brand-icon" src="/nebula.svg" alt=""><span dir="ltr">Nebula<span class="brand-muted"> / Studio</span></span>
    </button>
    <nav data-aria="workspace">
      <button data-view="studio">${icon('panels-top-left')}${tr('studio')}</button>
      <button data-view="gallery">${icon('images')}${tr('gallery')}</button>
      <button data-view="settings">${icon('settings-2')}${tr('settings')}</button>
    </nav>
    <div class="top-tools"><span class="local"><i></i>${tr('local')}</span><button class="icon-button language-shortcut" id="language-shortcut" data-aria="language" data-title="language">${languagesIcon}</button></div>
  </header>
  <main class="shell">
    <section id="studio" class="page">
      <div class="page-title">
        <h1>${tr('studioTitle')}</h1>
        <button class="button primary" id="choose">${icon('folder-open')}${tr('open')}</button>
      </div>
      <input id="file" type="file" hidden accept=".jpg,.jpeg,.png,.webp,.bmp,.tiff,.tif,image/jpeg,image/png,image/webp,image/bmp,image/tiff">
      <div class="workspace">
        <div class="viewer panel">
          <div class="panel-header">
            <span class="section-title">${icon('scan')}${tr('preview')}</span>
            <div class="preview-tools" id="preview-tools" hidden>
              <button id="zoom-out" class="icon-button" data-aria="zoomOut">${icon('minus')}</button>
              <button id="zoom-label" class="zoom-label" data-aria="zoomReset">100%</button>
              <button id="zoom-in" class="icon-button" data-aria="zoomIn">${icon('plus')}</button>
            </div>
          </div>
          <div class="preview-stage" id="preview-stage" aria-busy="false">
            <div id="empty" class="drop-zone">
              <div class="drop-content">
                <div class="star-field" aria-hidden="true"></div>
                <div class="drop-symbol">${icon('image-plus')}</div>
                <h2>${tr('dropTitle')}</h2>
                <p>${tr('fileTypes')}</p>
                <button id="browse" class="button secondary">${tr('browse')} ${icon('arrow-up-right')}</button>
              </div>
              <button id="featured" class="featured">
                <img src="/samples/${featured.file}" alt="">
                <span class="feature-caption"><strong>${tr(featured.title)}</strong><span>${tr('demo')} ${icon('arrow-up-right')}</span></span>
              </button>
            </div>
            <div id="result" class="result" hidden>
              <div class="image-pane"><div class="image-label"><span>${photoIcon}${tr('original')}</span><small id="original-size" dir="ltr"></small></div><div class="image-scroll" dir="ltr"><img id="original" data-alt="originalAlt"></div></div>
              <div class="image-pane art-pane"><div class="image-label"><span>${gridIcon}${tr('artwork')}</span><small id="grid-size" dir="auto"></small></div><div class="image-scroll" dir="ltr"><img id="art" data-alt="artworkAlt"></div></div>
            </div>
            <div class="scan-effect" aria-hidden="true"><div class="scan-grid"></div><div class="scan-beam"></div></div>
          </div>
          <div class="viewer-footer">
            <span id="work-status" role="status"></span>
            <button class="text-button" id="copy" disabled>${icon('copy')}${tr('copy')}</button>
          </div>
        </div>
        <aside class="panel controls">
          <div class="panel-header"><span class="section-title">${icon('sliders-horizontal')}${tr('renderSettings')}</span><button id="reset" class="icon-button" data-title="resetControls" data-aria="resetControls">${icon('rotate-ccw')}</button></div>
          <div class="controls-body">
            <fieldset><legend>${tr('mode')}</legend><div class="mode-grid">${Object.entries(modes).map(([key, title], i) => `<button class="mode" data-mode="${key}" aria-pressed="false">${icon(['scan-line','palette','scan-face'][i])}${tr(title)}</button>`).join('')}</div></fieldset>
            <label class="field">${tr('palette')}<select id="palette">${Object.entries(palettes).map(([key, title]) => `<option value="${key}" data-message="${title}"></option>`).join('')}</select></label>
            <label class="field range"><span>${tr('columns')} <output id="width-value"></output></span><input id="width" type="range" min="40" max="500" step="1"></label>
            <label class="field range"><span>${tr('contrast')} <output id="contrast-value"></output></span><input id="contrast" type="range" min="50" max="200" step="1"></label>
            <label class="field range"><span>${tr('brightness')} <output id="brightness-value"></output></span><input id="brightness" type="range" min="50" max="150" step="1"></label>
            <label class="toggle"><span>${tr('invert')}</span><input id="invert" type="checkbox"></label>
            <button class="button primary convert" id="convert" disabled>${icon('sparkles')}${tr('convert')}</button>
          </div>
        </aside>
        <section class="panel samples" id="samples"><div class="panel-header"><span class="section-title">${icon('images')}${tr('samples')}</span></div><div class="sample-list">
          ${samples.map((sample, i) => `<button class="sample" data-sample="${i}"><img src="/samples/${sample.file}" alt="">${tr(sample.title)}${icon('arrow-up-right')}</button>`).join('')}
        </div></section>
        <section class="panel export"><div class="panel-header"><span class="section-title">${icon('download')}${tr('export')}</span></div><div class="export-body">
          <label class="field">${tr('fileFormat')}<select id="format">${Object.entries(formats).map(([key,[title]]) => `<option value="${key}" data-message="${title}"></option>`).join('')}</select></label>
          <button class="button primary" id="export" disabled>${icon('download')}${tr('saveFile')}</button>
          <button class="button secondary" id="save-project" disabled>${icon('bookmark')}${tr('saveProject')}</button>
        </div></section>
      </div>
    </section>
    <section id="gallery" class="page" hidden>
      <div class="page-title"><h1>${tr('gallery')}</h1><button class="button primary" id="new-conversion">${icon('plus')}${tr('open')}</button></div>
      <div class="gallery-grid" id="gallery-grid"></div>
    </section>
    <section id="settings" class="page" hidden>
      <div class="page-title"><h1>${tr('settings')}</h1></div>
      <div class="settings-grid">
        <section class="panel">
          <div class="panel-header"><span class="section-title">${icon('settings-2')}${tr('workspace')}</span></div>
          <div class="preferences">
            <label class="field"><span class="label-icon">${languagesIcon}${tr('language')}</span><select id="language"><option value="fa" lang="fa">فارسی</option><option value="en" lang="en">English</option></select></label>
            <label class="toggle"><span><strong>${tr('livePreview')}</strong><small>${tr('liveHelp')}</small></span><input id="auto-render" type="checkbox"></label>
            <label class="toggle"><span><strong>${tr('reduceMotion')}</strong><small>${tr('motionHelp')}</small></span><input id="reduce-motion" type="checkbox"></label>
          </div>
        </section>
        <section class="panel">
          <div class="panel-header"><span class="section-title">${icon('sliders-horizontal')}${tr('defaults')}</span></div>
          <div class="preferences">
            <p id="default-summary"></p>
            <button class="button primary" id="save-defaults">${icon('bookmark')}${tr('saveDefaults')}</button>
            <button class="button secondary" id="reset-defaults">${icon('rotate-ccw')}${tr('resetDefaults')}</button>
          </div>
        </section>
      </div>
    </section>
  </main>
  <div id="toast" class="toast" role="status" hidden></div>
  <dialog id="delete-dialog"><form method="dialog"><h2>${tr('deleteTitle')}</h2><p>${tr('deleteHelp')}</p><div><button class="button secondary" value="cancel" autofocus>${tr('cancel')}</button><button class="button danger" value="delete">${tr('remove')}</button></div></form></dialog>
`;

const fileInput = el<HTMLInputElement>('file');
const palette = el<HTMLSelectElement>('palette');
const invert = el<HTMLInputElement>('invert');
const autoRender = el<HTMLInputElement>('auto-render');
const reduceMotion = el<HTMLInputElement>('reduce-motion');
const language = el<HTMLSelectElement>('language');

function syncLanguage() {
  document.documentElement.lang = preferences.language;
  document.documentElement.dir = preferences.language === 'fa' ? 'rtl' : 'ltr';
  document.title = preferences.language === 'fa' ? 'استودیو ASCII نبولا' : 'Nebula ASCII Studio';
  app.querySelectorAll<HTMLElement>('[data-message]').forEach(element => {
    element.textContent = t(element.dataset.message as Message);
  });
  for (const [data, attribute] of [['aria', 'aria-label'], ['title', 'title'], ['alt', 'alt']] as const) {
    app.querySelectorAll<HTMLElement>('[data-' + data + ']').forEach(element => {
      element.setAttribute(attribute, t(element.dataset[data] as Message));
    });
  }
  language.value = preferences.language;
  el('toast').hidden = true;
  syncControls();
  syncPreferences();
  syncActions();
  syncPreviewLabels();
  if (view === 'gallery') void populateGallery();
}

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

function report(key: Message, error: unknown) {
  console.error(error);
  toast(t(key), true);
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
    el(key + '-value').textContent = key === 'width' ? number(value) + ' ' + t('col') : percent(value);
  }
}

function syncPreferences() {
  autoRender.checked = preferences.autoRender;
  reduceMotion.checked = preferences.reduceMotion;
  document.documentElement.classList.toggle('reduced-motion', preferences.reduceMotion);
  const d = preferences.defaults;
  el('default-summary').textContent = t(modes[d.mode]) + ' · ' + t(palettes[d.palette]) + ' · ' + number(d.width) + ' ' + t('col');
}

function persistPreferences() {
  try { localStorage.setItem('nebula.preferences', JSON.stringify(preferences)); }
  catch (error) { report('preferencesError', error); }
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
  const status = el('work-status');
  status.replaceChildren();
  if (busy || !project) {
    status.textContent = t(busy ? 'converting' : 'waiting');
  } else {
    const file = document.createElement('bdi');
    file.textContent = project.name;
    status.append(file);
    if (dirty) status.append(' · ' + t('ready'));
  }
  status.classList.toggle('processing', busy);
  el('preview-stage').setAttribute('aria-busy', String(busy));
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
    reader.onerror = () => reject(new Error(t('readError')));
    reader.onload = () => resolve(String(reader.result).split(',', 2)[1]);
    reader.readAsDataURL(file);
  });
}

async function openImage(file: Blob, name: string, saved?: Project) {
  if (!file.size || file.size > 24 * 1024 * 1024) {
    toast(t('fileLimit'), true);
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
    const art = el<HTMLImageElement>('art');
    art.src = 'data:image/png;base64,' + next.art;
    syncPreviewLabels();
    void art.decode().then(() => {
      if (project === current && preview === next) revealArtwork();
    }).catch(() => { /* A newer image can replace this one during decoding. */ });
  } catch (error) {
    if (project === current) {
      const detail = errorText(error);
      const key = detail.includes('32 megapixels') ? 'pixelLimit'
        : detail.includes('very tall') ? 'tallImage'
        : detail.includes('readable JPG') || detail.includes('Could not decode') ? 'invalidImage' : 'renderError';
      report(key, error);
    }
  } finally {
    busy = false;
    syncActions();
    if (renderQueued) { renderQueued = false; void convert(); }
  }
}

let reveal: Animation | undefined;
function revealArtwork() {
  reveal?.cancel();
  if (preferences.reduceMotion || matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  reveal = el('art').animate([
    { clipPath: 'inset(0 0 100% 0)', filter: 'brightness(1.6)', opacity: 0.35 },
    { clipPath: 'inset(0 0 0 0)', filter: 'brightness(1)', opacity: 1 },
  ], { duration: 600, easing: 'cubic-bezier(.2,.7,.2,1)' });
}

function syncPreviewLabels() {
  setZoom(zoom);
  if (!preview) return;
  el('original-size').textContent = number(preview.originalWidth) + ' × ' + number(preview.originalHeight);
  el('grid-size').textContent = number(preview.width) + ' × ' + number(preview.height) + ' ' + t('glyphs');
}

function setZoom(value: number) {
  zoom = Math.max(75, Math.min(250, value));
  el('zoom-label').textContent = percent(zoom);
  for (const id of ['original', 'art']) el(id).style.setProperty('--zoom', zoom + '%');
}

async function transferArt(format: ExportFormat) {
  if (!project || !preview || dirty || busy || transfer) return;
  const stem = project.name.replace(/\.[^.]+$/, '').replace(/[<>:"/\\|?*]/g, '_') || 'nebula';
  const [label, ext] = formats[format];
  transfer = true;
  syncActions();
  try {
    const path = await save({ defaultPath: stem + (format === 'comparison' ? '-comparison.' : '-ascii.') + ext, filters: [{ name: t(label), extensions: [ext] }] });
    if (!path) return;
    const result = await invoke<ArrayBuffer | number[]>('export_art', { format });
    await writeFile(path, new Uint8Array(result));
    toast(t('fileSaved'));
  } catch (error) {
    if (!/cancelled|canceled/i.test(errorText(error))) report('saveError', error);
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
    toast(t('projectSaved'));
    if (view === 'gallery') void populateGallery();
  } catch (error) { report('projectError', error); }
  finally {
    transfer = false;
    syncActions();
    if (renderQueued) { renderQueued = false; void convert(); }
  }
}

async function populateGallery() {
  const request = ++galleryRequest;
  const grid = el('gallery-grid');
  grid.innerHTML = `<p class="empty-gallery">${t('loadingGallery')}</p>`;
  try {
    const entries = await galleryOperation<Project[]>('readonly', store => store.getAll());
    if (request !== galleryRequest || view !== 'gallery') return;
    grid.replaceChildren();
    if (!entries.length) {
      grid.innerHTML = `<div class="panel empty-gallery">${icon('images')}<h2>${t('emptyGallery')}</h2><p>${t('galleryHelp')}</p></div>`;
    }
    for (const entry of entries.sort((a, b) => b.created - a.created)) {
      const card = document.createElement('article');
      card.className = 'panel gallery-card';
      card.innerHTML = `<button class="gallery-open"><img alt=""><bdi></bdi></button><div class="gallery-meta"><time></time><button class="icon-button gallery-delete" aria-label="${t('removeProject')}" title="${t('removeProject')}">${icon('trash-2')}</button></div>`;
      card.querySelector('img')!.src = entry.thumb;
      card.querySelector('bdi')!.textContent = entry.name;
      const time = card.querySelector('time')!;
      time.dateTime = new Date(entry.created).toISOString();
      time.textContent = new Date(entry.created).toLocaleDateString(preferences.language);
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
            toast(t('projectRemoved'));
          } catch (error) { report('removeError', error); }
        }, { once: true });
        dialog.showModal();
      };
      grid.append(card);
    }
  } catch (error) {
    if (request !== galleryRequest || view !== 'gallery') return;
    console.error(error);
    grid.textContent = t('galleryError');
  }
}

async function loadSample(sample: { file: string; title: Message }) {
  const request = ++inputRequest;
  try {
    const response = await fetch('/samples/' + sample.file);
    if (!response.ok) throw new Error(t('sampleError'));
    const file = await response.blob();
    if (request === inputRequest) await openImage(file, sample.file);
  } catch (error) { if (request === inputRequest) report('sampleError', error); }
}

for (const id of ['choose', 'browse', 'new-conversion']) el(id).onclick = () => fileInput.click();
el('brand').onclick = () => show('studio');
el('featured').onclick = () => void loadSample(featured);
el('language-shortcut').onclick = () => { show('settings'); language.focus(); };
language.onchange = () => {
  preferences.language = language.value === 'en' ? 'en' : 'fa';
  persistPreferences();
  syncLanguage();
};
fileInput.onchange = () => {
  const file = fileInput.files?.[0];
  fileInput.value = '';
  if (file) { ++inputRequest; void openImage(file, file.name); }
};
document.querySelectorAll<HTMLButtonElement>('[data-view]').forEach(button => {
  button.onclick = () => show(button.dataset.view as View);
});
document.querySelectorAll<HTMLButtonElement>('[data-sample]').forEach(button => {
  button.onclick = () => void loadSample(samples[Number(button.dataset.sample)]);
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
  try { await writeText(preview.text); toast(t('copied')); }
  catch (error) { report('copyError', error); }
};
el('export').onclick = () => void transferArt(el<HTMLSelectElement>('format').value as ExportFormat);
el('save-project').onclick = () => void saveProject();
autoRender.onchange = () => {
  preferences.autoRender = autoRender.checked;
  clearTimeout(renderTimer);
  persistPreferences();
  if (preferences.autoRender && dirty) void convert();
};
reduceMotion.onchange = () => {
  preferences.reduceMotion = reduceMotion.checked;
  if (preferences.reduceMotion) reveal?.cancel();
  persistPreferences();
};
el('save-defaults').onclick = () => { preferences.defaults = { ...options }; persistPreferences(); toast(t('defaultsSaved')); };
el('reset-defaults').onclick = () => { preferences.defaults = { ...defaults }; persistPreferences(); toast(t('defaultsReset')); };

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
  if ((event.ctrlKey || event.metaKey) && event.code === 'KeyO') {
    event.preventDefault(); fileInput.click();
  }
});

syncLanguage();
show('studio');
