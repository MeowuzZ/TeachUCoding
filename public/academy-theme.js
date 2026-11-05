(() => {
  const root = document.documentElement;
  let saved;
  try { saved = localStorage.getItem('academy-theme'); } catch {}
  let theme = saved === 'light' || saved === 'dark' ? saved : 'light';
  const sheet = document.getElementById('dark-theme-sheet');
  const button = document.createElement('button');
  button.type = 'button';
  button.className = 'theme-toggle';
  function apply() {
    root.dataset.theme = theme;
    sheet.disabled = theme !== 'dark';
    button.textContent = theme === 'dark' ? '☀ 浅色' : '☾ 深色';
    button.setAttribute('aria-label', theme === 'dark' ? '切换为浅色模式' : '切换为深色模式');
    button.setAttribute('aria-pressed', String(theme === 'dark'));
    document.querySelector('meta[name="theme-color"]')?.setAttribute('content', theme === 'dark' ? '#14151d' : '#ffffff');
  }
  button.addEventListener('click', () => {
    theme = theme === 'dark' ? 'light' : 'dark';
    try { localStorage.setItem('academy-theme', theme); } catch {}
    apply();
  });
  apply();
  document.querySelector('.topbar').append(button);
})();
