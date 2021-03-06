# Analze the pixel and population data.

import sys, csv, colorsys
from PIL import Image, ImageDraw, ImageFont

# Settings.
unit = sys.argv[1]
raster_width = 800
font_ttf_file = '/usr/share/fonts/truetype/gentium/GenR102.ttf'

# Load demographic data. Turn numeric columns into floats (rather than strings).
# Map each row from a GEOID that concatenates the state, county, and tract FIPS IDs.
demographics = csv.DictReader(open("%s_population.csv" % unit))
demographics = {
	(item["state"] + item["county"] + (item["tract"] if unit=="tract" else "")):
		{
			k: float(v) if v != "" else None
			for (k, v) in item.items()
			if k not in ("state", "county", "tract")
		}
	for item in demographics
}

# Load 2012 presidential election data.
prezelection = csv.DictReader(open("prez2012county.csv"))
prezelection = {
	row["FIPS"]: row
	for row in prezelection
}

# Compute how many pixels each geographic unit is assigned to. When multiple units
# share a pixel, apportion the pixel evenly to those units.
unit_pixel_count = { }
for x, y, *units in csv.reader(open("%s_pixels_%d.csv" % (unit, raster_width))):
	# Drop geographic units with no residents & pixels with no residents.
	units = [t for t in units if demographics[t]["population"] > 0]
	if len(units) == 0: continue

	# Apportion a part of this pixel to the units that are drawn on it.
	for item in units:
		unit_pixel_count[item] = unit_pixel_count.get(item, 0) + 1/len(units)

print(len(unit_pixel_count), unit, "count")
print(int(round(sum(unit_pixel_count.values()))), "pixels")

########################################################################

# DISTORTION

def compute_distortion(title, f_numerator, f_denominator):
	# Compare a population demographic to how that demographic appears
	# when proportined to pixels in the map.

	numerator_population = 0
	denominator_population = 0
	numerator_pixels = 0
	denominator_pixels = 0

	for item, pixels in unit_pixel_count.items():
		# Compute the numerator and denominator for a demographic statistic.
		n = f_numerator(item)
		d = f_denominator(item)

		# For things other than whole population, the denominator might
		# be zero in some places. There are no relevant people for this
		# statistic in this item.
		if d == 0: continue

		# Make a grand total.
		numerator_population += n
		denominator_population += d

		# Apportion the pixels this item is drawn on according to the
		# demographics in this item.
		numerator_pixels += (n/d) * pixels
		denominator_pixels += pixels

	print("population %", round(numerator_population/denominator_population*1000)/10)
	print("pixels %", round(numerator_pixels/denominator_pixels*1000)/10)
	print("(total population", int(round(denominator_population)), "; total pixels", int(round(denominator_pixels)), ")")

########################################################################

def draw_map(title, pct_pop_to_draw, func, png_file):
	# Highly where X% of the population lives on a map.

	# Assign a rank order to the geographic units to put the population
	# compactly into a tight space, along some dimension.
	unit_rank = { }
	total = sum(func(item) for item in unit_pixel_count.keys())
	sorted_units = sorted(unit_pixel_count.keys(), key=lambda item : -func(item) / unit_pixel_count[item])
	running_total = 0
	for item in sorted_units:
		running_total += func(item)
		unit_rank[item] = (func(item), running_total/total)

	# Plot.
	height = int(raster_width * 500/800)
	img = Image.new("RGBA", (raster_width, height), (0, 0, 0, 0))
	total_units = set()
	total_pixels = 0
	total_hot_units = set()
	total_hot_pixels = 0
	for x, y, *units in csv.reader(open("%s_pixels_%d.csv" % (unit, raster_width))):
		# Drop geographic units with no residents & pixels with no residents.
		units = [t for t in units if demographics[t]["population"] > 0]
		if len(units) == 0: continue

		# How many pixels are in the map?
		total_pixels += 1

		# Get the proportion of geographic units at this pixel that
		# are above the threshold to plot.
		v = 0.0
		for item in units:
			total_units.add(item)
			if unit_rank[item][1] <= pct_pop_to_draw:
				# 90% of population
				total_hot_units.add(item)
				total_hot_pixels += 1/len(units)
				v += 1/len(units)

		# Rescale the proportion of this pixel that is lit up [0, 1]
		# to a saturation value.
		saturation = .1 + .8*v
		lightness = 0.9 - .3*v # actually HSV's "value"

		# Draw.
		r, g, b = colorsys.hsv_to_rgb(0.15, saturation, lightness)
		value = (int(255*r), int(255*g), int(220*b), 255)
		img.putpixel((int(x),int(y)), value)

	# Finish computations.
	total_units = sum(unit_rank[item][0] for item in total_units)
	total_hot_units = sum(unit_rank[item][0] for item in total_hot_units)

	# Legend.
	fnt = ImageFont.truetype(font_ttf_file, int(height/22))
	draw = ImageDraw.Draw(img)
	y = [.8*height]
	line_height = 1.33 * draw.textsize("Hg", font=fnt)[1]
	def write_line(text, y):
		draw.text((raster_width/50,y[0]), text, font=fnt, fill=(30,30,30,255))
		y[0] += line_height
	write_line(title + ":", y)
	write_line("%d%% of the population" % int(round(total_hot_units/total_units*1000)/10), y)
	write_line("lives in %s%% of the map" % int(round(total_hot_pixels/total_pixels*1000)/10), y)

	# Save.
	img.save(png_file, format="png")

	print("total population units", int(round(total_units)))
	print("total displayed population units", int(round(total_hot_units)), int(round(total_hot_units/total_units*1000)/10))
	print("total pixels", int(round(total_pixels)))
	print("total displayed population pixels", int(round(total_hot_pixels)), int(round(total_hot_pixels/total_pixels*1000)/10))

########################################################################

def go(title, numerator, denominator, pct_pop_to_draw, map_png_file):
	print()
	print(title)
	if denominator: compute_distortion(title, numerator, denominator)
	draw_map(title, pct_pop_to_draw, numerator, map_png_file)

########################################################################

go(
	"all people",
	lambda item : demographics[item]["population"],
	None,
	.5,
	"all_50.png")

go(
	"all people",
	lambda item : demographics[item]["population"],
	None,
	.95,
	"all_95.png")

go(
	"all people",
	lambda item : demographics[item]["population"],
	None,
	.99,
	"all_99.png")

go(
	"non-whites",
	lambda item : demographics[item]["population"] - demographics[item]["white"],
	lambda item : demographics[item]["population"],
	.95,
	"non_whites.png")

go(
	"use public transit",
	lambda item : demographics[item]["public_transit"],
	lambda item : demographics[item]["all_workers"],
	.95,
	"public_transit.png")

median_income = 53150 if unit == "tract" else 53350 # yields 50%
go(
	"household income < $%d" % int(round(median_income)),
	lambda item : demographics[item]["population"] if demographics[item]["median_income"] is not None and demographics[item]["median_income"] <= median_income else 0,
	lambda item : demographics[item]["population"],
	.95,
	"income.png")

go(
	"in poverty",
	lambda item : demographics[item]["in_poverty"],
	lambda item : demographics[item]["poverty_status_denominator"],
	.95,
	"poverty.png")

go(
	"multi-unit housing structures",
	lambda item : demographics[item]["housing_units"] - demographics[item]["housing_units_single_detached"],
	lambda item : demographics[item]["housing_units"],
	.95,
	"multi_unit_homes.png")

# we have county-level totals, but when we're plotting tracts it's
# easier to apportion the county percentages to the tracts
go(
	"voted for Obama in 2012",
	lambda item : float(prezelection[item[0:5]]["PCT_OBM"])/100 * demographics[item]["population"],
	lambda item : demographics[item]["population"],
	.95,
	"obama.png")
go(
	"voted for Romney in 2012",
	lambda item : float(prezelection[item[0:5]]["PCT_ROM"])/100 * demographics[item]["population"],
	lambda item : demographics[item]["population"],
	.95,
	"romney.png")
