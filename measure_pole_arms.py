from __future__ import annotations

import argparse
import math
from dataclasses import dataclass
from pathlib import Path

import ezdxf

from config import ARM_LAYERS, SURVEY_FILE, SURVEY_TO_OUTPUT_UNITS


@dataclass(frozen=True)
class PolylineMeasurement:
    layer: str
    handle: str
    midpoint_x: float
    midpoint_y: float
    distance_to_pole: float
    length_dxf_units: float
    length_mm: int


def iter_polyline_vertices(entity) -> list[tuple[float, float, float]]:
    dxftype = entity.dxftype()
    if dxftype == "POLYLINE":
        return [(vertex.dxf.location.x, vertex.dxf.location.y, vertex.dxf.location.z) for vertex in entity.vertices]
    if dxftype == "LWPOLYLINE":
        elevation = float(entity.dxf.elevation or 0)
        return [(point[0], point[1], elevation) for point in entity.get_points("xy")]
    return []


def polyline_length(vertices: list[tuple[float, float, float]]) -> float:
    total = 0.0
    for start, end in zip(vertices, vertices[1:]):
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        dz = end[2] - start[2]
        total += math.sqrt(dx * dx + dy * dy + dz * dz)
    return total


def polyline_midpoint(vertices: list[tuple[float, float, float]]) -> tuple[float, float]:
    return (
        sum(vertex[0] for vertex in vertices) / len(vertices),
        sum(vertex[1] for vertex in vertices) / len(vertices),
    )


def distance_xy(x1: float, y1: float, x2: float, y2: float) -> float:
    return math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)


def closest_polyline_per_layer(survey_path: Path, pole_x: float, pole_y: float) -> dict[str, PolylineMeasurement]:
    doc = ezdxf.readfile(survey_path)
    msp = doc.modelspace()
    closest: dict[str, PolylineMeasurement] = {}

    for entity in msp.query("POLYLINE LWPOLYLINE"):
        layer = entity.dxf.layer
        if layer not in ARM_LAYERS:
            continue

        vertices = iter_polyline_vertices(entity)
        if len(vertices) < 2:
            continue

        mid_x, mid_y = polyline_midpoint(vertices)
        distance = distance_xy(mid_x, mid_y, pole_x, pole_y)
        length = polyline_length(vertices)
        measurement = PolylineMeasurement(
            layer=layer,
            handle=entity.dxf.handle,
            midpoint_x=mid_x,
            midpoint_y=mid_y,
            distance_to_pole=distance,
            length_dxf_units=length,
            length_mm=round(length * SURVEY_TO_OUTPUT_UNITS),
        )

        current = closest.get(layer)
        if current is None or measurement.distance_to_pole < current.distance_to_pole:
            closest[layer] = measurement

    return closest


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Print the closest 3D polyline length per configured arm layer for one pole XY coordinate."
    )
    parser.add_argument("--x", required=True, type=float, help="Pole X coordinate in the same coordinate system as survey.dxf")
    parser.add_argument("--y", required=True, type=float, help="Pole Y coordinate in the same coordinate system as survey.dxf")
    parser.add_argument(
        "--survey",
        default=str(SURVEY_FILE),
        help=f"Survey DXF path. Default: {SURVEY_FILE}",
    )
    parser.add_argument(
        "--dxf-units",
        action="store_true",
        help="Print raw DXF units instead of converted millimeters.",
    )
    args = parser.parse_args()

    survey_path = Path(args.survey)
    measurements = closest_polyline_per_layer(survey_path, args.x, args.y)

    if not measurements:
        print("No matching POLYLINE/LWPOLYLINE entities found on configured arm layers.")
        print(f"Configured layers: {', '.join(ARM_LAYERS)}")
        return

    for layer in ARM_LAYERS:
        measurement = measurements.get(layer)
        if measurement is None:
            print(f"{layer} = MISSING")
            continue

        length = measurement.length_dxf_units if args.dxf_units else measurement.length_mm
        unit = "dxf_units" if args.dxf_units else "mm"
        print(
            f"{layer} = {length} {unit} "
            f"(handle={measurement.handle}, distance_xy={measurement.distance_to_pole:.3f}, "
            f"midpoint=({measurement.midpoint_x:.3f}, {measurement.midpoint_y:.3f}))"
        )


if __name__ == "__main__":
    main()
