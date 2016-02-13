import sys
import glob
import csv
from collections import defaultdict

import shapefile
import tqdm
import pyproj
from PIL import Image, ImageDraw, ImageFont

##########################################

unit = sys.argv[1] # "tract" or "county"
width = int(sys.argv[2])

##########################################

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
for fn in glob.glob("shapefiles_%s/*.shp" % unit):
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

# Store which geographic units occur in which pixels.
pixels = defaultdict(lambda : [])

# Combined map.
img_all = Image.new("L", (width, height), 0)
draw_all = ImageDraw.Draw(img_all)

# iterate through all of the shapes
for sf, shape, fields in \
	tqdm.tqdm(iter_all_shapes(), total=total_shapes, file=sys.stderr, leave=True):
	assert shape.shapeType == 5

	# Because we're making a statement about how the units appears on a map,
	# project the lat/lng coordinates into a standard US map projection.
	# Skip the states that aren't in the contiguous U.S., since far-away
	# places will come out distorted in a projection meant for the contiguous
	# U.S.
	if fields["STATEFP"] not in contiguous_us:
		continue

	geo_id = fields["GEOID"]
	# fields["ALAND"] is land (excluding water) area as computed by the Census,
	# which is also interesting.

	# Project points to map coordinates.
	polygon = shape.points
	polygon = [project(lng, lat) for (lng, lat) in polygon]

	# Scale to image coordinates.
	polygon = [(lng*width, height - lat*height) for (lng, lat) in polygon]

	# Create an empty greyscale image of a certain pixel size to rasterize the tract.
	img = Image.new("L", (width, height), 0)
	draw = ImageDraw.Draw(img)

	# Draw the shape.
	draw.polygon(polygon, fill=255)
	draw_all.polygon(polygon, fill=255)

	# We could count up the number of pixels that are now turned on
	# by calling img.histogram(), which is really fast. But because
	# at regular map resolutions some tracts will tend to fall on the same
	# pixels, we'll record which geographic units end up on which pixels.
	# img.getdata() returns a flat array of the pixels in raster order,
	# by row. By enumerating, each pixel gets a consistent integer identifier.
	is_drawn = False
	for pixel, value in enumerate(img.getdata()):
		if value > 0: # really just 255 so long as there is no antialiasing
			if value != 255: raise Exception("encountered a pixel value that's not 0 or 255")
			pixels[pixel].append(geo_id)
			is_drawn = True

	if not is_drawn:
		# Shape was too small to be represented in the raster image at all.
		# That means it's smaller than one pixel. All of the points on the
		# polygon will probably round to the same coordinate. But to be
		# sure, take the average of the coordinates and mark the shape
		# as being drawn at that one lump location.
		x = int(round(sum(latlng[0] for latlng in polygon)/len(polygon)))
		y = int(round(sum(latlng[1] for latlng in polygon)/len(polygon)))
		pixel = y*width + x
		pixels[pixel].append(geo_id)

	# Release object.
	del draw

# Save the image that has all of the shapes drawn, to verify that we're
# drawing the right thing.
del draw_all
img_all.save("map_%s_%d.png" % (unit, width), format="png")

# Write out each pixel that got lit up at all and the geographic unit IDs that did so.
import csv
w = csv.writer(sys.stdout)
for pixel_id, geoid_list in sorted(pixels.items()):
	x = (pixel_id % width)
	y = pixel_id // width
	w.writerow([x, y] + geoid_list)

