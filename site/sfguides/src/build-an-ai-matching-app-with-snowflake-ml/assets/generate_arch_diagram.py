#!/usr/bin/env python3
"""
Generate architecture diagram for AI Matching App sfquickstart.
v13 — Obstacle-aware orthogonal routing with rounded corners, visual hierarchy,
      segment nudging, and declarative edge definitions.
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
import heapq
import os

# ── Colors ──────────────────────────────────────────────────────────
SF_WHITE = '#FFFFFF'
SF_TEXT = '#1B2A4A'
SF_SUBTITLE = '#5A6B7D'
SF_BOUNDARY = '#29B5E8'

# 3-tier edge colors
TIER_COLORS = {
    'primary':   '#2E4057',   # dark — main pipeline flow
    'secondary': '#4A6B8A',   # medium — deployment/monitoring
    'tertiary':  '#7A9BB5',   # light — cross-cutting
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

# ── Node definitions ────────────────────────────────────────────────
nodes = [
    ('raw_events',      'RAW Events',       '500K rows',         'raw_events.png',      0, 0),
    ('dynamic_table',   'Dynamic Table',    '2-min refresh',     'dynamic_table.png',    1, 0),
    ('feature_store',   'Feature Store',    'Entity + Views',    'feature_store.png',    1, 1),
    ('xgboost',         'XGBoost',          'GridSearchCV',      'xgboost.png',          2, 0),
    ('model_registry',  'Model Registry',   'V1 + V2',          'model_registry.png',   2, 1),
    ('spcs',            'SPCS REST API',    'scale-to-zero',     'spcs.png',             3, 0),
    ('cortex_search',   'Cortex Search',    'hybrid semantic',   'cortex_search.png',    3, 1),
    ('model_monitor',   'Model Monitor',    'PSI drift',         'model_monitor.png',    4, 0),
    ('ml_lineage',      'ML Lineage',       'auto-tracked',      'ml_lineage.png',       4, 1),
    ('cdp_profiles',    'CDP Profiles',     'Dynamic Table',     'cdp_profiles.png',     5, 0),
    ('streamlit',       'Streamlit',        '6-page dashboard',  'streamlit.png',        5, 1),
]

column_labels = ['Ingest', 'Features', 'Train', 'Serve', 'Observe', 'App']

# ── Declarative edge definitions ────────────────────────────────────
# (source_id, target_id, tier, options_dict)
# Tier: 'primary' = main data flow, 'secondary' = deploy/monitor, 'tertiary' = cross-cutting
# Options: label=str, exit_side=str, enter_side=str (default: auto-computed)
edges = [
    # Main pipeline: left-to-right flow across columns
    ('raw_events',     'dynamic_table',  'primary',   {}),                                        # col0r0 → col1r0  (right→left)
    ('dynamic_table',  'feature_store',  'primary',   {'exit_side': 'bottom', 'enter_side': 'top'}),  # col1r0 → col1r1 (same column, down)
    ('feature_store',  'xgboost',        'primary',   {'exit_side': 'right', 'enter_side': 'left'}),  # col1r1 → col2r0 (diagonal: right→left)
    ('xgboost',        'model_registry', 'primary',   {'exit_side': 'bottom', 'enter_side': 'top'}),  # col2r0 → col2r1 (same column, down)

    # Model Registry fan-out: split UP (top channels) and RIGHT (mid-gap)
    ('model_registry', 'spcs',           'secondary', {'exit_side': 'right', 'enter_side': 'left'}),   # col2r1 → col3r0: right then up (natural diagonal)
    ('model_registry', 'model_monitor',  'secondary', {'exit_side': 'top',   'enter_side': 'left'}),   # col2r1 → col4r0: up through top channels
    ('model_registry', 'ml_lineage',     'tertiary',  {'exit_side': 'bottom', 'enter_side': 'bottom', 'label': 'lineage'}),  # col2r1 → col4r1: route under row1
    ('model_registry', 'cdp_profiles',   'secondary', {'exit_side': 'top',   'enter_side': 'left', 'label': 'batch score'}),  # col2r1 → col5r0: up through top channels

    # Converge to Streamlit
    ('spcs',           'streamlit',      'secondary', {'exit_side': 'bottom', 'enter_side': 'left'}),   # col3r0 → col5r1: down then right
    ('model_monitor',  'streamlit',      'secondary', {'exit_side': 'bottom', 'enter_side': 'left'}),   # col4r0 → col5r1: down then right
    ('cdp_profiles',   'streamlit',      'primary',   {'exit_side': 'bottom', 'enter_side': 'top'}),    # col5r0 → col5r1 (same column, down)

    # Cross-cutting
    ('raw_events',     'cortex_search',  'tertiary',  {'exit_side': 'bottom', 'enter_side': 'left', 'label': 'content'}),  # col0r0 → col3r1 (far right+down)
    ('cortex_search',  'streamlit',      'tertiary',  {'exit_side': 'right', 'enter_side': 'left', 'label': 'search results', 'label_below': True}),  # col3r1 → col5r1 (right, same row)
]

# ── Layout constants ────────────────────────────────────────────────
COL_SPACING = 2.5
ROW_SPACING = 2.5
LEFT_MARGIN = 1.6
CONTENT_TOP = 5.0
CARD_W = 1.85
CARD_H = 1.45
HW, HH = CARD_W / 2, CARD_H / 2
OBSTACLE_MARGIN = 0.25          # clearance around cards for routing
CORNER_RADIUS = 0.12            # radius for rounded bends
NUDGE_SPACING = 0.22            # offset between parallel edges on same channel
BEND_PENALTY = 2.5              # A* cost multiplier per bend
GRID_STEP = 0.25                # visibility graph grid resolution


def gp(col, row):
    """Grid position for a node."""
    return LEFT_MARGIN + col * COL_SPACING, CONTENT_TOP - row * ROW_SPACING


def load_icon(fn, sz=44):
    img = Image.open(f'{ICON_DIR}/{fn}').convert('RGBA')
    return np.array(img.resize((sz, sz), Image.LANCZOS))


# ════════════════════════════════════════════════════════════════════
#  OBSTACLE-AWARE ORTHOGONAL ROUTER
# ════════════════════════════════════════════════════════════════════

def build_obstacles(positions):
    """Build padded bounding boxes for all nodes as routing obstacles.
    Returns list of (x_min, y_min, x_max, y_max) tuples."""
    obstacles = []
    m = OBSTACLE_MARGIN
    for nid in positions:
        cx, cy = positions[nid]
        obstacles.append((cx - HW - m, cy - HH - m, cx + HW + m, cy + HH + m))
    return obstacles


def rect_intersects_segment(rect, x0, y0, x1, y1):
    """Check if an axis-aligned segment (H or V) intersects a rectangle interior.
    The segment endpoints themselves are allowed to touch the rect boundary."""
    rx_min, ry_min, rx_max, ry_max = rect
    # Shrink rect slightly to allow edge-touching
    eps = 0.01
    rx_min += eps; ry_min += eps; rx_max -= eps; ry_max -= eps

    if abs(x0 - x1) < 0.001:  # vertical segment
        x = x0
        if x < rx_min or x > rx_max:
            return False
        seg_y_min, seg_y_max = min(y0, y1), max(y0, y1)
        return seg_y_max > ry_min and seg_y_min < ry_max
    else:  # horizontal segment
        y = y0
        if y < ry_min or y > ry_max:
            return False
        seg_x_min, seg_x_max = min(x0, x1), max(x0, x1)
        return seg_x_max > rx_min and seg_x_min < rx_max


def segment_blocked(obstacles, x0, y0, x1, y1, exclude_rects=None):
    """Check if a segment is blocked by any obstacle."""
    for i, rect in enumerate(obstacles):
        if exclude_rects and i in exclude_rects:
            continue
        if rect_intersects_segment(rect, x0, y0, x1, y1):
            return True
    return False


def get_port(positions, nid, side, port_offset=0.0):
    """Get connection port coordinates on card edge.
    port_offset shifts along the edge: + is right/up, - is left/down."""
    cx, cy = positions[nid]
    if side == 'right':  return (cx + HW, cy + port_offset)
    if side == 'left':   return (cx - HW, cy + port_offset)
    if side == 'top':    return (cx + port_offset, cy + HH)
    if side == 'bottom': return (cx + port_offset, cy - HH)
    return (cx, cy)


def auto_sides(positions, src_id, dst_id):
    """Determine best exit/enter sides based on relative position."""
    sx, sy = positions[src_id]
    dx, dy = positions[dst_id]
    delta_x = dx - sx
    delta_y = dy - sy

    # Direct neighbors in same column (vertical)
    if abs(delta_x) < 0.5:
        if delta_y > 0:
            return 'top', 'bottom'
        else:
            return 'bottom', 'top'

    # Direct neighbors in same row (horizontal)
    if abs(delta_y) < 0.5:
        if delta_x > 0:
            return 'right', 'left'
        else:
            return 'left', 'right'

    # Diagonal: prefer horizontal flow (right→left) for forward movement
    if delta_x > 0:
        if abs(delta_y) > abs(delta_x):
            # More vertical than horizontal
            if delta_y > 0:
                return 'top', 'bottom'
            else:
                return 'bottom', 'top'
        else:
            return 'right', 'left'
    else:
        if abs(delta_y) > abs(delta_x):
            if delta_y > 0:
                return 'top', 'bottom'
            else:
                return 'bottom', 'top'
        else:
            return 'left', 'right'


def build_visibility_graph(obstacles, ports, positions):
    """Build candidate routing points from obstacle corners + port stubs.
    Returns a set of (x, y) candidate waypoints."""
    candidates = set()
    m = OBSTACLE_MARGIN

    # Add all obstacle corner points (expanded)
    for (rx_min, ry_min, rx_max, ry_max) in obstacles:
        for x in [rx_min, rx_max]:
            for y in [ry_min, ry_max]:
                candidates.add((round(x, 3), round(y, 3)))

    # Add stub points extending from each port
    stub = 0.45
    for (px, py, direction) in ports:
        candidates.add((round(px, 3), round(py, 3)))
        if direction == 'right':
            candidates.add((round(px + stub, 3), round(py, 3)))
        elif direction == 'left':
            candidates.add((round(px - stub, 3), round(py, 3)))
        elif direction == 'top':
            candidates.add((round(px, 3), round(py + stub, 3)))
        elif direction == 'bottom':
            candidates.add((round(px, 3), round(py - stub, 3)))

    # Add routing channel Y-coordinates (above row 0, below row 1, mid-gap)
    row0_top = CONTENT_TOP + HH + OBSTACLE_MARGIN
    row1_bot = CONTENT_TOP - ROW_SPACING - HH - OBSTACLE_MARGIN
    mid_gap = (CONTENT_TOP + (CONTENT_TOP - ROW_SPACING)) / 2

    channel_ys = [
        # Above row0 (for edges exiting top of row1 nodes, routing over row0)
        row0_top + 0.15,
        row0_top + 0.35,
        row0_top + 0.55,
        row0_top + 0.75,
        row0_top + 0.95,
        row0_top + 1.15,
        # Below row1 (for edges routing under everything)
        row1_bot - 0.15,
        row1_bot - 0.35,
        row1_bot - 0.55,
        row1_bot - 0.75,
        # Mid-gap channels (between row0 and row1)
        mid_gap,
        mid_gap + 0.20,
        mid_gap - 0.20,
        mid_gap + 0.40,
        mid_gap - 0.40,
        mid_gap + 0.60,
        mid_gap - 0.60,
    ]

    # Add X-coordinates at column midpoints (between columns) for vertical runs
    channel_xs = []
    for ci in range(5):
        mid_x = LEFT_MARGIN + ci * COL_SPACING + COL_SPACING / 2
        channel_xs.append(mid_x)
        # Also add 1/3 and 2/3 points between columns
        channel_xs.append(LEFT_MARGIN + ci * COL_SPACING + COL_SPACING / 3)
        channel_xs.append(LEFT_MARGIN + ci * COL_SPACING + 2 * COL_SPACING / 3)
    # Also add X at each column center ± offset
    for ci in range(6):
        cx = LEFT_MARGIN + ci * COL_SPACING
        channel_xs.extend([cx - HW - 0.3, cx + HW + 0.3])

    # Create grid intersections of channels
    all_xs = sorted(set([c[0] for c in candidates] + channel_xs))
    all_ys = sorted(set([c[1] for c in candidates] + channel_ys))

    for x in all_xs:
        for y in channel_ys:
            candidates.add((round(x, 3), round(y, 3)))
    for y in all_ys:
        for x in channel_xs:
            candidates.add((round(x, 3), round(y, 3)))

    return candidates


def astar_ortho(start, end, start_dir, end_dir, obstacles, candidates,
                src_obstacle_idx, dst_obstacle_idx):
    """A* search for shortest orthogonal path from start to end,
    avoiding obstacles. Returns list of waypoints."""
    exclude = set()
    if src_obstacle_idx is not None:
        exclude.add(src_obstacle_idx)
    if dst_obstacle_idx is not None:
        exclude.add(dst_obstacle_idx)

    # Build the set of all nodes including start and end
    all_points = set(candidates)
    all_points.add(start)
    all_points.add(end)

    # Index points by x and y for fast neighbor lookup
    by_x = {}
    by_y = {}
    for pt in all_points:
        x, y = pt
        rx = round(x, 2)
        ry = round(y, 2)
        by_x.setdefault(rx, []).append(pt)
        by_y.setdefault(ry, []).append(pt)

    def get_neighbors(pt):
        """Get reachable neighbors via unblocked H/V segments."""
        x, y = pt
        rx, ry = round(x, 2), round(y, 2)
        neighbors = []

        # Horizontal neighbors (same y)
        for other in by_y.get(ry, []):
            if other == pt:
                continue
            if not segment_blocked(obstacles, x, y, other[0], other[1], exclude):
                # Check no intermediate point lies between them on this line
                neighbors.append(other)

        # Vertical neighbors (same x)
        for other in by_x.get(rx, []):
            if other == pt:
                continue
            if not segment_blocked(obstacles, x, y, other[0], other[1], exclude):
                neighbors.append(other)

        return neighbors

    def heuristic(pt):
        """Manhattan distance to goal."""
        return abs(pt[0] - end[0]) + abs(pt[1] - end[1])

    def direction_of(p1, p2):
        """Return 'h' for horizontal, 'v' for vertical."""
        if abs(p1[1] - p2[1]) < 0.01:
            return 'h'
        return 'v'

    # A* with bend counting
    # State: (cost, bend_count, point, prev_direction, path)
    initial_dir = 'h' if start_dir in ('left', 'right') else 'v'
    target_dir = 'h' if end_dir in ('left', 'right') else 'v'

    open_set = [(heuristic(start), 0, 0, start, initial_dir, [start])]
    visited = {}  # point -> best cost
    counter = 0

    while open_set:
        f_cost, g_cost, _, current, prev_dir, path = heapq.heappop(open_set)

        state_key = (current, prev_dir)
        if state_key in visited and visited[state_key] <= g_cost:
            continue
        visited[state_key] = g_cost

        if current == end:
            return path

        for neighbor in get_neighbors(current):
            seg_dir = direction_of(current, neighbor)
            bend = 1 if seg_dir != prev_dir else 0
            seg_len = abs(neighbor[0] - current[0]) + abs(neighbor[1] - current[1])
            new_g = g_cost + seg_len + bend * BEND_PENALTY

            nstate = (neighbor, seg_dir)
            if nstate in visited and visited[nstate] <= new_g:
                continue

            new_f = new_g + heuristic(neighbor)
            counter += 1
            heapq.heappush(open_set, (new_f, new_g, counter, neighbor, seg_dir, path + [neighbor]))

    # Fallback: direct L-shaped route if A* fails
    return fallback_route(start, end, start_dir, end_dir)


def fallback_route(start, end, start_dir, end_dir):
    """Simple L-shaped or Z-shaped fallback route."""
    sx, sy = start
    ex, ey = end

    if start_dir in ('right', 'left') and end_dir in ('top', 'bottom'):
        return [start, (ex, sy), end]
    elif start_dir in ('top', 'bottom') and end_dir in ('left', 'right'):
        return [start, (sx, ey), end]
    elif start_dir in ('right', 'left'):
        mid_x = (sx + ex) / 2
        return [start, (mid_x, sy), (mid_x, ey), end]
    else:
        mid_y = (sy + ey) / 2
        return [start, (sx, mid_y), (ex, mid_y), end]


def simplify_path(waypoints):
    """Remove redundant collinear waypoints."""
    if len(waypoints) <= 2:
        return waypoints
    result = [waypoints[0]]
    for i in range(1, len(waypoints) - 1):
        prev = result[-1]
        curr = waypoints[i]
        nxt = waypoints[i + 1]
        # Check if prev→curr→nxt are collinear
        dx1 = curr[0] - prev[0]
        dy1 = curr[1] - prev[1]
        dx2 = nxt[0] - curr[0]
        dy2 = nxt[1] - curr[1]
        # Same direction?  Both horizontal or both vertical
        if (abs(dx1) < 0.01 and abs(dx2) < 0.01) or (abs(dy1) < 0.01 and abs(dy2) < 0.01):
            continue  # skip this intermediate point
        result.append(curr)
    result.append(waypoints[-1])
    return result


def nudge_parallel_edges(all_routes, obstacles=None, edge_list=None, obs_idx=None):
    """Detect edges sharing horizontal or vertical channel segments and
    offset them to prevent overlap. Mutates waypoints in place.
    If obstacles provided, validates nudges don't cross node boundaries."""
    # Collect all horizontal segments grouped by y-coordinate
    h_segments = {}  # rounded_y -> list of (edge_idx, seg_idx, x_min, x_max)
    v_segments = {}  # rounded_x -> list of (edge_idx, seg_idx, y_min, y_max)

    for ei, route in enumerate(all_routes):
        for si in range(len(route) - 1):
            x0, y0 = route[si]
            x1, y1 = route[si + 1]
            if abs(y0 - y1) < 0.01:  # horizontal
                ry = round(y0, 1)
                h_segments.setdefault(ry, []).append(
                    (ei, si, min(x0, x1), max(x0, x1)))
            elif abs(x0 - x1) < 0.01:  # vertical
                rx = round(x0, 1)
                v_segments.setdefault(rx, []).append(
                    (ei, si, min(y0, y1), max(y0, y1)))

    def _exclude_set(ei):
        """Build exclude set for an edge's own src/dst obstacles."""
        if not obstacles or not edge_list or not obs_idx:
            return None
        src_id, dst_id = edge_list[ei][0], edge_list[ei][1]
        exc = set()
        if src_id in obs_idx: exc.add(obs_idx[src_id])
        if dst_id in obs_idx: exc.add(obs_idx[dst_id])
        return exc

    def _nudge_ok(x0, y0, x1, y1, ei):
        """Check if a nudged segment is clear of obstacles."""
        if not obstacles:
            return True
        exc = _exclude_set(ei)
        return not segment_blocked(obstacles, x0, y0, x1, y1, exc)

    # Nudge overlapping horizontal segments
    for ry, segs in h_segments.items():
        if len(segs) <= 1:
            continue
        # Check for actual overlap (x-range intersection)
        groups = []
        for seg in segs:
            placed = False
            for group in groups:
                # Check if this seg overlaps any seg in the group
                for gseg in group:
                    if seg[2] < gseg[3] and seg[3] > gseg[2]:  # x-ranges overlap
                        group.append(seg)
                        placed = True
                        break
                if placed:
                    break
            if not placed:
                groups.append([seg])

        for group in groups:
            if len(group) <= 1:
                continue
            n = len(group)
            for k, (ei, si, _, _) in enumerate(group):
                offset = (k - (n - 1) / 2) * NUDGE_SPACING
                if abs(offset) < 0.001:
                    continue
                route = all_routes[ei]
                x0, y0 = route[si]
                x1, y1 = route[si + 1]
                # Check if nudged position is obstacle-free
                if not _nudge_ok(x0, y0 + offset, x1, y1 + offset, ei):
                    # Try opposite direction
                    if _nudge_ok(x0, y0 - offset, x1, y1 - offset, ei):
                        offset = -offset
                    else:
                        # Try half offset
                        half = offset / 2
                        if _nudge_ok(x0, y0 + half, x1, y1 + half, ei):
                            offset = half
                        else:
                            continue  # skip nudge entirely
                route[si] = (x0, y0 + offset)
                route[si + 1] = (x1, y1 + offset)
                # Also adjust adjacent vertical segments to connect
                if si > 0:
                    px, py = route[si - 1]
                    if abs(px - x0) < 0.01:  # vertical segment before
                        route[si - 1] = (px, py)  # keep, the y0+offset handles it
                        route[si] = (x0, y0 + offset)
                if si + 2 < len(route):
                    nx, ny = route[si + 2]
                    if abs(nx - x1) < 0.01:  # vertical segment after
                        route[si + 1] = (x1, y1 + offset)

    # Nudge overlapping vertical segments
    for rx, segs in v_segments.items():
        if len(segs) <= 1:
            continue
        groups = []
        for seg in segs:
            placed = False
            for group in groups:
                for gseg in group:
                    if seg[2] < gseg[3] and seg[3] > gseg[2]:
                        group.append(seg)
                        placed = True
                        break
                if placed:
                    break
            if not placed:
                groups.append([seg])

        for group in groups:
            if len(group) <= 1:
                continue
            n = len(group)
            for k, (ei, si, _, _) in enumerate(group):
                offset = (k - (n - 1) / 2) * NUDGE_SPACING
                if abs(offset) < 0.001:
                    continue
                route = all_routes[ei]
                x0, y0 = route[si]
                x1, y1 = route[si + 1]
                # Check if nudged position is obstacle-free
                if not _nudge_ok(x0 + offset, y0, x1 + offset, y1, ei):
                    if _nudge_ok(x0 - offset, y0, x1 - offset, y1, ei):
                        offset = -offset
                    else:
                        half = offset / 2
                        if _nudge_ok(x0 + half, y0, x1 + half, y1, ei):
                            offset = half
                        else:
                            continue  # skip nudge
                route[si] = (x0 + offset, y0)
                route[si + 1] = (x1 + offset, y1)


# ════════════════════════════════════════════════════════════════════
#  RENDERING WITH ROUNDED CORNERS
# ════════════════════════════════════════════════════════════════════

def draw_rounded_ortho_arrow(ax, waypoints, color, lw, dash=None, arrow_scale=14):
    """Draw orthogonal polyline with rounded corners at bends and arrowhead at end."""
    if len(waypoints) < 2:
        return

    r = CORNER_RADIUS
    # Build a matplotlib Path with CURVE3 at each bend
    verts = []
    codes = []

    if len(waypoints) == 2:
        # Simple straight line + arrowhead
        verts = [waypoints[0], waypoints[1]]
        codes = [MplPath.MOVETO, MplPath.LINETO]
    else:
        # Start point
        verts.append(waypoints[0])
        codes.append(MplPath.MOVETO)

        for i in range(1, len(waypoints) - 1):
            prev = waypoints[i - 1]
            curr = waypoints[i]
            nxt = waypoints[i + 1]

            # Direction vectors
            dx_in = curr[0] - prev[0]
            dy_in = curr[1] - prev[1]
            dx_out = nxt[0] - curr[0]
            dy_out = nxt[1] - curr[1]

            len_in = max(abs(dx_in), abs(dy_in))
            len_out = max(abs(dx_out), abs(dy_out))

            # Clamp radius to half the shorter segment
            actual_r = min(r, len_in / 2, len_out / 2)

            if actual_r < 0.02:
                # Too small for curve, just use the point
                verts.append(curr)
                codes.append(MplPath.LINETO)
                continue

            # Normalize directions
            if len_in > 0:
                ndx_in = dx_in / len_in
                ndy_in = dy_in / len_in
            else:
                ndx_in, ndy_in = 0, 0
            if len_out > 0:
                ndx_out = dx_out / len_out
                ndy_out = dy_out / len_out
            else:
                ndx_out, ndy_out = 0, 0

            # Point before curve starts
            p_before = (curr[0] - ndx_in * actual_r, curr[1] - ndy_in * actual_r)
            # Point after curve ends
            p_after = (curr[0] + ndx_out * actual_r, curr[1] + ndy_out * actual_r)

            # Line to curve start
            verts.append(p_before)
            codes.append(MplPath.LINETO)

            # Quadratic bezier through corner point
            verts.append(curr)         # control point
            codes.append(MplPath.CURVE3)
            verts.append(p_after)      # end of curve
            codes.append(MplPath.CURVE3)

        # Line to last waypoint (but stop short for arrowhead)
        last = waypoints[-1]
        second_last = waypoints[-2]

        # Stop the path slightly before the end so the arrowhead draws cleanly
        arrow_gap = 0.08
        dx_final = last[0] - second_last[0]
        dy_final = last[1] - second_last[1]
        flen = max(abs(dx_final), abs(dy_final), 0.01)
        stop_x = last[0] - (dx_final / flen) * arrow_gap
        stop_y = last[1] - (dy_final / flen) * arrow_gap

        verts.append((stop_x, stop_y))
        codes.append(MplPath.LINETO)

    path = MplPath(verts, codes)

    # Draw the path
    ls = '-' if dash is None else (0, dash)
    patch = mpatches.FancyArrowPatch(
        path=path, arrowstyle='-', color=color, lw=lw,
        linestyle=ls, zorder=5, mutation_scale=arrow_scale)
    ax.add_patch(patch)

    # Draw arrowhead on the last segment
    if len(waypoints) >= 2:
        # Use a short annotate for just the arrowhead
        p_from = verts[-1] if len(verts) >= 1 else waypoints[-2]
        p_to = waypoints[-1]
        ax.annotate('', xy=p_to, xytext=p_from,
                    arrowprops=dict(arrowstyle='-|>', color=color, lw=lw,
                                    mutation_scale=arrow_scale, shrinkA=0, shrinkB=1),
                    zorder=5)


def edge_label(ax, x, y, text):
    """Draw a label with white background on an edge."""
    ax.text(x, y, text, fontsize=7, ha='center', va='center',
            color=SF_TEXT, style='italic', fontweight='medium', zorder=8,
            bbox=dict(boxstyle='round,pad=0.15', facecolor=SF_WHITE,
                      edgecolor='#C0C0C0', linewidth=0.6, alpha=0.97))


def compute_label_pos(waypoints, y_offset=0.18, x_offset=0.25):
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
            # Offset label above horizontal segments, right of vertical
            if abs(y0 - y1) < 0.01:  # horizontal
                best_mid = (mid_x, mid_y + y_offset)
            else:  # vertical
                best_mid = (mid_x + x_offset, mid_y)
    return best_mid


# ════════════════════════════════════════════════════════════════════
#  MAIN
# ════════════════════════════════════════════════════════════════════

def main():
    fig, ax = plt.subplots(1, 1, figsize=(16, 10), dpi=180)
    fig.patch.set_facecolor(SF_WHITE)
    ax.set_facecolor(SF_WHITE)

    # Compute positions
    positions = {nid: gp(col, row) for nid, _, _, _, col, row in nodes}
    x_max = LEFT_MARGIN + 5 * COL_SPACING + 2.0
    row0_top = CONTENT_TOP + HH
    row1_bot = CONTENT_TOP - ROW_SPACING - HH

    # View bounds
    bx, by = -0.35, row1_bot - 0.65
    btop = row0_top + 0.85
    y_min, y_max_v = by - 0.5, btop + 2.0
    ax.set_xlim(-0.6, x_max + 0.4)
    ax.set_ylim(y_min, y_max_v)
    ax.set_aspect('equal')
    ax.axis('off')

    x_center = LEFT_MARGIN + 2.5 * COL_SPACING

    # ── Title ───────────────────────────────────────────────────────
    ax.text(x_center, y_max_v - 0.25,
            'AI Matching App  \u2014  End-to-End ML Pipeline',
            fontsize=17, fontweight='bold', ha='center', va='top',
            color=SF_TEXT, fontfamily='sans-serif')
    ax.text(x_center, y_max_v - 0.75,
            'Snowflake Native Architecture',
            fontsize=10, ha='center', va='top',
            color=SF_SUBTITLE, fontfamily='sans-serif')

    # ── Boundary ────────────────────────────────────────────────────
    bw, bh = x_max + 0.25, btop - by
    boundary = mpatches.FancyBboxPatch(
        (bx, by), bw, bh,
        boxstyle=mpatches.BoxStyle.Round(pad=0.2),
        facecolor='none', edgecolor=SF_BOUNDARY,
        linewidth=2.0, linestyle=(0, (6, 4)), alpha=0.55, zorder=0)
    ax.add_patch(boundary)
    ax.text(bx + 0.15, btop - 0.08, 'Snowflake',
            fontsize=8.5, color=SF_BOUNDARY, fontweight='bold',
            fontfamily='sans-serif', alpha=0.55, va='top')

    # ── Column labels ───────────────────────────────────────────────
    for ci in range(6):
        cx = LEFT_MARGIN + ci * COL_SPACING
        ax.text(cx, btop + 0.35, column_labels[ci],
                fontsize=10.5, fontweight='bold', ha='center', va='bottom',
                color=SF_GROUP_BORDER[ci], fontfamily='sans-serif')

    # ── Column group backgrounds ────────────────────────────────────
    for ci in range(6):
        cx = LEFT_MARGIN + ci * COL_SPACING
        cn = [n for n in nodes if n[4] == ci]
        mr = max(n[5] for n in cn)
        pad = 0.15
        rx = cx - HW - pad
        rt = CONTENT_TOP + HH + pad
        rb = CONTENT_TOP - mr * ROW_SPACING - HH - pad
        bg = mpatches.FancyBboxPatch(
            (rx, rb), CARD_W + 2 * pad, rt - rb,
            boxstyle=mpatches.BoxStyle.Round(pad=0.1),
            facecolor=SF_GROUP_BG[ci], edgecolor=SF_GROUP_BORDER[ci],
            linewidth=1.6, alpha=0.80, zorder=1)
        ax.add_patch(bg)

    # ── Nodes ───────────────────────────────────────────────────────
    for nid, label, subtitle, icon_file, col, row in nodes:
        x, y = positions[nid]
        card = mpatches.FancyBboxPatch(
            (x - HW, y - HH), CARD_W, CARD_H,
            boxstyle=mpatches.BoxStyle.Round(pad=0.08),
            facecolor=SF_WHITE, edgecolor=SF_GROUP_BORDER[col],
            linewidth=1.3, alpha=0.97, zorder=3)
        ax.add_patch(card)

        icon_data = load_icon(icon_file)
        ib = OffsetImage(icon_data, zoom=0.78)
        ab = AnnotationBbox(ib, (x, y + 0.22), frameon=False, zorder=4)
        ax.add_artist(ab)

        ax.text(x, y - 0.32, label, fontsize=8.5, fontweight='bold',
                ha='center', va='center', color=SF_TEXT,
                fontfamily='sans-serif', zorder=6)
        ax.text(x, y - 0.53, subtitle, fontsize=6.5,
                ha='center', va='center', color=SF_SUBTITLE,
                fontfamily='sans-serif', zorder=6)

    # ════════════════════════════════════════════════════════════════
    #  ROUTE ALL EDGES
    # ════════════════════════════════════════════════════════════════
    obstacles = build_obstacles(positions)
    node_list = [n[0] for n in nodes]

    # Build obstacle index mapping: node_id -> obstacle index
    obs_idx = {nid: i for i, nid in enumerate(node_list)}

    # Pre-compute port offsets: spread edges sharing the same (node, side)
    # Count edges per (node, side) for both source and destination
    port_counts = {}  # (node_id, side) -> count
    port_assign = {}  # (edge_index, 'src'|'dst') -> offset

    resolved_sides = []
    for src_id, dst_id, tier, opts in edges:
        exit_side = opts.get('exit_side')
        enter_side = opts.get('enter_side')
        if not exit_side or not enter_side:
            es, ns = auto_sides(positions, src_id, dst_id)
            exit_side = exit_side or es
            enter_side = enter_side or ns
        resolved_sides.append((exit_side, enter_side))
        port_counts.setdefault((src_id, exit_side), []).append(len(resolved_sides) - 1)
        port_counts.setdefault((dst_id, enter_side), []).append(len(resolved_sides) - 1)

    PORT_SPREAD = 0.18  # spacing between ports on same side
    for key, edge_indices in port_counts.items():
        n = len(edge_indices)
        if n <= 1:
            for ei in edge_indices:
                if key[0] == edges[ei][0]:  # source
                    port_assign[(ei, 'src')] = 0.0
                else:
                    port_assign[(ei, 'dst')] = 0.0
            continue
        for k, ei in enumerate(edge_indices):
            offset = (k - (n - 1) / 2) * PORT_SPREAD
            if key[0] == edges[ei][0] and key[1] == resolved_sides[ei][0]:
                port_assign[(ei, 'src')] = offset
            if key[0] == edges[ei][1] and key[1] == resolved_sides[ei][1]:
                port_assign[(ei, 'dst')] = offset

    # Collect all ports for visibility graph
    all_ports = []
    for i, (src_id, dst_id, tier, opts) in enumerate(edges):
        exit_side, enter_side = resolved_sides[i]
        src_off = port_assign.get((i, 'src'), 0.0)
        dst_off = port_assign.get((i, 'dst'), 0.0)
        sp = get_port(positions, src_id, exit_side, src_off)
        ep = get_port(positions, dst_id, enter_side, dst_off)
        all_ports.append((sp[0], sp[1], exit_side))
        all_ports.append((ep[0], ep[1], enter_side))

    # Build visibility graph once
    candidates = build_visibility_graph(obstacles, all_ports, positions)

    # Route each edge
    all_routes = []
    edge_meta = []  # (tier, opts) for each route

    for i, (src_id, dst_id, tier, opts) in enumerate(edges):
        exit_side, enter_side = resolved_sides[i]
        src_off = port_assign.get((i, 'src'), 0.0)
        dst_off = port_assign.get((i, 'dst'), 0.0)
        sp = get_port(positions, src_id, exit_side, src_off)
        ep = get_port(positions, dst_id, enter_side, dst_off)

        route = astar_ortho(
            sp, ep, exit_side, enter_side,
            obstacles, candidates,
            obs_idx.get(src_id), obs_idx.get(dst_id)
        )
        route = simplify_path(route)
        all_routes.append(list(route))
        edge_meta.append((tier, opts))

    # Nudge parallel edges (obstacle-aware)
    nudge_parallel_edges(all_routes, obstacles, edges, obs_idx)

    # ════════════════════════════════════════════════════════════════
    #  DRAW ALL EDGES
    # ════════════════════════════════════════════════════════════════
    for i, (route, (tier, opts)) in enumerate(zip(all_routes, edge_meta)):
        color = TIER_COLORS[tier]
        lw = TIER_LW[tier]
        dash = TIER_DASH[tier]
        arrow_scale = TIER_ARROW_SCALE[tier]

        draw_rounded_ortho_arrow(ax, route, color, lw, dash, arrow_scale)

        # Draw label if specified
        label_text = opts.get('label')
        if label_text:
            y_off = -0.18 if opts.get('label_below') else 0.18
            label_pos = compute_label_pos(route, y_offset=y_off)
            if label_pos:
                edge_label(ax, label_pos[0], label_pos[1], label_text)

    # ── Save ────────────────────────────────────────────────────────
    plt.tight_layout(pad=0.3)
    out = f'{ICON_DIR}/architecture_diagram.png'
    fig.savefig(out, dpi=180, bbox_inches='tight',
                facecolor=SF_WHITE, edgecolor='none', pad_inches=0.2)
    plt.close()

    sz = os.path.getsize(out) / 1024
    print(f'Generated: {out}  ({sz:.0f} KB)')
    if sz > 800:
        Image.open(out).save(out, 'PNG', optimize=True)
        print(f'Optimized: {os.path.getsize(out) / 1024:.0f} KB')


if __name__ == '__main__':
    main()
