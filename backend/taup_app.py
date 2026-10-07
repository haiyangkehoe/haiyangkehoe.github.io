"""Backend for taup.html — computes TauP arrivals and figures with ObsPy.

Run from the project root:
    pip install flask obspy matplotlib
    python backend/taup_app.py
Then open http://localhost:5001
"""
import base64
import io
import os
import threading
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from flask import Flask, jsonify, request, send_file

try:
    from flask_cors import CORS
except ImportError:  # only needed when the page is hosted on a different domain
    CORS = None
from obspy.taup import TauPyModel
from obspy.taup.tau import plot_ray_paths, plot_travel_times

ROOT = Path(__file__).resolve().parent.parent  # folder containing taup.html

app = Flask(__name__)

# Let the page hosted on seismolo.gy call this API from the browser
if CORS is not None:
    CORS(app, resources={r"/api/*": {"origins": [
        "https://seismolo.gy",
        "https://www.seismolo.gy",
    ]}})

_models = {}
_plot_lock = threading.Lock()  # pyplot is not thread-safe


def get_model(name):
    if name not in _models:
        _models[name] = TauPyModel(model=name)
    return _models[name]


def fig_to_b64(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=130, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode()


def fig_rays_at_distance(model_name, depth, dist, phases):
    """Ray paths pinned to the chosen distance."""
    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
    plot_ray_paths(
        source_depth=depth,
        phase_list=phases,
        min_degrees=dist,
        max_degrees=dist,
        model=model_name,
        ax=ax,
        fig=fig,
        legend=True,
        show=False,
    )
    return fig


def fig_rays_all(model_name, depth, phases):
    """Ray paths over a fan of distances (npoints=36)."""
    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
    plot_ray_paths(
        source_depth=depth,
        phase_list=phases,
        npoints=36,
        model=model_name,
        ax=ax,
        fig=fig,
        legend=True,
        show=False,
    )
    return fig


def fig_travel_times(model_name, depth, dist, phases):
    """Travel-time curves, with the chosen distance marked."""
    fig, ax = plt.subplots(figsize=(8, 8))  # same size as the polar figures
    res = plot_travel_times(
        source_depth=depth,
        phase_list=phases,
        model=model_name,
        ax=ax,
        fig=fig,
        show=False,
    )
    fig = getattr(res, "figure", res)  # returns an Axes or a Figure by version
    for ax in fig.axes:
        ax.axvline(dist, color="#ffb454", ls="--", lw=1)
    return fig


@app.route("/")
def index():
    # The page is either taup/index.html (as hosted on seismolo.gy) or taup.html
    for page in (ROOT / "taup" / "index.html", ROOT / "taup.html"):
        if page.exists():
            return send_file(page)
    return "Could not find taup/index.html or taup.html next to the backend folder.", 404


@app.route("/api/taup", methods=["POST"])
def taup():
    data = request.get_json(force=True)
    try:
        model_name = str(data.get("model", "ak135"))
        source_depth_in_km = float(data.get("source_depth_in_km", 100))
        distance_in_degree = float(data.get("distance_in_degree", 120))
        phase_list = [p.strip() for p in data.get("phase_list", []) if p.strip()]
        if not phase_list:
            return jsonify(error="Provide at least one phase."), 400
        if not (0 <= distance_in_degree <= 180):
            return jsonify(error="Distance must be between 0 and 180 degrees."), 400
        if source_depth_in_km < 0:
            return jsonify(error="Depth must be >= 0 km."), 400

        model = get_model(model_name)
        arrivals = model.get_travel_times(
            source_depth_in_km=source_depth_in_km,
            distance_in_degree=distance_in_degree,
            phase_list=phase_list,
        )

        rows = [{
            "phase": a.name,
            "time": a.time,
            "ray_param": a.ray_param_sec_degree,
            "takeoff": a.takeoff_angle,
            "incident": a.incident_angle,
            "distance": a.purist_distance,
            "purist_name": a.purist_name,
        } for a in arrivals]

        builders = {
            "rays_at_distance": lambda: fig_rays_at_distance(
                model_name, source_depth_in_km, distance_in_degree, phase_list),
#            "rays_all": lambda: fig_rays_all(
#                model_name, source_depth_in_km, phase_list),
            "times": lambda: fig_travel_times(
                model_name, source_depth_in_km, distance_in_degree, phase_list),
        }

        # Match the figures to the page theme ("dark" or "light")
        style = "default" if data.get("theme") == "light" else "dark_background"

        figures = {}
        with _plot_lock, plt.style.context(style):
            for key, build in builders.items():
                try:
                    figures[key] = fig_to_b64(build())
                except Exception as e:  # one failed figure shouldn't break the rest
                    plt.close("all")
                    figures[key + "_error"] = str(e)

        return jsonify(arrivals=rows, arrivals_text=str(arrivals), figures=figures)
    except Exception as e:
        return jsonify(error=str(e)), 400


if __name__ == "__main__":
    # Local testing. Port 5001 because macOS uses 5000 for AirPlay Receiver.
    port = int(os.environ.get("PORT", 5001))
    print(f"Open http://localhost:{port}")
    app.run(debug=True, port=port)
