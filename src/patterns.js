export const patterns = {
  balance: (x, y, t, w, h) => {
    const cx = w / 2;
    const cy = h / 2;
    const dx = x - cx;
    const dy = y - cy;
    const dist = Math.sqrt(dx * dx + dy * dy);
    return Math.sin(dx * 0.3 + t * 0.5) * Math.cos(dy * 0.3 + t * 0.3) *
      Math.sin(dist * 0.1 - t * 0.4);
  },
  duality: (x, y, t, w) => {
    const cx = w / 2;
    // Smooth blend factor: 0 on far left, 1 on far right, gradual transition at center
    const blend = 1 / (1 + Math.exp(-(x - cx) * 0.15));
    const left = Math.sin(x * 0.2 + t * 0.3);
    const right = Math.cos(x * 0.2 - t * 0.3);
    return (1 - blend) * left + blend * right + Math.sin(y * 0.3 + t * 0.2);
  },
  flow: (x, y, t, w, h) => {
    const cx = w / 2;
    const cy = h / 2;
    const angle = Math.atan2(y - cy, x - cx);
    const dist = Math.sqrt((x - cx) ** 2 + (y - cy) ** 2);
    return Math.sin(angle * 3 + t * 0.4) * Math.cos(dist * 0.1 - t * 0.3);
  },
  chaos: (x, y, t) => {
    const noise1 = Math.sin(x * 0.5 + t) * Math.cos(y * 0.3 - t);
    const noise2 = Math.sin(y * 0.4 + t * 0.5) * Math.cos(x * 0.2 + t * 0.7);
    const noise3 = Math.sin((x + y) * 0.2 + t * 0.8);
    return noise1 * 0.3 + noise2 * 0.3 + noise3 * 0.4;
  }
};

export const patternTypes = Object.keys(patterns);

export const ASCII_CHARS = ['█', '▓', '▒', '░', '·', ' '];

// Approximate pixel dimensions of a monospace character at 12px font
export const CHAR_WIDTH = 7.2;
export const CHAR_HEIGHT = 12;
