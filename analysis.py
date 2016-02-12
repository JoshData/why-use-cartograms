# Analze the pixel and population data.

import csv, colorsys
from PIL import Image, ImageDraw, ImageFont

raster_width = 800
font_ttf_file = '/usr/share/fonts/truetype/gentium/GenR102.ttf'

# Load demographic data. Turn numeric columns into floats (rather than strings).
demographics = csv.DictReader(open("tract_population.csv"))
demographics = {
	(tract["state"] + tract["county"] + tract["tract"]): {
		k: float(v) if v != "" else None
		for (k, v) in tract.items()
		if k not in ("state", "county", "tract")
	}
	for tract in demographics
}

# Load 2012 presidential election data.
prezelection = csv.DictReader(open("prez2012county.csv"))
prezelection = {
	row["FIPS"]: row
	for row in prezelection
}

# Compute how many pixels each tract is assigned to. When multiple tracts
# share a pixel, apportion the pixel evenly to those tracts.
tract_pixels = { }
for x, y, *tracts in csv.reader(open("tract_pixels_%d.csv" % raster_width)):
	# Drop tracts with no residents & pixels with no residents.
	tracts = [t for t in tracts if demographics[t]["population"] > 0]
	if len(tracts) == 0: continue

	# Apportion a part of this pixel to the tracts that are drawn on it.
	for tract in tracts:
		tract_pixels[tract] = tract_pixels.get(tract, 0) + 1/len(tracts)

print(len(tract_pixels), "tracts")
print(int(round(sum(tract_pixels.values()))), "pixels")

########################################################################

# DISTORTION

def compute_distortion(title, f_numerator, f_denominator):
	# Compare a population demographic to how that demographic appears
	# when proportined to pixels in the map.

	numerator_population = 0
	denominator_population = 0
	numerator_pixels = 0
	denominator_pixels = 0

	for tract, pixels in tract_pixels.items():
		# Compute the numerator and denominator for a demographic statistic.
		n = f_numerator(tract)
		d = f_denominator(tract)

		# For things other than whole population, the denominator might
		# be zero in some places. There are no relevant people for this
		# statistic in this tract.
		if d == 0: continue

		# Make a grand total.
		numerator_population += n
		denominator_population += d

		# Apportion the pixels this tract is drawn on according to the
		# demographics in this tract.
		numerator_pixels += (n/d) * pixels
		denominator_pixels += pixels

	print("population %", round(numerator_population/denominator_population*1000)/10)
	print("pixels %", round(numerator_pixels/denominator_pixels*1000)/10)
	print("(total population", int(round(denominator_population)), "; total pixels", int(round(denominator_pixels)), ")")

########################################################################

def draw_map(title, pct_pop_to_draw, func, png_file):
	# Highly where X% of the population lives on a map.

	# Assign a rank order to the tracts to put the population
	# compactly into few tracts, along some dimension.
	tract_rank = { }
	total = sum(func(tract) for tract in tract_pixels.keys())
	tracts = sorted(tract_pixels.keys(), key=lambda tract : -func(tract) / tract_pixels[tract])
	running_total = 0
	for tract in tracts:
		running_total += func(tract)
		tract_rank[tract] = (func(tract), running_total/total)

	# Plot.
	height = int(raster_width * 500/800)
	img = Image.new("RGBA", (raster_width, height), (0, 0, 0, 0))
	total_units = set()
	total_pixels = 0
	total_hot_units = set()
	total_hot_pixels = 0
	for x, y, *tracts in csv.reader(open("tract_pixels_%d.csv" % raster_width)):
		# Drop tracts with no residents & pixels with no residents.
		tracts = [t for t in tracts if demographics[t]["population"] > 0]
		if len(tracts) == 0: continue

		# How many pixels are in the map?
		total_pixels += 1

		# Get the proportion of tracts at this pixel that
		# are above the threshold to plot.
		v = 0.0
		for tract in tracts:
			total_units.add(tract)
			if tract_rank[tract][1] <= pct_pop_to_draw:
				# 90% of population
				total_hot_units.add(tract)
				total_hot_pixels += 1/len(tracts)
				v += 1/len(tracts)

		# Rescale the proportion of this pixel that is lit up [0, 1]
		# to a saturation value.
		saturation = .1 + .8*v
		lightness = 0.9 - .3*v # actually HSV's "value"

		# Draw.
		r, g, b = colorsys.hsv_to_rgb(0.15, saturation, lightness)
		value = (int(255*r), int(255*g), int(220*b), 255)
		img.putpixel((int(x),int(y)), value)

	# Finish computations.
	total_units = sum(tract_rank[tract][0] for tract in total_units)
	total_hot_units = sum(tract_rank[tract][0] for tract in total_hot_units)

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
	lambda tract : demographics[tract]["population"],
	None,
	.95,
	"all.png")

go(
	"non-whites",
	lambda tract : demographics[tract]["population"] - demographics[tract]["white"],
	lambda tract : demographics[tract]["population"],
	.95,
	"non_whites.png")

go(
	"use public transit",
	lambda tract : demographics[tract]["public_transit"],
	lambda tract : demographics[tract]["all_workers"],
	.95,
	"public_transit.png")

median_income = 53150 # yields 50%
go(
	"household income < $%d" % int(round(median_income)),
	lambda tract : demographics[tract]["population"] if demographics[tract]["median_income"] is not None and demographics[tract]["median_income"] <= median_income else 0,
	lambda tract : demographics[tract]["population"],
	.95,
	"income.png")

go(
	"in poverty",
	lambda tract : demographics[tract]["in_poverty"],
	lambda tract : demographics[tract]["poverty_status_denominator"],
	.95,
	"poverty.png")

go(
	"multi-unit housing structures",
	lambda tract : demographics[tract]["housing_units"] - demographics[tract]["housing_units_single_detached"],
	lambda tract : demographics[tract]["housing_units"],
	.95,
	"multi_unit_homes.png")

# we have county-level totals, but since we're plotting tracts it's
# easier to apportion the county percentages to the tracts
go(
	"voted for Obama in 2012",
	lambda tract : float(prezelection[tract[0:5]]["PCT_OBM"])/100 * demographics[tract]["population"],
	lambda tract : demographics[tract]["population"],
	.95,
	"obama.png")
go(
	"voted for Romney in 2012",
	lambda tract : float(prezelection[tract[0:5]]["PCT_ROM"])/100 * demographics[tract]["population"],
	lambda tract : demographics[tract]["population"],
	.95,
	"romney.png")
