import { useState, useEffect, useRef, useCallback } from 'react';
import { patterns, patternTypes, ASCII_CHARS, CHAR_WIDTH, CHAR_HEIGHT } from './patterns';
import { useCamera } from './hooks/useCamera';
import { useFaceDetection } from './hooks/useFaceDetection';

function calcGridSize() {
  const cols = Math.floor(window.innerWidth / CHAR_WIDTH);
  const rows = Math.floor(window.innerHeight / CHAR_HEIGHT);
  return { cols, rows };
}

const BACKGROUND_COLOR = '#F0EEE6';
// 240 frames per cycle × slowdown factor = total animation loop length
const CYCLE_LENGTH = 240;
const SLOWDOWN_FACTOR = 12;

const CameraAsciiProjection = () => {
  const { cameraActive, cameraError, videoRef, startCamera, stopCamera } = useCamera();
  const { faceDetected } = useFaceDetection(videoRef, cameraActive);

  const [statusMsg, setStatusMsg] = useState('Click anywhere to cycle patterns');
  const [buttonHover, setButtonHover] = useState(false);

  const containerRef = useRef(null);
  const canvasRef = useRef(null);
  const canvasCtxRef = useRef(null);
  const preRef = useRef(null);
  const cameraFrameRef = useRef(null);
  const frameRef = useRef(0);
  const patternTypeRef = useRef(0);
  const gridSizeRef = useRef(calcGridSize());
  const mousePosRef = useRef({ x: 0, y: 0 });
  const mouseDownRef = useRef(false);

  // Mirror reactive state to refs for the animation loop
  const cameraActiveRef = useRef(false);
  const faceDetectedRef = useRef(false);
  useEffect(() => { cameraActiveRef.current = cameraActive; }, [cameraActive]);
  useEffect(() => { faceDetectedRef.current = faceDetected; }, [faceDetected]);

  // Resize listener — ref-only, no state update needed
  useEffect(() => {
    const onResize = () => { gridSizeRef.current = calcGridSize(); };
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  }, []);

  // Process video frame → brightness grid
  const processVideoFrame = useCallback(() => {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (!video || !canvas || video.readyState < 2) return;

    const { cols: w, rows: h } = gridSizeRef.current;
    canvas.width = w;
    canvas.height = h;
    // Re-acquire context after canvas resize (old context is invalidated)
    canvasCtxRef.current = canvas.getContext('2d', { willReadFrequently: true });
    const ctx = canvasCtxRef.current;

    ctx.save();
    ctx.scale(-1, 1);
    ctx.drawImage(video, -w, 0, w, h);
    ctx.restore();

    const imageData = ctx.getImageData(0, 0, w, h);
    const totalPixels = w * h;

    // Reuse flat array when size matches, otherwise allocate
    if (!cameraFrameRef.current || cameraFrameRef.current.length !== totalPixels) {
      cameraFrameRef.current = { data: new Float32Array(totalPixels), w, h };
    }
    const frame = cameraFrameRef.current;
    frame.w = w;
    frame.h = h;

    for (let i = 0; i < totalPixels; i++) {
      const pi = i * 4;
      frame.data[i] = (0.299 * imageData.data[pi] + 0.587 * imageData.data[pi + 1] + 0.114 * imageData.data[pi + 2]) / 255;
    }
  }, [videoRef]);

  // Generate ASCII art — reads entirely from refs, no React state dependency
  const generateAsciiArt = useCallback(() => {
    const { cols: w, rows: h } = gridSizeRef.current;
    const t = (frameRef.current * Math.PI) / (60 * SLOWDOWN_FACTOR);
    const chars = [];

    if (cameraActiveRef.current && faceDetectedRef.current && cameraFrameRef.current) {
      const frame = cameraFrameRef.current;
      for (let y = 0; y < h; y++) {
        for (let x = 0; x < w; x++) {
          const brightness = (y < frame.h && x < frame.w) ? frame.data[y * frame.w + x] : 0.5;
          const wave = Math.sin(x * 0.15 + t * 0.3) * Math.cos(y * 0.15 + t * 0.2) * 0.08;
          const adjusted = Math.max(0, Math.min(1, brightness + wave));
          const inverted = 1 - adjusted;
          const charIndex = Math.floor(inverted * (ASCII_CHARS.length - 1));
          chars.push(ASCII_CHARS[Math.min(charIndex, ASCII_CHARS.length - 1)]);
        }
        chars.push('\n');
      }
      return chars.join('');
    }

    const currentPattern = patterns[patternTypes[patternTypeRef.current]];

    for (let y = 0; y < h; y++) {
      for (let x = 0; x < w; x++) {
        let value = currentPattern(x, y, t, w, h);

        if (mouseDownRef.current && containerRef.current) {
          const rect = containerRef.current.getBoundingClientRect();
          const mPos = mousePosRef.current;
          const dx = x - (((mPos.x - rect.left) / rect.width) * w);
          const dy = y - (((mPos.y - rect.top) / rect.height) * h);
          const dist = Math.sqrt(dx * dx + dy * dy);
          const mouseInfluence = Math.exp(-dist * 0.1) * Math.sin(t * 2);
          value += mouseInfluence * 0.8;
        }

        // Map pattern value (-1..1) to ASCII_CHARS index (0..len-1)
        const normalized = (1 - value) / 2; // map -1..1 → 1..0
        const clamped = Math.max(0, Math.min(1, normalized));
        const charIndex = Math.floor(clamped * (ASCII_CHARS.length - 1));
        chars.push(ASCII_CHARS[Math.min(charIndex, ASCII_CHARS.length - 1)]);
      }
      chars.push('\n');
    }
    return chars.join('');
  }, []);

  // Main animation loop — writes directly to DOM, bypasses React reconciliation
  useEffect(() => {
    let animationId;
    const animate = () => {
      frameRef.current = (frameRef.current + 1) % (CYCLE_LENGTH * SLOWDOWN_FACTOR);

      if (cameraActiveRef.current) {
        processVideoFrame();
      }

      if (preRef.current) {
        preRef.current.textContent = generateAsciiArt();
      }

      animationId = requestAnimationFrame(animate);
    };
    animationId = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(animationId);
  }, [generateAsciiArt, processVideoFrame]);

  // Keyboard handler
  useEffect(() => {
    const handleKey = (e) => {
      if (e.key === 'c' || e.key === 'C') {
        if (cameraActiveRef.current) {
          stopCamera();
          cameraFrameRef.current = null;
          setStatusMsg('Click anywhere to cycle patterns');
        } else {
          setStatusMsg('Requesting camera access...');
          startCamera();
        }
      }
    };
    window.addEventListener('keydown', handleKey);
    return () => window.removeEventListener('keydown', handleKey);
  }, [startCamera, stopCamera]);

  // Update status when camera/face state changes
  useEffect(() => {
    if (cameraError) {
      setStatusMsg('Camera denied or unavailable');
    } else if (cameraActive && faceDetected) {
      setStatusMsg('Face detected · Projecting · Press C to stop camera');
    } else if (cameraActive && !faceDetected) {
      setStatusMsg('Camera active · No face detected · Press C to stop');
    } else if (!cameraActive) {
      setStatusMsg('Click anywhere to cycle patterns');
    }
  }, [cameraActive, faceDetected, cameraError]);

  const handleClick = () => {
    if (!cameraActiveRef.current || !faceDetectedRef.current) {
      patternTypeRef.current = (patternTypeRef.current + 1) % patternTypes.length;
    }
  };

  const handleMouseMove = (e) => {
    mousePosRef.current = { x: e.clientX, y: e.clientY };
  };

  const cameraButtonBg = buttonHover || cameraActive
    ? 'rgba(0,0,0,0.12)'
    : 'rgba(0,0,0,0.05)';

  return (
    <div
      style={{
        margin: 0,
        padding: 0,
        background: BACKGROUND_COLOR,
        overflow: 'hidden',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        height: '100vh',
        width: '100vw',
        position: 'relative'
      }}
      onMouseMove={handleMouseMove}
      onMouseDown={() => { mouseDownRef.current = true; }}
      onMouseUp={() => { mouseDownRef.current = false; }}
      onClick={handleClick}
      ref={containerRef}
    >
      <video
        ref={videoRef}
        style={{ position: 'absolute', opacity: 0, pointerEvents: 'none', width: 1, height: 1 }}
        playsInline
        muted
      />
      <canvas
        ref={canvasRef}
        style={{ position: 'absolute', opacity: 0, pointerEvents: 'none', width: 1, height: 1 }}
      />

      {cameraActive && (
        <div style={{
          position: 'absolute',
          top: 16,
          right: 16,
          display: 'flex',
          alignItems: 'center',
          gap: 8,
          padding: '6px 14px',
          background: 'rgba(0,0,0,0.06)',
          borderRadius: 20,
          fontSize: 12,
          fontFamily: 'monospace',
          color: '#555',
          userSelect: 'none',
          pointerEvents: 'none'
        }}>
          <div style={{
            width: 8,
            height: 8,
            borderRadius: '50%',
            background: faceDetected ? '#4a7' : '#c55',
            boxShadow: faceDetected ? '0 0 6px #4a7' : '0 0 6px #c55',
            transition: 'all 0.3s ease'
          }} />
          {faceDetected ? 'FACE DETECTED' : 'SCANNING'}
        </div>
      )}

      <pre
        ref={preRef}
        style={{
          fontFamily: 'monospace',
          fontSize: '12px',
          lineHeight: '1',
          letterSpacing: '0.1em',
          color: '#333',
          userSelect: 'none',
          cursor: 'pointer',
          margin: 0,
          padding: 0
        }}
      />

      <div
        role="status"
        aria-live="polite"
        style={{
          position: 'absolute',
          bottom: 16,
          fontSize: 11,
          fontFamily: 'monospace',
          color: '#999',
          userSelect: 'none',
          pointerEvents: 'none',
          textAlign: 'center',
          letterSpacing: '0.05em'
        }}
      >
        {statusMsg}
      </div>

      <button
        onClick={(e) => {
          e.stopPropagation();
          if (cameraActive) {
            stopCamera();
            cameraFrameRef.current = null;
          } else {
            startCamera();
          }
        }}
        aria-label={cameraActive ? 'Stop camera' : 'Enable camera'}
        style={{
          position: 'absolute',
          top: 16,
          left: 16,
          background: cameraButtonBg,
          border: '1px solid rgba(0,0,0,0.1)',
          borderRadius: 20,
          padding: '6px 14px',
          fontSize: 12,
          fontFamily: 'monospace',
          color: '#555',
          cursor: 'pointer',
          transition: 'all 0.2s ease',
          userSelect: 'none'
        }}
        onMouseEnter={() => setButtonHover(true)}
        onMouseLeave={() => setButtonHover(false)}
      >
        {cameraActive ? '⏹ Stop Camera' : '📷 Enable Camera'}
      </button>

      {cameraError && (
        <div style={{
          position: 'absolute',
          top: 52,
          left: 16,
          fontSize: 10,
          fontFamily: 'monospace',
          color: '#c55',
          maxWidth: 200,
          userSelect: 'none'
        }}>
          {cameraError}
        </div>
      )}
    </div>
  );
};

export default CameraAsciiProjection;
