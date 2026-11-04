"""Pure numpy functions for the drainage derivatives (no GDAL, no GCS) so they can be unit tested.

Height above drainage here is HAND-like: elevation minus the elevation of the NEAREST stream cell by
straight-line distance (not by flow path), because only flow accumulation and the conditioned DEM are
available. It is an approximation and is named `hand_euclid_m` everywhere.
"""

import numpy as np

MAX_PIXELS = 60_000_000  # in-memory regional processing only; national needs a tiled variant


def sigmoid(x, k, midpoint):
    z = np.clip(-k * (np.asarray(x, dtype="float64") - midpoint), -500, 500)
    return 1.0 / (1.0 + np.exp(z))


def stream_mask(acc, threshold_cells):
    """True where flow accumulation reaches the threshold; NaN cells are never streams."""
    with np.errstate(invalid="ignore"):
        return np.nan_to_num(acc, nan=-1.0) >= threshold_cells


def height_above_drainage(dem, streams):
    """dem - elevation of the nearest stream cell, floored at 0. NaN if there are no stream cells."""
    from scipy.ndimage import distance_transform_edt

    if not streams.any():
        return np.full(dem.shape, np.nan)
    _, (iy, ix) = distance_transform_edt(~streams, return_indices=True)
    return np.maximum(dem - dem[iy, ix], 0.0)


def s_drainage(acc, hand, slope_deg, params):
    """Blend three sigmoid terms into a 0..1 drainage hazard score (higher = more drainage-prone)."""
    w, c = params["weights"], params["curves"]
    up = c["upstream_area_log10_cells"]
    hd = c["height_above_drainage_m"]
    sl = c["slope_deg"]
    with np.errstate(invalid="ignore", divide="ignore"):
        s_up = sigmoid(np.log10(np.maximum(acc, 1.0)), up["k"], up["midpoint"])
    s_hand = 1.0 - sigmoid(hand, hd["k"], hd["midpoint"])
    s_slope = 1.0 - sigmoid(slope_deg, sl["k"], sl["midpoint"])
    score = w["upstream_area"] * s_up + w["height_above_drainage"] * s_hand + w["slope"] * s_slope
    total = sum(w.values())
    return (score / total).astype("float32")


def percentile_stops(values, percentiles=(2, 25, 50, 75, 98)):
    """Real data-driven colour-ramp stops (finite values only)."""
    finite = values[np.isfinite(values)]
    if finite.size == 0:
        raise ValueError("no finite values to derive colour stops from")
    return [float(np.percentile(finite, p)) for p in percentiles]

