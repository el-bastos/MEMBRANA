/**
 * Dynamic control panel generation (right sidebar).
 * Uses a horizontal tab strip instead of accordion sections.
 * Shape selection and presets are in the left nav rail (built by app.js).
 */

// Persist active tab across rebuilds
let _activeTab = 'membrane';

function buildControls(state, onUpdate) {

    let _rebuildLipidColors = null;

    // ── Helper builders ────────────────────────────────

    function slider(label, value, min, max, step, onChange) {
        const row = document.createElement('div');
        row.className = 'control-row';
        const lbl = document.createElement('label');
        lbl.textContent = label;
        const inp = document.createElement('input');
        inp.type = 'range';
        inp.min = min;
        inp.max = max;
        inp.step = step;
        inp.value = value;
        const val = document.createElement('span');
        val.className = 'value-display';
        val.textContent = Number(value).toFixed(step < 1 ? 1 : 0);
        inp.addEventListener('input', () => {
            val.textContent = Number(inp.value).toFixed(step < 1 ? 1 : 0);
            onChange(parseFloat(inp.value));
        });
        row.append(lbl, inp, val);
        return row;
    }

    function dropdown(label, value, options, onChange) {
        const row = document.createElement('div');
        row.className = 'control-row';
        const lbl = document.createElement('label');
        lbl.textContent = label;
        const sel = document.createElement('select');
        for (const opt of options) {
            const o = document.createElement('option');
            o.value = opt.value;
            o.textContent = opt.label;
            if (opt.value === value) o.selected = true;
            sel.appendChild(o);
        }
        sel.addEventListener('change', () => onChange(sel.value));
        row.append(lbl, sel);
        return row;
    }

    function toggle(label, checked, onChange) {
        const row = document.createElement('div');
        row.className = 'toggle-row';
        const lbl = document.createElement('label');
        lbl.textContent = label;
        const tog = document.createElement('label');
        tog.className = 'toggle';
        const inp = document.createElement('input');
        inp.type = 'checkbox';
        inp.checked = checked;
        const sl = document.createElement('span');
        sl.className = 'slider';
        inp.addEventListener('change', () => onChange(inp.checked));
        tog.append(inp, sl);
        row.append(lbl, tog);
        return row;
    }

    function colorPicker(label, value, onChange) {
        const row = document.createElement('div');
        row.className = 'control-row';
        const lbl = document.createElement('label');
        lbl.textContent = label;
        const inp = document.createElement('input');
        inp.type = 'color';
        inp.value = value;
        inp.addEventListener('input', () => onChange(inp.value));
        row.append(lbl, inp);
        return row;
    }

    function subHeader(text) {
        const h = document.createElement('div');
        h.className = 'panel-group-header';
        h.textContent = text;
        return h;
    }

    function textInput(label, value, onChange) {
        const row = document.createElement('div');
        row.className = 'control-row';
        const lbl = document.createElement('label');
        lbl.textContent = label;
        const inp = document.createElement('input');
        inp.type = 'text';
        inp.value = value;
        inp.style.cssText = 'flex:1; padding:5px 8px; background:var(--input-bg); color:var(--text-primary); border:1px solid var(--border-strong); border-radius:6px; font-size:11px; font-family:inherit; outline:none;';
        inp.addEventListener('focus', () => { inp.style.borderColor = 'var(--accent)'; });
        inp.addEventListener('blur', () => { inp.style.borderColor = 'var(--border-strong)'; });
        inp.addEventListener('change', () => onChange(inp.value));
        row.append(lbl, inp);
        return row;
    }

    // ── Build tab strip + panel container ────────────────

    const tabsContainer = document.getElementById('sidebar-tabs');
    const panelsContainer = document.getElementById('controls');
    tabsContainer.innerHTML = '';
    panelsContainer.innerHTML = '';

    const TABS = [
        {
            id: 'membrane',
            label: 'Membrane',
            icon: '<svg viewBox="0 0 16 16" fill="none"><path d="M1 5.5c4-3 10 3 14 0" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/><path d="M1 10.5c4-3 10 3 14 0" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>',
        },
        {
            id: 'lipids',
            label: 'Lipids',
            icon: '<svg viewBox="0 0 16 16" fill="none"><circle cx="8" cy="4.5" r="2.5" stroke="currentColor" stroke-width="1.5"/><line x1="8" y1="7" x2="8" y2="14" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>',
        },
        {
            id: 'proteins',
            label: 'Proteins',
            icon: '<svg viewBox="0 0 16 16" fill="none"><rect x="5" y="1" width="6" height="14" rx="3" stroke="currentColor" stroke-width="1.5"/></svg>',
        },
        {
            id: 'overlays',
            label: 'Overlays',
            icon: '<svg viewBox="0 0 16 16" fill="none"><path d="M2 10l6-3 6 3-6 3z" stroke="currentColor" stroke-width="1.3" stroke-linejoin="round"/><path d="M2 7l6-3 6 3" stroke="currentColor" stroke-width="1.3" stroke-linejoin="round" opacity="0.5"/></svg>',
        },
        {
            id: 'canvas',
            label: 'Canvas',
            icon: '<svg viewBox="0 0 16 16" fill="none"><rect x="2" y="2" width="12" height="12" rx="1.5" stroke="currentColor" stroke-width="1.5"/></svg>',
        },
    ];

    function switchTab(tabId) {
        _activeTab = tabId;
        tabsContainer.querySelectorAll('.sidebar-tab').forEach(t =>
            t.classList.toggle('active', t.dataset.tab === tabId));
        panelsContainer.querySelectorAll('.sidebar-panel').forEach(p =>
            p.classList.toggle('active', p.id === 'panel-' + tabId));
        panelsContainer.scrollTop = 0;
    }

    const panels = {};
    for (const tab of TABS) {
        const btn = document.createElement('button');
        btn.className = 'sidebar-tab' + (tab.id === _activeTab ? ' active' : '');
        btn.dataset.tab = tab.id;
        btn.innerHTML = tab.icon + '<span>' + tab.label + '</span>';
        btn.addEventListener('click', () => switchTab(tab.id));
        tabsContainer.appendChild(btn);

        const panel = document.createElement('div');
        panel.className = 'sidebar-panel' + (tab.id === _activeTab ? ' active' : '');
        panel.id = 'panel-' + tab.id;
        panelsContainer.appendChild(panel);
        panels[tab.id] = panel;
    }

    // ════════════════════════════════════════════════════════════
    // MEMBRANE TAB
    // ════════════════════════════════════════════════════════════

    const shapeParams = document.createElement('div');
    shapeParams.id = 'shape-params';
    panels.membrane.appendChild(shapeParams);

    function rebuildShapeControls() {
        shapeParams.innerHTML = '';
        const m = state.membrane;

        if (m.shape === 'linear') {
            shapeParams.appendChild(slider('Length', m.length, 200, 2000, 10, v => { m.length = v; onUpdate(); }));
        } else if (m.shape === 'circular') {
            shapeParams.appendChild(slider('Radius', m.radius, 50, 500, 5, v => { m.radius = v; onUpdate(); }));
        } else if (m.shape === 'elliptical') {
            shapeParams.appendChild(slider('Width (rx)', m.ellipse_rx, 50, 600, 5, v => { m.ellipse_rx = v; onUpdate(); }));
            shapeParams.appendChild(slider('Height (ry)', m.ellipse_ry, 50, 600, 5, v => { m.ellipse_ry = v; onUpdate(); }));
        } else if (m.shape === 'cristae') {
            shapeParams.appendChild(slider('Width', m.cristae_width, 30, 200, 5, v => { m.cristae_width = v; onUpdate(); }));
            shapeParams.appendChild(slider('Depth', m.cristae_depth, 50, 400, 10, v => { m.cristae_depth = v; onUpdate(); }));
            shapeParams.appendChild(slider('Count', m.cristae_count, 1, 6, 1, v => { m.cristae_count = v; onUpdate(); }));
            shapeParams.appendChild(slider('Spacing', m.cristae_spacing, 40, 300, 10, v => { m.cristae_spacing = v; onUpdate(); }));
        } else if (m.shape === 'bezier') {
            const info = document.createElement('div');
            info.className = 'sub-label';
            info.textContent = m.bezier_points.length + ' points — drag knots, drag handles to reshape';
            shapeParams.appendChild(info);

            const hint = document.createElement('div');
            hint.style.cssText = 'font-size:9px; color:var(--text-muted); margin-bottom:6px;';
            hint.textContent = 'Alt+click knot: toggle smooth/corner';
            shapeParams.appendChild(hint);

            const btnRow = document.createElement('div');
            btnRow.style.cssText = 'display:flex; gap:6px; margin-top:4px; margin-bottom:12px; flex-wrap:wrap;';

            const addBtn = document.createElement('button');
            addBtn.className = 'btn btn-sm';
            addBtn.textContent = '+ Add point';
            addBtn.addEventListener('click', () => {
                const pts = m.bezier_points;
                const last = pts[pts.length - 1];
                const prev = pts.length > 1 ? pts[pts.length - 2] : [last[0] - 100, last[1]];
                pts.push([(last[0] + prev[0]) / 2 + 80, (last[1] + prev[1]) / 2]);
                if (typeof computeCatmullRomHandles === 'function') {
                    m.bezier_handles = computeCatmullRomHandles(pts);
                    m.bezier_knot_modes = pts.map(() => 'smooth');
                }
                rebuildShapeControls();
                onUpdate();
            });

            const resetBtn = document.createElement('button');
            resetBtn.className = 'btn btn-sm';
            resetBtn.textContent = 'Reset points';
            resetBtn.addEventListener('click', () => {
                m.bezier_points = [[200,300],[450,250],[750,350],[1000,300]];
                m.bezier_handles = [];
                m.bezier_knot_modes = [];
                rebuildShapeControls();
                onUpdate();
            });

            const resetHandlesBtn = document.createElement('button');
            resetHandlesBtn.className = 'btn btn-sm';
            resetHandlesBtn.textContent = 'Reset handles';
            resetHandlesBtn.addEventListener('click', () => {
                if (typeof computeCatmullRomHandles === 'function') {
                    m.bezier_handles = computeCatmullRomHandles(m.bezier_points);
                    m.bezier_knot_modes = m.bezier_points.map(() => 'smooth');
                }
                onUpdate();
            });

            btnRow.append(addBtn, resetBtn, resetHandlesBtn);
            shapeParams.appendChild(btnRow);
        }

        shapeParams.appendChild(slider('Thickness', m.width, 20, 150, 2, v => { m.width = v; onUpdate(); }));
    }
    rebuildShapeControls();

    panels.membrane.appendChild(colorPicker('Membrane fill', state.membrane.membrane_color || '#FDEBD0', v => {
        state.membrane.membrane_color = v; onUpdate();
    }));

    // 3D depth effect (linear shape only)
    panels.membrane.appendChild(subHeader('3D Effect'));
    panels.membrane.appendChild(toggle('Enable 3D depth', state.membrane.show_3d, v => {
        state.membrane.show_3d = v; rebuild3D(); onUpdate();
    }));

    const depthContainer = document.createElement('div');
    panels.membrane.appendChild(depthContainer);

    function rebuild3D() {
        depthContainer.innerHTML = '';
        if (!state.membrane.show_3d) return;
        depthContainer.appendChild(slider('Depth rows', state.membrane.depth_rows, 2, 8, 1, v => {
            state.membrane.depth_rows = v; onUpdate();
        }));
        depthContainer.appendChild(slider('Row spacing', state.membrane.row_spacing, 2, 20, 1, v => {
            state.membrane.row_spacing = v; onUpdate();
        }));
    }
    rebuild3D();

    // ════════════════════════════════════════════════════════════
    // LIPIDS TAB
    // ════════════════════════════════════════════════════════════

    // ── Composition ──
    panels.lipids.appendChild(subHeader('Composition'));

    panels.lipids.appendChild(toggle('Asymmetric leaflets', state.composition.asymmetric, v => {
        state.composition.asymmetric = v;
        rebuildComposition();
        onUpdate();
    }));

    const compContainer = document.createElement('div');
    compContainer.id = 'comp-container';
    panels.lipids.appendChild(compContainer);

    function rebuildComposition() {
        compContainer.innerHTML = '';
        const lbl1 = document.createElement('div');
        lbl1.className = 'sub-label';
        lbl1.textContent = state.composition.asymmetric ? 'Outer leaflet' : 'Both leaflets';
        compContainer.appendChild(lbl1);
        compContainer.appendChild(buildCompositionSliders(state.composition.outer_leaflet.ratios, 'outer'));
        if (state.composition.asymmetric) {
            const lbl2 = document.createElement('div');
            lbl2.className = 'sub-label';
            lbl2.textContent = 'Inner leaflet';
            compContainer.appendChild(lbl2);
            compContainer.appendChild(buildCompositionSliders(state.composition.inner_leaflet.ratios, 'inner'));
        }
        if (_rebuildLipidColors) _rebuildLipidColors();
    }

    function buildCompositionSliders(ratios, leaflet) {
        const wrap = document.createElement('div');
        const types = state.lipid_types;
        const ids = Object.keys(ratios);
        const pctEls = {};
        const sliderEls = {};

        for (const id of ids) {
            const lt = types.find(t => t.id === id);
            if (!lt) continue;
            const row = document.createElement('div');
            row.className = 'composition-row';
            const sw = document.createElement('div');
            sw.className = 'swatch';
            sw.style.background = lt.head_color;
            const name = document.createElement('span');
            name.className = 'lipid-name';
            name.textContent = lt.abbreviation;
            const inp = document.createElement('input');
            inp.type = 'range';
            inp.min = 0;
            inp.max = 100;
            inp.step = 1;
            inp.value = Math.round(ratios[id] * 100);
            const pct = document.createElement('span');
            pct.className = 'pct';
            pct.textContent = Math.round(ratios[id] * 100) + '%';
            sliderEls[id] = inp;
            pctEls[id] = pct;

            inp.addEventListener('input', () => {
                const newVal = parseInt(inp.value);
                redistributeComposition(ratios, id, newVal / 100, ids, sliderEls, pctEls);
                onUpdate();
            });

            row.append(sw, name, inp, pct);

            if (ids.length > 1) {
                const rmBtn = document.createElement('button');
                rmBtn.className = 'remove-btn';
                rmBtn.innerHTML = '&times;';
                rmBtn.addEventListener('click', () => {
                    delete ratios[id];
                    const total = Object.values(ratios).reduce((a, b) => a + b, 0);
                    if (total > 0) for (const k of Object.keys(ratios)) ratios[k] /= total;
                    rebuildComposition();
                    onUpdate();
                });
                row.appendChild(rmBtn);
            }

            wrap.appendChild(row);
        }

        // Add lipid type button
        const addRow = document.createElement('div');
        addRow.style.marginTop = '6px';
        const addSel = document.createElement('select');
        addSel.style.cssText = 'flex:1; padding:3px 5px; background:var(--input-bg); color:var(--text-primary); border:1px solid var(--border-strong); border-radius:4px; font-size:10px; margin-right:4px; font-family:inherit;';
        for (const lt of types) {
            if (ratios[lt.id] !== undefined) continue;
            const o = document.createElement('option');
            o.value = lt.id;
            o.textContent = lt.abbreviation;
            addSel.appendChild(o);
        }
        if (addSel.options.length > 0) {
            const addBtn = document.createElement('button');
            addBtn.className = 'btn btn-sm';
            addBtn.textContent = '+ Add';
            addBtn.addEventListener('click', () => {
                const lid = addSel.value;
                ratios[lid] = 0.05;
                const total = Object.values(ratios).reduce((a, b) => a + b, 0);
                for (const k of Object.keys(ratios)) ratios[k] /= total;
                rebuildComposition();
                onUpdate();
            });
            addRow.append(addSel, addBtn);
            wrap.appendChild(addRow);
        }
        return wrap;
    }

    function redistributeComposition(ratios, changedId, newVal, ids, sliderEls, pctEls) {
        const others = ids.filter(id => id !== changedId);
        const oldOtherSum = others.reduce((s, id) => s + ratios[id], 0);
        const remainder = 1.0 - newVal;

        ratios[changedId] = newVal;
        if (oldOtherSum > 0.001) {
            const scale = remainder / oldOtherSum;
            for (const id of others) {
                ratios[id] = ratios[id] * scale;
            }
        } else {
            const each = remainder / others.length;
            for (const id of others) ratios[id] = each;
        }

        for (const id of ids) {
            const pctVal = Math.round(ratios[id] * 100);
            if (sliderEls[id]) sliderEls[id].value = pctVal;
            if (pctEls[id]) pctEls[id].textContent = pctVal + '%';
        }
    }

    rebuildComposition();

    // ── Colors ──
    panels.lipids.appendChild(subHeader('Colors'));
    const ltColorsContainer = document.createElement('div');
    panels.lipids.appendChild(ltColorsContainer);

    _rebuildLipidColors = function() {
        ltColorsContainer.innerHTML = '';
        const usedIds = new Set([
            ...Object.keys(state.composition.outer_leaflet.ratios),
            ...(state.composition.asymmetric ? Object.keys(state.composition.inner_leaflet.ratios) : []),
        ]);
        for (const lt of state.lipid_types) {
            if (!usedIds.has(lt.id)) continue;
            ltColorsContainer.appendChild(colorPicker(lt.abbreviation + ' head', lt.head_color, v => {
                lt.head_color = v; onUpdate();
            }));
            ltColorsContainer.appendChild(colorPicker(lt.abbreviation + ' tail', lt.tail_color, v => {
                lt.tail_color = v; onUpdate();
            }));
        }
    };
    _rebuildLipidColors();

    // ── Display ──
    panels.lipids.appendChild(subHeader('Display'));

    panels.lipids.appendChild(slider('Base size', state.membrane.lipid_base_size, 4, 30, 1, v => {
        state.membrane.lipid_base_size = v; onUpdate();
    }));
    panels.lipids.appendChild(slider('Spacing', state.membrane.lipid_spacing, -8, 15, 0.5, v => {
        state.membrane.lipid_spacing = v; onUpdate();
    }));
    panels.lipids.appendChild(slider('Tail length', state.membrane.tail_length_factor * 100, 20, 100, 5, v => {
        state.membrane.tail_length_factor = v / 100; onUpdate();
    }));
    panels.lipids.appendChild(slider('Leaflet gap', state.membrane.leaflet_gap, -20, 40, 1, v => {
        state.membrane.leaflet_gap = v; onUpdate();
    }));
    panels.lipids.appendChild(toggle('Geometric shapes', state.membrane.show_geometric_shapes, v => {
        state.membrane.show_geometric_shapes = v; onUpdate();
    }));
    panels.lipids.appendChild(toggle('Show cis kinks', state.membrane.show_kinks, v => {
        state.membrane.show_kinks = v; onUpdate();
    }));
    panels.lipids.appendChild(toggle('Head outline', state.membrane.show_head_stroke, v => {
        state.membrane.show_head_stroke = v; onUpdate();
    }));

    // ════════════════════════════════════════════════════════════
    // PROTEINS TAB
    // ════════════════════════════════════════════════════════════

    const protList = document.createElement('div');
    protList.id = 'protein-list';
    panels.proteins.appendChild(protList);

    const addProtBtn = document.createElement('button');
    addProtBtn.className = 'btn btn-sm';
    addProtBtn.textContent = '+ Add protein';
    addProtBtn.addEventListener('click', () => {
        state.proteins.push({
            id: 'prot_' + Date.now(),
            kind: 'single_pass_tm',
            label: '',
            color: '#8B5CF6',
            position_t: 0.5,
            width: 40,
            height: 80,
            num_passes: 1,
            leaflet: 'both',
        });
        rebuildProteins();
        onUpdate();
    });
    panels.proteins.appendChild(addProtBtn);

    function rebuildProteins() {
        protList.innerHTML = '';
        for (let i = 0; i < state.proteins.length; i++) {
            const p = state.proteins[i];
            const item = document.createElement('div');
            item.className = 'protein-item';

            const sel = document.createElement('select');
            for (const opt of [
                'single_pass_tm', 'multi_pass_tm', 'beta_barrel',
                'peripheral', 'gpi_anchored', 'ion_channel', 'atp_synthase',
            ]) {
                const o = document.createElement('option');
                o.value = opt;
                o.textContent = opt.replace(/_/g, ' ');
                if (opt === p.kind) o.selected = true;
                sel.appendChild(o);
            }
            sel.addEventListener('change', () => { p.kind = sel.value; rebuildProteins(); onUpdate(); });

            const posInp = document.createElement('input');
            posInp.type = 'range';
            posInp.min = 0;
            posInp.max = 100;
            posInp.value = Math.round(p.position_t * 100);
            posInp.title = 'Position along membrane';
            posInp.addEventListener('input', () => { p.position_t = parseInt(posInp.value) / 100; onUpdate(); });

            const colInp = document.createElement('input');
            colInp.type = 'color';
            colInp.value = p.color;
            colInp.style.cssText = 'width:24px; height:24px; border:1px solid var(--border-strong); border-radius:4px; padding:1px;';
            colInp.addEventListener('input', () => { p.color = colInp.value; onUpdate(); });

            const rmBtn = document.createElement('button');
            rmBtn.className = 'remove-btn';
            rmBtn.innerHTML = '&times;';
            rmBtn.addEventListener('click', () => {
                state.proteins.splice(i, 1);
                rebuildProteins();
                onUpdate();
            });

            item.append(sel, posInp, colInp, rmBtn);

            if (p.kind === 'multi_pass_tm') {
                const npInp = document.createElement('input');
                npInp.type = 'number';
                npInp.min = 2;
                npInp.max = 12;
                npInp.value = p.num_passes;
                npInp.style.width = '40px';
                npInp.title = 'Number of TM passes';
                npInp.addEventListener('change', () => { p.num_passes = parseInt(npInp.value) || 2; onUpdate(); });
                item.insertBefore(npInp, rmBtn);
            }

            protList.appendChild(item);
        }
    }
    rebuildProteins();

    // ════════════════════════════════════════════════════════════
    // OVERLAYS TAB
    // ════════════════════════════════════════════════════════════

    // ── Annotations ──
    panels.overlays.appendChild(subHeader('Annotations'));

    panels.overlays.appendChild(toggle('Show legend', state.show_legend, v => {
        state.show_legend = v; onUpdate();
    }));
    panels.overlays.appendChild(toggle('Leaflet labels', state.annotations.show_leaflet_labels, v => {
        state.annotations.show_leaflet_labels = v; onUpdate();
    }));
    panels.overlays.appendChild(toggle('Scale bar', state.annotations.show_scale_bar, v => {
        state.annotations.show_scale_bar = v; onUpdate();
    }));
    panels.overlays.appendChild(toggle('Thickness markers', state.annotations.show_thickness_markers, v => {
        state.annotations.show_thickness_markers = v; onUpdate();
    }));

    // Compartment labels
    if (!state.annotations.compartment_labels.find(l => l.position === 'top')) {
        state.annotations.compartment_labels.push({ text: '', position: 'top', font_size: 14, color: '#333333' });
    }
    if (!state.annotations.compartment_labels.find(l => l.position === 'bottom')) {
        state.annotations.compartment_labels.push({ text: '', position: 'bottom', font_size: 14, color: '#333333' });
    }

    const topLabel = state.annotations.compartment_labels.find(l => l.position === 'top');
    const botLabel = state.annotations.compartment_labels.find(l => l.position === 'bottom');
    panels.overlays.appendChild(textInput('Top label', topLabel.text, v => { topLabel.text = v; onUpdate(); }));
    panels.overlays.appendChild(textInput('Bottom label', botLabel.text, v => { botLabel.text = v; onUpdate(); }));

    // ── Special Modes ──
    panels.overlays.appendChild(subHeader('Special Modes'));

    // Scissors
    panels.overlays.appendChild(toggle('Scissor mode', state.scissor_mode.enabled, v => {
        state.scissor_mode.enabled = v; rebuildScissors(); onUpdate();
    }));

    const scissorContainer = document.createElement('div');
    panels.overlays.appendChild(scissorContainer);

    function rebuildScissors() {
        scissorContainer.innerHTML = '';
        if (!state.scissor_mode.enabled) return;

        scissorContainer.appendChild(dropdown('Enzyme', state.scissor_mode.enzyme, [
            { value: 'PLA1', label: 'PLA1' },
            { value: 'PLA2', label: 'PLA2' },
            { value: 'PLC', label: 'PLC' },
            { value: 'PLD', label: 'PLD' },
        ], v => { state.scissor_mode.enzyme = v; onUpdate(); }));

        scissorContainer.appendChild(slider('Scissor size', state.scissor_mode.scissor_size, 8, 50, 1, v => {
            state.scissor_mode.scissor_size = v; onUpdate();
        }));

        scissorContainer.appendChild(colorPicker('Scissor color', state.scissor_mode.scissor_color, v => {
            state.scissor_mode.scissor_color = v; onUpdate();
        }));

        const placementsLabel = document.createElement('div');
        placementsLabel.className = 'sub-label';
        placementsLabel.textContent = 'Scissor placements';
        scissorContainer.appendChild(placementsLabel);

        const placementsList = document.createElement('div');
        for (let i = 0; i < state.scissor_mode.placements.length; i++) {
            const pl = state.scissor_mode.placements[i];
            const item = document.createElement('div');
            item.className = 'protein-item';
            item.style.marginBottom = '4px';

            const posLabel = document.createElement('span');
            posLabel.textContent = '#' + (i + 1);
            posLabel.style.cssText = 'font-size:10px; color:var(--text-secondary); min-width:20px;';

            const posInp = document.createElement('input');
            posInp.type = 'range';
            posInp.min = 0;
            posInp.max = 100;
            posInp.step = 1;
            posInp.value = Math.round(pl.position_t * 100);
            posInp.title = 'Position along membrane';
            posInp.addEventListener('input', () => { pl.position_t = parseInt(posInp.value) / 100; onUpdate(); });

            const leafletSel = document.createElement('select');
            leafletSel.style.cssText = 'padding:2px 4px; background:var(--input-bg); color:var(--text-primary); border:1px solid var(--border-strong); border-radius:4px; font-size:10px; font-family:inherit;';
            for (const opt of [{ value: 'outer', label: 'Outer' }, { value: 'inner', label: 'Inner' }]) {
                const o = document.createElement('option');
                o.value = opt.value;
                o.textContent = opt.label;
                if (opt.value === pl.leaflet) o.selected = true;
                leafletSel.appendChild(o);
            }
            leafletSel.addEventListener('change', () => { pl.leaflet = leafletSel.value; onUpdate(); });

            const rmBtn = document.createElement('button');
            rmBtn.className = 'remove-btn';
            rmBtn.innerHTML = '&times;';
            rmBtn.addEventListener('click', () => {
                state.scissor_mode.placements.splice(i, 1);
                rebuildScissors();
                onUpdate();
            });

            item.append(posLabel, posInp, leafletSel, rmBtn);
            placementsList.appendChild(item);
        }
        scissorContainer.appendChild(placementsList);

        const addBtn = document.createElement('button');
        addBtn.className = 'btn btn-sm';
        addBtn.textContent = '+ Add scissor';
        addBtn.addEventListener('click', () => {
            state.scissor_mode.placements.push({ position_t: 0.5, leaflet: 'outer' });
            rebuildScissors();
            onUpdate();
        });
        scissorContainer.appendChild(addBtn);
    }
    rebuildScissors();

    // Pore
    panels.overlays.appendChild(toggle('Pore mode', state.pore_mode.enabled, v => {
        state.pore_mode.enabled = v; rebuildPore(); onUpdate();
    }));

    const poreContainer = document.createElement('div');
    panels.overlays.appendChild(poreContainer);

    function rebuildPore() {
        poreContainer.innerHTML = '';
        if (!state.pore_mode.enabled) return;

        // Ensure placements array exists (backward compat)
        if (!state.pore_mode.placements) {
            state.pore_mode.placements = [{ position_t: state.pore_mode.position_t || 0.5 }];
        }

        poreContainer.appendChild(slider('Pore radius', state.pore_mode.pore_radius, 10, 80, 2, v => {
            state.pore_mode.pore_radius = v; onUpdate();
        }));

        const placementsLabel = document.createElement('div');
        placementsLabel.className = 'sub-label';
        placementsLabel.textContent = 'Pore placements';
        poreContainer.appendChild(placementsLabel);

        const placementsList = document.createElement('div');
        for (let i = 0; i < state.pore_mode.placements.length; i++) {
            const pl = state.pore_mode.placements[i];
            const item = document.createElement('div');
            item.className = 'protein-item';
            item.style.marginBottom = '4px';

            const posLabel = document.createElement('span');
            posLabel.textContent = '#' + (i + 1);
            posLabel.style.cssText = 'font-size:10px; color:var(--text-secondary); min-width:20px;';

            const posInp = document.createElement('input');
            posInp.type = 'range';
            posInp.min = 5;
            posInp.max = 95;
            posInp.step = 1;
            posInp.value = Math.round(pl.position_t * 100);
            posInp.title = 'Position along membrane';
            posInp.addEventListener('input', () => { pl.position_t = parseInt(posInp.value) / 100; onUpdate(); });

            const rmBtn = document.createElement('button');
            rmBtn.className = 'remove-btn';
            rmBtn.innerHTML = '&times;';
            rmBtn.addEventListener('click', () => {
                state.pore_mode.placements.splice(i, 1);
                rebuildPore();
                onUpdate();
            });

            item.append(posLabel, posInp, rmBtn);
            placementsList.appendChild(item);
        }
        poreContainer.appendChild(placementsList);

        const addBtn = document.createElement('button');
        addBtn.className = 'btn btn-sm';
        addBtn.textContent = '+ Add pore';
        addBtn.addEventListener('click', () => {
            state.pore_mode.placements.push({ position_t: 0.5 });
            rebuildPore();
            onUpdate();
        });
        poreContainer.appendChild(addBtn);
    }
    rebuildPore();

    // Raft
    panels.overlays.appendChild(toggle('Lipid raft', state.raft_mode.enabled, v => {
        state.raft_mode.enabled = v; rebuildRaft(); onUpdate();
    }));

    const raftContainer = document.createElement('div');
    panels.overlays.appendChild(raftContainer);

    function rebuildRaft() {
        raftContainer.innerHTML = '';
        if (!state.raft_mode.enabled) return;

        // Ensure placements array exists (backward compat)
        if (!state.raft_mode.placements) {
            state.raft_mode.placements = [{ start_t: state.raft_mode.start_t || 0.3, end_t: state.raft_mode.end_t || 0.6 }];
        }

        raftContainer.appendChild(slider('Thickness factor', state.raft_mode.thickness_factor, 1.0, 2.0, 0.1, v => {
            state.raft_mode.thickness_factor = v; onUpdate();
        }));

        const placementsLabel = document.createElement('div');
        placementsLabel.className = 'sub-label';
        placementsLabel.textContent = 'Raft regions';
        raftContainer.appendChild(placementsLabel);

        const placementsList = document.createElement('div');
        for (let i = 0; i < state.raft_mode.placements.length; i++) {
            const pl = state.raft_mode.placements[i];
            const item = document.createElement('div');
            item.style.cssText = 'margin-bottom:8px; padding:6px; background:var(--surface-alt, rgba(255,255,255,0.03)); border-radius:6px;';

            const header = document.createElement('div');
            header.style.cssText = 'display:flex; align-items:center; justify-content:space-between; margin-bottom:4px;';
            const label = document.createElement('span');
            label.textContent = 'Region #' + (i + 1);
            label.style.cssText = 'font-size:10px; color:var(--text-secondary);';
            const rmBtn = document.createElement('button');
            rmBtn.className = 'remove-btn';
            rmBtn.innerHTML = '&times;';
            rmBtn.addEventListener('click', () => {
                state.raft_mode.placements.splice(i, 1);
                rebuildRaft();
                onUpdate();
            });
            header.append(label, rmBtn);
            item.appendChild(header);

            item.appendChild(slider('Start', pl.start_t * 100, 0, 100, 1, v => {
                pl.start_t = v / 100; onUpdate();
            }));
            item.appendChild(slider('End', pl.end_t * 100, 0, 100, 1, v => {
                pl.end_t = v / 100; onUpdate();
            }));

            placementsList.appendChild(item);
        }
        raftContainer.appendChild(placementsList);

        const addBtn = document.createElement('button');
        addBtn.className = 'btn btn-sm';
        addBtn.textContent = '+ Add raft region';
        addBtn.addEventListener('click', () => {
            state.raft_mode.placements.push({ start_t: 0.3, end_t: 0.6 });
            rebuildRaft();
            onUpdate();
        });
        raftContainer.appendChild(addBtn);
    }
    rebuildRaft();

    // ════════════════════════════════════════════════════════════
    // CANVAS TAB
    // ════════════════════════════════════════════════════════════

    panels.canvas.appendChild(slider('Width', state.canvas_width, 400, 3000, 50, v => {
        state.canvas_width = v; onUpdate();
    }));
    panels.canvas.appendChild(slider('Height', state.canvas_height, 300, 2000, 50, v => {
        state.canvas_height = v; onUpdate();
    }));
    panels.canvas.appendChild(colorPicker('Background', state.background_color || '#ffffff', v => {
        state.background_color = v === '#ffffff' ? null : v; onUpdate();
    }));
}
