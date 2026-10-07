"""
Runs inside the browser (Pyodide). Same calculations as the old Flask backend,
but local: ObsPy's TauPyModel for the arrivals, matplotlib for the figures.

Two modes, chosen by the page:
  * "single": phases and travel times at one distance
  * "range":  travel times at N evenly spaced distances between two limits

Figures are returned as SVG that has no theme baked in: text, axes and the
legend background use placeholder colours that are swapped for CSS ones
(currentColor / var(--fig-bg)). The page can therefore switch between dark and
light instantly, without recomputing anything.

The page calls compute(...) and gets back a JSON string.
"""
import io
import json
import re

import matplotlib
import numpy as np

matplotlib.use("agg")  # draw to memory, not to a canvas
import matplotlib.pyplot as plt  # noqa: E402
from obspy.taup import TauPyModel  # noqa: E402
from obspy.taup.tau import plot_ray_paths, plot_travel_times  # noqa: E402

MAX_DISTANCES = 360  # keeps the range mode quick

# Placeholder colours, replaced in the SVG text afterwards.
FG = "#fe0001"   # text, axes, outlines -> currentColor (set by the page's CSS)
BG = "#fe0002"   # legend background    -> var(--fig-bg)
MUTED = "#8b949e"  # grid lines and legend frame: readable on dark and light

_RC = {
    "text.color": FG,
    "axes.labelcolor": FG,
    "axes.edgecolor": FG,
    "xtick.color": FG,
    "ytick.color": FG,
    "lines.color": FG,
    "patch.edgecolor": FG,
    "grid.color": MUTED,
    "grid.alpha": 0.5,
    "axes.facecolor": "none",
    "figure.facecolor": "none",
    "savefig.facecolor": "none",
    "legend.facecolor": BG,
    "legend.edgecolor": MUTED,
    "legend.framealpha": 0.85,
    "svg.fonttype": "path",   # text as shapes: identical look everywhere
}

_models = {}


def _get_model(name):
    if name not in _models:
        _models[name] = TauPyModel(model=name)
    return _models[name]


def _svg(fig, key):
    buf = io.StringIO()
    # a distinct salt keeps clip-path ids unique across the inline SVGs
    with plt.rc_context({"svg.hashsalt": key}):
        fig.savefig(buf, format="svg", bbox_inches="tight", transparent=True)
    plt.close(fig)
    svg = buf.getvalue()
    svg = svg[svg.index("<svg"):]  # drop the XML prolog and doctype
    svg = re.sub(re.escape(FG), "currentColor", svg, flags=re.I)
    svg = re.sub(re.escape(BG), "var(--fig-bg)", svg, flags=re.I)
    return svg


def _rays(model, depth, phases, lo, hi, n):
    """Ray paths to n evenly spaced distances from lo to hi (n=1: just lo)."""
    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
    plot_ray_paths(source_depth=depth, phase_list=phases, min_degrees=lo,
                   max_degrees=hi, npoints=n, model=model, ax=ax, fig=fig,
                   legend=True, show=False)
    return fig


def _travel_times(model, depth, phases, lo, hi, is_range):
    """Travel-time curves; always drawn over 0-180 degrees.

    Single distance: a dashed line marks it. Range: the range is shaded.
    """
    fig, ax = plt.subplots(figsize=(8, 8))
    res = plot_travel_times(source_depth=depth, phase_list=phases,
                            model=model, ax=ax, fig=fig, show=False)
    fig = getattr(res, "figure", res)  # an Axes in current ObsPy
    for a in fig.axes:
        if is_range:
            if lo < 180:
                a.axvspan(lo, min(hi, 180), color=MUTED, alpha=0.2, lw=0)
        else:
            a.axvline(lo, color=FG, ls="--", lw=1, alpha=0.6)
    return fig


def _friendly(err):
    msg = str(err)
    if "No ray paths" in msg:
        return ("No arrivals for these phases at these distances and this "
                "depth, so there is nothing to draw.")
    return msg


def _row(a, distance):
    return {
        "distance": distance,              # distance you asked for
        "phase": a.name,
        "time": a.time,
        "ray_param": a.ray_param_sec_degree,
        "takeoff": a.takeoff_angle,
        "incident": a.incident_angle,
        "path": a.purist_distance,         # angle the ray actually travels
    }


def compute(mode, model, depth, phases_json, params_json):
    """mode "single": params {"distance": d}
       mode "range":  params {"min": lo, "max": hi, "n": count}"""
    try:
        phases = [p.strip() for p in json.loads(phases_json) if p.strip()]
        params = json.loads(params_json)
        depth = float(depth)
        if not phases:
            return json.dumps({"error": "Provide at least one phase."})
        if depth < 0:
            return json.dumps({"error": "Depth must be >= 0 km."})

        if mode == "single":
            d = float(params["distance"])
            if not (0 <= d <= 180):
                return json.dumps(
                    {"error": "Distance must be between 0 and 180 degrees."})
            distances = [d]
            lo = hi = d
            n = 1
        elif mode == "range":
            lo, hi = float(params["min"]), float(params["max"])
            n = int(params["n"])
            if not (0 <= lo <= 360 and 0 <= hi <= 360):
                return json.dumps(
                    {"error": "The range must lie between 0 and 360 degrees."})
            if lo > hi:
                return json.dumps(
                    {"error": "\"From\" must not be larger than \"To\"."})
            if not (1 <= n <= MAX_DISTANCES):
                return json.dumps({"error": (
                    f"Number of distances must be between 1 and "
                    f"{MAX_DISTANCES}.")})
            distances = [float(x) for x in np.linspace(lo, hi, n)]
        else:
            return json.dumps({"error": f"Unknown mode: {mode}"})

        m = _get_model(model)
        rows = []
        text = None
        for d in distances:
            arrivals = m.get_travel_times(source_depth_in_km=depth,
                                          distance_in_degree=d,
                                          phase_list=phases)
            rows.extend(_row(a, d) for a in arrivals)
            if mode == "single":
                text = str(arrivals)

        builders = {
            "rays": lambda: _rays(model, depth, phases, lo, hi, n),
            "times": lambda: _travel_times(
                model, depth, phases, lo, hi, mode == "range"),
        }
        figures = {}
        with plt.rc_context(_RC):
            for key, build in builders.items():
                try:
                    figures[key] = _svg(build(), key)
                except Exception as e:  # one failed figure shouldn't hide the rest
                    plt.close("all")
                    figures[key + "_error"] = _friendly(e)

        return json.dumps({
            "mode": mode,
            "arrivals": rows,
            "arrivals_text": text,
            "distances": distances,
            "figures": figures,
        })
    except Exception as e:
        return json.dumps({"error": _friendly(e)})
