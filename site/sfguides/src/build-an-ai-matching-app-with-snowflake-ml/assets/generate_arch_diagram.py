#!/usr/bin/env python3
"""
Generate architecture diagram using ELK for layout + matplotlib for rendering.
v15 — Fix edge crossing and edge-boundary spacing issues.

Pipeline:  Graph spec → ELK (Node.js) → positioned JSON → matplotlib PNG
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from matplotlib.path import Path as MplPath
import matplotlib.patheffects as pe
from PIL import Image
import numpy as np
import json
import subprocess
import os
import tempfile

# ── Colors ──────────────────────────────────────────────────────────
SF_WHITE = '#FFFFFF'
SF_TEXT = '#1B2A4A'
SF_SUBTITLE = '#5A6B7D'
SF_BOUNDARY = '#29B5E8'

TIER_COLORS = {
    'primary':   '#2E4057',
    'secondary': '#4A6B8A',
    'tertiary':  '#7A9BB5',
}
TIER_LW = {'primary': 2.2, 'secondary': 1.7, 'tertiary': 1.4}
TIER_DASH = {'primary': None, 'secondary': None, 'tertiary': (4, 3)}
TIER_ARROW_SCALE = {'primary': 15, 'secondary': 13, 'tertiary': 11}

SF_GROUP_BG = [
    '#DCF2FB', '#D8EFD9', '#FFF0D6', '#EDD9F7', '#F7D9D9', '#D9E6F7',
]
SF_GROUP_BORDER = [
    '#1A8AB5', '#2E7D42', '#E68A00', '#7B1FA2', '#C62828', '#1565C0',
]

ICON_DIR = '/tmp/arch_diagram_icons'
ELK_DIR = '/tmp/elk_layout'

# ── Node definitions ────────────────────────────────────────────────
# (id, label, subtitle, icon_file, column_index)
nodes = [
    ('raw_events',      'RAW Events',       '500K rows',         'raw_events.png',      0),
    ('dynamic_table',   'Dynamic Table',    '2-min refresh',     'dynamic_table.png',    1),
    ('feature_store',   'Feature Store',    'Entity + Views',    'feature_store.png',    1),
    ('xgboost',         'XGBoost',          'GridSearchCV',      'xgboost.png',          2),
    ('model_registry',  'Model Registry',   'V1 + V2',          'model_registry.png',   2),
    ('spcs',            'SPCS REST API',    'scale-to-zero',     'spcs.png',             3),
    ('cortex_search',   'Cortex Search',    'hybrid semantic',   'cortex_search.png',    3),
    ('model_monitor',   'Model Monitor',    'PSI drift',         'model_monitor.png',    4),
    ('ml_lineage',      'ML Lineage',       'auto-tracked',      'ml_lineage.png',       4),
    ('cdp_profiles',    'CDP Profiles',     'Dynamic Table',     'cdp_profiles.png',     5),
    ('streamlit',       'Streamlit',        '6-page dashboard',  'streamlit.png',        5),
]

column_labels = ['Ingest', 'Features', 'Train', 'Serve', 'Observe', 'App']

# ── Edge definitions ────────────────────────────────────────────────
# (source, target, tier, options)
# Tiers determine visual style only — ELK handles all routing
edges = [
    ('raw_events',     'dynamic_table',  'primary',   {}),
    ('dynamic_table',  'feature_store',  'primary',   {}),
    ('feature_store',  'xgboost',        'primary',   {}),
    ('xgboost',        'model_registry', 'primary',   {}),
    ('model_registry', 'spcs',           'secondary', {}),
    ('model_registry', 'model_monitor',  'secondary', {}),
    ('model_registry', 'ml_lineage',     'tertiary',  {'label': 'lineage'}),
    ('model_registry', 'cdp_profiles',   'secondary', {'label': 'batch score'}),
    ('spcs',           'streamlit',      'secondary', {}),
    ('model_monitor',  'streamlit',      'secondary', {}),
    ('cdp_profiles',   'streamlit',      'primary',   {}),
    ('raw_events',     'cortex_search',  'tertiary',  {'label': 'content'}),
    ('cortex_search',  'streamlit',      'tertiary',  {'label': 'search results'}),
]

# ── ELK node dimensions (in ELK px) ────────────────────────────────
ELK_NODE_W = 150
ELK_NODE_H = 120


def build_elk_graph():
    """Build ELK JSON graph from node/edge definitions.
    
    Uses ELK compound graph with groups to enforce 6-column semantic layout.
    Each column is a group node; real nodes are children of their group.
    This forces ELK to respect column assignments while still computing
    optimal vertical placement and edge routing within/between groups.
    """
    # Build column groups
    groups = {}  # col_idx -> list of node defs
    for nid, label, subtitle, icon_file, col in nodes:
        groups.setdefault(col, []).append((nid, label, subtitle, icon_file, col))

    group_children = []
    for ci in range(6):
        group_nodes = groups.get(ci, [])
        children = []
        for nid, label, subtitle, icon_file, col in group_nodes:
            node = {
                'id': nid,
                'width': ELK_NODE_W,
                'height': ELK_NODE_H,
                'labels': [{'text': label}],
            }
            children.append(node)

        group_opts = {
            'elk.algorithm': 'layered',
            'elk.direction': 'DOWN',
            'elk.spacing.nodeNode': '30',
            'elk.padding': '[top=8,left=12,bottom=8,right=12]',
        }

        group = {
            'id': 'col_{}'.format(ci),
            'layoutOptions': group_opts,
            'children': children,
        }
        group_children.append(group)

    # Build edges (reference node IDs directly — ELK resolves hierarchically)
    elk_edges = []
    for i, (src, dst, tier, opts) in enumerate(edges):
        e = {
            'id': 'e{}'.format(i + 1),
            'sources': [src],
            'targets': [dst],
        }
        # Give primary edges higher priority for straighter routing
        if tier == 'primary':
            e['layoutOptions'] = {'elk.layered.priority.direction': '10'}
        label = opts.get('label')
        if label:
            e['labels'] = [{'text': label, 'width': len(label) * 7, 'height': 14}]
        elk_edges.append(e)

    return {
        'id': 'root',
        'layoutOptions': {
            'elk.algorithm': 'layered',
            'elk.direction': 'RIGHT',
            'elk.edgeRouting': 'ORTHOGONAL',
            'elk.layered.spacing.nodeNodeBetweenLayers': '60',
            'elk.spacing.nodeNode': '30',
            'elk.layered.spacing.edgeEdgeBetweenLayers': '15',
            'elk.layered.spacing.edgeNodeBetweenLayers': '40',
            'elk.spacing.edgeNode': '35',
            'elk.spacing.edgeEdge': '15',
            'elk.layered.nodePlacement.strategy': 'NETWORK_SIMPLEX',
            'elk.layered.crossingMinimization.strategy': 'LAYER_SWEEP',
            'elk.layered.crossingMinimization.semiInteractive': 'true',
            'elk.layered.nodePlacement.bk.fixedAlignment': 'BALANCED',
            'elk.layered.mergeEdges': 'false',
            'elk.layered.nodePlacement.favorStraightEdges': 'true',
            'elk.padding': '[top=60,left=40,bottom=40,right=40]',
            'elk.hierarchyHandling': 'INCLUDE_CHILDREN',
        },
        'children': group_children,
        'edges': elk_edges,
    }


def run_elk_layout(graph):
    """Run ELK layout via Node.js subprocess, return layouted JSON."""
    graph_json = json.dumps(graph)

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write(graph_json)
        tmp_path = f.name

    try:
        result = subprocess.run(
            ['node', os.path.join(ELK_DIR, 'layout.mjs'), tmp_path],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode != 0:
            raise RuntimeError('ELK layout failed: ' + result.stderr)
        return json.loads(result.stdout)
    finally:
        os.unlink(tmp_path)


def extract_positions(layouted):
    """Extract node centers from ELK layout output (handles compound graphs).
    
    With hierarchyHandling=INCLUDE_CHILDREN, child positions are relative to
    their parent group. We add the parent offset to get absolute coordinates.
    
    Returns dict: node_id -> (center_x, center_y) in absolute ELK pixels.
    Also returns group_bounds: col_id -> (x, y, w, h) for column backgrounds."""
    positions = {}
    group_bounds = {}

    for group in layouted['children']:
        gx = group.get('x', 0)
        gy = group.get('y', 0)
        gw = group.get('width', 0)
        gh = group.get('height', 0)
        group_bounds[group['id']] = (gx, gy, gw, gh)

        for child in group.get('children', []):
            # Child coords are relative to parent group
            cx = gx + child['x'] + child['width'] / 2
            cy = gy + child['y'] + child['height'] / 2
            positions[child['id']] = (cx, cy)

    return positions, group_bounds


def extract_edge_routes(layouted):
    """Extract edge waypoints from ELK layout (handles compound graphs).
    
    With INCLUDE_CHILDREN, cross-group edge coordinates are in root space,
    but intra-group edges get coordinates relative to their common parent group
    even when listed at root level. We detect intra-group edges by checking
    if both source and target share the same parent, then add that offset.
    Returns list of (edge_id, waypoints, label_pos)."""
    routes = []

    # Build map: node_id -> parent group (id, x, y)
    node_parent = {}
    for group in layouted.get('children', []):
        gid = group['id']
        gx = group.get('x', 0)
        gy = group.get('y', 0)
        for child in group.get('children', []):
            node_parent[child['id']] = (gid, gx, gy)

    def collect_edges(node, offset_x=0, offset_y=0):
        """Recursively collect edges, adjusting offsets for intra-group edges."""
        for edge in node.get('edges', []):
            sec = edge['sections'][0]
            pts = [sec['startPoint']]
            pts += sec.get('bendPoints', [])
            pts += [sec['endPoint']]

            # Determine if this is an intra-group edge at root level
            src = edge['sources'][0]
            tgt = edge['targets'][0]
            extra_ox, extra_oy = 0, 0
            if offset_x == 0 and offset_y == 0:
                # Root-level edge — check if src and tgt share a parent group
                sp = node_parent.get(src)
                tp = node_parent.get(tgt)
                if sp and tp and sp[0] == tp[0]:
                    # Intra-group: ELK gives group-relative coords
                    extra_ox = sp[1]
                    extra_oy = sp[2]

            waypoints = [(p['x'] + offset_x + extra_ox,
                          p['y'] + offset_y + extra_oy) for p in pts]

            label_pos = None
            if edge.get('labels'):
                lbl = edge['labels'][0]
                if 'x' in lbl and 'y' in lbl:
                    label_pos = (
                        lbl['x'] + lbl.get('width', 0) / 2 + offset_x + extra_ox,
                        lbl['y'] + lbl.get('height', 0) / 2 + offset_y + extra_oy
                    )

            routes.append((edge['id'], waypoints, label_pos))

        for child in node.get('children', []):
            child_ox = offset_x + child.get('x', 0)
            child_oy = offset_y + child.get('y', 0)
            collect_edges(child, child_ox, child_oy)

    collect_edges(layouted)
    return routes


def load_icon(fn, sz=44):
    img = Image.open(os.path.join(ICON_DIR, fn)).convert('RGBA')
    return np.array(img.resize((sz, sz), Image.LANCZOS))


# ── Matplotlib rendering helpers ────────────────────────────────────

def draw_rounded_ortho_arrow(ax, waypoints, color, lw, dash, arrow_scale, corner_radius=0.06):
    """Draw an orthogonal path with rounded corners and arrowhead.
    Waypoints are in matplotlib coordinates."""
    if len(waypoints) < 2:
        return

    r = corner_radius
    verts = [waypoints[0]]
    codes = [MplPath.MOVETO]

    for i in range(1, len(waypoints) - 1):
        prev = waypoints[i - 1]
        curr = waypoints[i]
        nxt = waypoints[i + 1]

        dx_in = curr[0] - prev[0]
        dy_in = curr[1] - prev[1]
        dx_out = nxt[0] - curr[0]
        dy_out = nxt[1] - curr[1]

        len_in = max(abs(dx_in), abs(dy_in))
        len_out = max(abs(dx_out), abs(dy_out))

        actual_r = min(r, len_in / 2, len_out / 2)

        if actual_r < 0.01:
            verts.append(curr)
            codes.append(MplPath.LINETO)
            continue

        ndx_in = dx_in / len_in if len_in > 0 else 0
        ndy_in = dy_in / len_in if len_in > 0 else 0
        ndx_out = dx_out / len_out if len_out > 0 else 0
        ndy_out = dy_out / len_out if len_out > 0 else 0

        p_before = (curr[0] - ndx_in * actual_r, curr[1] - ndy_in * actual_r)
        p_after = (curr[0] + ndx_out * actual_r, curr[1] + ndy_out * actual_r)

        verts.append(p_before)
        codes.append(MplPath.LINETO)
        verts.append(curr)
        codes.append(MplPath.CURVE3)
        verts.append(p_after)
        codes.append(MplPath.CURVE3)

    # Stop short for arrowhead
    last = waypoints[-1]
    second_last = waypoints[-2] if len(waypoints) >= 2 else waypoints[-1]
    arrow_gap = 0.04
    dx_f = last[0] - second_last[0]
    dy_f = last[1] - second_last[1]
    flen = max(abs(dx_f), abs(dy_f), 0.01)
    stop_x = last[0] - (dx_f / flen) * arrow_gap
    stop_y = last[1] - (dy_f / flen) * arrow_gap

    verts.append((stop_x, stop_y))
    codes.append(MplPath.LINETO)

    path = MplPath(verts, codes)
    ls = '-' if dash is None else (0, dash)
    patch = mpatches.FancyArrowPatch(
        path=path, arrowstyle='-', color=color, lw=lw,
        linestyle=ls, zorder=5, mutation_scale=arrow_scale)
    ax.add_patch(patch)

    # Arrowhead
    ax.annotate('', xy=last, xytext=(stop_x, stop_y),
                arrowprops=dict(arrowstyle='-|>', color=color, lw=lw,
                                mutation_scale=arrow_scale, shrinkA=0, shrinkB=1),
                zorder=5)


def edge_label(ax, x, y, text):
    """Draw a label with white background on an edge."""
    ax.text(x, y, text, fontsize=7, ha='center', va='center',
            color=SF_TEXT, style='italic', fontweight='medium', zorder=8,
            bbox=dict(boxstyle='round,pad=0.15', facecolor=SF_WHITE,
                      edgecolor='#C0C0C0', linewidth=0.6, alpha=0.97))


def compute_label_pos(waypoints, y_offset=0.10):
    """Find the best position for a label: midpoint of the longest segment."""
    best_len = 0
    best_mid = None
    for i in range(len(waypoints) - 1):
        x0, y0 = waypoints[i]
        x1, y1 = waypoints[i + 1]
        seg_len = abs(x1 - x0) + abs(y1 - y0)
        if seg_len > best_len:
            best_len = seg_len
            mid_x = (x0 + x1) / 2
            mid_y = (y0 + y1) / 2
            if abs(y0 - y1) < 0.01:  # horizontal
                best_mid = (mid_x, mid_y + y_offset)
            else:  # vertical
                best_mid = (mid_x + 0.15, mid_y)
    return best_mid


# ════════════════════════════════════════════════════════════════════
#  MAIN
# ════════════════════════════════════════════════════════════════════

def main():
    print('Building ELK graph...')
    elk_graph = build_elk_graph()

    print('Running ELK layout...')
    layouted = run_elk_layout(elk_graph)

    # ── Post-layout vertical alignment ─────────────────────────────
    # ELK places col_0 (single-node Ingest) much lower than col_1 (Features)
    # because it balances edge lengths globally. We shift col_0's Y to align
    # its first child with col_1's first child, then RECONSTRUCT edge routes
    # for affected edges with proper orthogonal paths.
    col0_group = col1_group = None
    for group in layouted['children']:
        if group['id'] == 'col_0':
            col0_group = group
        elif group['id'] == 'col_1':
            col1_group = group
    if col0_group and col1_group:
        dy = col0_group['y'] - col1_group['y']
        if abs(dy) > 5:  # only adjust if meaningfully offset
            print('  Aligning col_0: shifting Y by {:.0f}px'.format(-dy))
            col0_group['y'] = col1_group['y']

            # Build lookup: node_id -> absolute center position AFTER shift
            def abs_center(group):
                """Get absolute center positions for all children in group."""
                centers = {}
                gx, gy = group.get('x', 0), group.get('y', 0)
                for ch in group.get('children', []):
                    centers[ch['id']] = (
                        gx + ch['x'] + ch['width'] / 2,
                        gy + ch['y'] + ch['height'] / 2
                    )
                return centers

            # Get col_0 node positions (after shift) and all other node positions
            all_centers = {}
            for grp in layouted['children']:
                all_centers.update(abs_center(grp))

            col0_node_ids = {ch['id'] for ch in col0_group.get('children', [])}

            # Find the bottom Y of all groups (for routing long-span edges below)
            max_group_bottom = 0
            for grp in layouted['children']:
                bottom = grp.get('y', 0) + grp.get('height', 0)
                if bottom > max_group_bottom:
                    max_group_bottom = bottom
            below_y = max_group_bottom + 30  # 30px margin below all groups

            # Reconstruct edges connected to col_0 with orthogonal routing
            for edge in layouted.get('edges', []):
                src = edge['sources'][0]
                tgt = edge['targets'][0]
                if src not in col0_node_ids and tgt not in col0_node_ids:
                    continue

                sec = edge['sections'][0]
                old_start = sec['startPoint']
                old_end = sec['endPoint']

                # Compute new start/end based on shifted positions
                if src in col0_node_ids:
                    # Source is in col_0 — shift start point
                    new_start_y = old_start['y'] - dy
                    new_start = {'x': old_start['x'], 'y': new_start_y}
                    new_end = dict(old_end)  # target unchanged
                else:
                    new_start = dict(old_start)
                    new_end_y = old_end['y'] - dy
                    new_end = {'x': old_end['x'], 'y': new_end_y}

                y_diff = abs(new_start['y'] - new_end['y'])

                if y_diff < 10:
                    # Nearly horizontal — straight line, no bends needed
                    new_bends = []
                elif abs(new_end['x'] - new_start['x']) > 600:
                    # Long-span edge (crosses multiple columns) — route BELOW
                    # all groups to avoid crossing over intermediate nodes.
                    # Path: right from start → down to below_y → right to
                    # target X → up to target Y
                    exit_x = new_start['x'] + 40  # short horizontal stub out
                    enter_x = new_end['x'] - 40   # short horizontal stub in
                    new_bends = [
                        {'x': exit_x,  'y': new_start['y']},
                        {'x': exit_x,  'y': below_y},
                        {'x': enter_x, 'y': below_y},
                        {'x': enter_x, 'y': new_end['y']},
                    ]
                else:
                    # Short-span edge — Z-route with midpoint vertical segment
                    mid_x = (new_start['x'] + new_end['x']) / 2
                    new_bends = [
                        {'x': mid_x, 'y': new_start['y']},
                        {'x': mid_x, 'y': new_end['y']},
                    ]

                sec['startPoint'] = new_start
                sec['endPoint'] = new_end
                sec['bendPoints'] = new_bends

                # Reposition edge labels at midpoint of new route
                for lbl in edge.get('labels', []):
                    if 'y' in lbl:
                        # Place label on the longest horizontal segment
                        if len(new_bends) >= 3:
                            # Long-span: label on bottom horizontal segment
                            seg_mid_x = (new_bends[1]['x'] + new_bends[2]['x']) / 2
                            lbl['x'] = seg_mid_x - lbl.get('width', 0) / 2
                            lbl['y'] = below_y + 4
                        else:
                            mid_x = (new_start['x'] + new_end['x']) / 2
                            lbl['x'] = mid_x - lbl.get('width', 0) / 2
                            lbl['y'] = (new_start['y'] + new_end['y']) / 2 - lbl.get('height', 0) / 2

    graph_w = layouted.get('width', 2500)
    graph_h = layouted.get('height', 600)
    print('  ELK graph: {} x {} px'.format(int(graph_w), int(graph_h)))

    # Extract layout data
    elk_positions, elk_group_bounds = extract_positions(layouted)
    elk_routes = extract_edge_routes(layouted)

    # ── Coordinate transform: ELK px → matplotlib units ─────────
    # Scale so the graph fits nicely in ~14 x 8 matplotlib figure units
    # ELK Y increases downward; matplotlib Y increases upward → flip Y
    SCALE = 14.0 / graph_w   # normalize width to ~14 units
    X_OFFSET = 0.5
    Y_OFFSET = 8.5   # flip anchor

    def to_mpl(ex, ey):
        """Convert ELK pixel coords to matplotlib coords."""
        return ex * SCALE + X_OFFSET, Y_OFFSET - ey * SCALE

    # Convert positions
    positions = {}
    for nid, (ex, ey) in elk_positions.items():
        positions[nid] = to_mpl(ex, ey)

    # Convert group bounds (ELK: x,y is top-left; matplotlib: y-flipped)
    mpl_group_bounds = {}
    for gid, (gx, gy, gw, gh) in elk_group_bounds.items():
        # Top-left in ELK → bottom-left in matplotlib (since Y is flipped)
        mpl_x = gx * SCALE + X_OFFSET
        mpl_y_top = Y_OFFSET - gy * SCALE
        mpl_y_bottom = Y_OFFSET - (gy + gh) * SCALE
        mpl_w = gw * SCALE
        mpl_h = mpl_y_top - mpl_y_bottom
        mpl_group_bounds[gid] = (mpl_x, mpl_y_bottom, mpl_w, mpl_h)

    # Convert edge routes
    mpl_routes = []
    for eid, waypoints, label_pos in elk_routes:
        mpl_wp = [to_mpl(x, y) for x, y in waypoints]
        mpl_lp = to_mpl(*label_pos) if label_pos else None
        mpl_routes.append((eid, mpl_wp, mpl_lp))

    # Card dimensions in matplotlib units
    card_w = ELK_NODE_W * SCALE
    card_h = ELK_NODE_H * SCALE
    hw = card_w / 2
    hh = card_h / 2

    # ── Figure setup ────────────────────────────────────────────
    fig_w = graph_w * SCALE + 1.5
    fig_h = graph_h * SCALE + 3.0
    fig, ax = plt.subplots(1, 1, figsize=(fig_w, fig_h), dpi=180)
    fig.patch.set_facecolor(SF_WHITE)
    ax.set_facecolor(SF_WHITE)

    # Compute bounds from actual positions
    all_x = [p[0] for p in positions.values()]
    all_y = [p[1] for p in positions.values()]
    x_min = min(all_x) - hw - 0.6
    x_max = max(all_x) + hw + 0.6
    y_min = min(all_y) - hh - 0.8
    y_max = max(all_y) + hh + 1.6

    ax.set_xlim(x_min, x_max)
    ax.set_ylim(y_min, y_max)
    ax.set_aspect('equal')
    ax.axis('off')

    x_center = (x_min + x_max) / 2

    # ── Title ───────────────────────────────────────────────────
    ax.text(x_center, y_max - 0.15,
            'AI Matching App  \u2014  End-to-End ML Pipeline',
            fontsize=17, fontweight='bold', ha='center', va='top',
            color=SF_TEXT, fontfamily='sans-serif')
    ax.text(x_center, y_max - 0.55,
            'Snowflake Native Architecture',
            fontsize=10, ha='center', va='top',
            color=SF_SUBTITLE, fontfamily='sans-serif')

    # ── Boundary ────────────────────────────────────────────────
    bx = x_min + 0.15
    by = y_min + 0.15
    bw = (x_max - x_min) - 0.3
    bh = (y_max - y_min) - 1.2
    boundary = mpatches.FancyBboxPatch(
        (bx, by), bw, bh,
        boxstyle=mpatches.BoxStyle.Round(pad=0.15),
        facecolor='none', edgecolor=SF_BOUNDARY,
        linewidth=2.0, linestyle=(0, (6, 4)), alpha=0.55, zorder=0)
    ax.add_patch(boundary)
    ax.text(bx + 0.1, by + bh + 0.12, 'Snowflake',
            fontsize=8.5, color=SF_BOUNDARY, fontweight='bold',
            fontfamily='sans-serif', alpha=0.55, va='bottom')

    # ── Column labels and backgrounds (from ELK group bounds) ────
    node_lookup = {n[0]: n for n in nodes}
    for ci in range(6):
        gid = 'col_{}'.format(ci)
        if gid not in mpl_group_bounds:
            continue
        gx, gy, gw, gh = mpl_group_bounds[gid]
        pad = 0.06

        # Column background
        bg = mpatches.FancyBboxPatch(
            (gx - pad, gy - pad), gw + 2 * pad, gh + 2 * pad,
            boxstyle=mpatches.BoxStyle.Round(pad=0.08),
            facecolor=SF_GROUP_BG[ci], edgecolor=SF_GROUP_BORDER[ci],
            linewidth=1.6, alpha=0.80, zorder=1)
        ax.add_patch(bg)

        # Column label centered above the group
        ax.text(gx + gw / 2, gy + gh + pad + 0.35, column_labels[ci],
                fontsize=10.5, fontweight='bold', ha='center', va='bottom',
                color=SF_GROUP_BORDER[ci], fontfamily='sans-serif')

    # ── Nodes ───────────────────────────────────────────────────
    for nid, label, subtitle, icon_file, col in nodes:
        x, y = positions[nid]
        card = mpatches.FancyBboxPatch(
            (x - hw, y - hh), card_w, card_h,
            boxstyle=mpatches.BoxStyle.Round(pad=0.05),
            facecolor=SF_WHITE, edgecolor=SF_GROUP_BORDER[col],
            linewidth=1.3, alpha=0.97, zorder=3)
        ax.add_patch(card)

        icon_data = load_icon(icon_file)
        ib = OffsetImage(icon_data, zoom=0.78)
        ab = AnnotationBbox(ib, (x, y + hh * 0.3), frameon=False, zorder=4)
        ax.add_artist(ab)

        ax.text(x, y - hh * 0.38, label, fontsize=8.5, fontweight='bold',
                ha='center', va='center', color=SF_TEXT,
                fontfamily='sans-serif', zorder=6)
        ax.text(x, y - hh * 0.70, subtitle, fontsize=6.5,
                ha='center', va='center', color=SF_SUBTITLE,
                fontfamily='sans-serif', zorder=6)

    # ── Edges ───────────────────────────────────────────────────
    edge_tier_map = {}
    edge_opts_map = {}
    for i, (src, dst, tier, opts) in enumerate(edges):
        eid = 'e{}'.format(i + 1)
        edge_tier_map[eid] = tier
        edge_opts_map[eid] = opts

    for eid, waypoints, elk_label_pos in mpl_routes:
        tier = edge_tier_map.get(eid, 'secondary')
        opts = edge_opts_map.get(eid, {})
        color = TIER_COLORS[tier]
        lw = TIER_LW[tier]
        dash = TIER_DASH[tier]
        arrow_scale = TIER_ARROW_SCALE[tier]

        draw_rounded_ortho_arrow(ax, waypoints, color, lw, dash, arrow_scale)

        label_text = opts.get('label')
        if label_text:
            # Prefer ELK's computed label position, fallback to our heuristic
            if elk_label_pos:
                edge_label(ax, elk_label_pos[0], elk_label_pos[1], label_text)
            else:
                lpos = compute_label_pos(waypoints)
                if lpos:
                    edge_label(ax, lpos[0], lpos[1], label_text)

    # ── Save ────────────────────────────────────────────────────
    plt.tight_layout(pad=0.3)
    out = os.path.join(ICON_DIR, 'architecture_diagram_elk.png')
    fig.savefig(out, dpi=180, bbox_inches='tight',
                facecolor=SF_WHITE, edgecolor='none', pad_inches=0.2)
    plt.close()

    sz = os.path.getsize(out) / 1024
    print('Generated: {}  ({:.0f} KB)'.format(out, sz))
    if sz > 800:
        Image.open(out).save(out, 'PNG', optimize=True)
        print('Optimized: {:.0f} KB'.format(os.path.getsize(out) / 1024))


if __name__ == '__main__':
    main()
