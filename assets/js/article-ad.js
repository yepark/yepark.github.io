(() => {
  const container = document.querySelector('.article-ad');
  const unit = container?.querySelector('.adsbygoogle');
  if (!unit) return;

  const updateStatus = () => {
    const status = unit.getAttribute('data-ad-status');
    if (status === 'unfilled') container.hidden = true;
    if (status === 'filled') {
      container.hidden = false;
      container.classList.add('article-ad--filled');
    }
  };
  const statusObserver = new MutationObserver(updateStatus);
  statusObserver.observe(unit, { attributes: true, attributeFilter: ['data-ad-status'] });
  updateStatus();

  let requested = false;
  const requestAd = () => {
    if (requested || container.hidden) return;
    requested = true;
    try {
      (window.adsbygoogle = window.adsbygoogle || []).push({});
    } catch {
      container.hidden = true;
    }
  };

  if ('IntersectionObserver' in window) {
    const observer = new IntersectionObserver(entries => {
      if (entries.some(entry => entry.isIntersecting)) {
        observer.disconnect();
        requestAd();
      }
    }, { rootMargin: '300px 0px' });
    observer.observe(container);
  } else {
    requestAd();
  }
})();
