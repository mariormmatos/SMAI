// Run this once to generate PWA icons: node generate-icons.js
// Requires: npm install canvas
const { createCanvas } = require('canvas');
const fs = require('fs');
const path = require('path');

function generateIcon(size) {
  const canvas = createCanvas(size, size);
  const ctx = canvas.getContext('2d');
  const r = size * 0.12;

  // Background gradient
  const grad = ctx.createLinearGradient(0, 0, size, size);
  grad.addColorStop(0, '#2d1b5e');
  grad.addColorStop(1, '#0d1117');
  ctx.fillStyle = grad;
  roundRect(ctx, 0, 0, size, size, r);
  ctx.fill();

  // Emoji-style controller icon
  ctx.font = `${size * 0.55}px serif`;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText('🎮', size / 2, size / 2);

  return canvas.toBuffer('image/png');
}

function roundRect(ctx, x, y, w, h, r) {
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.lineTo(x + w - r, y);
  ctx.quadraticCurveTo(x + w, y, x + w, y + r);
  ctx.lineTo(x + w, y + h - r);
  ctx.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
  ctx.lineTo(x + r, y + h);
  ctx.quadraticCurveTo(x, y + h, x, y + h - r);
  ctx.lineTo(x, y + r);
  ctx.quadraticCurveTo(x, y, x + r, y);
  ctx.closePath();
}

const publicDir = path.join(__dirname, 'public');
fs.writeFileSync(path.join(publicDir, 'icon-192.png'), generateIcon(192));
fs.writeFileSync(path.join(publicDir, 'icon-512.png'), generateIcon(512));
console.log('Icons generated!');
