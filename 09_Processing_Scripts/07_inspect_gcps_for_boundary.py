"""Step 1 of Urban Unit MC Boundary extraction: inspect OSM GCP coordinates & render pixel-grid map image."""

import os
import geopandas as gpd
import matplotlib.pyplot as plt
from PIL import Image

ROOT = r"C:\Users\LENOVO\.gemini\antigravity\scratch\Narowal_Urban_Green_Infrastructure"
GPKG = os.path.join(ROOT, "03_Processed_Data", "01_Base_Mapping", "Narowal_OSM_Extracted_WGS84.gpkg")
MAPS_DIR = os.path.join(ROOT, "02_Raw_Data", "08_Government_Reports", "extracted_maps")
OUT_TMP = os.path.join(ROOT, "03_Processed_Data", "01_Base_Mapping")


def main():
    fac = gpd.read_file(GPKG, layer="osm_facilities_poly_raw")
    print("=== Facility Polygon Centroids (WGS84) ===")
    for _, r in fac.iterrows():
        if r["name"]:
            c = r.geometry.centroid
            print(f"  {r['name']}: ({c.x:.6f}, {c.y:.6f})")

    parks = gpd.read_file(GPKG, layer="osm_parks_green_poly_raw")
    print("=== Park Centroids (WGS84) ===")
    for _, r in parks.iterrows():
        if r["name"]:
            c = r.geometry.centroid
            print(f"  {r['name']}: ({c.x:.6f}, {c.y:.6f})")

    places = gpd.read_file(GPKG, layer="osm_places_pts_raw")
    print("=== City / Key Village Points (WGS84) ===")
    for _, r in places.iterrows():
        if r["place"] == "city" or (r["name"] in ("چندووال", "رنسیوال", "سراں", "کوٹلی باجوہ", "مانک", "جمن چندووال")):
            print(f"  {r['place']} {r['name']}: ({r.geometry.x:.6f}, {r.geometry.y:.6f})")

    # Find major road intersections in primary/secondary/tertiary roads
    roads = gpd.read_file(GPKG, layer="osm_roads_raw")
    major = roads[roads["highway"].isin(["primary", "secondary", "tertiary"])]
    print(f"=== Major road segments: {len(major)} ===")
    for _, r in major.iterrows():
        if r["name"]:
            c = r.geometry.centroid
            print(f"  {r['highway']} | {r['name']} | mid=({c.x:.6f}, {c.y:.6f}) | start={r.geometry.coords[0]} end={r.geometry.coords[-1]}")

    # Render pixel coordinate grids on page_70_img_1.jpg and page_53_img_5.jpg for accurate GCP reading
    for img_name in ["page_70_img_1.jpg", "page_53_img_5.jpg"]:
        p = os.path.join(MAPS_DIR, img_name)
        im = Image.open(p)
        w, h = im.size
        print(f"{img_name}: {w}x{h}")
        fig, ax = plt.subplots(figsize=(14, 10), dpi=150)
        ax.imshow(im)
        ax.set_xticks(range(0, w, 100))
        ax.set_yticks(range(0, h, 100))
        ax.grid(color="cyan", linestyle="-", linewidth=0.5, alpha=0.6)
        ax.tick_params(axis="both", labelsize=7)
        plt.tight_layout()
        out_png = os.path.join(OUT_TMP, f"gcp_grid_{img_name}.png")
        plt.savefig(out_png, dpi=150)
        plt.close(fig)
        print("Saved grid image:", out_png)


if __name__ == "__main__":
    main()
