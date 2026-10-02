(() => {
  const startBtn = document.getElementById('judgeStartBtn');
  if (!startBtn) return;
  const resetBtn = document.getElementById('judgeResetBtn');
  const stage = document.getElementById('judgeStage');
  const narration = document.getElementById('judgeNarration');
  const progress = document.getElementById('judgeProgress');
  const ownerBody = document.getElementById('judgeOwnerBody');
  const helperBody = document.getElementById('judgeHelperBody');
  const linkBadge = document.getElementById('judgeLinkBadge');
  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const pause = reduced ? 220 : 2300;
  const steps = ['accepted','arrived','paid','completed','rated'];
  const esc = value => String(value ?? '').replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[ch]));
  const icon = name => `<svg class="ui-icon" aria-hidden="true"><use href="#icon-${name}"></use></svg>`;
  const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));

  function setProgress(step) {
    const index = steps.indexOf(step);
    progress.querySelectorAll('[data-step]').forEach(node => {
      const n = steps.indexOf(node.dataset.step);
      node.classList.toggle('active', n <= index);
      node.classList.toggle('current', n === index);
    });
  }

  function ownerCard(match) {
    const parts = [`<div class="judge-status-line">${icon('ripple')} ${esc(match.need.title)}</div>`];
    if (match.status === 'accepted') parts.push('<p class="muted">Waiting for the helper to arrive.</p>');
    if (match.status === 'arrived') parts.push('<p class="muted">Arrival is confirmed. Record the handoff payment.</p>');
    if (match.status === 'paid') {
      parts.push(`<p class="muted">Payment of ₹${Number(match.amount_paid || 0).toFixed(0)} recorded.</p>`);
      parts.push(`<div class="judge-otp-box"><span class="muted">SHARE THE OTP AT THE HANDOFF</span><strong>${esc(match.otp || '')}</strong></div>`);
    }
    if (match.status === 'completed' || match.rated) {
      parts.push(`<p class="muted">Payment of ₹${Number(match.amount_paid || 0).toFixed(0)} recorded.</p>`);
      parts.push(`<div class="judge-points">${icon('check')} Verified · +15 Impact Points</div>`);
      if (match.rated) parts.push(`<div class="judge-stars">${[1,2,3,4,5].map(() => '<svg class="ui-icon" aria-hidden="true"><use href="#icon-star"></use></svg>').join('')} <span class="muted">rated Arjun</span></div>`);
    }
    return parts.join('');
  }

  function helperCard(match) {
    const parts = [`<div class="judge-status-line">${icon('plus')} ${esc(match.offer.title)}</div>`];
    if (match.status === 'accepted') parts.push('<p class="muted">Heading to Priya’s location.</p>');
    if (match.status === 'arrived') parts.push('<p class="muted">Arrived. Deliver the service, then collect payment.</p>');
    if (match.status === 'paid') parts.push('<p class="muted">Payment is recorded. Ask Priya for the OTP.</p>');
    if (match.status === 'completed' || match.rated) {
      parts.push('<p class="muted">OTP verified. The handoff is confirmed.</p>');
      parts.push(`<div class="judge-points">${icon('check')} Verified · +20 Impact Points</div>`);
      if (match.rated) parts.push(`<div class="judge-stars">${[1,2,3,4,5].map(() => '<svg class="ui-icon" aria-hidden="true"><use href="#icon-star"></use></svg>').join('')} <span class="muted">rated Priya</span></div>`);
    }
    return parts.join('');
  }

  function render(match, text) {
    setProgress(match.rated ? 'rated' : match.status);
    ownerBody.innerHTML = ownerCard(match);
    helperBody.innerHTML = helperCard(match);
    if (text) narration.textContent = text;
    linkBadge.innerHTML = `<span class="judge-distance">${esc(match.distance_km)} km</span>`;
    linkBadge.style.transform = `rotate(${Number(match.bearing_deg || 0)}deg)`;
  }

  async function post(url, body) {
    const response = await fetch(url, {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:body ? JSON.stringify(body) : undefined
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(data.error || 'Judge Mode could not advance.');
    return data;
  }

  async function runDemo() {
    startBtn.disabled = true;
    startBtn.classList.add('is-loading');
    resetBtn.hidden = true;
    stage.hidden = false;
    progress?.setAttribute('aria-busy', 'true');
    try {
      const started = await post('/api/judge/start');
      render(started.match, started.narration);
      await sleep(pause);
      for (const step of ['arrive','pay','complete','rate']) {
        const result = await post(`/api/judge/advance/${started.match.id}`, {step});
        render(result.match, result.narration);
        await sleep(pause);
      }
      window.showToast?.('Judge demo complete.', 'success');
    } catch (error) {
      window.showToast?.(error.message, 'error');
    } finally {
      progress?.setAttribute('aria-busy', 'false');
      startBtn.disabled = false;
      startBtn.classList.remove('is-loading');
      resetBtn.hidden = false;
    }
  }

  startBtn.addEventListener('click', runDemo);
  resetBtn.addEventListener('click', runDemo);

  // Toolbar links use ?demo=1 so Judge Mode is immediately useful to a judge.
  // Still leaves the manual Run button available when opened directly.
  if (new URLSearchParams(window.location.search).get('demo') === '1') {
    window.setTimeout(() => startBtn.click(), 120);
  }
})();
