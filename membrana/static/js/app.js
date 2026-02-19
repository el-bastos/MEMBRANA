/**
 * Main application: state management, nav rail, initialization.
 */

// Default state mirrors SceneConfig
const state = {
    canvas_width: 1200,
    canvas_height: 600,
    background_color: null,
    membrane: {
        shape: 'linear',
        length: 800,
        width: 60,
        radius: 200,
        ellipse_rx: 250,
        ellipse_ry: 150,
        cristae_width: 80,
        cristae_depth: 200,
        cristae_count: 2,
        cristae_spacing: 100,
        bezier_points: [[200,300],[450,250],[750,350],[1000,300]],
        bezier_handles: [],
        bezier_knot_modes: [],
        lipid_base_size: 10,
        lipid_spacing: 0.5,
        tail_length_factor: 0.9,
        leaflet_gap: 0,
        show_geometric_shapes: false,
        show_kinks: true,
        show_head_stroke: true,
        show_3d: false,
        depth_rows: 5,
        row_spacing: 6,
        membrane_color: '#FDEBD0',
    },
    lipid_types: [],  // Loaded from server
    composition: {
        outer_leaflet: { ratios: { PC: 0.5, PE: 0.3, cholesterol: 0.2 } },
        inner_leaflet: { ratios: { PC: 0.5, PE: 0.3, cholesterol: 0.2 } },
        asymmetric: false,
    },
    proteins: [],
    annotations: {
        compartment_labels: [],
        show_scale_bar: false,
        scale_bar_nm: 5,
        show_thickness_markers: false,
        flip_flop_arrows: [],
        show_leaflet_labels: false,
        outer_leaflet_label: 'Outer leaflet',
        inner_leaflet_label: 'Inner leaflet',
    },
    scissor_mode: { enabled: false, enzyme: 'PLA2', placements: [{ position_t: 0.5, leaflet: 'outer' }], scissor_color: '#FF0000', scissor_size: 20 },
    pore_mode: { enabled: false, pore_radius: 30, num_lipids_in_pore: 8, placements: [{ position_t: 0.5 }] },
    raft_mode: { enabled: false, thickness_factor: 1.3, placements: [{ start_t: 0.3, end_t: 0.6 }] },
    show_legend: true,
};

// ── Shape definitions for nav rail ──────────────────────────

const SHAPES = [
    {
        value: 'linear',
        label: 'Linear',
        icon: '<svg viewBox="0 0 24 24" fill="none"><line x1="3" y1="12" x2="21" y2="12" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/></svg>',
    },
    {
        value: 'circular',
        label: 'Circle',
        icon: '<svg viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="8" stroke="currentColor" stroke-width="2"/></svg>',
    },
    {
        value: 'elliptical',
        label: 'Ellipse',
        icon: '<svg viewBox="0 0 24 24" fill="none"><ellipse cx="12" cy="12" rx="10" ry="6" stroke="currentColor" stroke-width="2"/></svg>',
    },
    {
        value: 'cristae',
        label: 'Cristae',
        icon: '<svg viewBox="0 0 24 24" fill="none"><path d="M2 6h3v0a4 4 0 0 1 4 4v4a4 4 0 0 0 4 4v0h0a4 4 0 0 0 4-4v-4a4 4 0 0 1 4-4h1" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>',
    },
    {
        value: 'bezier',
        label: 'Bezier',
        icon: '<svg viewBox="0 0 24 24" fill="none"><path d="M3 16C7 6 17 20 21 10" stroke="currentColor" stroke-width="2" stroke-linecap="round"/><circle cx="3" cy="16" r="2" fill="currentColor"/><circle cx="21" cy="10" r="2" fill="currentColor"/></svg>',
    },
];

const PRESET_COLORS = {
    plasma_membrane: '#4A90D9',
    mito_imm: '#E74C3C',
    vesicle: '#5DADE2',
    bacterial_om: '#27AE60',
    thylakoid: '#2ECC71',
    er_membrane: '#8E44AD',
    custom: '#888888',
};

// ── Initialization ──────────────────────────────────────────

async function init() {
    // Load lipid types from server
    try {
        const r = await fetch('/api/lipid-types');
        const data = await r.json();
        state.lipid_types = data.lipid_types;
    } catch (e) {
        console.error('Failed to load lipid types:', e);
    }

    // Set up WebSocket
    onSvgUpdate = (svg) => {
        updatePreview(svg);
        const status = document.getElementById('ws-status');
        status.textContent = 'Live';
        status.className = 'status connected';
    };

    onStatusChange = (s) => {
        const status = document.getElementById('ws-status');
        if (s === 'connected') {
            status.textContent = 'Live';
            status.className = 'status connected';
        } else if (s === 'error') {
            status.textContent = 'Error';
            status.className = 'status error';
        } else {
            status.textContent = 'Reconnecting...';
            status.className = 'status';
        }
    };

    connectWebSocket();
    initPreview();

    // Build nav rail
    buildShapeNav();

    // Load presets into nav
    try {
        const presets = await fetchPresets();
        buildPresetNav(presets);
    } catch (e) {
        console.error('Failed to load presets:', e);
    }

    // Build right sidebar controls
    buildControls(state, () => requestRender(state));

    // Export buttons
    document.getElementById('btn-export-svg').addEventListener('click', () => exportSvg(state));
    document.getElementById('btn-export-png').addEventListener('click', () => exportPng(state));
    document.getElementById('btn-reset-zoom').addEventListener('click', resetZoom);

    // Initial render
    requestRender(state);
}

// ── Nav rail builders ───────────────────────────────────────

function buildShapeNav() {
    const nav = document.getElementById('shape-nav');
    nav.innerHTML = '';

    for (const shape of SHAPES) {
        const btn = document.createElement('button');
        btn.className = 'nav-item' + (state.membrane.shape === shape.value ? ' active' : '');
        btn.innerHTML = shape.icon + '<span class="nav-label">' + shape.label + '</span>';
        btn.title = shape.label;
        btn.dataset.shape = shape.value;

        btn.addEventListener('click', async () => {
            // Convert current shape to bezier by sampling its curve
            if (shape.value === 'bezier' && state.membrane.shape !== 'bezier') {
                const nPoints = { linear: 5, circular: 16, elliptical: 16, cristae: 30 }[state.membrane.shape] || 20;
                try {
                    const r = await fetch(`/api/sample-curve?num_points=${nPoints}`, {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify(state),
                    });
                    const data = await r.json();
                    if (data.points && data.points.length >= 2) {
                        state.membrane.bezier_points = data.points;
                        // Initialize handles from Catmull-Rom
                        if (typeof computeCatmullRomHandles === 'function') {
                            state.membrane.bezier_handles = computeCatmullRomHandles(data.points);
                            state.membrane.bezier_knot_modes = data.points.map(() => 'smooth');
                        }
                    }
                } catch (e) {
                    console.error('Convert to Bezier failed:', e);
                }
            }
            state.membrane.shape = shape.value;
            // Update active state
            nav.querySelectorAll('.nav-item').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            // Rebuild right sidebar (shape params change)
            buildControls(state, () => requestRender(state));
            requestRender(state);
        });

        nav.appendChild(btn);
    }
}

function buildPresetNav(presets) {
    const nav = document.getElementById('preset-nav');
    nav.innerHTML = '';

    for (const p of presets) {
        const btn = document.createElement('button');
        btn.className = 'preset-item';
        const dot = document.createElement('span');
        dot.className = 'preset-dot';
        dot.style.background = PRESET_COLORS[p.id] || '#888';
        const label = document.createElement('span');
        label.textContent = p.name;
        btn.append(dot, label);

        btn.addEventListener('click', async () => {
            const config = await loadPreset(p.id);
            if (config.error) return;
            Object.assign(state.membrane, config.membrane);
            Object.assign(state.composition, config.composition);
            state.proteins = config.proteins || [];
            Object.assign(state.annotations, config.annotations || {});
            state.show_legend = config.show_legend ?? true;
            if (config.lipid_types) state.lipid_types = config.lipid_types;
            // Update shape nav active state
            buildShapeNav();
            // Rebuild right sidebar
            buildControls(state, () => requestRender(state));
            requestRender(state);
        });

        nav.appendChild(btn);
    }
}

// ── PNG export ──────────────────────────────────────────────

function exportPng(appState) {
    const container = document.getElementById('svg-preview');
    const svgEl = container.querySelector('svg');
    if (!svgEl) return;

    const svgData = new XMLSerializer().serializeToString(svgEl);
    const svgBlob = new Blob([svgData], { type: 'image/svg+xml;charset=utf-8' });
    const url = URL.createObjectURL(svgBlob);

    const img = new Image();
    img.onload = () => {
        const scale = 2;  // 2x for retina
        const canvas = document.createElement('canvas');
        canvas.width = appState.canvas_width * scale;
        canvas.height = appState.canvas_height * scale;
        const ctx = canvas.getContext('2d');
        ctx.scale(scale, scale);
        // White background
        ctx.fillStyle = '#ffffff';
        ctx.fillRect(0, 0, appState.canvas_width, appState.canvas_height);
        ctx.drawImage(img, 0, 0, appState.canvas_width, appState.canvas_height);
        URL.revokeObjectURL(url);

        canvas.toBlob((blob) => {
            const a = document.createElement('a');
            a.href = URL.createObjectURL(blob);
            a.download = 'membrane.png';
            a.click();
            URL.revokeObjectURL(a.href);
        }, 'image/png');
    };
    img.src = url;
}

document.addEventListener('DOMContentLoaded', init);
