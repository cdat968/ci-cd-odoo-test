/** @odoo-module **/

// Global singleton lightbox for qa-evidence gallery.
// Uses event delegation so it works with Odoo's dynamically rendered views.

let _lb = null;   // lightbox DOM element
let _items = [];  // [{url, caption}]
let _idx = 0;

function _build() {
    if (_lb) return;
    _lb = document.createElement('div');
    _lb.id = 'qa-lightbox';
    _lb.style.display = 'none';
    _lb.innerHTML = `
        <div class="qa-lb-overlay">
            <div class="qa-lb-panel">
                <div class="qa-lb-header">
                    <span class="qa-lb-caption" id="qa-lb-caption"></span>
                    <button class="qa-lb-close" id="qa-lb-close" title="Close (Esc)">&#10005;</button>
                </div>
                <div class="qa-lb-body">
                    <button class="qa-lb-nav qa-lb-prev" id="qa-lb-prev" title="Previous (&#8592;)">&#8249;</button>
                    <img class="qa-lb-img" id="qa-lb-img" src="" alt=""/>
                    <button class="qa-lb-nav qa-lb-next" id="qa-lb-next" title="Next (&#8594;)">&#8250;</button>
                </div>
                <div class="qa-lb-footer">
                    <span id="qa-lb-counter"></span>
                </div>
            </div>
        </div>
    `;
    document.body.appendChild(_lb);

    _lb.querySelector('#qa-lb-close').addEventListener('click', _close);
    _lb.querySelector('#qa-lb-prev').addEventListener('click', _prev);
    _lb.querySelector('#qa-lb-next').addEventListener('click', _next);
    _lb.querySelector('.qa-lb-overlay').addEventListener('click', (e) => {
        if (e.target === e.currentTarget) _close();
    });
    document.addEventListener('keydown', _onKey);
}

function _open(items, index) {
    _build();
    _items = items;
    _idx = index;
    _render();
    _lb.style.display = 'block';
    document.body.style.overflow = 'hidden';
}

function _close() {
    if (!_lb) return;
    _lb.style.display = 'none';
    document.body.style.overflow = '';
}

function _render() {
    const item = _items[_idx];
    _lb.querySelector('#qa-lb-img').src = item.url;
    _lb.querySelector('#qa-lb-caption').textContent = item.caption;
    _lb.querySelector('#qa-lb-counter').textContent = `${_idx + 1} / ${_items.length}`;
    _lb.querySelector('#qa-lb-prev').disabled = _idx === 0;
    _lb.querySelector('#qa-lb-next').disabled = _idx === _items.length - 1;
}

function _prev() { if (_idx > 0) { _idx--; _render(); } }
function _next() { if (_idx < _items.length - 1) { _idx++; _render(); } }

function _onKey(e) {
    if (!_lb || _lb.style.display === 'none') return;
    if (e.key === 'ArrowLeft')  { e.preventDefault(); _prev(); }
    if (e.key === 'ArrowRight') { e.preventDefault(); _next(); }
    if (e.key === 'Escape')     _close();
}

// Event delegation — works with Odoo's dynamic view rendering
document.addEventListener('click', function (e) {
    const card = e.target.closest('.qa-evidence-card');
    if (!card) return;
    const gallery = card.closest('.qa-evidence-gallery');
    if (!gallery) return;

    const cards = Array.from(gallery.querySelectorAll('.qa-evidence-card'));
    const index = cards.indexOf(card);
    const items = cards.map(c => {
        const img = c.querySelector('img');
        return { url: img ? img.getAttribute('src') : '', caption: img ? (img.alt || '') : '' };
    });
    _open(items, index);
});
