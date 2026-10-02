(() => {
  const params = new URLSearchParams(window.location.search);
  const state = {type: params.get('type') || 'needs', q: params.get('q') || '', category: params.get('category') || '', urgency: params.get('urgency') || '', sort: params.get('sort') || 'newest', page: Number(params.get('page') || 1)};
  const pageSize = 9;
  let allItems = [];
  let timer = null;
  const grid = document.getElementById('browseGrid');
  const search = document.getElementById('browseSearch');
  const category = document.getElementById('browseCategory');
  const urgency = document.getElementById('browseUrgency');
  const sort = document.getElementById('browseSort');
  const resultCount = document.getElementById('browseResultCount');
  const filterChips = document.getElementById('browseFilterChips');
  const loadMore = document.getElementById('browseLoadMore');
  const esc = value => String(value ?? '').replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[ch]));
  const icon = name => `<svg class="ui-icon" aria-hidden="true"><use href="#icon-${name}"></use></svg>`;

  function syncControls() {
    search.value = state.q;
    category.value = state.category;
    urgency.value = state.urgency;
    sort.value = state.sort;
    urgency.disabled = state.type !== 'needs';
    document.querySelectorAll('[data-browse-tab]').forEach(tab => {
      const active = tab.dataset.browseTab === state.type;
      tab.classList.toggle('active', active);
      tab.setAttribute('aria-selected', String(active));
    });
    document.querySelectorAll('[data-category-chip]').forEach(button => { const active = button.dataset.categoryChip === state.category; button.classList.toggle('active', active); button.setAttribute('aria-pressed', String(active)); });
    document.querySelectorAll('[data-urgency-chip]').forEach(button => { const active = button.dataset.urgencyChip === state.urgency; button.classList.toggle('active', active); button.setAttribute('aria-pressed', String(active)); });
  }

  function syncUrl() {
    const query = new URLSearchParams();
    Object.entries(state).forEach(([key, value]) => { if (value && !(key === 'page' && value === 1)) query.set(key, value); });
    history.replaceState(null, '', `${window.location.pathname}${query.toString() ? `?${query.toString()}` : ''}`);
  }

  function renderChips() {
    const chips = [];
    if (state.q) chips.push(['Search', state.q, 'q']);
    if (state.category) chips.push(['Category', state.category, 'category']);
    if (state.urgency) chips.push(['Urgency', state.urgency, 'urgency']);
    filterChips.innerHTML = chips.map(([label, value, key]) => `<button class="filter-chip" type="button" data-clear-filter="${key}">${esc(label)}: ${esc(value)} ${icon('x')}</button>`).join('');
  }

  function render() {
    renderChips();
    const visible = allItems.slice(0, state.page * pageSize);
    resultCount.textContent = `${allItems.length} result${allItems.length === 1 ? '' : 's'}`;
    loadMore.hidden = visible.length >= allItems.length;
    if (!visible.length) {
      grid.innerHTML = `<div class="empty-state"><div class="empty-art">${icon('ripple')}</div><h3>No results in this circle.</h3><p>Try another category, urgency, or search phrase.</p></div>`;
      return;
    }
    grid.innerHTML = visible.map((item, index) => {
      const link = state.type === 'needs' ? `/needs/${Number(item.id)}` : `/offers/${Number(item.id)}`;
      const urgencyLabel = state.type === 'needs' ? `<span class="badge badge-${esc(item.urgency)}">${icon(item.urgency === 'high' ? 'alert' : item.urgency === 'medium' ? 'flag' : 'leaf')} ${esc(item.urgency)}</span>` : `<span class="badge badge-success">${icon('check')} available</span>`;
      const accept = state.type === 'needs' ? `<button class="btn btn-primary btn-small" type="button" data-accept-need="${Number(item.id)}">${icon('plus')} Accept this need</button>` : '';
      const mapLink = item.lat != null && item.lng != null ? `<a class="btn btn-secondary btn-small" target="_blank" rel="noopener noreferrer" href="https://www.google.com/maps/dir/?api=1&destination=${encodeURIComponent(`${item.lat},${item.lng}`)}">${icon('pin')} Directions</a>` : '';
      const price = state.type === 'needs' && Number(item.price) > 0 ? `<span class="need-price-pill">₹${Number(item.price).toFixed(0)} · price set</span>` : '';
      return `<article class="item-card" style="--card-delay:${index * 40}ms"><div class="card-top"><span class="badge badge-category">${esc(item.category)}</span>${urgencyLabel}</div><div class="card-price-row">${price}</div><h3><a href="${link}">${esc(item.title)}</a></h3><p>${esc(item.description)}</p><div class="card-meta">${item.distance_km != null ? `${Number(item.distance_km).toFixed(1)} km away · ` : ''}${item.start_time && item.end_time ? `<span class=\"time-window-pill\">${esc(item.start_time)} → ${esc(item.end_time)}</span> · ` : ''}${esc(item.time_posted || 'Posted recently')} · <a href="/profile/${encodeURIComponent(item.username)}">${esc(item.full_name)}</a> · ${esc(item.location || 'Nearby')}</div><div class="browse-card-actions">${accept}${mapLink}<a class="btn btn-ghost btn-small" href="${link}">View details</a></div></article>`;
    }).join('');
  }

  async function load() {
    syncUrl();
    resultCount.textContent = 'Loading results…';
    grid.innerHTML = '<div class="card-skeleton-grid"><div class="skeleton skeleton-card"></div><div class="skeleton skeleton-card"></div><div class="skeleton skeleton-card"></div></div>';
    const query = new URLSearchParams({q:state.q, category:state.category, sort:state.sort, include_distance:'1'});
    if (state.type === 'needs') query.set('urgency', state.urgency);
    const response = await fetch(`/api/${state.type}?${query.toString()}`);
    if (response.status === 401) { window.location.href = '/auth/login?next=/browse'; return; }
    if (!response.ok) { grid.innerHTML = '<div class="mini-empty">Browse is temporarily unavailable.</div>'; return; }
    const data = await response.json();
    allItems = data.items || [];
    state.page = 1;
    render();
    syncControls();
    syncUrl();
  }

  const schedule = () => { clearTimeout(timer); timer = setTimeout(load, 260); };
  search.addEventListener('input', () => { state.q = search.value.trim(); state.page = 1; schedule(); });
  category.addEventListener('change', () => { state.category = category.value; load(); });
  urgency.addEventListener('change', () => { state.urgency = urgency.value; load(); });
  sort.addEventListener('change', () => { state.sort = sort.value; load(); });

  document.addEventListener('click', async event => {
    const categoryButton = event.target.closest('[data-category-chip]');
    if (categoryButton) { state.category = categoryButton.dataset.categoryChip; category.value = state.category; state.page = 1; syncControls(); load(); return; }
    const urgencyButton = event.target.closest('[data-urgency-chip]');
    if (urgencyButton) { state.urgency = urgencyButton.dataset.urgencyChip; urgency.value = state.urgency; state.page = 1; syncControls(); load(); return; }
    const tab = event.target.closest('[data-browse-tab]');
    if (tab) { state.type = tab.dataset.browseTab; state.page = 1; syncControls(); load(); return; }
    const clearFilter = event.target.closest('[data-clear-filter]');
    if (clearFilter) { state[clearFilter.dataset.clearFilter] = ''; state.page = 1; syncControls(); load(); return; }
    const accept = event.target.closest('[data-accept-need]');
    if (!accept) return;
    accept.disabled = true;
    accept.classList.add('is-loading');
    const response = await fetch('/api/matches', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({need_id:Number(accept.dataset.acceptNeed)})});
    if (response.status === 401) { window.location.href = `/auth/login?next=${encodeURIComponent(window.location.pathname)}`; return; }
    const data = await response.json().catch(() => ({}));
    if (!response.ok) { window.showToast?.(data.error || 'Could not accept this need.', 'error'); accept.disabled = false; accept.classList.remove('is-loading'); return; }
    window.showToast?.('Need accepted. Opening the overlap.', 'success');
    window.location.href = `/match/${Number(data.id)}`;
  });

  loadMore.addEventListener('click', () => { state.page += 1; render(); syncUrl(); });
  syncControls();
  load();
})();
