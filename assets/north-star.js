(() => {
  const tiles = [...document.querySelectorAll('.ns-tile')];
  const panel = document.querySelector('.ns-focus');
  if (!tiles.length || !panel) return;
  const label = document.querySelector('#focus-label');
  const goal = document.querySelector('#focus-goal');
  const status = document.querySelector('.ns-status');
  const clear = document.querySelector('.ns-clear');
  const key = 'north-star:focus:v1';
  let active = null;
  function select(id, announce = true) {
    active = tiles.find(tile => tile.id === id) || null;
    tiles.forEach(tile => tile.setAttribute('aria-pressed', String(tile === active)));
    panel.hidden = !active;
    if (active) {
      label.textContent = active.firstElementChild.textContent;
      goal.textContent = 'In focus / ' + (active.id.startsWith('wealth-') ? 'Wealth' : 'YouTube');
      if (announce) status.textContent = label.textContent + ' is in focus. Selection stays on this device.';
    } else if (announce) {
      status.textContent = 'Focus cleared.';
    }
    try {
      if (active) localStorage.setItem(key, active.id);
      else localStorage.removeItem(key);
    } catch (_) {}
  }
  tiles.forEach(tile => tile.addEventListener('click', () => select(tile === active ? null : tile.id)));
  clear.addEventListener('click', () => {
    const previous = active;
    select(null);
    if (previous) previous.focus();
  });
  try { select(localStorage.getItem(key), false); } catch (_) {}
})();
