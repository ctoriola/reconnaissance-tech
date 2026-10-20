(() => {
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => Array.from(r.querySelectorAll(s));

  // ---------- desktop mega menus
  const menuButtons = $$('.nav-item > .nav-link');
  const closeMenus = (except) => menuButtons.forEach((b) => {
    if (b === except) return;
    b.setAttribute('aria-expanded', 'false');
    b.nextElementSibling.classList.remove('is-open');
  });
  menuButtons.forEach((btn) => {
    const menu = btn.nextElementSibling;
    btn.addEventListener('click', (ev) => {
      ev.stopPropagation();
      const open = btn.getAttribute('aria-expanded') !== 'true';
      closeMenus(btn);
      btn.setAttribute('aria-expanded', String(open));
      menu.classList.toggle('is-open', open);
    });
  });
  document.addEventListener('click', (ev) => { if (!ev.target.closest('.nav-item')) closeMenus(); });
  document.addEventListener('keydown', (ev) => {
    if (ev.key !== 'Escape') return;
    const openBtn = menuButtons.find((b) => b.getAttribute('aria-expanded') === 'true');
    closeMenus();
    if (openBtn) openBtn.focus();
    closeDrawer();
  });

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

  // ---------- compact bar once the hero has scrolled away
  const bar = $('.sticky-bar');
  const heroEl = $('.hero');
  if (bar && heroEl && 'IntersectionObserver' in window) {
    new IntersectionObserver(([entry]) => {
      const show = !entry.isIntersecting;
      bar.classList.toggle('is-visible', show);
      bar.setAttribute('aria-hidden', String(!show));
      $$('a', bar).forEach((a) => (show ? a.removeAttribute('tabindex') : a.setAttribute('tabindex', '-1')));
    }, { threshold: 0.12 }).observe(heroEl);
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

  $$('[data-year]').forEach((el) => { el.textContent = new Date().getFullYear(); });
})();
