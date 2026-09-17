import zipfile
from xml.etree import ElementTree as ET

from shapely.geometry import Point, Polygon
from shapely.ops import unary_union

KML_TAG = "{http://www.opengis.net/kml/2.2}"
KML_NS = {"kml": "http://www.opengis.net/kml/2.2"}


def _parse_ring(coords_el):
    ring = []
    for triplet in coords_el.text.strip().split():
        lon, lat, *_ = triplet.split(",")
        ring.append((float(lon), float(lat)))
    return ring


def _parse_polygon_element(polygon_el):
    outer_el = polygon_el.find(f"{KML_TAG}outerBoundaryIs/{KML_TAG}LinearRing/{KML_TAG}coordinates")
    exterior = _parse_ring(outer_el)
    holes = []
    for inner_el in polygon_el.findall(f"{KML_TAG}innerBoundaryIs/{KML_TAG}LinearRing/{KML_TAG}coordinates"):
        holes.append(_parse_ring(inner_el))
    return Polygon(exterior, holes)


def _parse_placemark_geometry(placemark):
    polygons = [_parse_polygon_element(el) for el in placemark.iter(f"{KML_TAG}Polygon")]
    if not polygons:
        return None
    if len(polygons) == 1:
        return polygons[0]
    return unary_union(polygons)


def _load_kml_bytes(path):
    path = str(path)
    if path.lower().endswith(".kmz"):
        with zipfile.ZipFile(path) as zf:
            kml_name = next(n for n in zf.namelist() if n.endswith(".kml"))
            return zf.read(kml_name)
    with open(path, "rb") as f:
        return f.read()


def load_named_polygons(path):
    """Parses every Placemark in a KML/KMZ into (name, shapely geometry) pairs."""
    root = ET.fromstring(_load_kml_bytes(path))
    named_polygons = []
    for placemark in root.iter(f"{KML_TAG}Placemark"):
        name_el = placemark.find("kml:name", KML_NS)
        name = name_el.text if name_el is not None else None
        geometry = _parse_placemark_geometry(placemark)
        if geometry is None:
            continue
        named_polygons.append((name, geometry))
    return named_polygons


def load_polygons_from_kmz(kmz_path):
    return load_named_polygons(kmz_path)


def is_inside(latitude, longitude, polygons):
    point = Point(float(longitude), float(latitude))
    return any(polygon.intersects(point) for _, polygon in polygons)


def find_intersecting(named_polygons, region):
    """Returns [(name, geometry)] for every entry whose geometry intersects `region`."""
    return [(name, geom) for name, geom in named_polygons if geom.intersects(region)]
