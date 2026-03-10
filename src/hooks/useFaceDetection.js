import { useState, useRef, useCallback, useEffect } from 'react';

let haarFileLoaded = false;

export function useFaceDetection(videoRef, cameraActive) {
  const [faceDetected, setFaceDetected] = useState(false);
  const classifierRef = useRef(null);
  const detCanvasRef = useRef(null);

  // Initialize OpenCV and load Haar cascade classifier
  useEffect(() => {
    let cancelled = false;

    const initOpenCV = async () => {
      const waitForCV = () => new Promise((resolve) => {
        if (window.cv && window.cv.Mat) { resolve(); return; }
        if (window.cv) { window.cv['onRuntimeInitialized'] = resolve; return; }
        const interval = setInterval(() => {
          if (window.cv && window.cv.Mat) {
            clearInterval(interval);
            resolve();
          } else if (window.cv) {
            clearInterval(interval);
            window.cv['onRuntimeInitialized'] = resolve;
          }
        }, 200);
      });

      try {
        await waitForCV();
        if (cancelled) return;

        const cv = window.cv;

        if (!haarFileLoaded) {
          const resp = await fetch('/haarcascade_frontalface_default.xml');
          const buf = await resp.arrayBuffer();
          if (cancelled) return;

          const data = new Uint8Array(buf);
          cv.FS_createDataFile('/', 'haarcascade.xml', data, true, false, false);
          haarFileLoaded = true;
        }

        const classifier = new cv.CascadeClassifier();
        classifier.load('haarcascade.xml');
        classifierRef.current = classifier;
      } catch (err) {
        console.warn('OpenCV init failed:', err);
      }
    };

    initOpenCV();
    return () => {
      cancelled = true;
      if (classifierRef.current) {
        classifierRef.current.delete();
        classifierRef.current = null;
      }
    };
  }, []);

  const runFaceDetection = useCallback(() => {
    const video = videoRef.current;
    if (!video || video.readyState < 2 || !classifierRef.current || !window.cv) return;

    const cv = window.cv;

    // Reuse a single canvas for detection instead of creating one per call
    if (!detCanvasRef.current) {
      detCanvasRef.current = document.createElement('canvas');
      detCanvasRef.current.width = 320;
      detCanvasRef.current.height = 240;
    }

    const detCtx = detCanvasRef.current.getContext('2d', { willReadFrequently: true });
    detCtx.drawImage(video, 0, 0, 320, 240);
    const imageData = detCtx.getImageData(0, 0, 320, 240);

    let src, gray, faces, minSize, maxSize;
    try {
      src = cv.matFromImageData(imageData);
      gray = new cv.Mat();
      cv.cvtColor(src, gray, cv.COLOR_RGBA2GRAY);
      faces = new cv.RectVector();
      minSize = new cv.Size(40, 40);
      maxSize = new cv.Size(0, 0);
      classifierRef.current.detectMultiScale(
        gray, faces, 1.1, 4, 0, minSize, maxSize
      );
      setFaceDetected(faces.size() > 0);
    } catch {
      // ignore detection errors
    } finally {
      if (src) src.delete();
      if (gray) gray.delete();
      if (faces) faces.delete();
      if (minSize) minSize.delete();
      if (maxSize) maxSize.delete();
    }
  }, [videoRef]);

  // Run face detection at 500ms intervals when camera is active
  useEffect(() => {
    if (!cameraActive) {
      setFaceDetected(false);
      return;
    }
    const intervalId = setInterval(runFaceDetection, 500);
    return () => clearInterval(intervalId);
  }, [cameraActive, runFaceDetection]);

  return { faceDetected };
}
