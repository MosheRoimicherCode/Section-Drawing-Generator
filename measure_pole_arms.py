from __future__ import annotations

import argparse
import math
from dataclasses import dataclass
from pathlib import Path

import ezdxf

from config import ARM_LAYERS, SURVEY_FILE, SURVEY_TO_OUTPUT_UNITS


@dataclass(frozen=True)
class PolylineMeasurement:
    """Stores all calculated information for one candidate arm polyline."""

    layer: str
    handle: str
    midpoint_x: float
    midpoint_y: float
    distance_to_pole: float
    length_dxf_units: float
    length_mm: int


def iter_polyline_vertices(entity) -> list[tuple[float, float, float]]:
    """Return the polyline vertices as (x, y, z) points.

    AutoCAD can store polylines in different DXF entity types:
    - POLYLINE: can contain true 3D vertices.
    - LWPOLYLINE: lightweight 2D polyline; z comes from its elevation.
    """
    dxftype = entity.dxftype()

    # dxftype() tells us the AutoCAD/DXF entity type, for example POLYLINE or LWPOLYLINE.
    if dxftype == "POLYLINE":
        # entity.vertices is the ezdxf API for reading vertex objects from a POLYLINE entity.
        # vertex.dxf.location contains the real CAD coordinate of that vertex.
        return [(vertex.dxf.location.x, vertex.dxf.location.y, vertex.dxf.location.z) for vertex in entity.vertices]

    if dxftype == "LWPOLYLINE":
        # LWPOLYLINE stores XY points only. The shared z value is stored as dxf.elevation.
        elevation = float(entity.dxf.elevation or 0)

        # get_points("xy") asks ezdxf to return only the X and Y values for each lightweight point.
        return [(point[0], point[1], elevation) for point in entity.get_points("xy")]

    return []


def polyline_length(vertices: list[tuple[float, float, float]]) -> float:
    """Calculate the 3D length by summing the distance between each vertex pair."""
    total = 0.0

    # zip(vertices, vertices[1:]) creates pairs: point 1-2, point 2-3, point 3-4, etc.
    for start, end in zip(vertices, vertices[1:]):
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        dz = end[2] - start[2]
        total += math.sqrt(dx * dx + dy * dy + dz * dz)
    return total


def polyline_midpoint(vertices: list[tuple[float, float, float]]) -> tuple[float, float]:
    """Calculate a simple average XY midpoint for choosing the nearest pole."""
    return (
        sum(vertex[0] for vertex in vertices) / len(vertices),
        sum(vertex[1] for vertex in vertices) / len(vertices),
    )


def distance_xy(x1: float, y1: float, x2: float, y2: float) -> float:
    """Return the 2D distance between two XY coordinates."""
    return math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)


def closest_polyline_per_layer(survey_path: Path, pole_x: float, pole_y: float) -> dict[str, PolylineMeasurement]:
    """Find the closest arm polyline to one pole for every configured layer."""
    # ezdxf.readfile opens the DXF file and parses it into a document object.
    doc = ezdxf.readfile(survey_path)

    # modelspace() is the main drawing area where normal CAD geometry usually lives.
    msp = doc.modelspace()
    closest: dict[str, PolylineMeasurement] = {}

    # query("POLYLINE LWPOLYLINE") returns only these entity types from modelspace.
    for entity in msp.query("POLYLINE LWPOLYLINE"):
        # entity.dxf.layer is the AutoCAD layer name assigned to this entity.
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

        # Keep only one line per layer: the line whose midpoint is closest to the pole XY.
        if current is None or measurement.distance_to_pole < current.distance_to_pole:
            closest[layer] = measurement

    return closest


def main() -> None:
    """Parse command-line arguments and print the closest line length per layer."""
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

    # Core calculation: scan the DXF and keep the nearest measured polyline for each configured layer.
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

        # By default we print millimeters. --dxf-units prints the raw AutoCAD drawing units.
        length = measurement.length_dxf_units if args.dxf_units else measurement.length_mm
        unit = "dxf_units" if args.dxf_units else "mm"
        print(
            f"{layer} = {length} {unit} "
            f"(handle={measurement.handle}, distance_xy={measurement.distance_to_pole:.3f}, "
            f"midpoint=({measurement.midpoint_x:.3f}, {measurement.midpoint_y:.3f}))"
        )


if __name__ == "__main__":
    main()
