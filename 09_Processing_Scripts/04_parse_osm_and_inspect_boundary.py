"""Phase 1 Script: Parse raw OSM XML into clean GeoPackage/GeoJSON layers (UTM 43N & WGS84) and inspect Narowal features."""

import json
import os
import xml.etree.ElementTree as ET
import geopandas as gpd
from shapely.geometry import Point, LineString, Polygon, MultiPolygon
from shapely.ops import polygonize

PROJECT_ROOT = r"C:\Users\LENOVO\.gemini\antigravity\scratch\Narowal_Urban_Green_Infrastructure"
OSM_RAW = os.path.join(PROJECT_ROOT, "02_Raw_Data", "01_OSM", "narowal_urban_bbox_raw.osm")
OUT_DIR = os.path.join(PROJECT_ROOT, "03_Processed_Data", "01_Base_Mapping")
os.makedirs(OUT_DIR, exist_ok=True)


def parse_osm_xml(osm_path: str):
    """Parse nodes, ways, and relations from raw Overpass OSM XML."""
    nodes = {}
    ways = {}
    relations = []
    tagged_nodes = []

    for event, elem in ET.iterparse(osm_path, events=("end",)):
        tag = elem.tag
        if tag == "node":
            nid = int(elem.attrib["id"])
            lat = float(elem.attrib["lat"])
            lon = float(elem.attrib["lon"])
            nodes[nid] = (lon, lat)
            tags = {c.attrib["k"]: c.attrib["v"] for c in elem.findall("tag")}
            if tags:
                tagged_nodes.append((nid, lon, lat, tags))
            elem.clear()
        elif tag == "way":
            wid = int(elem.attrib["id"])
            nds = [int(nd.attrib["ref"]) for nd in elem.findall("nd")]
            tags = {c.attrib["k"]: c.attrib["v"] for c in elem.findall("tag")}
            ways[wid] = (nds, tags)
            elem.clear()
        elif tag == "relation":
            rid = int(elem.attrib["id"])
            members = [(m.attrib["type"], int(m.attrib["ref"]), m.attrib.get("role", "")) for m in elem.findall("member")]
            tags = {c.attrib["k"]: c.attrib["v"] for c in elem.findall("tag")}
            relations.append((rid, members, tags))
            elem.clear()

    return nodes, tagged_nodes, ways, relations


def way_to_geom(nds, nodes, as_poly=False):
    coords = [nodes[n] for n in nds if n in nodes]
    if len(coords) < 2:
        return None
    if as_poly and len(coords) >= 4 and coords[0] == coords[-1]:
        p = Polygon(coords)
        if not p.is_valid:
            p = p.buffer(0)
        return p if not p.is_empty else None
    return LineString(coords)


def main():
    print("Parsing raw OSM XML:", OSM_RAW)
    nodes, tagged_nodes, ways, relations = parse_osm_xml(OSM_RAW)
    print(f"Loaded {len(nodes):,} nodes ({len(tagged_nodes):,} tagged), {len(ways):,} ways, {len(relations):,} relations")

    roads = []
    buildings = []
    parks_green = []
    waterways = []
    waterbodies = []
    railways = []
    facilities_poly = []

    for wid, (nds, tags) in ways.items():
        if not tags:
            continue
        is_closed = len(nds) >= 4 and nds[0] == nds[-1]

        if "highway" in tags:
            g = way_to_geom(nds, nodes, as_poly=False)
            if g is not None:
                roads.append({
                    "osm_id": f"way/{wid}",
                    "highway": tags.get("highway"),
                    "name": tags.get("name"),
                    "surface": tags.get("surface"),
                    "access": tags.get("access"),
                    "foot": tags.get("foot"),
                    "oneway": tags.get("oneway"),
                    "geometry": g,
                })

        if "building" in tags and is_closed:
            g = way_to_geom(nds, nodes, as_poly=True)
            if g is not None:
                buildings.append({
                    "osm_id": f"way/{wid}",
                    "building": tags.get("building"),
                    "name": tags.get("name"),
                    "amenity": tags.get("amenity"),
                    "geometry": g,
                })

        leisure = tags.get("leisure", "")
        landuse = tags.get("landuse", "")
        if leisure in ("park", "playground", "recreation_ground", "garden", "pitch", "stadium", "sports_centre") or landuse in ("recreation_ground", "village_green", "grass", "meadow", "cemetery"):
            if is_closed:
                g = way_to_geom(nds, nodes, as_poly=True)
                if g is not None:
                    parks_green.append({
                        "osm_id": f"way/{wid}",
                        "name": tags.get("name"),
                        "leisure": leisure,
                        "landuse": landuse,
                        "access": tags.get("access"),
                        "geometry": g,
                    })

        if "waterway" in tags:
            g = way_to_geom(nds, nodes, as_poly=False)
            if g is not None:
                waterways.append({
                    "osm_id": f"way/{wid}",
                    "waterway": tags.get("waterway"),
                    "name": tags.get("name"),
                    "intermittent": tags.get("intermittent"),
                    "geometry": g,
                })

        if tags.get("natural") == "water" or landuse == "reservoir" or "water" in tags:
            if is_closed:
                g = way_to_geom(nds, nodes, as_poly=True)
                if g is not None:
                    waterbodies.append({
                        "osm_id": f"way/{wid}",
                        "natural": tags.get("natural"),
                        "water": tags.get("water"),
                        "name": tags.get("name"),
                        "geometry": g,
                    })

        if "railway" in tags:
            g = way_to_geom(nds, nodes, as_poly=False)
            if g is not None:
                railways.append({
                    "osm_id": f"way/{wid}",
                    "railway": tags.get("railway"),
                    "name": tags.get("name"),
                    "geometry": g,
                })

        if "amenity" in tags and is_closed:
            g = way_to_geom(nds, nodes, as_poly=True)
            if g is not None:
                facilities_poly.append({
                    "osm_id": f"way/{wid}",
                    "amenity": tags.get("amenity"),
                    "name": tags.get("name"),
                    "geometry": g,
                })

    # Multipolygon relations for parks / buildings / waterbodies
    for rid, members, tags in relations:
        leisure = tags.get("leisure", "")
        landuse = tags.get("landuse", "")
        if leisure in ("park", "playground", "recreation_ground", "garden", "pitch", "stadium", "sports_centre") or landuse in ("recreation_ground", "village_green"):
            outer_lines = []
            for mtype, mref, role in members:
                if mtype == "way" and mref in ways and role in ("outer", ""):
                    g = way_to_geom(ways[mref][0], nodes, as_poly=False)
                    if g is not None:
                        outer_lines.append(g)
            if outer_lines:
                polys = list(polygonize(outer_lines))
                if polys:
                    geom = polys[0] if len(polys) == 1 else MultiPolygon(polys)
                    parks_green.append({
                        "osm_id": f"rel/{rid}",
                        "name": tags.get("name"),
                        "leisure": leisure,
                        "landuse": landuse,
                        "access": tags.get("access"),
                        "geometry": geom,
                    })

    # Tagged point nodes (places, parks, amenities)
    places = []
    facility_pts = []
    park_pts = []
    for nid, lon, lat, tags in tagged_nodes:
        pt = Point(lon, lat)
        if "place" in tags:
            places.append({"osm_id": f"node/{nid}", "place": tags.get("place"), "name": tags.get("name"), "geometry": pt})
        if "amenity" in tags:
            facility_pts.append({"osm_id": f"node/{nid}", "amenity": tags.get("amenity"), "name": tags.get("name"), "geometry": pt})
        if tags.get("leisure") in ("park", "playground", "recreation_ground", "garden"):
            park_pts.append({"osm_id": f"node/{nid}", "leisure": tags.get("leisure"), "name": tags.get("name"), "geometry": pt})

    layers = {
        "osm_roads_raw": roads,
        "osm_buildings_raw": buildings,
        "osm_parks_green_poly_raw": parks_green,
        "osm_parks_pts_raw": park_pts,
        "osm_waterways_raw": waterways,
        "osm_waterbodies_raw": waterbodies,
        "osm_railways_raw": railways,
        "osm_facilities_poly_raw": facilities_poly,
        "osm_facilities_pts_raw": facility_pts,
        "osm_places_pts_raw": places,
    }

    summary = {}
    gpkg_wgs84 = os.path.join(OUT_DIR, "Narowal_OSM_Extracted_WGS84.gpkg")
    gpkg_utm = os.path.join(OUT_DIR, "Narowal_OSM_Extracted_UTM43N.gpkg")
    for name, rows in layers.items():
        summary[name] = len(rows)
        if rows:
            gdf = gpd.GeoDataFrame(rows, crs="EPSG:4326")
            gdf.to_file(gpkg_wgs84, layer=name, driver="GPKG")
            gdf_utm = gdf.to_crs("EPSG:32643")
            gdf_utm.to_file(gpkg_utm, layer=name, driver="GPKG")

    with open(os.path.join(OUT_DIR, "osm_extraction_summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print("OSM extraction summary:", json.dumps(summary, indent=2))

    if parks_green:
        print("\n=== Mapped Green/Leisure Polygons in Narowal BBox ===")
        for p in parks_green:
            print(" ", p["osm_id"], "| leisure=", p["leisure"], "| landuse=", p["landuse"], "| name=", p["name"], "| access=", p["access"])
    if places:
        print("\n=== Mapped Places ===")
        for pl in places:
            print(" ", pl["place"], "|", pl["name"], "|", pl["geometry"].wkt)


if __name__ == "__main__":
    main()
