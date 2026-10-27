/*
 * Figurinen auf der About-Seite.
 * Die Linien liegen zuerst als einzelne, verstreute Striche im Hintergrund und setzen sich
 * beim Scrollen zur Figurine zusammen (fertig, wenn die Figur in der Fenstermitte steht).
 * Zeichnungen: images/figurines/<slug>.svg (erzeugt von tools/figurines/figurines.py),
 * jede Linie ein eigener <path>. Rein dekorativ. Mit „Bewegung reduzieren“: fertige Figuren.
 * Doku: tools/figurines/README.md
 */
(function () {
    'use strict';

    // Desktop: Figuren abwechselnd links/rechts neben Foto und Text;
    // "at" = Höhe als Anteil des Hauptbereichs (Foto oben bis Textende)
    var MARGIN_FIGURES = [
        { slug: 'traviata', side: 'left', at: 0.02 },
        { slug: 'coriolan', side: 'right', at: 0.21 },
        { slug: 'traum', side: 'left', at: 0.40 },
        { slug: 'kleiner-mann', side: 'right', at: 0.59 },
        { slug: 'sonne', side: 'left', at: 0.78 }
    ];
    // Schmale Fenster: alle Figuren, je eine klein unter einem Absatz, locker versetzt und
    // leicht gekippt ("after" = Index des Absatzes, ohne Sprachumschalter)
    var INLINE_FIGURES = [
        { slug: 'traviata', after: 1, align: 'left', tilt: -4 },
        { slug: 'coriolan', after: 2, align: 'right', tilt: 5 },
        { slug: 'traum', after: 3, align: 'center', tilt: -2 },
        { slug: 'kleiner-mann', after: 4, align: 'left', tilt: 4 },
        { slug: 'sonne', after: 5, align: 'right', tilt: -5 }
    ];

    var MIN_MARGIN = 190;   // freier Rand (px) neben dem Text, ab dem die Randfiguren erscheinen
    var MAX_WIDTH = 190;    // Breite einer Randfigur
    // Wie weit die Striche anfangs verstreut sind: quer über die Seite (auch über den Text),
    // als Anteil der Fensterbreite/-höhe; Randfiguren streuen vor allem Richtung Seitenmitte
    var SCATTER_X = 0.6, SCATTER_Y = 0.5, SCATTER_ROT = 120;
    var STAGGER = 0.42;     // wie unterschiedlich früh die Striche losgehen (Anteil des Wegs)
    var FIRST_END = 0.45;   // erste Figur frühestens fertig nach 0.45 Fensterhöhen Scrollweg …
    var NEXT_END = 0.3;     // … jede weitere mindestens 0.3 Fensterhöhen später
    var SPAN = 0.95;        // Scrollweg (in Fensterhöhen), über den sich eine Figur zusammensetzt
    var LINE_OPACITY = 0.55, ACCENT_OPACITY = 0.95;
    var FADE_IN = 140;      // px Scrollweg, über den die Striche nach dem ersten Scrollen einblenden
                            // (ohne Scrollen ist der Hintergrund leer)
    // Desktop: die Figuren werden gleichmäßig über den ganzen Scrollweg fertig
    // (erste bei 30 %, letzte kurz vor Seitenende) und setzen sich je über DESK_SPAN Abstände zusammen
    var DESK_FIRST = 0.3, DESK_SPAN = 1.6;
    var FIRST_VISIBLE = 70; // Desktop: keine Figur wird oben im Kopfbereich fertig – steht eine Figur beim
                            // Fertigwerden höher als so viele px unter dem Fensterrand, rutscht sie tiefer
                            // (betrifft derzeit Traviata und Coriolan); alle anderen bleiben, wo sie sind

    var main = document.querySelector('main');
    var bio = document.querySelector('.biography');
    if (!main || !bio || !window.fetch) return;

    var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
    var figures = [];   // { el, strokes: [{ path, dx, dy, rot, delay }] }
    var mode = null;    // 'margin' | 'inline'

    function rng(seed) {   // mulberry32 – feste Streuung je Figur, kein Flackern beim Neuladen
        return function () {
            seed |= 0; seed = seed + 0x6D2B79F5 | 0;
            var t = Math.imul(seed ^ seed >>> 15, 1 | seed);
            t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t;
            return ((t ^ t >>> 14) >>> 0) / 4294967296;
        };
    }

    function seedOf(s) {
        var h = 2166136261;
        for (var i = 0; i < s.length; i++) h = Math.imul(h ^ s.charCodeAt(i), 16777619);
        return h;
    }

    var svgCache = {};
    function loadSvg(slug) {
        if (!svgCache[slug]) {
            svgCache[slug] = fetch('images/figurines/' + slug + '.svg')
                .then(function (r) { return r.ok ? r.text() : null; })
                .catch(function () { return null; });
        }
        return svgCache[slug];
    }

    function makeFigure(slug, className) {
        var el = document.createElement('div');
        el.className = 'figurine ' + className;
        el.setAttribute('aria-hidden', 'true');
        var fig = { el: el, strokes: [] };
        loadSvg(slug).then(function (text) {
            if (!text) { el.remove(); return; }
            el.innerHTML = text;
            var rand = rng(seedOf(slug));
            el.querySelectorAll('path').forEach(function (path) {
                fig.strokes.push({
                    path: path,
                    // farbiges Kostümteil (data-accent) steht kräftiger als die weißen Linien
                    base: path.hasAttribute('data-accent') ? ACCENT_OPACITY : LINE_OPACITY,
                    ux: rand(), uy: rand() * 2 - 1, uz: rand(),   // Streuung, in px umgerechnet in scatterPx()
                    rot: (rand() * 2 - 1) * SCATTER_ROT,
                    delay: rand() * STAGGER
                });
            });
            measure();
            scatterPx(fig);
            requestUpdate();
        });
        return fig;
    }

    // Streuweite in px: abhängig von Fenstergröße, Seite und Höhe der Figur.
    // Links stehende Figuren streuen nach rechts (über den Text), rechte nach links,
    // eingebettete Figuren in beide Richtungen. Weiter unten stehende Figuren schicken
    // einen Teil ihrer Striche nach oben – so liegen schon beim Laden Teile aller Figuren
    // verstreut auf der Seite.
    function scatterPx(fig) {
        var vw = window.innerWidth, vh = window.innerHeight;
        var side = fig.cfg ? fig.cfg.side : null;
        var scale = (fig.el.getBoundingClientRect().width || 260) / 260;   // px -> SVG-Einheiten
        var rise = Math.max(0, (fig.docTop || 0) - 0.3 * vh);
        fig.strokes.forEach(function (s) {
            var x = side === 'left' ? (s.ux * 1.25 - 0.25) : side === 'right' ? -(s.ux * 1.25 - 0.25) : (s.ux * 2 - 1);
            var dx = x * SCATTER_X * vw * (side ? 1 : 0.7);
            var dy = s.uy * SCATTER_Y * vh - s.uz * s.uz * rise;
            s.dx = dx / scale;
            s.dy = dy / scale;
        });
    }

    // Scroll-Fenster je Figur: ganz oben (scrollY 0) ist alles verstreut; die Figuren setzen
    // sich nacheinander zusammen und sind fertig, wenn ihre Mitte die Fenstermitte erreicht
    // (frühestens nach einem kleinen Stück Scrollweg, in der Reihenfolge von oben nach unten).
    function measure() {
        var vh = window.innerHeight, sy = window.scrollY;
        figures.forEach(function (f) {
            var r = f.el.getBoundingClientRect();
            f.docTop = r.top + sy;
            f.docCenter = r.top + sy + r.height / 2;
        });
        var ordered = figures.slice().sort(function (a, b) { return a.docCenter - b.docCenter; });
        var maxEnd = 0.97 * (document.documentElement.scrollHeight - vh);
        if (mode === 'margin' && ordered.length > 1 && maxEnd > 0) {
            var gap = (1 - DESK_FIRST) * maxEnd / (ordered.length - 1);
            ordered.forEach(function (f, i) {
                f.end = maxEnd * DESK_FIRST + i * gap;
                f.start = Math.max(0, f.end - DESK_SPAN * gap);
            });
            return;
        }
        ordered.forEach(function (f, i) {
            f.end = Math.max(f.docCenter - 0.5 * vh, (FIRST_END + i * NEXT_END) * vh);
        });
        // Alle Figuren müssen fertig werden, bevor die Seite zu Ende ist: sonst Zeitplan stauchen
        var last = ordered.length ? ordered[ordered.length - 1].end : 0;
        var squeeze = last > maxEnd && maxEnd > 0 ? maxEnd / last : 1;
        ordered.forEach(function (f) {
            f.end *= squeeze;
            f.start = Math.max(0, f.end - SPAN * vh);
        });
    }

    function clear() {
        figures.forEach(function (f) { f.el.remove(); });
        figures = [];
    }

    function freeMargin() {
        var m = main.getBoundingClientRect(), b = bio.getBoundingClientRect();
        return Math.min(b.left - m.left, m.right - b.right);
    }

    function layout() {
        var wanted = freeMargin() >= MIN_MARGIN ? 'margin' : 'inline';
        if (wanted !== mode) {
            clear();
            mode = wanted;
            if (mode === 'margin') {
                MARGIN_FIGURES.forEach(function (cfg) {
                    var f = makeFigure(cfg.slug, 'figurine--margin');
                    f.cfg = cfg;
                    main.appendChild(f.el);
                    figures.push(f);
                });
            } else {
                var paragraphs = bio.querySelectorAll('p:not(.language-switch)');
                INLINE_FIGURES.forEach(function (cfg) {
                    var anchor = paragraphs[cfg.after];
                    if (!anchor) return;   // weniger Absätze als Figuren: der Rest entfällt
                    var f = makeFigure(cfg.slug, 'figurine--inline figurine--' + cfg.align);
                    f.el.style.setProperty('--tilt', cfg.tilt + 'deg');
                    anchor.insertAdjacentElement('afterend', f.el);
                    figures.push(f);
                });
            }
        }
        if (mode === 'margin') {
            var m = main.getBoundingClientRect(), b = bio.getBoundingClientRect();
            var marginW = Math.min(b.left - m.left, m.right - b.right);
            var w = Math.min(MAX_WIDTH, marginW - 40);
            figures.forEach(function (f) {
                var left = f.cfg.side === 'left'
                    ? (b.left - m.left - w) / 2
                    : (b.right - m.left) + (m.right - b.right - w) / 2;
                f.el.style.width = w + 'px';
                f.el.style.left = left + 'px';
                f.el.style.top = (f.cfg.at * m.height) + 'px';
            });
            // Figuren, die beim Fertigwerden oben unter dem Kopfbereich stünden, tiefer setzen,
            // bis sie in diesem Moment vollständig zu sehen sind – nie in die nächste Figur derselben
            // Seite hinein. Figuren, die ohnehin gut stehen, bleiben unverändert.
            var vh = window.innerHeight, n = figures.length;
            var maxEnd = 0.97 * (document.documentElement.scrollHeight - vh);
            var gap = n > 1 ? (1 - DESK_FIRST) * maxEnd / (n - 1) : 0;
            var mainDocTop = m.top + window.scrollY;
            var figH = w * 560 / 260;
            var tops = figures.map(function (f, i) {
                var end = maxEnd * DESK_FIRST + i * gap;   // gleicher Zeitplan wie in measure()
                return Math.max(f.cfg.at * m.height, end + FIRST_VISIBLE - mainDocTop);
            });
            // von unten nach oben: nie in die (endgültige) nächste Figur derselben Seite hinein
            for (var i = figures.length - 1; i >= 0; i--) {
                for (var j = i + 1; j < figures.length; j++) {
                    if (figures[j].cfg.side === figures[i].cfg.side) {
                        tops[i] = Math.min(tops[i], tops[j] - figH - 24);
                        break;
                    }
                }
            }
            figures.forEach(function (f, i) {
                f.el.style.top = Math.max(0, tops[i]) + 'px';
            });
        }
        measure();
        figures.forEach(scatterPx);
        requestUpdate();
    }

    function update() {
        ticking = false;
        var sy = window.scrollY;
        var still = reduceMotion.matches;
        // ohne Scrollen leer; kurz nach Scrollbeginn sind die verstreuten Striche da
        var maxScroll = document.documentElement.scrollHeight - window.innerHeight;
        var shown = still || maxScroll < 50 ? 1 : Math.min(1, sy / FADE_IN);
        figures.forEach(function (f) {
            if (!f.strokes.length || f.end === undefined) return;
            // 0 = alles verstreut, 1 = Figur fertig
            var p = still ? 1 : Math.min(1, Math.max(0, (sy - f.start) / Math.max(1, f.end - f.start)));
            f.strokes.forEach(function (s) {
                var t = Math.min(1, Math.max(0, (p - s.delay) / (1 - STAGGER)));
                var e = 1 - Math.pow(1 - t, 3);   // sanft ankommen
                var k = 1 - e;
                s.path.style.transform = k > 0.001
                    ? 'translate(' + (s.dx * k).toFixed(1) + 'px,' + (s.dy * k).toFixed(1) + 'px) rotate(' + (s.rot * k).toFixed(1) + 'deg)'
                    : '';
                s.path.style.opacity = (shown * s.base * (0.35 + 0.65 * e)).toFixed(3);
            });
        });
    }

    var ticking = false;
    function requestUpdate() {
        if (!ticking) {
            ticking = true;
            requestAnimationFrame(update);
        }
    }

    window.addEventListener('scroll', requestUpdate, { passive: true });
    window.addEventListener('resize', layout, { passive: true });
    if (reduceMotion.addEventListener) reduceMotion.addEventListener('change', requestUpdate);
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', layout);
    } else {
        layout();
    }
    window.addEventListener('load', layout);
})();
