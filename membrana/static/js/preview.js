/**
 * SVG preview panel: inject, zoom, pan, bézier handle dragging.
 *
 * During bézier drag, the curve is computed client-side for instant feedback.
 * A full server re-render (with lipid placement) happens only on mouse-up.
 */

let zoomLevel = 1.0;
let panX = 0;
let panY = 0;
let isPanning = false;
let startPanX = 0;
let startPanY = 0;
let _draggingHandle = false;  // suppress pan while dragging a handle

function initPreview() {
    const container = document.getElementById('svg-preview');

    container.addEventListener('wheel', (e) => {
        e.preventDefault();
        const delta = e.deltaY > 0 ? 0.9 : 1.1;
        zoomLevel = Math.max(0.1, Math.min(5, zoomLevel * delta));
        applyTransform(container);
    });

    container.addEventListener('mousedown', (e) => {
        if (_draggingHandle) return;
        if (e.button === 1 || (e.button === 0 && e.altKey)) {
            isPanning = true;
            startPanX = e.clientX - panX;
            startPanY = e.clientY - panY;
            container.style.cursor = 'grabbing';
            e.preventDefault();
        }
    });

    window.addEventListener('mousemove', (e) => {
        if (isPanning) {
            panX = e.clientX - startPanX;
            panY = e.clientY - startPanY;
            applyTransform(container);
        }
    });

    window.addEventListener('mouseup', () => {
        if (isPanning) {
            isPanning = false;
            container.style.cursor = '';
        }
    });

    // Double-click to add a bezier point
    container.addEventListener('dblclick', (e) => {
        if (typeof state === 'undefined' || state.membrane.shape !== 'bezier') return;
        const svg = container.querySelector('svg');
        if (!svg) return;

        const pt = svg.createSVGPoint();
        pt.x = e.clientX;
        pt.y = e.clientY;
        const ctm = svg.getScreenCTM();
        if (!ctm) return;
        const svgPt = pt.matrixTransform(ctm.inverse());

        // Insert at correct index sorted by X
        const pts = state.membrane.bezier_points;
        let idx = pts.length;
        for (let i = 0; i < pts.length; i++) {
            if (svgPt.x < pts[i][0]) { idx = i; break; }
        }
        pts.splice(idx, 0, [svgPt.x, svgPt.y]);
        // Keep handle/mode arrays in sync
        if (state.membrane.bezier_handles.length > 0) {
            state.membrane.bezier_handles = computeCatmullRomHandles(pts);
        }
        if (state.membrane.bezier_knot_modes.length > 0) {
            state.membrane.bezier_knot_modes.splice(idx, 0, 'smooth');
        }
        requestRender(state);
        buildControls(state, () => requestRender(state));
    });
}

function applyTransform(container) {
    const svg = container.querySelector('svg');
    if (svg) {
        svg.style.transform = `translate(${panX}px, ${panY}px) scale(${zoomLevel})`;
        svg.style.transformOrigin = 'center center';
    }
}

function updatePreview(svgString) {
    const container = document.getElementById('svg-preview');
    container.innerHTML = svgString;
    applyTransform(container);
    _addBezierHandles(container);
}

function resetZoom() {
    zoomLevel = 1.0;
    panX = 0;
    panY = 0;
    const container = document.getElementById('svg-preview');
    applyTransform(container);
}

// ── Catmull-Rom handle computation ────────────────────────────────

function computeCatmullRomHandles(knots) {
    const n = knots.length;
    if (n < 2) return [];
    const handles = [];
    for (let i = 0; i < n; i++) {
        const pi = knots[i];
        const pim1 = i === 0
            ? [2 * pi[0] - knots[1][0], 2 * pi[1] - knots[1][1]]
            : knots[i - 1];
        const pip1 = i === n - 1
            ? [2 * pi[0] - knots[i - 1][0], 2 * pi[1] - knots[i - 1][1]]
            : knots[i + 1];
        const outDx = (pip1[0] - pim1[0]) / 6.0;
        const outDy = (pip1[1] - pim1[1]) / 6.0;
        handles.push([[-outDx, -outDy], [outDx, outDy]]);
    }
    return handles;
}

function _ensureHandles() {
    const pts = state.membrane.bezier_points;
    if (!state.membrane.bezier_handles || state.membrane.bezier_handles.length !== pts.length) {
        state.membrane.bezier_handles = computeCatmullRomHandles(pts);
    }
    if (!state.membrane.bezier_knot_modes || state.membrane.bezier_knot_modes.length !== pts.length) {
        state.membrane.bezier_knot_modes = pts.map(() => 'smooth');
    }
}

// ── Client-side bézier path computation ──────────────────────────
// Mirrors the Python build_spline_curve() Catmull-Rom → cubic Bézier
// formula so we can show the curve shape instantly during drag.

function _buildBezierPathD(knots, handles) {
    const n = knots.length;
    if (n < 2) return '';

    let d = `M ${knots[0][0]} ${knots[0][1]}`;

    if (n === 2 && (!handles || handles.length === 0)) {
        d += ` L ${knots[1][0]} ${knots[1][1]}`;
        return d;
    }

    for (let i = 0; i < n - 1; i++) {
        const p_i = knots[i];
        const p_ip1 = knots[i + 1];

        // Catmull-Rom neighbours (mirror at endpoints)
        const p_im1 = i === 0
            ? [2 * p_i[0] - p_ip1[0], 2 * p_i[1] - p_ip1[1]]
            : knots[i - 1];
        const p_ip2 = (i + 2 >= n)
            ? [2 * p_ip1[0] - p_i[0], 2 * p_ip1[1] - p_i[1]]
            : knots[i + 2];

        // Catmull-Rom → cubic Bézier control points
        let cp1x = p_i[0] + (p_ip1[0] - p_im1[0]) / 6.0;
        let cp1y = p_i[1] + (p_ip1[1] - p_im1[1]) / 6.0;
        let cp2x = p_ip1[0] - (p_ip2[0] - p_i[0]) / 6.0;
        let cp2y = p_ip1[1] - (p_ip2[1] - p_i[1]) / 6.0;

        // Override with explicit handles when provided
        if (handles && i < handles.length && handles[i] && handles[i].length > 1) {
            const out_h = handles[i][1];
            if (out_h) {
                cp1x = p_i[0] + out_h[0];
                cp1y = p_i[1] + out_h[1];
            }
        }
        if (handles && (i + 1) < handles.length && handles[i + 1]) {
            const in_h = handles[i + 1][0];
            if (in_h) {
                cp2x = p_ip1[0] + in_h[0];
                cp2y = p_ip1[1] + in_h[1];
            }
        }

        d += ` C ${cp1x} ${cp1y}, ${cp2x} ${cp2y}, ${p_ip1[0]} ${p_ip1[1]}`;
    }

    return d;
}

// ── Drag preview (client-side, no server round-trip) ─────────────

function _updateDragPreview(svg) {
    const knots = state.membrane.bezier_points;
    const handles = state.membrane.bezier_handles;
    const modes = state.membrane.bezier_knot_modes;
    const ns = 'http://www.w3.org/2000/svg';

    // 1. Update or create the preview curve path
    let preview = svg.querySelector('.bezier-drag-preview');
    if (!preview) {
        preview = document.createElementNS(ns, 'path');
        preview.setAttribute('class', 'bezier-drag-preview');
        preview.setAttribute('fill', 'none');
        preview.setAttribute('stroke', '#4A90D9');
        preview.setAttribute('stroke-width', '2.5');
        preview.setAttribute('stroke-dasharray', '8,4');
        preview.setAttribute('opacity', '0.7');
        svg.appendChild(preview);
    }
    preview.setAttribute('d', _buildBezierPathD(knots, handles));

    // 2. Rebuild handle overlay
    const oldG = svg.querySelector('.bezier-handles');
    if (oldG) oldG.remove();
    svg.appendChild(_buildHandleGroup(knots, handles, modes));
}

function _removeDragPreview(svg) {
    const preview = svg.querySelector('.bezier-drag-preview');
    if (preview) preview.remove();
}

// ── Shared handle-overlay construction ───────────────────────────

function _buildHandleGroup(points, handles, modes) {
    const ns = 'http://www.w3.org/2000/svg';
    const g = document.createElementNS(ns, 'g');
    g.setAttribute('class', 'bezier-handles');

    for (let i = 0; i < points.length; i++) {
        const kx = points[i][0], ky = points[i][1];
        const h = handles[i] || [null, null];
        const hIn = h[0], hOut = h[1];

        // Handle-in line + tip (skip first knot — no incoming handle)
        if (i > 0 && hIn) {
            const hx = kx + hIn[0], hy = ky + hIn[1];
            const line = document.createElementNS(ns, 'line');
            line.setAttribute('x1', kx); line.setAttribute('y1', ky);
            line.setAttribute('x2', hx); line.setAttribute('y2', hy);
            line.setAttribute('stroke', '#4A90D9');
            line.setAttribute('stroke-width', '1');
            line.setAttribute('opacity', '0.5');
            g.appendChild(line);

            const tip = document.createElementNS(ns, 'circle');
            tip.setAttribute('cx', hx); tip.setAttribute('cy', hy);
            tip.setAttribute('r', '5');
            tip.setAttribute('fill', '#4A90D9');
            tip.setAttribute('fill-opacity', '0.5');
            tip.setAttribute('stroke', '#fff');
            tip.setAttribute('stroke-width', '1.5');
            tip.style.cursor = 'grab';
            tip.dataset.idx = i;
            tip.dataset.handleType = 'in';
            tip.addEventListener('mousedown', _handleTipDragStart);
            g.appendChild(tip);
        }

        // Handle-out line + tip (skip last knot — no outgoing handle)
        if (i < points.length - 1 && hOut) {
            const hx = kx + hOut[0], hy = ky + hOut[1];
            const line = document.createElementNS(ns, 'line');
            line.setAttribute('x1', kx); line.setAttribute('y1', ky);
            line.setAttribute('x2', hx); line.setAttribute('y2', hy);
            line.setAttribute('stroke', '#4A90D9');
            line.setAttribute('stroke-width', '1');
            line.setAttribute('opacity', '0.5');
            g.appendChild(line);

            const tip = document.createElementNS(ns, 'circle');
            tip.setAttribute('cx', hx); tip.setAttribute('cy', hy);
            tip.setAttribute('r', '5');
            tip.setAttribute('fill', '#4A90D9');
            tip.setAttribute('fill-opacity', '0.5');
            tip.setAttribute('stroke', '#fff');
            tip.setAttribute('stroke-width', '1.5');
            tip.style.cursor = 'grab';
            tip.dataset.idx = i;
            tip.dataset.handleType = 'out';
            tip.addEventListener('mousedown', _handleTipDragStart);
            g.appendChild(tip);
        }

        // Knot circle (on top so always grabbable)
        const c = document.createElementNS(ns, 'circle');
        c.setAttribute('cx', kx); c.setAttribute('cy', ky);
        c.setAttribute('r', '7');
        c.setAttribute('fill', '#4A90D9');
        c.setAttribute('fill-opacity', '0.85');
        c.setAttribute('stroke', modes[i] === 'corner' ? '#F59E0B' : '#ffffff');
        c.setAttribute('stroke-width', '2');
        c.style.cursor = 'grab';
        c.dataset.idx = i;
        c.addEventListener('mousedown', _handleKnotDragStart);

        // Alt+click toggles smooth/corner
        c.addEventListener('click', (e) => {
            if (e.altKey) {
                const idx = parseInt(e.target.dataset.idx);
                modes[idx] = modes[idx] === 'corner' ? 'smooth' : 'corner';
                requestRender(state);
            }
        });

        // Right-click to remove (min 2 points)
        c.addEventListener('contextmenu', (e) => {
            e.preventDefault();
            if (points.length > 2) {
                const idx = parseInt(e.target.dataset.idx);
                points.splice(idx, 1);
                handles.splice(idx, 1);
                modes.splice(idx, 1);
                requestRender(state);
                buildControls(state, () => requestRender(state));
            }
        });

        g.appendChild(c);
    }

    return g;
}

// ── Bézier handle overlay (added after server render) ────────────

function _addBezierHandles(container) {
    if (typeof state === 'undefined' || state.membrane.shape !== 'bezier') return;
    const svg = container.querySelector('svg');
    if (!svg) return;

    _ensureHandles();
    svg.appendChild(_buildHandleGroup(
        state.membrane.bezier_points,
        state.membrane.bezier_handles,
        state.membrane.bezier_knot_modes,
    ));
}

// ── Knot drag (moves the through-point) ──────────────────────────

function _handleKnotDragStart(e) {
    if (e.button !== 0 || e.altKey) return;
    e.preventDefault();
    e.stopPropagation();

    _draggingHandle = true;
    const circle = e.target;
    const idx = parseInt(circle.dataset.idx);
    const svg = circle.ownerSVGElement;

    circle.style.cursor = 'grabbing';

    const onMove = (ev) => {
        ev.preventDefault();
        const pt = svg.createSVGPoint();
        pt.x = ev.clientX;
        pt.y = ev.clientY;
        const ctm = svg.getScreenCTM();
        if (!ctm) return;
        const svgPt = pt.matrixTransform(ctm.inverse());

        // Update state (handles are offsets — they travel with the knot)
        state.membrane.bezier_points[idx] = [svgPt.x, svgPt.y];

        // Client-side preview only — no server round-trip
        _updateDragPreview(svg);
    };

    const onUp = () => {
        _draggingHandle = false;
        window.removeEventListener('mousemove', onMove);
        window.removeEventListener('mouseup', onUp);
        _removeDragPreview(svg);
        requestRender(state);  // full server render with lipid placement
    };

    window.addEventListener('mousemove', onMove);
    window.addEventListener('mouseup', onUp);
}

// ── Handle tip drag (adjusts tangent direction/length) ───────────

function _handleTipDragStart(e) {
    if (e.button !== 0) return;
    e.preventDefault();
    e.stopPropagation();

    _draggingHandle = true;
    const tip = e.target;
    const idx = parseInt(tip.dataset.idx);
    const handleType = tip.dataset.handleType;  // 'in' or 'out'
    const svg = tip.ownerSVGElement;

    tip.style.cursor = 'grabbing';

    const onMove = (ev) => {
        ev.preventDefault();
        const pt = svg.createSVGPoint();
        pt.x = ev.clientX;
        pt.y = ev.clientY;
        const ctm = svg.getScreenCTM();
        if (!ctm) return;
        const svgPt = pt.matrixTransform(ctm.inverse());

        const knot = state.membrane.bezier_points[idx];
        const dx = svgPt.x - knot[0];
        const dy = svgPt.y - knot[1];

        const handles = state.membrane.bezier_handles;
        if (handleType === 'in') {
            handles[idx][0] = [dx, dy];
        } else {
            handles[idx][1] = [dx, dy];
        }

        // Mirror opposite handle in smooth mode
        const mode = state.membrane.bezier_knot_modes[idx];
        if (mode === 'smooth') {
            const len = Math.hypot(dx, dy);
            if (handleType === 'in' && handles[idx][1]) {
                const otherLen = Math.hypot(handles[idx][1][0], handles[idx][1][1]);
                if (len > 0.01) {
                    handles[idx][1] = [-dx / len * otherLen, -dy / len * otherLen];
                }
            } else if (handleType === 'out' && handles[idx][0]) {
                const otherLen = Math.hypot(handles[idx][0][0], handles[idx][0][1]);
                if (len > 0.01) {
                    handles[idx][0] = [-dx / len * otherLen, -dy / len * otherLen];
                }
            }
        }

        // Client-side preview only — no server round-trip
        _updateDragPreview(svg);
    };

    const onUp = () => {
        _draggingHandle = false;
        window.removeEventListener('mousemove', onMove);
        window.removeEventListener('mouseup', onUp);
        _removeDragPreview(svg);
        requestRender(state);  // full server render with lipid placement
    };

    window.addEventListener('mousemove', onMove);
    window.addEventListener('mouseup', onUp);
}
