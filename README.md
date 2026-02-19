# Membrana

Interactive web app for creating publication-quality biological membrane SVG diagrams. 29 lipid types, 7 built-in proteins, 5 membrane shapes, real-time preview. Export SVG/PNG for journal figures and teaching. Built with Python (FastAPI) and vanilla JavaScript.

## Quick Start

```bash
# Install
pip install -e .

# Run
python -m membrana
```

The app opens automatically at `http://127.0.0.1:8000`. Changes render in real time via WebSocket.

## Requirements

- Python 3.10+
- fastapi, uvicorn, pydantic (installed automatically)

## Features

### Membrane Shapes

| Shape | Description |
|-------|-------------|
| **Linear** | Straight horizontal bilayer |
| **Circular** | Closed vesicle (full circle) |
| **Elliptical** | Elongated closed vesicle |
| **Cristae** | Mitochondrial inner membrane folds with U-bends and rounded corners |
| **Bezier (custom)** | Free-form curved membrane — drag control points directly on the preview |

The Bezier shape uses Catmull-Rom spline interpolation: you place through-points and the curve passes smoothly through all of them. Double-click the preview to add points, right-click to remove, drag to reshape. Lipids, proteins, and all annotations follow the curve automatically.

**Convert to Bezier** — Any shape can be converted to an editable Bezier curve via the "Convert to Bezier" button in the shape controls. This samples the current shape at evenly-spaced points and switches to Bezier mode, letting you fine-tune any shape with full control-point editing.

### Lipid Types (29 built-in)

All lipids render as schematic headgroup circles with acyl chains. Saturated tails are drawn as wavy curves; unsaturated (cis) tails show a wavy saturated portion followed by a straight segment at 30°, representing the cis double-bond kink. Each lipid has accurate tail count, geometric shape (cylinder/cone/inverted cone), and distinct colors.

Every glycerophospholipid and glycolipid comes in two variants — **saturated** (all-trans, e.g. `PC`) and **unsaturated** (cis, e.g. `cis-PC`) — so you can mix them in any ratio to control membrane fluidity in your diagram.

| Category | Saturated | Unsaturated (cis) |
|----------|-----------|-------------------|
| **Glycerophospholipids** | PC, PE, PS, PI, PA, PG | cis-PC, cis-PE, cis-PS, cis-PI, cis-PA, cis-PG |
| **Cardiolipin** | CL (4 tails) | cis-CL (sn-2 & sn-4 kinked) |
| **Sphingolipids** | SM | — |
| **Sterols** | Cholesterol (rigid ring + short tail) | — |
| **Ceramides** | Ceramide (Cer) | — |
| **Glycolipids** | MGDG, DGDG, MGlcDG, DGlcDG, SQDG | cis-MGDG, cis-DGDG |
| **Lysolipids** | LysoPC, LysoPE | cis-LysoPC, cis-LysoPE |
| **Oxidized** | Truncated PC (tPC) | — |

Lipid composition is set per-leaflet with percentage sliders. Asymmetric leaflets are supported. Distribution along the membrane uses deterministic Bresenham-style dithering for reproducible, evenly mixed placement.

Head and tail colors are independently customizable. Lipid types can be added or removed from the composition at any time. A global "Show cis kinks" toggle lets you turn kink rendering on or off.

### Geometric Shapes Mode

Toggle to overlay each lipid with its molecular geometry outline (cylinder, cone, or inverted cone), useful for teaching lipid shape theory and membrane curvature.

### Proteins (7 built-in)

| Type | Description |
|------|-------------|
| **Single-pass TM** | Single alpha-helix spanning the bilayer |
| **Multi-pass TM** | Multiple transmembrane helices with connecting loops (configurable pass count) |
| **Beta-barrel** | Porin-like barrel structure |
| **Peripheral** | Surface-associated protein on one leaflet |
| **GPI-anchored** | Protein attached via glycosylphosphatidylinositol anchor |
| **Ion channel** | Channel pore structure |
| **ATP synthase** | Rotary motor complex with F0/F1 domains |

Proteins are placed at any position along the membrane (0-100% slider) and colored individually. Multiple proteins can be added to the same membrane.

### Special Modes

**Scissor Mode** — Visualize phospholipase cleavage sites. Supports PLA1, PLA2, PLC, and PLD enzymes. Place multiple scissors on either leaflet at any position. Configurable icon size and color.

**Pore Mode** — Render membrane pores (toroidal or barrel-stave). Lipids in the pore zone are removed and replaced with pore-lining lipids. Adjustable pore radius and position.

**Lipid Raft Mode** — Highlight a membrane domain with increased thickness. Define the raft region (start/end position) and thickness factor.

### Annotations

- **Compartment labels** — Place text above, below, left, or right of the membrane (e.g., "Extracellular", "Cytoplasm")
- **Scale bar** — Configurable length in nanometers
- **Thickness markers** — Show bilayer width measurement
- **Leaflet labels** — Label outer and inner leaflets with custom text
- **Flip-flop arrows** — Show lipid translocation direction

### Presets & Saved Configurations

Seven ready-made presets for common membrane types:

| Preset | Description |
|--------|-------------|
| **Plasma membrane** | Asymmetric animal cell PM — SM/cholesterol-rich outer, PE/PS-rich inner |
| **Mitochondrial IMM** | Cristae shape with high cardiolipin content |
| **Vesicle** | Simple circular vesicle |
| **Bacterial OM** | Bacterial outer membrane (PE/PG/CL) |
| **Thylakoid** | Photosynthetic membrane (MGDG/DGDG glycolipids) |
| **ER membrane** | Endoplasmic reticulum (PC/PE/PI) |
| **Custom** | Blank canvas with PC only |

**Save & Load** — Save your current configuration (all settings: membrane shape, lipid composition, proteins, annotations, special modes) to a named slot. Saved configurations appear in the left nav rail under "Saved" and persist across server restarts. Click to reload, click x to delete.

### Canvas & Export

- Adjustable canvas dimensions (up to 3000 x 2000 px)
- Optional background color
- Configurable membrane fill color (hydrophobic core)
- Zoom (scroll wheel, 0.1x–5x) and pan (Alt+drag or middle mouse)
- One-click SVG and PNG export for use in Illustrator, Inkscape, or directly in publications
- Optional legend showing lipid type color key

## Architecture

```
membrana/
  models/         Pydantic data models (SceneConfig, MembraneConfig, lipids, proteins)
  geometry/       Parametric curves, lipid placement, pore geometry
  rendering/      SVG generation (lipids, proteins, annotations, membrane background)
  server/         FastAPI app, routes, WebSocket handler
  presets/         Built-in preset configurations
  data/           Persistent storage (saved configs)
  static/         Frontend (HTML, CSS, vanilla JS)
```

All membrane shapes are `ParametricCurve` subclasses defining `point(t)`, `tangent(t)`, `normal(t)`, and `arc_length()`. Lipids are placed by sampling curves at uniform arc-length intervals. The geometry module has no SVG knowledge — rendering is cleanly separated.

The frontend maintains a state object mirroring `SceneConfig`. Every control change sends the full state over WebSocket; the server validates with Pydantic, renders SVG, and streams it back. Typical round-trip is under 100ms.

## API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/render` | POST | Render SVG from a SceneConfig JSON body |
| `/api/presets` | GET | List available presets |
| `/api/presets/{id}` | GET | Load a specific preset configuration |
| `/api/lipid-types` | GET | Get the default lipid type library |
| `/api/export` | POST | Export SVG as a downloadable file |
| `/api/sample-curve` | POST | Sample current curve as points (for Bezier conversion) |
| `/api/saved-configs` | GET | List user-saved configurations |
| `/api/saved-configs` | POST | Save the current configuration |
| `/api/saved-configs/{id}` | GET | Load a saved configuration |
| `/api/saved-configs/{id}` | DELETE | Delete a saved configuration |
| `/ws/preview` | WebSocket | Live preview — send config, receive SVG |

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Lint
ruff check .
```

## License

MIT
