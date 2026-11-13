mod art;

use art::{Artwork, Format, Options, Preview};
use std::sync::{Arc, Mutex};
use tauri::{ipc::Response, State};

#[derive(Default)]
struct Studio(Mutex<Option<Arc<Artwork>>>);

#[tauri::command]
async fn convert(
    studio: State<'_, Studio>,
    encoded: String,
    name: String,
    options: Options,
) -> Result<Preview, String> {
    let (artwork, preview) =
        tauri::async_runtime::spawn_blocking(move || art::render(&encoded, name, options))
            .await
            .map_err(|e| e.to_string())??;
    *studio.0.lock().map_err(|e| e.to_string())? = Some(Arc::new(artwork));
    Ok(preview)
}

#[tauri::command]
async fn export_art(studio: State<'_, Studio>, format: Format) -> Result<Response, String> {
    let artwork = studio
        .0
        .lock()
        .map_err(|e| e.to_string())?
        .clone()
        .ok_or("Convert an image first.")?;
    tauri::async_runtime::spawn_blocking(move || artwork.export(format).map(Response::new))
        .await
        .map_err(|e| e.to_string())?
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .manage(Studio::default())
        .plugin(tauri_plugin_fs::init())
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_clipboard_manager::init())
        .invoke_handler(tauri::generate_handler![convert, export_art])
        .run(tauri::generate_context!())
        .expect("failed to start Nebula ASCII Studio");
}
