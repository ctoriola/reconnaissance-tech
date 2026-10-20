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

  const reduceMotion = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const finePointer = matchMedia('(hover: hover) and (pointer: fine)').matches;

  // ---------- smooth, inertial scrolling (Lenis); native scrolling if unavailable or reduced motion
  let lenis = null;
  if (window.Lenis && !reduceMotion) {
    lenis = new window.Lenis({ duration: 1.15, easing: (t) => 1 - Math.pow(1 - t, 4), smoothWheel: true, anchors: { offset: -90 } });
    const raf = (time) => { lenis.raf(time); requestAnimationFrame(raf); };
    requestAnimationFrame(raf);
    // in-page anchors glide instead of jumping
    $$('a[href^="#"]').forEach((a) => a.addEventListener('click', (ev) => {
      const target = a.getAttribute('href').length > 1 && document.querySelector(a.getAttribute('href'));
      if (!target) return;
      ev.preventDefault();
      lenis.scrollTo(target, { offset: -90 });
    }));
  }
  // the drawer and menus scroll on their own
  $$('.drawer, .mega, .rail').forEach((el) => el.setAttribute('data-lenis-prevent', ''));
  if (lenis && drawer && burger) {
    burger.addEventListener('click', () => lenis.stop());
    $('[data-close]', drawer).addEventListener('click', () => lenis.start());
    document.addEventListener('keydown', (ev) => { if (ev.key === 'Escape') lenis.start(); });
  }

  // ---------- accordion rows: height-animated, one open at a time per list
  const animateRow = (row, open) => {
    row._target = open;
    if (row._anim) row._anim.cancel();
    const summary = $('summary', row);
    if (reduceMotion) { row.open = open; return; }
    const start = row.offsetHeight;
    if (open) row.open = true;
    const end = open ? row.offsetHeight : summary.offsetHeight;
    row.style.overflow = 'hidden';
    row._anim = row.animate({ height: [`${start}px`, `${end}px`] }, { duration: open ? 560 : 420, easing: 'cubic-bezier(.22, 1, .36, 1)' });
    row._anim.onfinish = () => { if (!open) row.open = false; row.style.overflow = ''; row._anim = null; };
    row._anim.oncancel = () => { row.style.overflow = ''; };
  };
  $$('.rows').forEach((list) => {
    const rows = $$('details.row', list);
    rows.forEach((row) => $('summary', row).addEventListener('click', (ev) => {
      ev.preventDefault();
      const opening = !(row._target ?? row.open); // respects a row clicked mid-animation
      rows.forEach((r) => { if (r !== row && r.open) animateRow(r, false); });
      animateRow(row, opening);
    }));
  });

  // ---------- magnetic buttons: CTAs lean toward the cursor
  if (finePointer && !reduceMotion) {
    $$('.circle-btn, .header-cta .pill, .cta-band .pill, .hero-actions .link-underline').forEach((el) => {
      el.classList.add('magnetic');
      el.addEventListener('mousemove', (ev) => {
        const r = el.getBoundingClientRect();
        const x = (ev.clientX - r.left - r.width / 2) * 0.25;
        const y = (ev.clientY - r.top - r.height / 2) * 0.35;
        el.style.transform = `translate(${x}px, ${y}px)`;
      });
      el.addEventListener('mouseleave', () => { el.style.transform = ''; });
    });
  }

  // ---------- reveal on scroll, with grouped children arriving one by one
  const reveals = $$('.reveal');
  reveals.forEach((el) => {
    $$(':scope .grid-cards > *, :scope .stats > *, :scope .rows > *, :scope .quotes > *, :scope .team > *, :scope .chips:not([hidden]) > *, :scope .badges > *', el)
      .forEach((child, i) => { child.classList.add('reveal-child'); child.style.setProperty('--d', Math.min(i, 10)); });
  });
  if ('IntersectionObserver' in window) {
    const io = new IntersectionObserver((entries) => entries.forEach((en) => {
      if (en.isIntersecting) { en.target.classList.add('is-in'); io.unobserve(en.target); }
    }), { rootMargin: '0px 0px -8% 0px' });
    reveals.forEach((el) => io.observe(el));
  } else {
    reveals.forEach((el) => el.classList.add('is-in'));
  }

  // ---------- hero parallax: the wordmark drifts down, the copy eases away
  const heroWord = $('.hero .wordmark');
  const heroCopy = $('.hero .hero-copy');
  if (heroWord && !reduceMotion) {
    let ticking = false;
    const update = () => {
      const y = Math.min(window.scrollY, 900);
      heroWord.style.transform = `translate3d(0, ${y * 0.22}px, 0)`;
      if (heroCopy) {
        heroCopy.style.transform = `translate3d(0, ${y * -0.08}px, 0)`;
        heroCopy.style.opacity = String(Math.max(0, 1 - y / 650));
      }
      ticking = false;
    };
    window.addEventListener('scroll', () => { if (!ticking) { ticking = true; requestAnimationFrame(update); } }, { passive: true });
    update();
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
