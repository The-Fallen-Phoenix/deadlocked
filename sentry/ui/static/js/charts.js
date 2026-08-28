/**
 * Charting & Visualizer Helpers for SENTRY Cyber-Defense Platform
 */

const Charts = {
  /**
   * Updates circular SVG risk gauge with color transitions
   */
  updateRiskGauge(circleElement, textElement, score, tier) {
    if (!circleElement || !textElement) return;

    // Circumference of r=70 is 2 * PI * 70 = ~440
    const circumference = 440;
    const offset = circumference - (score / 100) * circumference;
    circleElement.style.strokeDashoffset = offset;

    let color = '#10b981'; // Green (Low)
    if (score > 80) color = '#ef4444'; // Crimson (Critical)
    else if (score > 60) color = '#f97316'; // Orange (High)
    else if (score > 30) color = '#f59e0b'; // Amber (Moderate)

    circleElement.style.stroke = color;
    textElement.textContent = Math.round(score);
    textElement.style.color = color;
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
    ctx.strokeStyle = 'rgba(239, 68, 68, 0.3)';
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

      ctx.fillStyle = prob > 0.65 ? '#ef4444' : (prob > 0.4 ? '#f59e0b' : '#10b981');
      ctx.fillRect(x, y, barWidth, barH);
    });
  }
};

window.Charts = Charts;
