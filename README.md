# 🧠 Neuroviai Bg Remover

AI-powered background removal that preserves full original resolution — 4K in, 4K out. File size naturally reduces as the background pixels are removed.

## Features

- **Full resolution preservation** — output matches exact input dimensions (4K stays 4K)
- **Smaller output files** — transparent areas compress efficiently, so a 5 MB photo may become ~3 MB
- **5 AI models** to choose from depending on your subject
- **Enhanced edge detection** — alpha matting for clean cuts on hair, fur, and fine details
- **Custom background color** — transparent, white, black, or any custom hex color
- **Side-by-side preview** with before/after comparison
- **Drag & drop** interface with instant download

## AI Models

| Model | Best For |
|---|---|
| `isnet-general-use` | General purpose (default, best quality) |
| `u2net` | Objects and products |
| `u2net_human_seg` | Portraits and people |
| `silueta` | Fast processing |
| `isnet-anime` | Anime and illustrations |

## Quick Start

### Local

```bash
pip install -r requirements.txt
python app.py
```

Open [http://localhost:8000](http://localhost:8000)

### Docker

```bash
docker build -t neuroviai-bg-remover .
docker run -p 8000:8000 neuroviai-bg-remover
```

## API

### `POST /remove-bg`

Remove background and return a transparent PNG.

| Field | Type | Default | Description |
|---|---|---|---|
| `file` | file | required | Image to process |
| `model` | string | `isnet-general-use` | AI model to use |
| `alpha_matting` | bool | `true` | Enable edge refinement |
| `alpha_matting_foreground_threshold` | int | `240` | Foreground sensitivity |
| `alpha_matting_background_threshold` | int | `10` | Background sensitivity |
| `alpha_matting_erode_size` | int | `10` | Edge erosion amount |
| `post_process_mask` | bool | `true` | Clean up mask edges |
| `bg_color` | string | `null` | Hex background color (e.g. `#ffffff`) |

**Response headers:**
- `X-Resolution` — original image resolution (e.g. `3840x2160`)
- `X-Original-Size` — input file size in bytes
- `X-Output-Size` — output file size in bytes

### `POST /remove-bg-webp`

Same as above but returns a WebP file (smaller, still supports transparency).

| Field | Type | Default | Description |
|---|---|---|---|
| `file` | file | required | Image to process |
| `model` | string | `isnet-general-use` | AI model to use |
| `quality` | int | `95` | WebP quality (1–100) |

### `GET /models`

Returns available models and their descriptions.

## Requirements

- Python 3.10+
- See [requirements.txt](requirements.txt)

## Tech Stack

- [FastAPI](https://fastapi.tiangolo.com/) — web framework
- [rembg](https://github.com/danielgatis/rembg) — AI background removal
- [Pillow](https://python-pillow.org/) — image processing
- [ONNX Runtime](https://onnxruntime.ai/) — model inference
