(() => {
  const activeCard = document.getElementById('activeMatchCard');
  const messageModal = document.getElementById('messageModal');
  const ratingModal = document.getElementById('ratingModal');
  const messageList = document.getElementById('messageList');
  const messageForm = document.getElementById('messageForm');
  const messageBody = document.getElementById('messageBody');
  const ratingForm = document.getElementById('ratingForm');
  const ratingMatchId = document.getElementById('ratingMatchId');
  const ratingStarsLegacy = document.getElementById('ratingStarsLegacy');
  let activeMatchData = null;
  let activeMatchId = null;
  let messagePoll = null;
  let activePoll = null;

  const esc = value => String(value ?? '').replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[ch]));
  const mapsUrl = (lat, lng) => `https://www.google.com/maps/dir/?api=1&destination=${encodeURIComponent(`${lat},${lng}`)}`;

  function closeMessageModal() {
    if (messageModal) window.closeModal?.(messageModal);
    if (messagePoll) clearInterval(messagePoll);
    messagePoll = null;
  }

  async function loadMessages() {
    if (!activeMatchId || !messageList) return;
    const response = await fetch(`/api/matches/${activeMatchId}/messages`);
    if (response.status === 401) { window.location.href = '/auth/login'; return; }
    if (!response.ok) return;
    const data = await response.json();
    messageList.innerHTML = data.items?.length
      ? data.items.map(item => `<article class="message ${item.sender_id === window.SHARECIRCLE_USER_ID ? 'own' : ''}"><div class="message-bubble"><strong>${esc(item.full_name)}</strong><p>${esc(item.body).replace(/\n/g, '<br>')}</p><small>${esc(String(item.created_at || '').slice(11, 16))}</small></div></article>`).join('')
      : '<div class="mini-empty">No messages yet. Start the overlap.</div>';
    messageList.scrollTop = messageList.scrollHeight;
  }

  document.querySelectorAll('[data-open-messages]').forEach(button => button.addEventListener('click', async () => {
    activeMatchId = Number(button.dataset.openMessages);
    window.openModal?.(messageModal, button);
    await loadMessages();
    await fetch(`/api/matches/${activeMatchId}/messages/seen`, {method:'POST'});
    if (messagePoll) clearInterval(messagePoll);
    messagePoll = setInterval(loadMessages, 3000);
  }));

  document.querySelectorAll('[data-close-modal]').forEach(button => button.addEventListener('click', () => {
    const modal = button.closest('.modal-backdrop');
    if (modal === messageModal) closeMessageModal();
  }));

  messageForm?.addEventListener('submit', async event => {
    event.preventDefault();
    const body = messageBody?.value.trim();
    if (!body || !activeMatchId) return;
    const button = messageForm.querySelector('button[type="submit"]');
    button.disabled = true;
    const response = await fetch(`/api/matches/${activeMatchId}/messages`, {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({body})
    });
    if (response.status === 401) { window.location.href = '/auth/login'; return; }
    if (!response.ok) {
      const data = await response.json().catch(() => ({}));
      window.showToast?.(data.error || 'Message could not be sent.', 'error');
    } else {
      messageBody.value = '';
      await loadMessages();
    }
    button.disabled = false;
  });

  messageBody?.addEventListener('input', () => { const counter=document.getElementById('messageBodyCount'); if(counter) counter.textContent=`${messageBody.value.length}/1000`; });

  messageBody?.addEventListener('keydown', event => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      messageForm?.requestSubmit();
    }
  });

  document.querySelectorAll('[data-open-rating]').forEach(button => button.addEventListener('click', () => {
    ratingMatchId.value = button.dataset.openRating;
    window.openModal?.(ratingModal, button);
  }));

  document.querySelectorAll('.dashboard-rating-stars input').forEach(input => input.addEventListener('change', () => {
    const hidden = document.getElementById('ratingStars');
    if (hidden) hidden.value = input.value; if (ratingStarsLegacy) ratingStarsLegacy.value = input.value;
  }));
  document.querySelectorAll('[data-dashboard-rating-tag]').forEach(tag => tag.addEventListener('click', () => {
    const box = document.getElementById('ratingComment');
    if (!box) return;
    box.value = box.value ? `${box.value}, ${tag.dataset.dashboardRatingTag}` : tag.dataset.dashboardRatingTag;
    tag.classList.toggle('active');
  }));

  ratingForm?.addEventListener('submit', async event => {
    event.preventDefault();
    const response = await fetch('/api/ratings', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({
        match_id:Number(ratingMatchId.value),
        stars:Number(document.getElementById('ratingStars')?.value || 5),
        comment:document.getElementById('ratingComment')?.value || ''
      })
    });
    if (response.status === 401) { window.location.href = '/auth/login'; return; }
    const data = await response.json().catch(() => ({}));
    if (!response.ok) { window.showToast?.(data.error || 'Rating could not be saved.', 'error'); return; }
    window.closeModal?.(ratingModal);
    window.showToast?.('Rating saved.', 'success');
  });

  function openConfirm({title, body, confirmLabel = 'Confirm'}) {
    return new Promise(resolve => {
      const backdrop = document.createElement('div');
      backdrop.className = 'modal-backdrop';
      backdrop.innerHTML = `<div class="modal-card" role="dialog" aria-modal="true" aria-labelledby="deleteConfirmTitle"><div class="modal-head"><div><span class="eyebrow">CONFIRM</span><h2 id="deleteConfirmTitle">${esc(title)}</h2></div><button class="icon-btn" type="button" data-local-close aria-label="Close"><svg class="ui-icon" aria-hidden="true"><use href="#icon-x"></use></svg></button></div><p class="muted">${esc(body)}</p><div class="match-confirm-actions"><button class="btn btn-ghost" data-local-close type="button">Keep it</button><button class="btn btn-primary" data-local-confirm type="button">${esc(confirmLabel)}</button></div></div>`;
      document.body.appendChild(backdrop);
      const close = value => { window.closeModal?.(backdrop); backdrop.remove(); resolve(value); };
      window.openModal?.(backdrop);
      backdrop.querySelectorAll('[data-local-close]').forEach(button => button.addEventListener('click', () => close(false), {once:true}));
      backdrop.querySelector('[data-local-confirm]')?.addEventListener('click', () => close(true), {once:true});
      backdrop.addEventListener('click', event => { if (event.target === backdrop) close(false); }, {once:true});
    });
  }

  async function runItemAction(action) {
    const type = action.dataset.itemType;
    const id = Number(action.dataset.itemId);
    const verb = action.dataset.itemAction;
    if (verb === 'delete') {
      const confirmed = await openConfirm({title:'Delete this item?', body:'This removes it from your circle and cannot be undone.', confirmLabel:'Delete'});
      if (!confirmed) return;
    }
    action.disabled = true;
    const response = await fetch(`/api/${type}s/${id}/${verb}`, {method:'POST'});
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      action.disabled = false;
      window.showToast?.(data.error || 'That action could not be completed.', 'error');
      return;
    }
    window.showToast?.(verb === 'delete' ? 'Item deleted.' : 'Item status updated.', 'success');
    window.location.reload();
  }

  document.addEventListener('click', event => {
    const menuBtn = event.target.closest('[data-card-menu]');
    if (menuBtn) {
      const menu = menuBtn.parentElement.querySelector('.card-menu-pop');
      document.querySelectorAll('.card-menu-pop').forEach(item => { if (item !== menu) item.hidden = true; });
      if (menu) menu.hidden = !menu.hidden;
      return;
    }
    const itemAction = event.target.closest('[data-item-action]');
    if (itemAction) runItemAction(itemAction);
  });

  function renderActiveActions(data) {
    if (!activeCard || !data) return;
    const actions = activeCard.querySelector('[data-active-actions]');
    if (!actions) return;
    const owner = data.viewer_role === 'need_owner';
    const need = data.need || {};
    const maps = (need.lat != null && need.lng != null) ? `<a class="btn btn-primary btn-small" target="_blank" rel="noopener noreferrer" href="${mapsUrl(need.lat, need.lng)}">Open directions</a>` : '';
    if (data.status === 'accepted') {
      actions.innerHTML = owner ? `<a class="btn btn-secondary btn-small" href="/match/${data.id}">Open match</a>` : `${maps}<button class="btn btn-secondary btn-small" type="button" data-dashboard-arrive>I've arrived</button>`;
    } else if (data.status === 'arrived') {
      actions.innerHTML = `<a class="btn btn-primary btn-small" href="/match/${data.id}">${owner ? 'Record payment' : 'Open active match'}</a>`;
    } else if (data.status === 'paid') {
      if (owner && data.otp) {
        actions.innerHTML = `<div class="dashboard-otp-inline"><div><span>6-DIGIT OTP</span><strong data-dashboard-otp-value aria-live="polite">••••••</strong><small>Show it to your helper after the handoff.</small></div><button type="button" class="btn btn-secondary btn-small" data-show-dashboard-otp>Reveal</button><button type="button" class="btn btn-ghost btn-small" data-copy-dashboard-otp hidden>Copy</button></div><a class="btn btn-secondary btn-small" href="/match/${data.id}">Open match</a>`;
      } else {
        actions.innerHTML = `<a class="btn btn-primary btn-small" href="/match/${data.id}">Enter OTP</a>`;
      }
    } else if (data.status === 'completed') {
      actions.innerHTML = `<a class="btn btn-secondary btn-small" href="/match/${data.id}">View completed match</a><a class="btn btn-primary btn-small" href="/match/${data.id}/receipt">Impact receipt</a>`;
    } else {
      actions.innerHTML = `<a class="btn btn-secondary btn-small" href="/match/${data.id}">Open match</a>`;
    }
    wireActiveActions();
  }

  function wireActiveActions() {
    const arrive = activeCard?.querySelector('[data-dashboard-arrive]');
    arrive?.addEventListener('click', async () => {
      arrive.disabled = true;
      arrive.classList.add('is-loading');
      const response = await fetch(`/api/matches/${activeMatchId}/arrive`, {method:'POST'});
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        arrive.disabled = false;
        arrive.classList.remove('is-loading');
        window.showToast?.(data.error || 'Could not mark arrival.', 'error');
        return;
      }
      window.showToast?.('Arrival marked.', 'success');
      refreshActiveMatch();
    });
    activeCard?.querySelector('[data-show-dashboard-otp]')?.addEventListener('click', button => {
      const value = activeCard.querySelector('[data-dashboard-otp-value]');
      const copy = activeCard.querySelector('[data-copy-dashboard-otp]');
      if (!value || !activeMatchData?.otp) return;
      value.textContent = activeMatchData.otp;
      button.currentTarget.hidden = true;
      if (copy) copy.hidden = false;
    });
    activeCard?.querySelector('[data-copy-dashboard-otp]')?.addEventListener('click', async () => {
      if (!activeMatchData?.otp) return;
      try {
        await navigator.clipboard.writeText(activeMatchData.otp);
        window.showToast?.('OTP copied.', 'success');
      } catch (_) {
        window.showToast?.('Copy failed. Read the OTP aloud.', 'error');
      }
    });
  }

  async function refreshActiveMatch() {
    if (!activeCard) return;
    const response = await fetch('/api/matches/active');
    if (response.status === 401) { window.location.href = '/auth/login'; return; }
    if (!response.ok) return;
    const data = await response.json();
    if (!data.match) return;
    activeMatchData = data.match;
    activeMatchId = Number(data.match.id);
    activeCard.dataset.status = data.match.status;
    const headStatus = activeCard.querySelector('.active-match-head p');
    if (headStatus) headStatus.textContent = `${data.match.need?.category || 'Match'} · ${String(data.match.status).replace('_',' ')}`;
    const title = activeCard.querySelector('[data-active-copy-title]');
    const copy = activeCard.querySelector('[data-active-copy-body]');
    const messages = {
      accepted: ['Accepted.','The next move is arrival.'],
      arrived: ['Arrived.','The handoff is underway.'],
      paid: ['Payment recorded.','Finish with the 6-digit OTP.'],
      completed: ['Completed.','Your impact is now part of the community receipt.']
    }[data.match.status];
    if (messages && title && copy) { title.textContent = messages[0]; copy.textContent = messages[1]; }
    renderActiveActions(data.match);
  }

  if (activeCard) {
    activeMatchId = Number(activeCard.dataset.activeMatchId);
    refreshActiveMatch();
    activePoll = setInterval(refreshActiveMatch, 5000);
    document.addEventListener('visibilitychange', () => {
      if (document.hidden) clearInterval(activePoll);
      else { refreshActiveMatch(); activePoll = setInterval(refreshActiveMatch, 5000); }
    });
  }

  window.addEventListener('pagehide', () => {
    clearInterval(activePoll);
    clearInterval(messagePoll);
  });
})();
