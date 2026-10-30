# FOX process v1.0
# visualisation of bounding boxes for aircraft positions
# using different bounding box calculation methods (Haversine vs WGS84)
# and distance or time based separations

from time import perf_counter

from module.geo import distance_haversine,  get_bounding_box_haversine
from module.geo_wgs84 import get_bounding_box


def test() -> None:
    """
    fixes = [(39,-20),(41,-20),(40,-15),(39,-15),(39,-20.0)]
    print(is_fix_inside(43,-18,fixes))
    print(is_fix_inside(39.5,-18,fixes))
    print(is_fix_inside(39.5,-18,fixes))
    """

    result = ""
    iterations = 250000

    p1 = [39.0, -20.0, 10000.0, 0, 460.0]

    st = perf_counter()
    for i in range(0, iterations):
        if i % 1000 == 0:
            print("\r{}".format(i), end="")
        result = get_bounding_box(p=p1)
    print("\n\n {}".format(perf_counter() - st), "\n\n")
    print(result, "\n\n")

    st = perf_counter()
    for i in range(0, iterations):
        if i % 1000 == 0:
            print("\r{}".format(i), end="")
        result = get_bounding_box_haversine(p=p1)
    print("\n {}".format(perf_counter() - st), "\n\n")
    print(result, "\n\n")

def plot_airplane(ax, p, color):
        # Heading is degrees from north; matplotlib rotation is CCW from east.
        rotation = 90 - p[3]
        ax.text(
            p[1],
            p[0],
            "✈",
            fontsize=24,
            color=color,
            ha="center",
            va="center",
            rotation=rotation,
            rotation_mode="anchor",
            transform=ccrs.PlateCarree(),
        )

def plot_box(ax, pts, label, color, linestyle="-"):
    lats = [pt[0] for pt in pts] + [pts[0][0]]
    lons = [pt[1] for pt in pts] + [pts[0][1]]
    ax.plot(lons, lats, color=color, linestyle=linestyle, label=label, transform=ccrs.PlateCarree())

def box_distance_differences(box_a, box_b):
    distances_nm = []
    for point_a, point_b in zip(box_a, box_b):
        distance_m = distance_haversine(point_a[0], point_a[1], point_b[0], point_b[1])
        distances_nm.append(distance_m / 1852)
    return distances_nm


if __name__ == "__main__":
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature
    import matplotlib.pyplot as plt

    # FOX process v1.0

    # Define the first aircraft's position and bounding boxes
    # [lat,lon,alt,heading,speed (kts)]
    p1 = [39.0, -20.0, 10000.0, 90, 448.0]
    result1 = get_bounding_box_haversine(p=p1, lateral=60, time_ahead=15, time_behind=15)
    result_120 = get_bounding_box_haversine(p=p1, lateral=60, dist=120, time_ahead = None, time_behind=None)

    # Define the second aircraft's position and bounding boxes
    # [lat,lon,alt,heading,speed (kts)]
    p2 = [40.0, -20.0, 10000.0, 225, 472.0]
    result2 = get_bounding_box_haversine(p = p2, lateral=60, time_ahead=15, time_behind=15)
    result3 = get_bounding_box(p = p2, lateral=60, time = 15, behind=15)
    result4 = get_bounding_box_haversine(p = p2, lateral=60, dist = 120)

    
    # define the center of the map based on the average latitude and longitude of the two aircraft
    centre_lat = (p1[0] + p2[0]) / 2
    centre_lon = (p1[1] + p2[1]) / 2

    projection = ccrs.LambertConformal(
        central_longitude=centre_lon,
        central_latitude=centre_lat,
        standard_parallels=(17, 51),
    )

    fig, ax = plt.subplots(subplot_kw={"projection": projection})
    ax.add_feature(cfeature.COASTLINE)
    ax.add_feature(cfeature.BORDERS, linestyle=":")
    ax.gridlines(draw_labels=True)

    plot_box(ax, result1, "AC1 - 15 minutes longitudinal", "blue")
    plot_box(ax, result_120, "AC1 - 120NM longitudinal", "green", linestyle="dashed")
    plot_box(ax, result2, "AC2 - Haversine", "red")
    plot_box(ax, result3, "AC2 - WGS84", "black", linestyle="dotted")    
    plot_box(ax, result4, "AC2 - 120NM longitudinal - Haversine", "pink", linestyle="dotted")

    box_differences_nm = box_distance_differences(result2, result3)
    summary = (
        f"differences between Haversine and WGS84 (NM)\n"
        f"LB: {box_differences_nm[0]:.3f}\n"
        f"LT: {box_differences_nm[1]:.3f}\n"
        f"RT: {box_differences_nm[2]:.3f}\n"
        f"RB: {box_differences_nm[3]:.3f}\n"
        f"Max: {max(box_differences_nm):.3f}"
    )
    print(summary)

    plot_airplane(ax, p1, "blue")
    plot_airplane(ax, p2, "red")
    ax.legend()
    ax.set_title("Bounding Box Comparison (LCC 17N/51N)")
    fig.text(
        0.02,
        0.02,
        summary,
        fontsize=9,
        bbox={"facecolor": "white", "alpha": 0.85, "edgecolor": "black"},
    )
    plt.tight_layout()
    plt.show()
    # test()
