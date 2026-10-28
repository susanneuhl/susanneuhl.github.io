/* Kontakt-Hintergrund „Stofflager“.
   Ein Gang im Stofflager in Zentralperspektive (wie die Saal-Zeichnungen auf der Termine-Seite):
   rechts eine Regalwand, auf jedem Boden liegen Stoffrollen quer, die Stirnseiten mit Wickelspirale
   und Papphülse zeigen in den Gang, an manchen hängen Etiketten, aus drei Rollen hängt eine Bahn
   über die Kante. Dielen laufen zum Fluchtpunkt und blenden zum Text hin aus.

   Bewegung: beim Laden eine kurze Kamerafahrt in den Gang. Danach steht das Bild still und
   reagiert nur: die Kamera folgt der Maus ein wenig (Parallaxe), Bahnen und Etiketten pendeln,
   wenn man durch sie hindurchfährt, und beim Kopieren der Adresse geht ein Luftzug durch den Gang,
   eine Rolle dreht sich. Gezeichnet wird nur, solange sich etwas bewegt.
   prefers-reduced-motion: ein stilles Bild, keine Animation.

   Alles im 3D-Modell in Metern; Kamera schaut entlang +z. Einstellungen siehe KONFIG unten.
   Kopier-Signal: contact.html löst nach erfolgreichem Kopieren 'contact:copied' auf document aus. */
(function () {
    'use strict';
    var hero = document.querySelector('.contact-hero');
    if (!hero || !window.HTMLCanvasElement) return;
    var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    var canvas = document.createElement('canvas');
    canvas.className = 'contact-stofflager';
    canvas.setAttribute('aria-hidden', 'true');
    hero.insertBefore(canvas, hero.firstChild);
    var ctx = canvas.getContext('2d');

    /* ---------- KONFIG ---------- */
    var WHITE = '255,255,255', OCHRE = '214,178,92', RED = '190,52,60', BG = '#1a1a1a';
    var A = 0.9;              // Abstand Kamera → Vorderkante der Regalwand (m)
    var DEPTH = 1.5;          // Regaltiefe = Rollenlänge (m)
    var EYE = 1.6;            // Augenhöhe (m)
    var LEVELS = [0.08, 0.62, 1.16, 1.7, 2.24], TOP = 2.78;   // Regalböden (m)
    var POST_STEP = 2.4;      // Abstand der Regalstützen (m)
    var SEED = 21;

    /* ---------- Maße / Kamera ---------- */
    var W = 0, H = 0, S = 1, dpr = 1, mobile = false;
    var VPX = 0, VPY = 0, F = 0, boxes = [], Z_MAX = 13;
    var cam = { x: 0, y: EYE, z: 0 };
    function measure() {
        var r = hero.getBoundingClientRect();
        W = r.width; H = r.height; mobile = W <= 768;
        S = mobile ? W / 390 : H / 900;
        dpr = Math.min(2, window.devicePixelRatio || 1);
        canvas.width = Math.round(W * dpr); canvas.height = Math.round(H * dpr);
        var sel = ['.contact-hero-overlay h2', '.mail-link', '#copyBtn'];
        if (mobile) sel.push('body.page-contact footer');   // Handy: Fußzeile liegt über der Fläche
        boxes = sel.map(function (s) {
            var e = document.querySelector(s); if (!e) return null;
            var q = e.getBoundingClientRect();
            return q.width ? [q.left - r.left, q.top - r.top, q.right - r.left, q.bottom - r.top] : null;
        }).filter(Boolean);
        var tb = boxes.slice(0, 3).reduce(function (a, b) { return [Math.min(a[0], b[0]), Math.min(a[1], b[1]), Math.max(a[2], b[2]), Math.max(a[3], b[3])]; }, [1e9, 1e9, -1e9, -1e9]);
        if (!boxes.length) tb = [W * 0.22, H * 0.4, W * 0.55, H * 0.68];
        if (mobile) {
            // Handy: Fluchtpunkt unter dem Kopier-Knopf, die Wand steigt rechts auf
            VPX = W * 0.36; VPY = Math.min(H - 150 * S, tb[3] + 120 * S); F = 560 * S;
        } else {
            // Desktop: Fluchtpunkt knapp rechts neben der Adresse, auf Höhe über dem Titel
            VPX = tb[2] + 110 * S; VPY = 330 * S; F = 900 * S;
        }
    }

    /* ---------- Szene erzeugen ---------- */
    function rng(seed) {
        return function () {
            seed |= 0; seed = seed + 0x6D2B79F5 | 0;
            var t = Math.imul(seed ^ seed >>> 15, 1 | seed);
            t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t;
            return ((t ^ t >>> 14) >>> 0) / 4294967296;
        };
    }
    var rand = rng(SEED);
    var KINDS = ['glatt', 'glatt', 'glatt', 'streifen', 'karo', 'fein', 'grob'];
    function makeRoll(y, z, r, li) {
        var p = rand();
        return {
            y: y, z: z, r: r, li: li, rgb: p < 0.05 ? OCHRE : p < 0.09 ? RED : WHITE,
            kind: KINDS[Math.floor(rand() * KINDS.length)], xf: A - rand() * 0.09, xb: A + DEPTH,
            rot: rand() * 6.28, spin: 0, turns: 3 + Math.floor(rand() * 4),
            tag: rand() < 0.22 ? { th: (rand() - 0.5) * 0.3, om: 0, ph: rand() * 6.28 } : null
        };
    }
    var rolls = [], posts = [];
    for (var pz = 1.2; pz < 15; pz += POST_STEP) posts.push(pz);
    LEVELS.forEach(function (yb, li) {
        var low = [], z = 1.3 + rand() * 0.2;
        while (z < 15) {
            var r = 0.075 + rand() * 0.065, cz = z + r;
            if (posts.some(function (p) { return Math.abs(p - cz) < r + 0.03; })) { z += 0.06; continue; }
            low.push(makeRoll(yb + r, cz, r, li));
            z = cz + r + 0.004 + (rand() < 0.08 ? rand() * 0.25 : 0);
        }
        rolls.push.apply(rolls, low);
        for (var i = 0; i + 1 < low.length; i++) {
            var a = low[i], b = low[i + 1];
            if (rand() < 0.45 || b.z - a.z > a.r + b.r + 0.08) continue;
            var r2 = 0.065 + rand() * 0.05;
            rolls.push(makeRoll(yb + Math.max(a.r, b.r) + r2 * 0.92, (a.z + b.z) / 2, r2, li));
        }
    });
    rolls.sort(function (a, b) { return b.z - a.z; });   // von hinten nach vorn zeichnen

    var tails = [];
    [[2.2, 3.0, 2, OCHRE, 0.46, 'satin'], [4.2, 5.2, 3, WHITE, 0.4, 'streifen'], [3.0, 3.8, 1, RED, 0.4, 'samt']].forEach(function (d) {
        var c = rolls.filter(function (R) { return R.li === d[2] && R.z > d[0] && R.z < d[1] && R.y - LEVELS[d[2]] < R.r + 0.01; });
        var R = c[Math.floor(c.length / 2)];
        if (!R) return;
        R.rgb = d[3]; R.tail = { R: R, L: d[4], kind: d[5], th: 0, om: 0, ph: rand() * 6.28 };
        tails.push(R.tail);
    });

    /* ---------- Zeichenhelfer ---------- */
    function P(x, y, z) {
        var zc = z - cam.z;
        if (zc < 0.25) return null;
        return [VPX + F * (x - cam.x) / zc, VPY - F * (y - cam.y) / zc, zc];
    }
    function pen(a, rgb, w) { ctx.strokeStyle = 'rgba(' + (rgb || WHITE) + ',' + Math.max(0, a).toFixed(3) + ')'; ctx.lineWidth = w || 1; }
    function path(pts, close) {
        ctx.beginPath();
        for (var i = 0; i < pts.length; i++) { if (i) ctx.lineTo(pts[i][0], pts[i][1]); else ctx.moveTo(pts[i][0], pts[i][1]); }
        if (close) ctx.closePath();
    }
    function seg(a, b, al, rgb, w) { if (!a || !b) return; pen(al, rgb, w); ctx.beginPath(); ctx.moveTo(a[0], a[1]); ctx.lineTo(b[0], b[1]); ctx.stroke(); }
    function fog(zc) { return Math.max(0.12, Math.min(1, 1.15 - (zc - 2.5) / 9)); }
    function ring(x, y, z, r, n) {
        var pts = [];
        for (var i = 0; i <= n; i++) { var t = i / n * 6.283, p = P(x, y + r * Math.cos(t), z + r * Math.sin(t)); if (!p) return null; pts.push(p); }
        return pts;
    }
    function mod(x) { return ((x % 6.283) + 6.283) % 6.283; }

    /* ---------- Rolle ---------- */
    function drawRoll(R, alpha) {
        var cf = P(R.xf, R.y, R.z), cb = P(R.xb, R.y, R.z);
        if (!cf || !cb) return;
        if (cf[0] > W + 400 || cf[1] < -300 || cf[1] > H + 300) return;
        var zc = cf[2], a = alpha * fog(zc) * (R.rgb === WHITE ? 0.2 : 0.28);
        var n = zc < 5 ? 24 : zc < 9 ? 14 : 10;
        var ef = ring(R.xf, R.y, R.z, R.r, n); if (!ef) return;
        // Umriss: die beiden Punkte der Stirnseite mit größtem Abstand zur Rollenachse
        var dx = cb[0] - cf[0], dy = cb[1] - cf[1], dl = Math.hypot(dx, dy) || 1, nx = -dy / dl, ny = dx / dl;
        var iMax = 0, iMin = 0, vMax = -1e9, vMin = 1e9, i;
        for (i = 0; i < n; i++) { var v = (ef[i][0] - cf[0]) * nx + (ef[i][1] - cf[1]) * ny; if (v > vMax) { vMax = v; iMax = i; } if (v < vMin) { vMin = v; iMin = i; } }
        var tMax = iMax / n * 6.283, tMin = iMin / n * 6.283;
        var bMax = P(R.xb, R.y + R.r * Math.cos(tMax), R.z + R.r * Math.sin(tMax)), bMin = P(R.xb, R.y + R.r * Math.cos(tMin), R.z + R.r * Math.sin(tMin));
        if (!bMax || !bMin) return;
        ctx.fillStyle = BG;
        path([ef[iMax], bMax, bMin, ef[iMin]], true); ctx.fill();
        path(ef, true); ctx.fill();
        pen(a, R.rgb); ctx.beginPath();
        ctx.moveTo(ef[iMax][0], ef[iMax][1]); ctx.lineTo(bMax[0], bMax[1]);
        ctx.moveTo(ef[iMin][0], ef[iMin][1]); ctx.lineTo(bMin[0], bMin[1]); ctx.stroke();
        path(ef, true); ctx.stroke();

        if (zc < 8) {   // Muster auf der sichtbaren Mantelseite
            var span = mod(tMax - tMin), phi = Math.atan2(cam.z - R.z, cam.y - R.y);
            var camSide = mod(phi - tMin) <= span;
            var visible = function (th) { return (mod(th - tMin) <= span) === camSide; };
            var k;
            if (R.kind === 'streifen' || R.kind === 'karo') {
                pen(a * 0.5, R.rgb, 0.8);
                for (k = 1; k < 7; k++) {
                    var x = R.xf + (R.xb - R.xf) * k / 7 * 0.6, pts = [], started = false;
                    for (i = 0; i <= 24; i++) {
                        var th = tMin + i / 24 * 6.283;
                        if (visible(th)) { var q = P(x, R.y + R.r * Math.cos(th), R.z + R.r * Math.sin(th)); if (q) { pts.push(q); started = true; } }
                        else if (started) break;
                    }
                    if (pts.length > 1) { path(pts); ctx.stroke(); }
                }
            }
            var gen = R.kind === 'karo' ? 4 : R.kind === 'grob' ? 3 : 1;
            for (k = 1; k <= gen; k++) {
                var th2 = camSide ? tMin + span * k / (gen + 1) : tMax + (6.283 - span) * k / (gen + 1);
                seg(P(R.xf, R.y + R.r * Math.cos(th2), R.z + R.r * Math.sin(th2)), P(R.xf + (R.xb - R.xf) * 0.7, R.y + R.r * Math.cos(th2), R.z + R.r * Math.sin(th2)), a * 0.4, R.rgb, 0.8);
            }
        }
        if (zc < 10) {  // Papphülse, ragt etwas heraus
            var tr = R.r * 0.3, t2 = ring(R.xf - 0.035, R.y, R.z, tr, 12);
            if (t2) {
                path(t2, true); ctx.fillStyle = BG; ctx.fill(); pen(a * 0.9, WHITE); ctx.stroke();
                if (zc < 5) { var t3 = ring(R.xf - 0.035, R.y, R.z, tr * 0.7, 10); if (t3) { pen(a * 0.5, WHITE, 0.8); path(t3, true); ctx.stroke(); } }
            }
        }
        if (zc < 7) {   // Wickelspirale: grob = wenige Windungen, fein = viele
            var turns = R.kind === 'fein' ? 8 : R.kind === 'grob' ? 3 : R.turns, steps = turns * (zc < 4 ? 14 : 9), sp = [];
            for (i = 0; i <= steps; i++) {
                var q2 = i / steps, ang = R.rot + q2 * turns * 6.283, rr = R.r * (0.32 + 0.64 * q2);
                var pp = P(R.xf, R.y + rr * Math.cos(ang), R.z + rr * Math.sin(ang)); if (pp) sp.push(pp);
            }
            pen(a * 0.55, R.rgb, 0.8); path(sp); ctx.stroke();
        }
        if (R.tag && zc < 6) drawTag(R, a);
        if (R.tail) drawTail(R.tail, alpha);
    }

    /* ---------- Etikett an der Hülse ---------- */
    function drawTag(R, a) {
        var T = R.tag, x = R.xf - 0.04, ty = R.y - R.r * 0.15, tz = R.z;
        var s = Math.sin(T.th), c = Math.cos(T.th), L = 0.07, hy = ty - L * c, hz = tz + L * s;
        var corners = [[-0.022, 0], [0.022, 0], [0.022, -0.06], [-0.022, -0.06]].map(function (o) {
            return P(x, hy + o[0] * s + o[1] * c, hz + o[0] * c - o[1] * s);
        });
        T.screen = P(x, ty, tz);
        seg(T.screen, P(x, hy, hz), a * 0.8, WHITE, 0.7);
        if (corners.every(Boolean)) { path(corners, true); ctx.fillStyle = BG; ctx.fill(); pen(a * 1.1, WHITE, 0.8); ctx.stroke(); }
    }

    /* ---------- Überhängende Stoffbahn ---------- */
    function tailPoint(T, u, v) {   // u quer (in die Wand), v nach unten (0…1)
        var R = T.R, x0 = R.xf + 0.01, x1 = R.xf + DEPTH * 0.85;
        var fold = Math.sin(u * 6.283 * 2.5 + T.ph) * 0.025 * v;
        return P(x0 + (x1 - x0) * u + T.th * 0.12 * v, R.y - R.r * 0.3 - T.L * v + 0.02 * Math.sin(u * 9 + T.ph) * v, R.z - R.r * 0.6 - T.th * 0.25 * v + fold);
    }
    function drawTail(T, alpha) {
        var sil = [], u, v, k;
        for (u = 0; u <= 1.0001; u += 0.05) sil.push(tailPoint(T, u, 0));
        for (u = 1; u >= -0.0001; u -= 0.05) sil.push(tailPoint(T, u, 1));
        if (!sil.every(Boolean)) return;
        T.screen = tailPoint(T, 0.3, 0.6);
        var a = alpha * fog(sil[0][2]) * 0.3, rgb = T.R.rgb;
        path(sil, true); ctx.fillStyle = BG; ctx.fill(); pen(a, rgb); ctx.stroke();
        var nLines = T.kind === 'samt' ? 12 : T.kind === 'streifen' ? 14 : 6;
        for (k = 1; k < nLines; k++) {
            u = k / nLines; var col = [];
            for (v = 0; v <= 1.0001; v += 0.1) col.push(tailPoint(T, u, v));
            var aa = T.kind === 'streifen' ? (k % 2 ? a * 0.7 : a * 0.3) : T.kind === 'samt' ? a * (0.3 + 0.4 * Math.max(0, Math.sin(k * 1.1))) : a * 0.45;
            pen(aa, rgb, 0.8); path(col); ctx.stroke();
        }
    }

    /* ---------- Regal, Boden, Textfreiraum ---------- */
    function drawShelf(alpha) {
        var X = A + 0.03, z0 = cam.z + 0.3, a = alpha * 0.18;
        LEVELS.concat([TOP]).forEach(function (y) {
            seg(P(X, y, z0), P(X, y, Z_MAX), a);
            seg(P(X, y - 0.035, z0), P(X, y - 0.035, Z_MAX), a * 0.6, WHITE, 0.8);
        });
        seg(P(A + DEPTH, TOP, z0), P(A + DEPTH, TOP, Z_MAX), a * 0.5);
        seg(P(X, 0, z0), P(X, 0, Z_MAX), a);
    }
    function drawPosts(alpha) {
        var X = A + 0.03;
        posts.forEach(function (z) {
            var p0 = P(X, 0, z), p1 = P(X, TOP + 0.05, z), q0 = P(X, 0, z + 0.05), q1 = P(X, TOP + 0.05, z + 0.05);
            if (!p0 || !q0) return;
            path([p0, p1, q1, q0], true); ctx.fillStyle = BG; ctx.fill();
            pen(alpha * 0.22 * fog(p0[2]), WHITE); ctx.stroke();
        });
    }
    function drawFloor(alpha) {
        [-2.2, -1.5, -0.8, -0.1, 0.5].forEach(function (x) {
            for (var z = cam.z + 0.6; z < Z_MAX; z += 0.5) seg(P(x, 0, z), P(x, 0, z + 0.5), alpha * 0.1 * fog(z - cam.z));
        });
        [3, 4.5, 6.5, 9].forEach(function (z) { seg(P(-3, 0, z), P(A, 0, z), alpha * 0.05 * fog(z - cam.z)); });
    }
    function clearText(list) {   // weicher Freiraum um Titel, Adresse und Knopf
        ctx.save(); ctx.globalCompositeOperation = 'destination-out';
        list.forEach(function (b) {
            function rr(p, al) {
                ctx.fillStyle = 'rgba(0,0,0,' + al + ')';
                var x = b[0] - p, y = b[1] - p, w = b[2] - b[0] + 2 * p, h = b[3] - b[1] + 2 * p, r = Math.min(p + 10, h / 2);
                ctx.beginPath(); ctx.moveTo(x + r, y); ctx.arcTo(x + w, y, x + w, y + h, r); ctx.arcTo(x + w, y + h, x, y + h, r);
                ctx.arcTo(x, y + h, x, y, r); ctx.arcTo(x, y, x + w, y, r); ctx.closePath(); ctx.fill();
            }
            rr(16, 1);
            for (var k = 1; k <= 10; k++) rr(16 + k * 12 * S, 0.16);
        });
        ctx.restore();
    }
    function union(list) {
        return [list.reduce(function (a, b) { return [Math.min(a[0], b[0]), Math.min(a[1], b[1]), Math.max(a[2], b[2]), Math.max(a[3], b[3])]; })];
    }

    function render(alpha) {
        ctx.setTransform(1, 0, 0, 1, 0, 0);
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
        ctx.lineJoin = 'round';
        drawFloor(alpha);
        if (!mobile && boxes.length) clearText(union(boxes));   // Desktop: nur die Dielen weichen dem Text
        drawShelf(alpha);
        rolls.forEach(function (R) { drawRoll(R, alpha); });
        drawPosts(alpha);
        if (mobile && boxes.length) clearText(boxes);           // Handy: die Wand steht hinter dem Text, also alles freistellen
    }

    /* ---------- Bewegung ---------- */
    var mouse = { x: 0.5, y: 0.5, tx: 0.5, ty: 0.5 };
    var ptr = { x: -1e4, y: -1e4, vx: 0, lx: null };
    var gust = 0, t0 = null, prev = 0, running = false;
    window.addEventListener('pointermove', function (e) {
        var r = hero.getBoundingClientRect(), x = e.clientX - r.left;
        if (e.pointerType === 'mouse') { mouse.tx = x / r.width; mouse.ty = (e.clientY - r.top) / r.height; }
        if (ptr.lx !== null) ptr.vx = x - ptr.lx;
        ptr.lx = x; ptr.x = x; ptr.y = e.clientY - r.top;
        wake();
    }, { passive: true });
    document.addEventListener('contact:copied', function () {
        if (reduce) return;
        gust = 1;
        var near = rolls.filter(function (R) { return R.z - cam.z < 3 && R.z - cam.z > 1.4 && R.li === 1; });
        (near[0] || rolls[rolls.length - 1]).spin = 9;
        wake();
    });

    function pendulum(o, k, damp, force, dt, lim) {
        o.om += (-k * o.th - damp * o.om + force) * dt;
        o.th = Math.max(-lim, Math.min(lim, o.th + o.om * dt));
        return Math.abs(o.om) > 0.005 || Math.abs(o.th) > 0.004;
    }
    function near(p, dx, dy) { return p && Math.abs(ptr.x - p[0]) < dx && Math.abs(ptr.y - p[1]) < dy; }

    function step(t, dt) {
        var busy = t < 3;
        var intro = reduce ? 1 : 1 - Math.pow(1 - Math.min(1, t / 2.6), 3);
        mouse.x += (mouse.tx - mouse.x) * 0.06; mouse.y += (mouse.ty - mouse.y) * 0.06;
        busy = busy || Math.abs(mouse.tx - mouse.x) > 0.0005 || Math.abs(mouse.ty - mouse.y) > 0.0005;
        cam.z = -1.6 * (1 - intro);
        cam.x = (mouse.x - 0.5) * (mobile ? 0 : 0.14);
        cam.y = EYE - (mouse.y - 0.5) * (mobile ? 0 : 0.08);
        tails.forEach(function (T) {
            var f = gust * 2.2 + (near(T.screen, 160 * S, 120 * S) ? ptr.vx * 0.06 : 0);
            if (pendulum(T, 6, 1.4, f, dt, 0.5)) busy = true;
        });
        rolls.forEach(function (R) {
            if (R.tag) {
                var f = gust * 3 * Math.sin(R.tag.ph) + (near(R.tag.screen, 40 * S, 60 * S) ? ptr.vx * 0.15 : 0);
                if (pendulum(R.tag, 14, 2.6, f, dt, 0.8)) busy = true;
            }
            if (R.spin) { R.rot += R.spin * dt; R.spin *= Math.pow(0.25, dt); if (R.spin < 0.02) R.spin = 0; else busy = true; }
        });
        if (gust > 0) { gust = Math.max(0, gust - dt * 1.8); busy = true; }
        ptr.vx *= 0.85;
        render(reduce ? 1 : Math.min(1, t / 1.2));
        return busy;
    }
    function frame(now) {
        if (t0 === null) t0 = now;
        var t = (now - t0) / 1000, dt = Math.max(0, Math.min(0.05, t - prev)); prev = t;
        if (step(t, dt)) requestAnimationFrame(frame); else running = false;
    }
    function wake() { if (!running && !reduce) { running = true; requestAnimationFrame(frame); } }

    measure();
    if (reduce) { cam.z = 0; render(1); }
    else wake();
    var rt = null;
    window.addEventListener('resize', function () {
        clearTimeout(rt);
        rt = setTimeout(function () { measure(); if (reduce || !running) render(1); }, 80);
    });
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(function () { measure(); if (reduce || !running) render(1); });
})();
