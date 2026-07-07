(function () {
  var BRAND_RED = '#ed1c24';

  function init() {
    if (document.getElementById('mh-panel')) return;

    var css = [
      '#mh-panel{position:fixed;top:0;right:0;bottom:0;width:82vw;max-width:340px;height:100vh;height:100dvh;background:#111;color:#fff;padding:4rem 1.25rem 2rem;z-index:99999;overflow-y:auto;-webkit-overflow-scrolling:touch;box-shadow:-8px 0 24px rgba(0,0,0,0.35);transform:translateX(100%);transition:transform .28s ease;list-style:none;margin:0}',
      '#mh-panel.open{transform:translateX(0)}',
      '#mh-panel ul{list-style:none;margin:0;padding:0}',
      '#mh-panel li{display:block;width:100%;margin:0;padding:0}',
      '#mh-panel a.mh-link{display:flex;align-items:center;justify-content:space-between;color:#fff;text-decoration:none;padding:.85rem .25rem;border-bottom:1px solid rgba(255,255,255,0.08);font-size:1.05rem;line-height:1.2;background:transparent}',
      '#mh-panel a.mh-link:hover,#mh-panel a.mh-link:focus{color:' + BRAND_RED + '}',
      '#mh-panel .mh-sub{display:none;padding:.25rem 0 .25rem 1rem;background:rgba(255,255,255,0.04);margin:0 0 .25rem}',
      '#mh-panel li.open>.mh-sub{display:block}',
      '#mh-panel .mh-sub a.mh-link{font-size:.95rem;padding:.6rem .25rem;color:rgba(255,255,255,0.85);border-bottom-color:rgba(255,255,255,0.05)}',
      '#mh-panel .mh-toggle{flex:0 0 32px;height:32px;display:inline-flex;align-items:center;justify-content:center;border-radius:4px;background:rgba(255,255,255,0.06);margin-left:.5rem;border:0;color:#fff;cursor:pointer;padding:0}',
      '#mh-panel .mh-toggle:before{content:"";width:8px;height:8px;border-right:2px solid #fff;border-bottom:2px solid #fff;transform:rotate(45deg) translate(-2px,-2px);transition:transform .2s ease;display:block}',
      '#mh-panel li.open>.mh-link .mh-toggle:before{transform:rotate(-135deg) translate(-2px,-2px)}',
      '#mh-panel .mh-close{position:absolute;top:.75rem;right:.75rem;width:36px;height:36px;background:rgba(255,255,255,0.08);border:0;border-radius:50%;color:#fff;font-size:1.5rem;line-height:1;cursor:pointer;display:flex;align-items:center;justify-content:center;padding:0}',
      '#mh-panel .mh-close:before{content:"\\00d7"}',

      '#mh-scrim{position:fixed;inset:0;background:rgba(0,0,0,0.55);opacity:0;pointer-events:none;transition:opacity .25s ease;z-index:99998}',
      'body.mh-open{overflow:hidden}',
      'body.mh-open #mh-scrim{opacity:1;pointer-events:auto}',
    ].join('');

    var styleEl = document.createElement('style');
    styleEl.id = 'mh-panel-style';
    styleEl.textContent = css;
    document.head.appendChild(styleEl);

    function buildMenuItems() {
      var src = document.querySelector('.ush_menu_1 .w-nav-list.level_1');
      if (!src) return '<p style="color:rgba(255,255,255,0.5);">Menu unavailable</p>';
      function walk(ul) {
        var html = '<ul>';
        var children = ul.children;
        for (var i = 0; i < children.length; i++) {
          var li = children[i];
          if (li.tagName !== 'LI' || li.classList.contains('w-nav-close')) continue;
          var anchor = li.querySelector(':scope > a');
          var sub = li.querySelector(':scope > ul');
          if (!anchor) continue;
          var href = anchor.getAttribute('href') || '#';
          var title = (anchor.querySelector('.w-nav-title') || anchor).textContent.trim();
          html += '<li' + (sub ? ' class="has-sub"' : '') + '>';
          html += '<a class="mh-link" href="' + href + '">' + '<span>' + escapeHTML(title) + '</span>';
          if (sub) html += '<button class="mh-toggle" aria-label="Expand ' + escapeHTML(title) + '" aria-expanded="false" type="button"></button>';
          html += '</a>';
          if (sub) html += '<div class="mh-sub">' + walk(sub) + '</div>';
          html += '</li>';
        }
        return html + '</ul>';
      }
      return walk(src);
    }

    function escapeHTML(s) {
      return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
    }

    var panel = document.createElement('nav');
    panel.id = 'mh-panel';
    panel.setAttribute('aria-label', 'Mobile menu');
    panel.innerHTML = '<button class="mh-close" id="mh-close" type="button" aria-label="Close menu"></button>' + buildMenuItems();

    var scrim = document.createElement('div');
    scrim.id = 'mh-scrim';

    document.body.appendChild(panel);
    document.body.appendChild(scrim);

    function setOpen(open) {
      panel.classList.toggle('open', open);
      document.body.classList.toggle('mh-open', open);
      var ctrls = document.querySelectorAll('.w-nav-control');
      for (var i = 0; i < ctrls.length; i++) {
        ctrls[i].setAttribute('aria-expanded', open ? 'true' : 'false');
        ctrls[i].classList.toggle('active', open);
      }
    }

    document.addEventListener('click', function (e) {
      var ctrl = e.target.closest && e.target.closest('.w-nav-control');
      if (ctrl) {
        e.preventDefault();
        e.stopPropagation();
        setOpen(!panel.classList.contains('open'));
        return;
      }
      if (e.target.closest('#mh-close')) {
        e.preventDefault();
        setOpen(false);
        return;
      }
      var toggle = e.target.closest('.mh-toggle');
      if (toggle) {
        e.preventDefault();
        e.stopPropagation();
        var li = toggle.closest('li.has-sub');
        if (li) {
          li.classList.toggle('open');
          toggle.setAttribute('aria-expanded', li.classList.contains('open') ? 'true' : 'false');
        }
        return;
      }
      if (e.target.closest('#mh-scrim')) {
        setOpen(false);
        return;
      }
      var link = e.target.closest('#mh-panel a.mh-link');
      if (link && !e.target.closest('.mh-toggle')) {
        setTimeout(function () { setOpen(false); }, 50);
      }
    });

    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') setOpen(false);
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
