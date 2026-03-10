# CodebaseExamples

# Camera ASCII Projection

A real-time camera-to-ASCII art visualizer built with React and OpenCV.js — transforms your webcam feed into animated ASCII characters with face detection, interactive pattern modes, and mouse-driven effects.

---

## Features

| Feature | Behaviour |
| --- | --- |
| Live ASCII Rendering | Converts camera video frames into a grid of ASCII characters (`█▓▒░·`) mapped by brightness |
| Face Detection | Uses OpenCV.js Haar cascade classifier to detect faces in real time, shown via a green/red indicator |
| Animated Patterns | 4 mathematical pattern modes (`balance`, `duality`, `flow`, `chaos`) cycle on click when camera is off |
| Mouse Interaction | Click-and-drag to influence ASCII patterns with attraction/repulsion effects |
| Keyboard Controls | Press `C` to toggle camera on/off |
| Responsive Grid | ASCII grid dynamically adapts to window dimensions using monospace character sizing |

---

## Project Structure

```
camera-ascii-projection/
├── index.html                 # Entry HTML — loads OpenCV.js async
├── package.json               # Dependencies and scripts
├── vite.config.js             # Vite + React plugin config
├── public/
│   ├── opencv.js              # OpenCV.js WASM library
│   └── haarcascade_frontalface_default.xml  # Haar cascade face model
├── src/
│   ├── main.jsx               # App entry point — mounts root component
│   ├── CameraAsciiProjection.jsx  # Core component — animation loop, rendering, UI
│   ├── ErrorBoundary.jsx      # Catches and displays runtime errors gracefully
│   ├── patterns.js            # 4 pattern functions + ASCII/sizing constants
│   └── hooks/
│       ├── useCamera.js       # Camera lifecycle — start, stop, permissions
│       └── useFaceDetection.js # OpenCV face detection at 500ms intervals
```

---

## Architecture

```
User Interaction (click / drag / keypress)
              │
              ▼
┌────────────────────────────────────────┐
│   CameraAsciiProjection                │
│   (main orchestrator)                  │
│                                        │
│  ┌─────────────┐ ┌──────────────────┐  │ 
│  │ useCamera   │ │ useFaceDetection │  │
│  │             │ │                  │  │
│  │ getUserMedia│ │ OpenCV.js        │  │
│  │ videoRef    │ │ Haar cascade     │  │
│  └─────┬───────┘ │ 500ms polling    │  │
│        │         └────────┬─────────┘  │
│        ▼                  ▼            │
│  ┌─────────────────────────────┐       │
│  │   requestAnimationFrame     │       │
│  │   Animation Loop            │       │
│  │                             │       │
│  │  Camera ON + Face?          │       │
│  │  → Brightness → ASCII       │       │
│  │                             │       │
│  │  Camera OFF?                │       │
│  │  → Pattern fn → ASCII       │       │
│  │  → Mouse influence          │       │
│  └─────────────┬───────────────┘       │
│                ▼                       │
│         <pre> element                  │
│         (rendered ASCII grid)          │
└────────────────────────────────────────┘
```

1. **useCamera** acquires the webcam stream via `getUserMedia` and exposes a video element ref
2. **useFaceDetection** loads OpenCV.js + Haar cascade XML asynchronously, then polls for faces every 500ms
3. **Animation loop** runs on every frame via `requestAnimationFrame`:
   - If camera is active and a face is detected → maps pixel brightness to ASCII characters with wave animation
   - Otherwise → evaluates the selected pattern function and applies mouse influence
4. The resulting ASCII string is written directly to a `<pre>` element for rendering

---

## Setup

### Prerequisites

- **Node.js** (v18+)
- **npm**
- A browser with webcam support (Chrome, Firefox, Edge)

### Step 1 — Clone Repository

```bash
git clone <repo-url>
cd camera-ascii-projection
git checkout ascii-projection
```

### Step 2 — Install Dependencies

```bash
npm install
```

No environment configuration is needed — all settings are hardcoded.

---

## Running the Application

```bash
npm run dev
```

This starts the Vite dev server. Open the URL shown in your terminal (typically `http://localhost:5173`).

### Usage

1. The app starts with animated ASCII patterns — **click anywhere** to cycle through modes (`balance` → `duality` → `flow` → `chaos`)
2. **Press `C`** or click the camera button (📷) to enable your webcam
3. Grant camera permission when prompted — your face will render as ASCII art
4. **Click and drag** to warp the pattern with mouse-driven effects
5. A **green dot** indicates a face is detected; **red** means no face found

---

## Verifying Everything Works

1. Run `npm run dev` and open the app in your browser
2. Confirm animated ASCII patterns are rendering and cycling on click
3. Press `C` — verify camera permission prompt appears
4. After granting access, confirm your video feed renders as ASCII characters
5. Check the face detection indicator (green = detected, red = not detected)
6. Click and drag on the pattern view to verify mouse interaction

---

## Configuration Reference

| Setting | Default | Description |
| --- | --- | --- |
| `BACKGROUND_COLOR` | `#F0EEE6` | Page background color (warm beige) |
| `CHAR_WIDTH` | `7.2` | Approximate pixel width of a monospace character at 12px |
| `CHAR_HEIGHT` | `12` | Pixel height of a monospace character |
| `CYCLE_LENGTH` | `240` | Number of animation frames per pattern cycle |
| `SLOWDOWN_FACTOR` | `12` | Divisor applied to time — slows wave animations |
| `ASCII_CHARS` | `█▓▒░·` | Character set used for brightness mapping (dark → light) |
| Face detection interval | `500ms` | Polling rate for OpenCV face detection |
| Face detection `scaleFactor` | `1.1` | Haar cascade multi-scale detection parameter |
| Face detection `minNeighbors` | `4` | Minimum detections required to confirm a face |
| Face detection `minSize` | `40×40` | Minimum face size in pixels |

All values are hardcoded in the source files — edit [src/patterns.js](src/patterns.js) and [src/hooks/useFaceDetection.js](src/hooks/useFaceDetection.js) to customize.

---

## License

This project is licensed under the MIT License.

---
