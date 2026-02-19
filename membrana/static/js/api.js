/**
 * API communication layer: WebSocket + REST.
 */

let ws = null;
let wsReady = false;
let onSvgUpdate = null;
let onStatusChange = null;

function connectWebSocket() {
    const proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
    ws = new WebSocket(`${proto}//${location.host}/ws/preview`);

    ws.onopen = () => {
        wsReady = true;
        if (onStatusChange) onStatusChange('connected');
    };

    ws.onclose = () => {
        wsReady = false;
        if (onStatusChange) onStatusChange('disconnected');
        // Reconnect after 2s
        setTimeout(connectWebSocket, 2000);
    };

    ws.onerror = () => {
        wsReady = false;
        if (onStatusChange) onStatusChange('error');
    };

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.status === 'ok' && onSvgUpdate) {
            onSvgUpdate(data.svg);
        } else if (data.status === 'error') {
            console.error('Render error:', data.message);
            if (onStatusChange) onStatusChange('error');
        }
    };
}

let _debounceTimer = null;

function requestRender(state) {
    clearTimeout(_debounceTimer);
    _debounceTimer = setTimeout(() => {
        if (ws && wsReady) {
            ws.send(JSON.stringify(state));
        } else {
            // Fallback to REST
            fetch('/api/render', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(state),
            })
            .then(r => r.json())
            .then(data => {
                if (data.svg && onSvgUpdate) onSvgUpdate(data.svg);
            })
            .catch(err => console.error('Render error:', err));
        }
    }, 100);
}

async function fetchPresets() {
    const r = await fetch('/api/presets');
    const data = await r.json();
    return data.presets;
}

async function loadPreset(presetId) {
    const r = await fetch(`/api/presets/${presetId}`);
    return await r.json();
}

async function exportSvg(state) {
    const r = await fetch('/api/export', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(state),
    });
    const blob = await r.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'membrane.svg';
    a.click();
    URL.revokeObjectURL(url);
}
