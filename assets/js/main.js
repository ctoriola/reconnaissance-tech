(() => {
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => Array.from(r.querySelectorAll(s));

  // ---------- desktop mega menus: open on hover (with intent delay) or click
  const header = $('[data-header]');
  const items = $$('[data-menu]');
  const setOpen = (item, open) => {
    const btn = $('.nav-link', item);
    btn.setAttribute('aria-expanded', String(open));
    $('.mega', item).classList.toggle('is-open', open);
  };
  const closeMenus = (except) => items.forEach((it) => { if (it !== except) setOpen(it, false); });
  const syncHeader = () => header && header.classList.toggle('has-open', items.some((it) => $('.mega', it).classList.contains('is-open')));
  const canHover = matchMedia('(hover: hover) and (pointer: fine)').matches;
  items.forEach((item) => {
    const btn = $('.nav-link', item);
    let timer;
    btn.addEventListener('click', (ev) => {
      ev.stopPropagation();
      const open = btn.getAttribute('aria-expanded') !== 'true';
      closeMenus(item); setOpen(item, open); syncHeader();
    });
    if (canHover) {
      item.addEventListener('mouseenter', () => { clearTimeout(timer); timer = setTimeout(() => { closeMenus(item); setOpen(item, true); syncHeader(); }, 90); });
      item.addEventListener('mouseleave', () => { clearTimeout(timer); timer = setTimeout(() => { setOpen(item, false); syncHeader(); }, 180); });
    }
    // vertical category tabs inside the panel: hover, focus or arrow keys switch the link grid
    const tabs = $$('.mega-tab', item);
    const select = (tab) => tabs.forEach((t) => {
      const on = t === tab;
      t.setAttribute('aria-selected', String(on)); t.tabIndex = on ? 0 : -1;
      document.getElementById(t.getAttribute('aria-controls')).hidden = !on;
    });
    tabs.forEach((tab, i) => {
      tab.addEventListener('mouseenter', () => select(tab));
      tab.addEventListener('click', () => select(tab));
      tab.addEventListener('keydown', (ev) => {
        const step = { ArrowDown: 1, ArrowUp: -1 }[ev.key];
        if (!step) return;
        ev.preventDefault();
        const next = tabs[(i + step + tabs.length) % tabs.length];
        select(next); next.focus();
      });
    });
  });
  document.addEventListener('click', (ev) => { if (!ev.target.closest('[data-menu]')) { closeMenus(); syncHeader(); } });
  document.addEventListener('keydown', (ev) => {
    if (ev.key !== 'Escape') return;
    const open = items.find((it) => $('.nav-link', it).getAttribute('aria-expanded') === 'true');
    closeMenus(); syncHeader();
    if (open) $('.nav-link', open).focus();
    closeDrawer();
  });

  // ---------- header gains a glass background once the page scrolls
  if (header) {
    const onScroll = () => header.classList.toggle('is-scrolled', window.scrollY > 24);
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
  }

  // ---------- mobile drawer
  const drawer = $('#drawer');
  const burger = $('.site-header .burger');
  const openDrawer = () => {
    drawer.classList.add('is-open');
    burger.setAttribute('aria-expanded', 'true');
    document.body.style.overflow = 'hidden';
    $('[data-close]', drawer).focus();
  };
  function closeDrawer() {
    if (!drawer || !drawer.classList.contains('is-open')) return;
    drawer.classList.remove('is-open');
    burger.setAttribute('aria-expanded', 'false');
    document.body.style.overflow = '';
    burger.focus();
  }
  if (burger && drawer) {
    burger.addEventListener('click', openDrawer);
    $('[data-close]', drawer).addEventListener('click', closeDrawer);
  }

  // ---------- card rail: the hovered / focused card expands
  $$('[data-rail]').forEach((rail) => {
    const cards = $$('.rail-card', rail);
    const activate = (card) => cards.forEach((c) => c.classList.toggle('is-active', c === card));
    cards.forEach((card) => {
      card.addEventListener('mouseenter', () => activate(card));
      card.addEventListener('focusin', () => activate(card));
    });
  });

  // ---------- tabs (arrow-key navigation per WAI-ARIA)
  $$('[data-tabs]').forEach((root) => {
    const tabs = $$('[role="tab"]', root);
    const select = (tab) => {
      tabs.forEach((t) => {
        const on = t === tab;
        t.setAttribute('aria-selected', String(on));
        t.tabIndex = on ? 0 : -1;
        document.getElementById(t.getAttribute('aria-controls')).hidden = !on;
      });
    };
    tabs.forEach((tab, i) => {
      tab.addEventListener('click', () => select(tab));
      tab.addEventListener('keydown', (ev) => {
        const step = { ArrowRight: 1, ArrowLeft: -1 }[ev.key];
        if (!step) return;
        const next = tabs[(i + step + tabs.length) % tabs.length];
        select(next);
        next.focus();
      });
    });
  });

  // ---------- accordion rows: one open at a time per list
  $$('.rows').forEach((list) => {
    const rows = $$('details.row', list);
    rows.forEach((row) => row.addEventListener('toggle', () => {
      if (row.open) rows.forEach((r) => { if (r !== row) r.open = false; });
    }));
  });

  // ---------- reveal on scroll
  const reveals = $$('.reveal');
  if ('IntersectionObserver' in window) {
    const io = new IntersectionObserver((entries) => entries.forEach((en) => {
      if (en.isIntersecting) { en.target.classList.add('is-in'); io.unobserve(en.target); }
    }), { rootMargin: '0px 0px -8% 0px' });
    reveals.forEach((el) => io.observe(el));
  } else {
    reveals.forEach((el) => el.classList.add('is-in'));
  }

  // ---------- enquiry form: compose an email (static hosting has no backend)
  $$('form[data-enquiry]').forEach((form) => {
    form.addEventListener('submit', (ev) => {
      ev.preventDefault();
      if (!form.reportValidity()) return;
      const data = new FormData(form);
      const lines = [
        `Name: ${data.get('name')}`,
        `Email: ${data.get('email')}`,
        data.get('mobile') && `Mobile: ${data.get('mobile')}`,
        data.get('company') && `Company: ${data.get('company')}`,
        data.get('service') && `Interested service: ${data.get('service')}`,
        data.get('nda') && 'Requests a signed NDA: yes',
        '',
        data.get('message'),
      ].filter((l) => l !== null && l !== undefined && l !== false);
      const subject = `Website enquiry from ${data.get('name')}${data.get('company') ? ` (${data.get('company')})` : ''}`;
      window.location.href = `mailto:${form.dataset.to}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(lines.join('\n'))}`;
      const status = $('.form-status', form);
      if (status) status.textContent = 'Opening your email app… If nothing happens, write to ' + form.dataset.to;
    });
  });

  // ---------- hero video: respect reduced-motion / data-saver, and pause off-screen
  $$('.hero-video').forEach((video) => {
    const saveData = navigator.connection && navigator.connection.saveData;
    if (matchMedia('(prefers-reduced-motion: reduce)').matches || saveData) {
      video.removeAttribute('autoplay'); video.pause(); video.preload = 'none';
      return;
    }
    if ('IntersectionObserver' in window) {
      new IntersectionObserver(([en]) => {
        if (en.isIntersecting) video.play().catch(() => {}); else video.pause();
      }).observe(video);
    }
  });

  $$('[data-year]').forEach((el) => { el.textContent = new Date().getFullYear(); });
})();
