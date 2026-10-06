/**
 * VoxPlayer SDK v1.0
 * Speed-invariant lip sync playback via animation manifest.
 *
 * Usage:
 *   const player = new VoxPlayer('container-id', { manifestUrl: '...' });
 *   player.play();
 */

class VoxPlayer {
  constructor(containerId, options = {}) {
    this.container = document.getElementById(containerId);
    this.manifestUrl = options.manifestUrl;
    this.width = options.width || 854;
    this.height = options.height || 480;
    this.showControls = options.controls !== false;

    this.manifest = null;
    this.video = null;
    this.canvas = null;
    this.ctx = null;
    this.animFrame = null;
    this.isPlaying = false;
    this.currentRate = 1.0;

    this._init();
  }

  async _init() {
    this.container.innerHTML = `
      <div style="position:relative;width:${this.width}px;height:${this.height}px;background:#000;border-radius:8px;overflow:hidden;">
        <video id="vp-video" crossorigin="anonymous"
               style="display:none;width:100%;height:100%"></video>
        <canvas id="vp-canvas" width="${this.width}" height="${this.height}"
                style="display:block;width:100%;height:100%"></canvas>
        <div id="vp-loading" style="position:absolute;inset:0;display:flex;align-items:center;
             justify-content:center;color:white;font-family:sans-serif;background:#0a0a0f;">
          Loading player...
        </div>
        <div id="vp-controls" style="position:absolute;bottom:0;left:0;right:0;
             background:linear-gradient(transparent,rgba(0,0,0,0.7));padding:12px 16px;
             display:flex;align-items:center;gap:12px;">
          <button id="vp-play-btn" onclick="window._vp_${this._id()}.togglePlay()"
                  style="background:none;border:none;color:white;font-size:18px;cursor:pointer;">▶</button>
          <div style="flex:1;height:4px;background:rgba(255,255,255,0.2);border-radius:2px;cursor:pointer"
               id="vp-progress-bar" onclick="window._vp_${this._id()}.seekBar(event)">
            <div id="vp-progress-fill" style="height:100%;background:#6c63ff;border-radius:2px;width:0%"></div>
          </div>
          <span id="vp-time" style="color:white;font-size:12px;font-family:monospace;min-width:80px">0:00 / 0:00</span>
          <div style="display:flex;gap:4px">
            ${[0.5, 1.0, 1.5, 2.0].map(r =>
              `<button onclick="window._vp_${this._id()}.setRate(${r})"
               id="vp-rate-${String(r).replace('.','')}"
               style="background:rgba(255,255,255,0.15);border:none;color:white;
                      padding:3px 8px;border-radius:4px;font-size:11px;cursor:pointer">${r}x</button>`
            ).join('')}
          </div>
        </div>
      </div>
    `;

    window[`_vp_${this._id()}`] = this;

    this.video = this.container.querySelector('#vp-video');
    this.canvas = this.container.querySelector('#vp-canvas');
    this.ctx = this.canvas.getContext('2d');

    if (this.manifestUrl) {
      await this._loadManifest();
    }
  }

  async _loadManifest() {
    try {
      const resp = await fetch(this.manifestUrl);
      this.manifest = await resp.json();

      this.video.src = this.manifest.base_video_url;
      await new Promise(resolve => { this.video.onloadedmetadata = resolve; });

      this.container.querySelector('#vp-loading').style.display = 'none';

      this.video.addEventListener('timeupdate', () => this._updateProgressBar());
      this.video.addEventListener('play', () => {
        this.isPlaying = true;
        this.container.querySelector('#vp-play-btn').textContent = '⏸';
        this._renderLoop();
      });
      this.video.addEventListener('pause', () => {
        this.isPlaying = false;
        this.container.querySelector('#vp-play-btn').textContent = '▶';
        if (this.animFrame) cancelAnimationFrame(this.animFrame);
      });
      this.video.addEventListener('ended', () => {
        this.isPlaying = false;
        this.container.querySelector('#vp-play-btn').textContent = '▶';
      });

    } catch (err) {
      this.container.querySelector('#vp-loading').textContent = 'Failed to load manifest';
      console.error('VoxPlayer manifest load error:', err);
    }
  }

  _renderLoop() {
    if (!this.isPlaying) return;

    this.ctx.drawImage(this.video, 0, 0, this.width, this.height);

    const currentMs = this.video.currentTime * 1000;
    const segment = this._findSegment(currentMs);

    if (segment && !this._isSkipped(currentMs)) {
      const next = this._findNextSegment(currentMs);
      const weights = this._interpolateWeights(segment, next, currentMs);
      this._renderBlendshape(segment, weights);
    }

    this.animFrame = requestAnimationFrame(() => this._renderLoop());
  }

  _findSegment(ms) {
    if (!this.manifest?.segments) return null;
    const segs = this.manifest.segments;
    for (let i = segs.length - 1; i >= 0; i--) {
      if (segs[i].timestamp_ms <= ms) return segs[i];
    }
    return null;
  }

  _findNextSegment(ms) {
    if (!this.manifest?.segments) return null;
    return this.manifest.segments.find(s => s.timestamp_ms > ms) || null;
  }

  _interpolateWeights(current, next, ms) {
    if (!next) return current.blend_weights;
    const t = Math.max(0, Math.min(1,
      (ms - current.timestamp_ms) / (next.timestamp_ms - current.timestamp_ms)
    ));
    const result = {};
    for (const key of Object.keys(current.blend_weights)) {
      const a = current.blend_weights[key] ?? 0;
      const b = next.blend_weights?.[key] ?? 0;
      result[key] = a + (b - a) * t;
    }
    return result;
  }

  _isSkipped(ms) {
    return (this.manifest?.skipped_ranges || []).some(
      r => ms >= r.start_ms && ms <= r.end_ms
    );
  }

  _renderBlendshape(segment, weights) {
    /**
     * Simplified blendshape rendering using Canvas 2D.
     * Full 3DMM rendering requires WebGL + face mesh.
     * This version applies visible jaw/lip deformation as a demonstration.
     *
     * Phase 3 full implementation:
     * - Load speaker face mesh (GLTF)
     * - Apply blend_weights to morph targets
     * - Render via WebGL onto canvas lip region
     * - Composite with CSS mix-blend-mode
     */
    const jawOpen = weights.jaw_open ?? 0;
    const lipStretch = weights.lip_corner_puller ?? 0;
    const lipRound = weights.lip_tightener ?? 0;

    if (jawOpen < 0.05 && lipStretch < 0.05) return;

    // Approximate lip region (bottom 35% of frame, center 60%)
    const lipX = this.width * 0.20;
    const lipY = this.height * 0.62;
    const lipW = this.width * 0.60;
    const lipH = this.height * 0.18;

    // This is a placeholder visual — replace with 3DMM WebGL renderer
    this.ctx.save();
    this.ctx.globalAlpha = Math.min(0.15, jawOpen * 0.2);
    this.ctx.fillStyle = '#000';
    const openH = lipH * jawOpen * 0.5;
    this.ctx.fillRect(lipX, lipY + lipH * 0.3, lipW, openH);
    this.ctx.restore();
  }

  _updateProgressBar() {
    const pct = this.video.duration
      ? (this.video.currentTime / this.video.duration) * 100
      : 0;
    const fill = this.container.querySelector('#vp-progress-fill');
    if (fill) fill.style.width = pct + '%';

    const timeEl = this.container.querySelector('#vp-time');
    if (timeEl) {
      timeEl.textContent = `${this._fmt(this.video.currentTime)} / ${this._fmt(this.video.duration)}`;
    }
  }

  _fmt(s) {
    if (!s || isNaN(s)) return '0:00';
    const m = Math.floor(s / 60);
    const sec = Math.floor(s % 60).toString().padStart(2, '0');
    return `${m}:${sec}`;
  }

  _id() {
    if (!this.__id) this.__id = Math.random().toString(36).slice(2, 8);
    return this.__id;
  }

  // Public API
  play() { this.video?.play(); }
  pause() { this.video?.pause(); }
  togglePlay() { this.isPlaying ? this.pause() : this.play(); }

  setRate(rate) {
    this.currentRate = rate;
    if (this.video) this.video.playbackRate = rate;
    [0.5, 1.0, 1.5, 2.0].forEach(r => {
      const btn = this.container.querySelector(`#vp-rate-${String(r).replace('.', '')}`);
      if (btn) {
        btn.style.background = r === rate
          ? '#6c63ff'
          : 'rgba(255,255,255,0.15)';
      }
    });
  }

  seekBar(e) {
    const bar = this.container.querySelector('#vp-progress-bar');
    const rect = bar.getBoundingClientRect();
    const pct = (e.clientX - rect.left) / rect.width;
    if (this.video?.duration) {
      this.video.currentTime = pct * this.video.duration;
    }
  }

  loadManifest(url) {
    this.manifestUrl = url;
    return this._loadManifest();
  }

  destroy() {
    if (this.animFrame) cancelAnimationFrame(this.animFrame);
    this.video?.pause();
    this.container.innerHTML = '';
    delete window[`_vp_${this._id()}`];
  }
}

if (typeof module !== 'undefined') module.exports = VoxPlayer;
