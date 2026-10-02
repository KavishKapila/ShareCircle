(() => {
  document.querySelectorAll('[data-explain]').forEach(button => button.addEventListener('click', () => {
    const panel = document.getElementById(`explain-${button.dataset.explain}`);
    if (panel) panel.hidden = !panel.hidden;
  }));

  document.addEventListener('click', async event => {
    const button = event.target.closest('[data-accept-need]');
    if (!button) return;
    const needId = Number(button.dataset.acceptNeed);
    button.disabled = true;
    button.classList.add('is-loading');
    const response = await fetch('/api/matches', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({need_id: needId}),
    });
    if (response.status === 401) {
      window.location.href = `/auth/login?next=${encodeURIComponent(window.location.pathname)}`;
      return;
    }
    if (!response.ok) {
      const data = await response.json().catch(() => ({error: 'Could not accept this need.'}));
      window.showToast?.(data.error || 'Could not accept this need.', 'error');
      button.disabled = false;
      button.classList.remove('is-loading');
      return;
    }
    const data = await response.json();
    window.showToast?.('Need accepted. Opening your active match.', 'success');
    window.location.href = `/match/${Number(data.id)}`;
  });
})();
