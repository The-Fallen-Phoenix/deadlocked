/**
 * Web Audio API Live Microphone Streamer & Visualizer for SENTRY
 */

class SentryAudioStreamer {
  constructor(options = {}) {
    this.sampleRate = 16000;
    this.chunkIntervalMs = options.chunkIntervalMs || 600;
    this.onAnalysisResult = options.onAnalysisResult || null;
    this.onError = options.onError || null;

    this.audioContext = null;
    this.mediaStream = null;
    this.analyser = null;
    this.processor = null;
    this.isStreaming = false;
    this.ws = null;
    this.audioBuffer = [];
    this.intervalHandle = null;
  }

  async startStream(claimedSpeakerId = null, transactionAmount = 0.0) {
    try {
      this.mediaStream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          sampleRate: this.sampleRate,
          echoCancellation: true,
          noiseSuppression: false
        }
      });

      this.audioContext = new (window.AudioContext || window.webkitAudioContext)({
        sampleRate: this.sampleRate
      });

      const source = this.audioContext.createMediaStreamSource(this.mediaStream);
      this.analyser = this.audioContext.createAnalyser();
      this.analyser.fftSize = 256;
      source.connect(this.analyser);

      // Audio processing node to collect raw PCM samples
      this.processor = this.audioContext.createScriptProcessor(4096, 1, 1);
      this.analyser.connect(this.processor);
      this.processor.connect(this.audioContext.destination);

      this.audioBuffer = [];
      this.processor.onaudioprocess = (e) => {
        if (!this.isStreaming) return;
        const inputData = e.inputBuffer.getChannelData(0);
        this.audioBuffer.push(new Float32Array(inputData));
      };

      this.isStreaming = true;

      // Send audio chunk periodically
      this.intervalHandle = setInterval(() => {
        this._dispatchAudioChunk(claimedSpeakerId, transactionAmount);
      }, this.chunkIntervalMs);

      return true;
    } catch (err) {
      console.error('Failed to access microphone:', err);
      if (this.onError) this.onError(err);
      return false;
    }
  }

  stopStream() {
    this.isStreaming = false;
    if (this.intervalHandle) {
      clearInterval(this.intervalHandle);
      this.intervalHandle = null;
    }
    if (this.processor) {
      this.processor.disconnect();
      this.processor = null;
    }
    if (this.analyser) {
      this.analyser.disconnect();
      this.analyser = null;
    }
    if (this.audioContext) {
      this.audioContext.close();
      this.audioContext = null;
    }
    if (this.mediaStream) {
      this.mediaStream.getTracks().forEach(track => track.stop());
      this.mediaStream = null;
    }
    this.audioBuffer = [];
  }

  drawWaveform(canvas) {
    if (!this.analyser || !canvas) return;
    const ctx = canvas.getContext('2d');
    const width = canvas.width = canvas.offsetWidth;
    const height = canvas.height = canvas.offsetHeight;

    const bufferLength = this.analyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);

    const render = () => {
      if (!this.isStreaming) {
        ctx.clearRect(0, 0, width, height);
        // Draw flat idle line
        ctx.strokeStyle = 'rgba(6, 182, 212, 0.3)';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(0, height / 2);
        ctx.lineTo(width, height / 2);
        ctx.stroke();
        return;
      }

      requestAnimationFrame(render);
      this.analyser.getByteTimeDomainData(dataArray);

      ctx.fillStyle = 'rgba(7, 11, 20, 0.4)';
      ctx.fillRect(0, 0, width, height);

      ctx.lineWidth = 2;
      ctx.strokeStyle = '#06b6d4';
      ctx.shadowBlur = 8;
      ctx.shadowColor = '#06b6d4';
      ctx.beginPath();

      const sliceWidth = width * 1.0 / bufferLength;
      let x = 0;

      for (let i = 0; i < bufferLength; i++) {
        const v = dataArray[i] / 128.0;
        const y = v * height / 2;
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
        x += sliceWidth;
      }

      ctx.lineTo(width, height / 2);
      ctx.stroke();
      ctx.shadowBlur = 0;
    };

    render();
  }

  async _dispatchAudioChunk(claimedSpeakerId, transactionAmount) {
    if (this.audioBuffer.length === 0) return;

    // Merge collected buffers
    let totalLength = 0;
    for (const buf of this.audioBuffer) totalLength += buf.length;
    const merged = new Float32Array(totalLength);
    let offset = 0;
    for (const buf of this.audioBuffer) {
      merged.set(buf, offset);
      offset += buf.length;
    }
    this.audioBuffer = []; // Clear for next interval

    // Convert Float32Array to 16-bit PCM WAV base64
    const wavBase64 = this._encodeWAVBase64(merged, this.sampleRate);

    try {
      const resp = await fetch('/api/analyze/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          audio_base64: wavBase64,
          claimed_speaker_id: claimedSpeakerId,
          transaction_amount_inr: parseFloat(transactionAmount || 0.0)
        })
      });

      if (resp.ok) {
        const data = await resp.json();
        if (this.onAnalysisResult) this.onAnalysisResult(data);
      }
    } catch (e) {
      console.warn('Stream chunk analysis error:', e);
    }
  }

  _encodeWAVBase64(samples, sampleRate) {
    const buffer = new ArrayBuffer(44 + samples.length * 2);
    const view = new DataView(buffer);

    // RIFF chunk descriptor
    this._writeString(view, 0, 'RIFF');
    view.setUint32(4, 36 + samples.length * 2, true);
    this._writeString(view, 8, 'WAVE');

    // fmt sub-chunk
    this._writeString(view, 12, 'fmt ');
    view.setUint32(16, 16, true);
    view.setUint16(20, 1, true); // PCM
    view.setUint16(22, 1, true); // Mono
    view.setUint32(24, sampleRate, true);
    view.setUint32(28, sampleRate * 2, true);
    view.setUint16(32, 2, true); // block align
    view.setUint16(34, 16, true); // bits per sample

    // data sub-chunk
    this._writeString(view, 36, 'data');
    view.setUint32(40, samples.length * 2, true);

    // Write PCM samples
    let index = 44;
    for (let i = 0; i < samples.length; i++) {
      const s = Math.max(-1, Math.min(1, samples[i]));
      view.setInt16(index, s < 0 ? s * 0x8000 : s * 0x7FFF, true);
      index += 2;
    }

    // Convert arrayBuffer to base64
    let binary = '';
    const bytes = new Uint8Array(buffer);
    for (let i = 0; i < bytes.byteLength; i++) {
      binary += String.fromCharCode(bytes[i]);
    }
    return window.btoa(binary);
  }

  _writeString(view, offset, string) {
    for (let i = 0; i < string.length; i++) {
      view.setUint8(offset + i, string.charCodeAt(i));
    }
  }
}

window.SentryAudioStreamer = SentryAudioStreamer;
