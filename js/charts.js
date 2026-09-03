/**
 * Charting & Visualizer Helpers for SENTRY (Pitch Black & Neon Orange Theme)
 */

const Charts = {
  /**
   * Updates circular SVG risk gauge with Neon Orange accent scheme
   */
  updateRiskGauge(circleElement, textElement, score, tier) {
    if (!circleElement || !textElement) return;

    // Circumference of r=70 is 2 * PI * 70 = ~440
    const circumference = 440;
    const offset = circumference - (score / 100) * circumference;
    circleElement.style.strokeDashoffset = offset;

    // Black & Neon Orange Theme Palette
    let color = '#ff8533';
    if (score > 80) color = '#ffffff';
    else if (score > 60) color = '#ff8533';
    else if (score > 30) color = '#ff6b00';

    circleElement.style.stroke = color;
    textElement.textContent = Math.round(score);
    textElement.style.color = '#ffffff';
  },

  /**
   * Draws temporal anomaly probability timeline on canvas
   */
  drawTemporalTimeline(canvas, slices) {
    if (!canvas || !slices || slices.length === 0) return;
    const ctx = canvas.getContext('2d');
    const width = canvas.width = canvas.offsetWidth;
    const height = canvas.height = canvas.offsetHeight;

    ctx.clearRect(0, 0, width, height);

    // Background grid
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.05)';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(0, height * 0.5); ctx.lineTo(width, height * 0.5);
    ctx.stroke();

    // Critical threshold line at 70%
    ctx.strokeStyle = 'rgba(255, 107, 0, 0.4)';
    ctx.setLineDash([4, 4]);
    ctx.beginPath();
    const thresholdY = height * (1 - 0.70);
    ctx.moveTo(0, thresholdY); ctx.lineTo(width, thresholdY);
    ctx.stroke();
    ctx.setLineDash([]);

    // Draw bars
    const barWidth = Math.max(width / slices.length - 3, 4);
    slices.forEach((s, idx) => {
      const x = idx * (width / slices.length);
      const prob = s.synthetic_prob;
      const barH = prob * (height - 10);
      const y = height - barH;

      ctx.fillStyle = prob > 0.65 ? '#ff8533' : (prob > 0.4 ? 'rgba(255, 107, 0, 0.7)' : 'rgba(255, 255, 255, 0.3)');
      ctx.fillRect(x, y, barWidth, barH);
    });
  }
};

window.Charts = Charts;
