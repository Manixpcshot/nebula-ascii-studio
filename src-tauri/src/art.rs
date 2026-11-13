use ab_glyph::{point, Font, FontRef, ScaleFont};
use base64::{engine::general_purpose::STANDARD, Engine};
use image::{
    imageops::{self, FilterType},
    DynamicImage, ImageDecoder, ImageFormat, ImageReader, Limits, Rgb, RgbImage,
};
use serde::{Deserialize, Serialize};
use std::io::Cursor;

const BG: Rgb<u8> = Rgb([12, 13, 17]);
const MAX_INPUT: usize = 24 * 1024 * 1024;
const MAX_PIXELS: u64 = 32_000_000;
const MAX_CELLS: u64 = 250_000;
const CELL_W: u32 = 10;
const CELL_H: u32 = 20;
const ULTRA: &str = r#" `-'.:_,"^~;=!<+>\/*TL?|cr7ilFzJ(v)It[Ys1{}xufnjC]253ZoeV4EkaySUPhwX6AK9HRdqDGm#pbONWBM8$0%gQ&@"#;
const PORTRAIT: &str = " .':;-+~*|1()/{}[vucxzrjftnXYUJCLQ0OZmwqpdbkhao#MW&8%B$@█";
const FONT: &[u8] = include_bytes!("../assets/IBMPlexMono-Regular.ttf");

#[derive(Clone, Copy, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum Mode {
    UltraDetail,
    RgbPhoto,
    Portrait,
}

#[derive(Clone, Copy, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum Palette {
    Truecolor,
    Grayscale,
    MonoGreen,
    MonoAmber,
}

#[derive(Clone, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct Options {
    pub mode: Mode,
    pub palette: Palette,
    pub width: u32,
    pub contrast: f32,
    pub brightness: f32,
    pub invert: bool,
}

#[derive(Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum Format {
    Png,
    Html,
    Txt,
    Comparison,
}

pub struct Artwork {
    frame: Frame,
    source: RgbImage,
    png: Vec<u8>,
    name: String,
}

struct Frame {
    grid: RgbImage,
    chars: Vec<char>,
    text: String,
}

#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
pub struct Preview {
    source: String,
    art: String,
    text: String,
    width: u32,
    height: u32,
    original_width: u32,
    original_height: u32,
}

pub fn render(encoded: &str, name: String, options: Options) -> Result<(Artwork, Preview), String> {
    if encoded.len() > MAX_INPUT.div_ceil(3) * 4 {
        return Err("Choose an image under 24 MB.".into());
    }
    if !(40..=500).contains(&options.width)
        || !(0.5..=2.0).contains(&options.contrast)
        || !(0.5..=1.5).contains(&options.brightness)
    {
        return Err("One or more conversion settings are outside the supported range.".into());
    }
    let bytes = STANDARD
        .decode(encoded)
        .map_err(|_| "Could not read image data.")?;
    let image = decode(&bytes)?;
    let (original_width, original_height) = (image.width(), image.height());
    let width = options.width;
    let height = (f64::from(width) * f64::from(original_height) / f64::from(original_width) * 0.5)
        .floor()
        .max(1.0) as u32;
    if u64::from(width) * u64::from(height) > MAX_CELLS || height * CELL_H > 16000 {
        return Err("This image is very tall at the selected width. Try fewer columns.".into());
    }
    let source = image.thumbnail(1400, 1400);
    let source_jpeg = encode(&source, ImageFormat::Jpeg)?;
    let source = source.into_rgb8();
    let grid = image
        .resize_exact(width, height, FilterType::Lanczos3)
        .into_rgb8();
    let frame = make_frame(grid, &options);
    let png = encode(&DynamicImage::ImageRgb8(paint(&frame)?), ImageFormat::Png)?;
    let preview = Preview {
        source: STANDARD.encode(source_jpeg),
        art: STANDARD.encode(&png),
        text: frame.text.clone(),
        width,
        height,
        original_width,
        original_height,
    };
    Ok((
        Artwork {
            frame,
            source,
            png,
            name,
        },
        preview,
    ))
}

fn decode(bytes: &[u8]) -> Result<DynamicImage, String> {
    if bytes.len() > MAX_INPUT {
        return Err("Choose an image under 24 MB.".into());
    }
    let mut reader = ImageReader::new(Cursor::new(bytes))
        .with_guessed_format()
        .map_err(|e| e.to_string())?;
    let mut limits = Limits::default();
    limits.max_image_width = Some(12000);
    limits.max_image_height = Some(12000);
    limits.max_alloc = Some(160 * 1024 * 1024);
    reader.limits(limits);
    let mut decoder = reader
        .into_decoder()
        .map_err(|_| "Choose a readable JPG, PNG, WebP, BMP or TIFF image.")?;
    let (w, h) = decoder.dimensions();
    if w == 0 || h == 0 || u64::from(w) * u64::from(h) > MAX_PIXELS {
        return Err("Choose an image under 32 megapixels.".into());
    }
    let orientation = decoder.orientation().map_err(|e| e.to_string())?;
    let mut image =
        DynamicImage::from_decoder(decoder).map_err(|e| format!("Could not decode image: {e}"))?;
    image.apply_orientation(orientation);
    if image.color().has_alpha() {
        let rgba = image.into_rgba8();
        return Ok(DynamicImage::ImageRgb8(RgbImage::from_fn(
            rgba.width(),
            rgba.height(),
            |x, y| {
                let pixel = rgba.get_pixel(x, y);
                let alpha = u16::from(pixel[3]);
                Rgb(std::array::from_fn(|c| {
                    ((u16::from(pixel[c]) * alpha + u16::from(BG[c]) * (255 - alpha)) / 255) as u8
                }))
            },
        )));
    }
    Ok(DynamicImage::ImageRgb8(image.into_rgb8()))
}

fn luminance(c: Rgb<u8>) -> f32 {
    0.2126 * f32::from(c[0]) + 0.7152 * f32::from(c[1]) + 0.0722 * f32::from(c[2])
}

fn make_frame(grid: RgbImage, options: &Options) -> Frame {
    let (ramp, macro_amount, micro_amount, base_contrast, saturation, gamma) = match options.mode {
        Mode::UltraDetail => (ULTRA, 0.65, 1.15, 1.25, 1.15, 1.0_f32),
        Mode::RgbPhoto => (PORTRAIT, 0.35, 0.7, 1.15, 1.30, 1.02),
        Mode::Portrait => (PORTRAIT, 0.55, 0.95, 1.22, 1.18, 1.04),
    };
    let ramp: Vec<_> = ramp.chars().collect();
    let blur_macro = imageops::blur(&grid, 2.5);
    let blur_micro = imageops::blur(&grid, 0.9);
    let mut enhanced = grid.clone();
    let mut histogram = [0_usize; 256];
    for (x, y, pixel) in enhanced.enumerate_pixels_mut() {
        let original = grid.get_pixel(x, y);
        let broad = blur_macro.get_pixel(x, y);
        let fine = blur_micro.get_pixel(x, y);
        *pixel = Rgb(std::array::from_fn(|c| {
            let v = f32::from(original[c]);
            (v + macro_amount * (v - f32::from(broad[c])) + micro_amount * (v - f32::from(fine[c])))
                .clamp(0.0, 255.0) as u8
        }));
        histogram[luminance(*pixel) as usize] += 1;
    }
    let count = grid.width() as usize * grid.height() as usize;
    let percentile = |rank| {
        histogram
            .iter()
            .scan(0, |total, frequency| {
                *total += frequency;
                Some(*total)
            })
            .position(|total| total > rank)
            .unwrap_or(255) as f32
    };
    let low = percentile(count / 100);
    let high = percentile(count * 99 / 100);

    let mut chars = Vec::with_capacity(count);
    let mut text = String::with_capacity(count + grid.height() as usize);
    for (x, y, pixel) in enhanced.enumerate_pixels_mut() {
        if x == 0 && y != 0 {
            text.push('\n');
        }
        let adjusted = Rgb(std::array::from_fn(|c| {
            let mut v = f32::from(pixel[c]);
            if high > low + 10.0 {
                v = (v - low) * 255.0 / (high - low);
            }
            v = ((v - 127.5) * base_contrast * options.contrast + 127.5) * options.brightness;
            (255.0 * (v / 255.0).clamp(0.0, 1.0).powf(1.0 / gamma)) as u8
        }));
        let lum = luminance(adjusted);
        let tone = if options.invert { 255.0 - lum } else { lum };
        let glyph = ramp[((tone / 255.0 * ramp.len() as f32) as usize).min(ramp.len() - 1)];
        chars.push(glyph);
        text.push(glyph);
        *pixel = match options.palette {
            Palette::Truecolor => Rgb(std::array::from_fn(|c| {
                (lum + (f32::from(adjusted[c]) - lum) * saturation).clamp(0.0, 255.0) as u8
            })),
            Palette::Grayscale => Rgb([lum as u8; 3]),
            Palette::MonoGreen => Rgb([(lum * 0.15) as u8, lum as u8, (lum * 0.25) as u8]),
            Palette::MonoAmber => Rgb([lum as u8, (lum * 0.72) as u8, (lum * 0.12) as u8]),
        };
    }
    Frame {
        grid: enhanced,
        chars,
        text,
    }
}

fn paint(frame: &Frame) -> Result<RgbImage, String> {
    let font = FontRef::try_from_slice(FONT).map_err(|e| e.to_string())?;
    let font = font.as_scaled(16.0);
    let mut canvas = RgbImage::from_pixel(
        frame.grid.width() * CELL_W,
        frame.grid.height() * CELL_H,
        BG,
    );
    // Cache glyph coverage once per character, then blend it into each cell.
    let mut glyphs = std::collections::HashMap::new();
    for (index, &ch) in frame.chars.iter().enumerate() {
        if ch == ' ' {
            continue;
        }
        let coverage = glyphs.entry(ch).or_insert_with(|| {
            let mut mask = [0_f32; (CELL_W * CELL_H) as usize];
            if ch == '█' {
                mask.fill(1.0);
                return mask;
            }
            let id = font.glyph_id(ch);
            if let Some(outline) = font.outline_glyph(id.with_scale_and_position(
                16.0,
                point((CELL_W as f32 - font.h_advance(id)) / 2.0, 14.0),
            )) {
                let bounds = outline.px_bounds();
                outline.draw(|dx, dy, alpha| {
                    let x = bounds.min.x as i32 + dx as i32;
                    let y = bounds.min.y as i32 + dy as i32;
                    if (0..CELL_W as i32).contains(&x) && (0..CELL_H as i32).contains(&y) {
                        mask[(y as u32 * CELL_W + x as u32) as usize] = alpha;
                    }
                });
            }
            mask
        });
        let x = index as u32 % frame.grid.width();
        let y = index as u32 / frame.grid.width();
        let color = frame.grid.get_pixel(x, y);
        for (position, &alpha) in coverage.iter().enumerate() {
            if alpha == 0.0 {
                continue;
            }
            let blended = Rgb(std::array::from_fn(|c| {
                (f32::from(BG[c]) + alpha * (f32::from(color[c]) - f32::from(BG[c]))).round() as u8
            }));
            canvas.put_pixel(
                x * CELL_W + position as u32 % CELL_W,
                y * CELL_H + position as u32 / CELL_W,
                blended,
            );
        }
    }
    Ok(canvas)
}

fn encode(img: &DynamicImage, format: ImageFormat) -> Result<Vec<u8>, String> {
    let mut out = Cursor::new(Vec::new());
    img.write_to(&mut out, format).map_err(|e| e.to_string())?;
    Ok(out.into_inner())
}

fn escape(input: &str) -> String {
    input
        .replace('&', "&amp;")
        .replace('<', "&lt;")
        .replace('>', "&gt;")
}

impl Artwork {
    pub fn export(&self, format: Format) -> Result<Vec<u8>, String> {
        match format {
            Format::Png => Ok(self.png.clone()),
            Format::Txt => Ok(self.frame.text.as_bytes().to_vec()),
            Format::Html => Ok(self.html().into_bytes()),
            Format::Comparison => self.comparison(),
        }
    }

    fn html(&self) -> String {
        use std::fmt::Write as _;
        let title = escape(&self.name);
        let font = STANDARD.encode(FONT);
        let mut html = format!(
            r#"<!doctype html>
<html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} · Nebula ASCII Studio</title>
<style>@font-face{{font-family:Plex;src:url(data:font/ttf;base64,{font})}}body{{margin:0;background:#0c0d11;color:#e9eee3;font:16px system-ui}}header{{position:sticky;top:0;padding:16px 24px;background:#191b20;display:flex;align-items:center;gap:18px;flex-wrap:wrap}}h1{{font-size:1rem;margin:0 auto 0 0}}main{{padding:24px;overflow:auto}}pre{{margin:0;font:14px/1.2 Plex,monospace;font-variant-ligatures:none}}button{{padding:6px 12px}}</style>
<header><h1>{title}</h1><label>Zoom <input id="zoom" type="range" min="5" max="32" value="14"></label><button id="copy">Copy text</button><span id="status" role="status"></span></header>
<main><pre id="art">"#
        );
        let width = self.frame.grid.width() as usize;
        for (index, row) in self.frame.chars.chunks(width).enumerate() {
            if index != 0 {
                html.push('\n');
            }
            let mut last = None;
            for (x, &ch) in row.iter().enumerate() {
                let color = *self.frame.grid.get_pixel(x as u32, index as u32);
                if last != Some(color) {
                    if last.is_some() {
                        html.push_str("</span>");
                    }
                    let _ = write!(
                        html,
                        "<span style=\"color:#{:02x}{:02x}{:02x}\">",
                        color[0], color[1], color[2]
                    );
                    last = Some(color);
                }
                match ch {
                    '&' => html.push_str("&amp;"),
                    '<' => html.push_str("&lt;"),
                    '>' => html.push_str("&gt;"),
                    _ => html.push(ch),
                }
            }
            html.push_str("</span>");
        }
        html.push_str(r#"</pre></main><script>
const art=document.getElementById('art');
document.getElementById('zoom').oninput=e=>art.style.fontSize=e.target.value+'px';
document.getElementById('copy').onclick=async()=>{
 const status=document.getElementById('status');
 try{await navigator.clipboard.writeText(art.textContent);status.textContent='Copied';}
 catch{const selection=getSelection();selection.selectAllChildren(art);status.textContent='Text selected. Press Ctrl+C to copy.';}
};
</script></html>"#);
        html
    }

    fn comparison(&self) -> Result<Vec<u8>, String> {
        let art = image::load_from_memory_with_format(&self.png, ImageFormat::Png)
            .map_err(|e| e.to_string())?;
        let art = art.thumbnail(1800, 1600).into_rgb8();
        let photo_width = (u64::from(self.source.width()) * u64::from(art.height())
            / u64::from(self.source.height()))
        .clamp(1, 2400) as u32;
        let photo = imageops::resize(
            &self.source,
            photo_width,
            art.height(),
            FilterType::Lanczos3,
        );
        let mut comparison = RgbImage::from_pixel(
            photo.width() + art.width() + 48,
            art.height() + 64,
            Rgb([27, 29, 34]),
        );
        imageops::replace(&mut comparison, &photo, 16, 48);
        imageops::replace(&mut comparison, &art, i64::from(photo.width() + 32), 48);
        let labels = [(16, "ORIGINAL"), (photo.width() + 32, "ASCII ART")];
        let font = FontRef::try_from_slice(FONT).map_err(|e| e.to_string())?;
        for (left, label) in labels {
            for (i, ch) in label.chars().enumerate() {
                let glyph = font
                    .glyph_id(ch)
                    .with_scale_and_position(17.0, point((left + i as u32 * 10) as f32, 31.0));
                if let Some(glyph) = font.outline_glyph(glyph) {
                    let bounds = glyph.px_bounds();
                    glyph.draw(|x, y, a| {
                        let x = bounds.min.x as i32 + x as i32;
                        let y = bounds.min.y as i32 + y as i32;
                        if x >= 0 && y >= 0 && (x as u32) < comparison.width() && (y as u32) < 48 {
                            comparison.put_pixel(
                                x as u32,
                                y as u32,
                                Rgb(std::array::from_fn(|c| {
                                    (27.0 + (f32::from([213_u8, 249, 140][c]) - 27.0) * a) as u8
                                })),
                            );
                        }
                    });
                }
            }
        }
        encode(&DynamicImage::ImageRgb8(comparison), ImageFormat::Png)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn options() -> Options {
        Options {
            mode: Mode::Portrait,
            palette: Palette::MonoGreen,
            width: 48,
            contrast: 1.0,
            brightness: 1.0,
            invert: false,
        }
    }

    #[test]
    fn converts_real_image_and_exports_all_formats() {
        let encoded = STANDARD.encode(include_bytes!("../../public/samples/portrait_hd.jpg"));
        let (artwork, preview) = render(&encoded, "<portrait>.jpg".into(), options()).unwrap();
        assert_eq!((preview.width, preview.height), (48, 30));
        assert_eq!(
            (preview.original_width, preview.original_height),
            (800, 1000)
        );
        assert!(preview.text.lines().all(|line| line.chars().count() == 48));
        assert!(preview.text.chars().any(|ch| !ch.is_whitespace()));
        assert_eq!(
            artwork.export(Format::Txt).unwrap(),
            preview.text.as_bytes()
        );
        let png = artwork.export(Format::Png).unwrap();
        let art = image::load_from_memory(&png).unwrap();
        assert_eq!((art.width(), art.height()), (480, 600));
        assert!(art.into_rgb8().pixels().any(|p| p[1] > 120 && p[1] > p[0]));
        let comparison =
            image::load_from_memory(&artwork.export(Format::Comparison).unwrap()).unwrap();
        assert!(comparison.width() > 960);
        assert!(comparison.height() > 600);
        let html = String::from_utf8(artwork.export(Format::Html).unwrap()).unwrap();
        assert!(html.contains("&lt;portrait&gt;.jpg"));
        assert!(html.contains("style=\"color:#"));
        assert!(html.contains("Copy text"));
    }

    #[test]
    fn rejects_unreadable_and_out_of_range_inputs() {
        assert!(render(
            &STANDARD.encode(b"not an image"),
            "bad.png".into(),
            options()
        )
        .is_err());
        let invalid = Options {
            width: 501,
            ..options()
        };
        assert!(render("", "bad.png".into(), invalid).is_err());
    }
}
