# Quantifying how distorted population maps are

https://medium.com/@joshuatauberer/4a98f89cbbb1#.ygy16f6hl

***

Choropleth maps that color-code geographies according to population statistics are distorted. Lots of space on the map to goes to rural settled areas (or totally unsettled areas!) and relatively little space is given to densely populated cities. As a result, we're seeing a distorted picture of the people the map is intending to represent.

That's nothing new. But I've quantified just how distorted these maps are.

I rasterized the 71,954 Census tracts in the contiguous United States with at least one resident individually and counted how many pixels each tract takes up in the final image. (Each tract takes up at least one pixel. When multiple tracts are drawn on the same pixel, I apportioned the pixel equally to each of those tracks. I rasterized to what would be an 800x500 pixel image of the contiguous United States.) Then I cross-referenced those pixels to the 2010-2014 American Community Survey 5-Year Estimates demographic data for the tracts in those pixels.

## How to reproduce this study

Get a US Census API key from http://api.census.gov/data/key_signup.html. Then fetch Census demographic data (American Community Survey) and geospatial data (TIGER):

	API_KEY=your_census_api_key_here python3 fetch_tract_stats.py > tract_population.csv
	./fetch_tract_shapefiles.sh

Now compute which pixels in a raster image correspond to which tracts (for an 800-pixel-wide map):

	python3 compute_tract_pixels.py 800 > tract_pixels_800.csv

This takes about an hour. The columns of `tract_pixels_800.csv` are the x and y coordinates of the pixel followed by the GEOIDs of as many tracts get drawn on that pixel as there are. (So, the rows of the CSV file don't all have the same number of columns.) The Python script also draws a composite raster map of all of the tracts in `map_800.png`.

Finally run the analysis:

	python3 analysis.py

which outputs some numbers and saves some images.

Note, these are all Python 3 scripts. Dependencies are listed in `pip-requirements.txt`.
