/* VOLTA BCN · interacción del sitio */
(function () {
  'use strict';

  /* ── Configuración de EmailJS (la misma cuenta que usaba la web anterior) ── */
  var EMAILJS = { service: 'service_amvle6q', template: 'template_ssh8rpu', key: '2lxyk7hQIq8VyMKuS' };

  var $ = function (s, c) { return (c || document).querySelector(s); };
  var $$ = function (s, c) { return Array.prototype.slice.call((c || document).querySelectorAll(s)); };

  /* ── Cabecera sobre el hero ── */
  var header = $('.site-header');
  if (header) {
    var onScroll = function () {
      if (header.classList.contains('overlay')) header.classList.toggle('solid', window.scrollY > 40);
      var y = header.getBoundingClientRect().bottom + 1, x = window.innerWidth / 2, under = null;
      var els = document.elementsFromPoint ? document.elementsFromPoint(x, y) : [];
      for (var i = 0; i < els.length; i++) { if (!header.contains(els[i])) { under = els[i]; break; } }
      var orange = !!(under && under.closest && under.closest('.bg-orange, .doors'));
      header.classList.toggle('on-orange', orange && (!header.classList.contains('overlay') || header.classList.contains('solid')));
    };
    onScroll(); window.addEventListener('scroll', onScroll, { passive: true }); window.addEventListener('resize', onScroll);
  }

  /* ── Desplegable "Propietarios" (teclado y táctil) ── */
  $$('.dd > button').forEach(function (b) {
    b.addEventListener('click', function () {
      var dd = b.parentNode, open = !dd.classList.contains('open');
      dd.classList.toggle('open', open); b.setAttribute('aria-expanded', open);
    });
  });
  document.addEventListener('click', function (e) {
    $$('.dd.open').forEach(function (dd) { if (!dd.contains(e.target)) { dd.classList.remove('open'); $('button', dd).setAttribute('aria-expanded', 'false'); } });
  });

  /* ── Menú móvil ── */
  var mnav = $('#mnav'), burger = $('.burger');
  function setMenu(open) {
    if (!mnav) return;
    mnav.classList.toggle('open', open); document.body.classList.toggle('menu-open', open);
    burger.setAttribute('aria-expanded', open); mnav.setAttribute('aria-hidden', !open);
    if (open) $('.mnav-close', mnav).focus(); else burger.focus();
  }
  if (burger) burger.addEventListener('click', function () { setMenu(true); });
  if (mnav) {
    $('.mnav-close', mnav).addEventListener('click', function () { setMenu(false); });
    $$('a', mnav).forEach(function (a) { a.addEventListener('click', function () { setMenu(false); }); });
  }
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && mnav && mnav.classList.contains('open')) setMenu(false); });

  /* ── Aparición discreta ── */
  if ('IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (es) { es.forEach(function (e) { if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); } }); }, { threshold: .12 });
    $$('.reveal').forEach(function (el) { io.observe(el); });
  } else { $$('.reveal').forEach(function (el) { el.classList.add('in'); }); }

  /* ── Galería / visor de fotos ── */
  var lb = $('#lb');
  if (lb) {
    var data = JSON.parse($('#gallery-data').textContent), i = 0, last = null, x0 = null;
    var img = $('img', lb), cap = $('figcaption', lb);
    var show = function () { img.src = data.fotos[i]; img.alt = data.alts[i] || data.titulo; cap.textContent = (data.alts[i] ? data.alts[i] + ' · ' : '') + (i + 1) + ' / ' + data.fotos.length; };
    var open = function (n) { i = n || 0; show(); last = document.activeElement; lb.hidden = false; document.body.style.overflow = 'hidden'; $('.x', lb).focus(); };
    var close = function () { lb.hidden = true; document.body.style.overflow = ''; if (last) last.focus(); };
    var go = function (d) { i = (i + d + data.fotos.length) % data.fotos.length; show(); };
    $$('[data-open]').forEach(function (b) { b.addEventListener('click', function () { open(+b.getAttribute('data-open')); }); });
    $('.x', lb).addEventListener('click', close);
    $('.pv', lb).addEventListener('click', function () { go(-1); });
    $('.nx', lb).addEventListener('click', function () { go(1); });
    lb.addEventListener('click', function (e) { if (e.target === lb) close(); });
    document.addEventListener('keydown', function (e) { if (lb.hidden) return; if (e.key === 'Escape') close(); if (e.key === 'ArrowLeft') go(-1); if (e.key === 'ArrowRight') go(1); });
    lb.addEventListener('touchstart', function (e) { x0 = e.touches[0].clientX; }, { passive: true });
    lb.addEventListener('touchend', function (e) { if (x0 === null) return; var dx = e.changedTouches[0].clientX - x0; if (Math.abs(dx) > 40) go(dx < 0 ? 1 : -1); x0 = null; });
  }

  /* ── Filtros del catálogo ── */
  var cat = $('[data-catalog]');
  if (cat) {
    var items = $$('[data-item]', cat), sel = $$('[data-filter]'), count = $('[data-count]'), empty = $('[data-empty]');
    var apply = function () {
      var n = 0;
      items.forEach(function (it) {
        var ok = sel.every(function (s) {
          var v = s.value, k = s.getAttribute('data-filter'); if (!v) return true;
          if (k === 'hab') return +it.getAttribute('data-hab') >= +v;
          return it.getAttribute('data-' + k) === v;
        });
        it.hidden = !ok; if (ok) n++;
      });
      if (count) count.textContent = n === 1 ? '1 inmueble' : n + ' inmuebles';
      if (empty) empty.hidden = n > 0;
    };
    sel.forEach(function (s) { s.addEventListener('change', apply); }); apply();
  }

  /* ── Testimonios ── */
  $$('[data-slider]').forEach(function (sl) {
    var slides = $$('.quote-slide', sl), pos = $('.pos', sl.parentNode), k = 0, t;
    var show = function (n) { slides[k].classList.remove('on'); k = (n + slides.length) % slides.length; slides[k].classList.add('on'); if (pos) pos.textContent = (k + 1) + ' / ' + slides.length; };
    var nav = sl.parentNode;
    $('.prev', nav).addEventListener('click', function () { show(k - 1); stop(); });
    $('.next', nav).addEventListener('click', function () { show(k + 1); stop(); });
    var stop = function () { clearInterval(t); };
    if (!window.matchMedia('(prefers-reduced-motion: reduce)').matches) t = setInterval(function () { show(k + 1); }, 9000);
    sl.addEventListener('mouseenter', stop); sl.addEventListener('focusin', stop);
    show(0);
  });

  /* ── Envío por EmailJS ── */
  function send(params) {
    if (!window.emailjs) return Promise.reject(new Error('EmailJS no disponible'));
    window.emailjs.init(EMAILJS.key);
    return window.emailjs.send(EMAILJS.service, EMAILJS.template, params);
  }
  function now() { return new Date().toLocaleString('es-ES'); }
  function msg(form, text, err) { var m = $('.form-msg', form); m.textContent = text; m.classList.toggle('err', !!err); m.hidden = false; }
  var EN = document.documentElement.lang === 'en';
  var FALLBACK = EN ? 'We could not send the form. Please write to info@voltabcn.com or call +34 647 224 442.' : 'No hemos podido enviar el formulario. Escríbenos a info@voltabcn.com o llámanos al +34 647 224 442.';

  /* Formularios de contacto, visita y propietarios */
  $$('form[data-form]').forEach(function (f) {
    f.addEventListener('submit', function (e) {
      e.preventDefault();
      if (!f.reportValidity()) return;
      var fd = new FormData(f), btn = $('button[type=submit]', f);
      var interes = fd.getAll('interes').join(', ') || f.getAttribute('data-form');
      var inmueble = fd.get('inmueble') || '';
      var mensaje = (fd.get('mensaje') || '').trim();
      var nombre = fd.get('nombre');
      var p = {
        subject: 'Web Volta · ' + f.getAttribute('data-form') + ' · ' + nombre + (inmueble ? ' · ' + inmueble : ''),
        nombre: nombre, telefono: fd.get('telefono') || '—', email_lead: fd.get('email'),
        barrio: inmueble || (fd.get('barrio') || '—'), metros: '—', habitaciones: '—',
        estado: 'Interés: ' + interes, precio_venta: mensaje || '—', precio_alquiler: '—',
        fecha: now(), interes: interes, mensaje: mensaje, inmueble: inmueble, pagina: location.href
      };
      btn.disabled = true; btn.textContent = EN ? 'Sending…' : 'Enviando…';
      send(p).then(function () {
        f.reset(); msg(f, EN ? 'Thank you, ' + nombre + '. We have received your message and will get back to you shortly.' : 'Gracias, ' + nombre + '. Hemos recibido tu mensaje y te contactaremos lo antes posible.');
      }, function () { msg(f, FALLBACK, true); })
        .then(function () { btn.disabled = false; btn.textContent = btn.getAttribute('data-label'); });
    });
  });

  /* ── Tasador (misma lógica de precios que la web anterior) ── */
  var PRICES = {
    eixample_dret:{s:[5580,7650],r:[18,24]},eixample_esq:{s:[4950,6480],r:[15,21]},antiga_esquerra:{s:[5220,6750],r:[16,22]},nova_esquerra:{s:[4680,6120],r:[14,19]},sagrada_familia:{s:[4500,5850],r:[14,19]},fort_pienc:{s:[4320,5580],r:[14,18]},
    gracia_vila:{s:[4950,6300],r:[16,21]},camp_grassot:{s:[4320,5580],r:[14,19]},gracia_nova:{s:[4500,5850],r:[15,20]},vallcarca:{s:[3420,4500],r:[12,16]},coll:{s:[3150,4320],r:[11,14]},
    sarria:{s:[4950,6750],r:[16,23]},sant_gervasi:{s:[5400,7200],r:[18,24]},bonanova:{s:[5850,8100],r:[19,26]},les_tres_torres:{s:[6300,9000],r:[20,28]},pedralbes_sarria:{s:[6750,10800],r:[21,30]},
    les_corts:{s:[4950,6750],r:[16,23]},maternitat:{s:[4500,6300],r:[15,21]},la_merce:{s:[4050,5400],r:[14,18]},
    poblenou:{s:[4500,6300],r:[15,21]},vila_olimpica:{s:[5400,7650],r:[18,24]},glories:{s:[4950,6750],r:[16,23]},el_clot:{s:[3780,5220],r:[13,17]},camp_arpa:{s:[4050,5400],r:[14,18]},provencals:{s:[3600,4950],r:[12,16]},
    sants:{s:[3600,4950],r:[13,17]},hostafrancs:{s:[3420,4680],r:[12,16]},poble_sec:{s:[3780,5220],r:[13,17]},la_font:{s:[3150,4320],r:[11,14]},montjuic:{s:[2880,4050],r:[10,14]},
    horta:{s:[2880,4050],r:[10,14]},guinardo:{s:[3150,4320],r:[11,15]},can_baro:{s:[3420,4680],r:[12,16]},baix_guinardo:{s:[3150,4320],r:[11,15]},
    via_julia:{s:[2250,3150],r:[8,12]},prosperitat:{s:[2160,3060],r:[8,11]},verdum:{s:[1980,2880],r:[7,11]},trinitat:{s:[1800,2700],r:[7,10]},
    sant_andreu:{s:[2880,4050],r:[11,15]},navas:{s:[3150,4320],r:[12,16]},sagrera:{s:[2700,3780],r:[10,14]},bon_pastor:{s:[2250,3150],r:[8,12]},
    gotico:{s:[5400,8100],r:[17,23]},raval:{s:[4050,5850],r:[13,17]},barceloneta:{s:[4950,7200],r:[15,21]},sant_pere:{s:[4500,6300],r:[14,20]}
  };
  var MULT = { reformar:[.78,.88], bueno:[.97,1.03], reformado:[1.10,1.22], lujo:[1.30,1.55] };
  var ESTADO = { reformar:'A reformar', bueno:'Buen estado', reformado:'Reformado', lujo:'Lujo / Alta calidad' };
  var REG = 0.82;
  var fmt = function (n) { return new Intl.NumberFormat('es-ES', { style:'currency', currency:'EUR', maximumFractionDigits:0 }).format(n); };

  $$('form[data-tasador]').forEach(function (f) {
    f.addEventListener('submit', function (e) {
      e.preventDefault();
      if (!f.reportValidity()) return;
      var fd = new FormData(f), b = fd.get('barrio'), m2 = parseFloat(fd.get('metros')), est = fd.get('estado');
      var p = PRICES[b], mu = MULT[est];
      var sMid = Math.round((p.s[0] + p.s[1]) / 2 * ((mu[0] + mu[1]) / 2) * m2 / 1000) * 1000;
      var rMid = Math.round((p.r[0] + p.r[1]) / 2 * ((mu[0] + mu[1]) / 2) * m2 * REG / 10) * 10;
      var r = $('.result', f.parentNode);
      $('[data-r=venta]', r).textContent = fmt(sMid);
      $('[data-r=venta-rg]', r).textContent = fmt(sMid - 35000) + ' – ' + fmt(sMid + 35000);
      $('[data-r=alq]', r).textContent = fmt(rMid) + '/mes';
      $('[data-r=alq-rg]', r).textContent = fmt(rMid - 150) + ' – ' + fmt(rMid + 150) + '/mes';
      r.classList.add('show'); r.scrollIntoView({ behavior:'smooth', block:'nearest' });
      var sel = $('select[name=barrio]', f), barrio = sel.options[sel.selectedIndex].text;
      var interes = fd.get('interes');
      send({
        subject: 'Nuevo lead tasador - ' + fd.get('nombre') + ' - ' + barrio + ' - ' + interes,
        nombre: fd.get('nombre'), telefono: fd.get('telefono'), email_lead: fd.get('email'),
        barrio: barrio, metros: m2 + ' m²', habitaciones: fd.get('habitaciones'), estado: (ESTADO[est] || est) + ' · Interés: ' + interes,
        precio_venta: fmt(sMid) + ' (' + fmt(sMid - 35000) + ' – ' + fmt(sMid + 35000) + ')',
        precio_alquiler: fmt(rMid) + '/mes (' + fmt(rMid - 150) + ' – ' + fmt(rMid + 150) + '/mes)',
        fecha: now(), interes: interes
      }).then(function () { msg(f, 'Te enviaremos el detalle y nos pondremos en contacto contigo.'); }, function () { msg(f, FALLBACK, true); });
    });
  });
})();
