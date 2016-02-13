# Quantifying how distorted population maps are

https://medium.com/@joshuatauberer/4a98f89cbbb1#.ygy16f6hl

***

Choropleth maps that color-code geographies according to population statistics are distorted. Lots of space on the map to goes to rural settled areas (or totally unsettled areas!) and relatively little space is given to densely populated cities. As a result, we're seeing a distorted picture of the people the map is intending to represent.

That's nothing new. But I've quantified just how distorted these maps are.

I rasterized each of the the 71,954 Census tracts and (in a separate analysis each of the 3,108 counties) in the contiguous United States with at least one resident and counted how many pixels each tract/county takes up in the final image. (Each tract/county takes up at least one pixel. When multiple tracts/counties are drawn on the same pixel, I apportioned the pixel equally to each of those tracks/counties. I rasterized to what would be an 800x500 pixel image of the contiguous United States.) Then I cross-referenced those pixels to the 2010-2014 American Community Survey 5-Year Estimates demographic data for the tracts/counties in those pixels.

## How to reproduce this study

Get a US Census API key from http://api.census.gov/data/key_signup.html. Then fetch Census demographic data (American Community Survey) and geospatial data (TIGER):

	export API_KEY=your_census_api_key_here
	python3 fetch_demo_stats.py tract > tract_population.csv
	python3 fetch_demo_stats.py county > county_population.csv

	./fetch_shapefiles.sh

Now compute which pixels in a raster image correspond to which tracts/counties (for an 800-pixel-wide map):

	python3 compute_pixels.py tract 800 > tract_pixels_800.csv
	python3 compute_pixels.py county 800 > county_pixels_800.csv

This takes about an hour. The columns of `tract_pixels_800.csv` are the x and y coordinates of the pixel followed by the GEOIDs of as many tracts get drawn on that pixel as there are. (So, the rows of the CSV file don't all have the same number of columns.) The Python script also draws a composite raster map of all of the tracts in `map_tract_800.png`. Likewise for the county script.

Finally run the analysis:

	python3 analysis.py tract
	or
	python3 analysis.py county

which outputs some numbers for tract-based maps and county-based maps and saves some images.

Note, these are all Python 3 scripts. Dependencies are listed in `pip-requirements.txt`.
