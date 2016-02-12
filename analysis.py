# Analze the pixel and population data.

import csv
from numpy import median
from PIL import Image, ImageDraw, ImageFont

# Load demographic data.
demographics = csv.DictReader(open("tract_population.csv"))
demographics = {
	(tract["state"] + tract["county"] + tract["tract"]): tract
	for tract in demographics
}

# Load 2012 presidential election data.
prezelection = csv.DictReader(open("prez2012county.csv"))
prezelection = {
	row["FIPS"]: row
	for row in prezelection
}

# Get median income across tracts.
median_income = median(list(float(tract["median_income"]) for tract in demographics.values() if tract["median_income"] != ""))

# Plot.
width = 800
height = 500
img = Image.new("L", (width, height), 0)

total_pixels = 0
total_tracts = 0

total_population = 0
total_white_population = 0
total_white_pixels = 0

total_median_income_pixels = 0
total_below_median_income_pixels = 0

total_working_population = 0
total_public_transit_population = 0
total_public_transit_pixels = 0

total_female_population = 0
total_female_married_population = 0
total_female_married_pixels = 0

total_housing_units = 0
total_housing_units_singledetached = 0
total_housing_units_singledetached_pixels = 0

total_voted = 0
total_voted_obama = 0
total_voted_obama_pixels = 0

# Get some population totals across tracts.
for tract in demographics.values():
	total_population += int(tract["population"])
	total_white_population += int(tract["white"])
	total_working_population += int(tract["all_transit"])
	total_public_transit_population += int(tract["public_transit"])
	total_female_population += int(tract["all_female_marital"])
	total_female_married_population += int(tract["female_married"])
	total_housing_units += int(tract["housing_units"])
	total_housing_units_singledetached += int(tract["housing_units_single_detached"])
	total_tracts += 1

# Get presidential totals across counties.
for county in prezelection.values():
	total_voted += float(county["TTL_VT"])
	total_voted_obama += float(county["OBAMA"])

tract_pixel_counts = { tract: 0 for tract in demographics }

# Analyze distribution in pixels.
for x, y, *tracts in csv.reader(open("tract_pixels_800.csv")):
	total_pixels += 1

	val = 0
	for tract in tracts:
		tract_pixel_counts[tract] += 1/len(tracts)

		# Race.
		if int(demographics[tract]["population"]) > 0:
			total_white_pixels += (1.0 / len(tracts)) * (int(demographics[tract]["white"]) / int(demographics[tract]["population"]))

		# Income.
		if demographics[tract]["median_income"] != "":
			total_median_income_pixels += (1.0 / len(tracts))
			if float(demographics[tract]["median_income"]) < median_income:
				total_below_median_income_pixels += (1.0 / len(tracts))

		# Transit.
		if int(demographics[tract]["all_transit"]) > 0:
			total_public_transit_pixels += (1.0 / len(tracts)) * (int(demographics[tract]["public_transit"]) / int(demographics[tract]["all_transit"]))

		# Married women.
		if int(demographics[tract]["all_female_marital"]) > 0:
			total_female_married_pixels += (1.0 / len(tracts)) * (int(demographics[tract]["female_married"]) / int(demographics[tract]["all_female_marital"]))

		# Single detached housing units.
		if int(demographics[tract]["housing_units"]) > 0:
			total_housing_units_singledetached_pixels += (1.0 / len(tracts)) * (int(demographics[tract]["housing_units_single_detached"]) / int(demographics[tract]["housing_units"]))
			val += (1.0 / len(tracts)) * (int(demographics[tract]["housing_units_single_detached"]) / int(demographics[tract]["housing_units"]))

		# Voted for Obama.
		prez = prezelection[tract[0:5]]
		if float(prez["TTL_VT"]) > 0:
			total_voted_obama_pixels += (1.0 / len(tracts)) * (float(prez["OBAMA"]) / float(prez["TTL_VT"]))

	img.putpixel((int(x),int(y)), int(round(255*val)))

img.save("map.png", format="png")

print("pixels", total_pixels)
print("tracts", total_tracts)
print()
print("population", total_population)
print("white population", total_white_population, round(1000*total_white_population/total_population)/10)
print("white pixels", total_white_pixels, round(1000*total_white_pixels/total_pixels)/10)
print()
print("pixels with median income known", int(round(total_median_income_pixels)))
print("pixels below median income", int(round(total_below_median_income_pixels)), round(1000*total_below_median_income_pixels/total_median_income_pixels)/10)
print()
print("working_population", total_working_population)
print("working + public transit population", total_public_transit_population, round(1000*total_public_transit_population/total_working_population)/10)
print("working + public transit pixels", int(round(total_public_transit_pixels)), round(1000*total_public_transit_pixels/total_pixels)/10)
print()
print("female population", total_female_population)
print("female married population", total_female_married_population, round(1000*total_female_married_population/total_female_population)/10)
print("female married pixels", int(round(total_female_married_pixels)), round(1000*total_female_married_pixels/total_pixels)/10)
print()
print("housing units", total_housing_units)
print("single detached housing units", total_housing_units_singledetached, round(1000*total_housing_units_singledetached/total_housing_units)/10)
print("single detached pixels", int(round(total_housing_units_singledetached_pixels)), round(1000*total_housing_units_singledetached_pixels/total_pixels)/10)
print()
print("voted", total_voted)
print("voted obama population", total_voted_obama, round(1000*total_voted_obama/total_voted)/10)
print("voted obama pixels", int(round(total_voted_obama_pixels)), round(1000*total_voted_obama_pixels/total_pixels)/10)

tract_order = sorted(tract_pixel_counts, key = lambda tract : int(demographics[tract]["population"]) / (tract_pixel_counts[tract] or 1), reverse=True)
population = 0
pixels = 0
histogram = []
for tract in tract_order:
	population += int(demographics[tract]["population"])
	pixels += tract_pixel_counts[tract]
	histogram.append((population/total_population, pixels/total_pixels))
	if pixels/total_pixels > .1:
		print(population/total_population, pixels/total_pixels)
		break
#print(max(histogram, key=lambda h : h[0]-h[1]))
