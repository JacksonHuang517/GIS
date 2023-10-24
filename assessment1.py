import geopandas as gpd
import matplotlib.pyplot as plt
import time
from mpl_toolkits.axes_grid1.anchored_artists import AnchoredSizeBar
from mpl_toolkits.axes_grid1.inset_locator import inset_axes


# Start the timer
start_time = time.time()

# Load the shapefile
world = gpd.read_file('./data/ne_10m_admin_0_countries.shp')

# Initialize variables to store shortest border information
shortest_length = float('inf')
shortest_border = None
country_a_name = ''
country_b_name = ''

# Set an appropriate CRS for calculating lengths accurately
world_mercator = world.to_crs('EPSG:3395')

# Using spatial index for optimization
sindex = world_mercator.sindex

# Set a minimum threshold for the border length (e.g., 1000 meters)
MIN_BORDER_LENGTH = 500

for i, country_a in world_mercator.iterrows():
    possible_matches_index = list(sindex.intersection(country_a['geometry'].bounds))
    possible_matches = world_mercator.iloc[possible_matches_index]
    precise_matches = possible_matches[possible_matches.intersects(country_a['geometry'])]

    for j, country_b in precise_matches.iterrows():
        if i != j:
            border = country_a.geometry.intersection(country_b.geometry)
            border_length = border.length
            if 0 < border_length < shortest_length and border_length > MIN_BORDER_LENGTH:
                shortest_length = border_length
                shortest_border = border
                country_a_name = country_a.NAME
                country_b_name = country_b.NAME

# Convert the shortest border back to EPSG:4326 for plotting
shortest_border_geo = gpd.GeoSeries([shortest_border], crs='EPSG:3395')
shortest_border_geo = shortest_border_geo.to_crs('EPSG:4326')
shortest_border = shortest_border_geo.geometry.iloc[0]

# Draw a map
fig, ax = plt.subplots(figsize=(10, 10))

# Get geometries of the two countries involved in the shortest border
country_a_geom = world[world['NAME'] == country_a_name].geometry.iloc[0]
country_b_geom = world[world['NAME'] == country_b_name].geometry.iloc[0]

# Adjust the map's extent to focus on the buffered area around the shortest border
buffer_distance = 0.5
buffered_border = shortest_border.buffer(buffer_distance)
ax.set_xlim(buffered_border.bounds[0], buffered_border.bounds[2])
ax.set_ylim(buffered_border.bounds[1], buffered_border.bounds[3])

# Plot all world boundaries in light gray
world.boundary.plot(ax=ax, linewidth=0.5, color='gray')

# Plot the boundaries of the two countries in light blue
gpd.GeoSeries([country_a_geom, country_b_geom]).boundary.plot(ax=ax, color='lightblue', linewidth=2)

# Plot only the intersecting boundary in red with a thicker linewidth
gpd.GeoSeries([shortest_border]).plot(ax=ax, color='red', linewidth=3)

# Inset plot (detailed map)
axins = inset_axes(ax, width="30%", height="30%", loc='upper right')
world.boundary.plot(ax=axins, linewidth=0.5, color='gray')
gpd.GeoSeries([country_a_geom, country_b_geom]).boundary.plot(ax=axins, color='lightblue', linewidth=2)
gpd.GeoSeries([shortest_border]).plot(ax=axins, color='red', linewidth=3)



# Adjust the inset map's extent to focus on the shortest border
inset_buffer = 0.001  # You can adjust this for the desired zoom level on the inset map
axins.set_xlim(shortest_border.bounds[0] - inset_buffer, shortest_border.bounds[2] + inset_buffer)
axins.set_ylim(shortest_border.bounds[1] - inset_buffer, shortest_border.bounds[3] + inset_buffer)

# Remove x and y axis tick labels for the inset plot
axins.set_xticks([])
axins.set_yticks([])
# Setting the title on top of the map frame
ax.set_title(f"Shortest border: {country_a_name} - {country_b_name}", fontsize=16, va='top', ha='center')

# Legend
lines = [plt.Line2D([0], [0], color='lightblue', linewidth=2, label='Country Borders'),
         plt.Line2D([0], [0], color='red', linewidth=3, label='Shortest Border')]

legend = ax.legend(handles=lines, loc='lower left')

# North Arrow
arrow_x = 0.05  # adjust these values based on your specific plot
arrow_y = 0.95
arrow_length = 0.06

ax.annotate('N', xy=(arrow_x, arrow_y), xytext=(arrow_x, arrow_y - arrow_length),
            arrowprops=dict(facecolor='black', arrowstyle='->'),
            ha='center', va='center', xycoords=ax.transAxes, fontsize=12, fontweight='bold')

# Scale Bar
scalebar = AnchoredSizeBar(ax.transData,
                           0.1, '0.1 Decimal Degrees', 'lower right',
                           pad=3,
                           color='black',
                           frameon=False,
                           size_vertical=0.005)

ax.add_artist(scalebar)
# plt.title(f"Shortest border: {country_a_name} - {country_b_name}")
plt.savefig("./out/shortest_border.png", dpi=300)
plt.show()

# End timer
end_time = time.time()
print(f"Shortest border is between {country_a_name} and {country_b_name} with a length of {shortest_length:.2f} meters.")
print(f"Time taken: {end_time - start_time:.2f} seconds.")