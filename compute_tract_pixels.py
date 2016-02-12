import sys
import glob
import csv
from collections import defaultdict

import shapefile
import tqdm
import pyproj
from PIL import Image, ImageDraw, ImageFont

contiguous_us = ("01", "04", "05", "06", "08", "09", "10", "11", "12", "13", "16",
	             "17", "18", "19", "20", "21", "22", "23", "24", "25", "26", "27",
	             "28", "29", "30", "31", "32", "33", "34", "35", "36", "37", "38",
	             "39", "40", "41", "42", "44", "45", "46", "47", "48", "49", "50",
	             "51", "53", "54", "55", "56", )

# Define map projections (lat/lng and a nice one for contiguous US)
p_latlng = pyproj.Proj(init='EPSG:4326')
p_mapproj = pyproj.Proj("+proj=aea +lat_1=29.5 +lat_2=45.5 +lat_0=23 +lon_0=-96 +x_0=0 +y_0=0 +ellps=clrk66 +units=m +no_defs") # http://spatialreference.org/ref/sr-org/7271/

# This is the bounding box of the projected map coordinates.
projected_bounds = [(-2387000, 254700), (2263000, 3169000)]

# Raster dimensions.
width = int(sys.argv[1])
height = int(round(width * (projected_bounds[1][1] - projected_bounds[0][1]) / (projected_bounds[1][0] - projected_bounds[0][0])))

# Helper function to project into map coordinates in [0,1].
def project(lng, lat):
	# Project.
	lng, lat = pyproj.transform(p_latlng, p_mapproj, lng, lat)

	# Scale to [0, 1].
	lng = (lng-projected_bounds[0][0]) / (projected_bounds[1][0] - projected_bounds[0][0])
	lat = (lat-projected_bounds[0][1]) / (projected_bounds[1][1] - projected_bounds[0][1])

	return (lng, lat)

# load shapefiles first so we can get a count of all shapes
total_shapes = 0
shapefiles = []
for fn in glob.glob("shapefiles/*.shp"):
	sf = shapefile.Reader(fn)
	shapefiles.append(sf)
	total_shapes += sf.numRecords

# iterator over all files
def iter_all_shapes():
	for sf in shapefiles:
		fields = [f[0] for f in sf.fields[1:]]
		for i, shape in enumerate(sf.iterShapes()):
			  # note: DeletionFlag is first in sf.fields but is not in sf.record(i)
			yield (sf, shape, dict(zip(fields, sf.record(i))))

# Store which tracts occur in which pixels.
pixels = defaultdict(lambda : [])
tract_aland = { }

# Combined map.
img_all = Image.new("L", (width, height), 0)
draw_all = ImageDraw.Draw(img_all)

# iterate through all of the shapes
for sf, shape, fields in \
	tqdm.tqdm(iter_all_shapes(), total=total_shapes, file=sys.stderr, leave=True):
	assert shape.shapeType == 5

	# Because we're making a statement about how the tract appears on a map,
	# project the lat/lng coordinates into a standard US map projection.
	# Skip the states that aren't in the contiguous U.S., since far-away
	# places will come out distorted in a projection meant for the continental
	# U.S.
	if fields["STATEFP"] not in contiguous_us:
		continue

	tract_id = fields["GEOID"]
	tract_aland[tract_id] = fields["ALAND"] # land area as computed by the Census

	# Project points to map coordinates.
	polygon = shape.points
	polygon = [project(lng, lat) for (lng, lat) in polygon]

	# Scale to image coordinates.
	polygon = [(lng*width, height - lat*height) for (lng, lat) in polygon]

	# Create an empty greyscale image of a certain pixel size to rasterize the tract.
	img = Image.new("L", (width, height), 0)
	draw = ImageDraw.Draw(img)

	# Draw the tract.
	draw.polygon(polygon, fill=255)
	draw_all.polygon(polygon, fill=255)

	# We could count up the number of pixels that are now turned on
	# by calling img.histogram(), which is really fast. But because
	# at regular map resolutions tracts will tend to fall on the same
	# pixels, we'll first record which tracts end up on which pixels.
	# img.getdata() returns a flat array of the pixels in raster order,
	# by row (or whatever). By enumerating, each pixel gets a consistent
	# integer identifier.
	for pixel, value in enumerate(img.getdata()):
		if value > 0: # really just 255 so long as there is no antialiasing
			pixels[pixel].append(tract_id)

	# Release object.
	del draw

del draw_all
img_all.save("map_%d.png" % width, format="png")

# Write out each pixel that got lit up at all and the tract IDs that did so.
import csv
w = csv.writer(sys.stdout)
for pixel_id, tract_list in pixels.items():
	x = (pixel_id % width)
	y = pixel_id // width
	w.writerow([x, y] + tract_list)

