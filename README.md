## Nebula ASCII Studio

Nebula converts photographs into colored character art on your device. Choose a photo, adjust the rendering, and compare the result with the original. Save work in the local gallery and reopen it later to keep editing.

[Download Windows, Linux and Android builds](https://github.com/Manixpcshot/nebula-ascii-studio/releases)

- **Windows x64** · NSIS installer
- **Linux x64** · Debian package or AppImage
- **Android** · Signed APK for ARM64 and x86-64

Open JPG, PNG, WebP, BMP or TIFF files up to 24 MB and 32 megapixels. Choose Ultra Detail, RGB Photo or Portrait, then adjust width, contrast, brightness, palette and character density. Export PNG, plain text, interactive HTML, or an original/ASCII comparison PNG. The image, gallery and preferences stay on the device. Use the bundled samples to try the app.

### Development

Install Rust stable, Node.js 24 and the [Tauri platform prerequisites](https://v2.tauri.app/start/prerequisites/). On Windows, use MSVC Build Tools and WebView2. On Linux, install the WebKitGTK 4.1 development libraries.

```sh
npm ci
npm run tauri -- dev
```

Run `npm run build` to type check and bundle the UI, and `cargo test --locked --manifest-path src-tauri/Cargo.toml` to test the Rust conversion engine. The browser UI calls the Rust engine through Tauri, so use the Tauri command to run the app.

For Android, set up JDK 21 and Android SDK/NDK according to the Tauri guide. Install SDK platforms 36 and 37.0, build tools 36.0.0 and NDK 28.2.13676358, and point `NDK_HOME` at that NDK.

```sh
rustup target add aarch64-linux-android x86_64-linux-android
npm run tauri -- android init
npm run tauri -- android build --apk --debug --target aarch64 x86_64
```

### Releases

GitHub Actions builds the Windows, Linux and Android installers for each push to `main` and each pull request. Download these builds from the workflow run's Artifacts section. For a public release, update the versions in `package.json`, `src-tauri/Cargo.toml` and `src-tauri/tauri.conf.json`, refresh both lockfiles, then push a matching tag such as `v1.0.1`. The release job publishes the installers and SHA-256 checksums after tests and all builds pass.

Tagged Android builds use a persistent PKCS#12 keystore with alias `nebula`. Configure `ANDROID_KEY_BASE64` and `ANDROID_KEY_PASSWORD` as repository Actions secrets. Back up the key securely and reuse it for all releases so Android accepts in-place upgrades. Windows installers are currently unsigned.

### Source and contributions

The Tauri interface is in `src/` and the Rust image pipeline and exporters are in `src-tauri/src/`. The previous Python terminal edition remains available through `main.py` and `requirements.txt`. Bug reports and pull requests are welcome. For rendering issues, include the operating system, app version, rendering settings and a shareable example.

The project is MIT licensed. The bundled IBM Plex Mono and Space Grotesk fonts use the SIL Open Font License. Interface icons are from Lucide under the ISC license. Third-party notices are included in `licenses/`.
