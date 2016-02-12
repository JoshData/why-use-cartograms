# Quantifying how distorted are population maps

Choropleth maps that color-code geographies according to population statistics are distorted. Lots of space on the map to goes to rural settled areas (or totally unsettled areas!) and relatively little space is given to densely populated cities. As a result, we're seeing a distorted picture of the people the map is intending to represent.

86% of the contiguous-U.S. population lives in just 10% of the land area. (99% of the population lives in just 52% of the land area.)

That's nothing new. But I've quantified just how distorted these maps are.

I rasterized the 74,001 Census tracts in the contiguous United States individually and counted how many pixels each tract takes up in the final image. (When multiple tracts are drawn on the same pixel, I apportioned the pixel equally to each of those tracks. I rasterized to what would be an 800x500 pixel image of the contiguous United States.) Then I cross-referenced those pixels to the 2010-2014 American Community Survey 5-Year Estimates demographic data for the tracts in those pixels.

## How to reproduce this study

Get a US Census API key from http://api.census.gov/data/key_signup.html. Then fetch Census demographic data (American Community Survey) and geospatial data (TIGER):

	API_KEY=your_census_api_key_here python3 fetch_tract_stats.py > tract_population.csv
	./fetch_tract_shapefiles.sh

Now compute which pixels in a raster image correspond to which tracts (for an 800-pixel-wide map):

	python3 compute_tract_pixels.py 800 > tract_pixels_800.csv

This takes about an hour. The columns of `tract_pixels_800.csv` are the x and y coordinates of the pixel followed by the GEOIDs of as many tracts get drawn on that pixel as there are. (So, the rows of the CSV file don't all have the same number of columns.) The Python script also draws a composite raster map of all of the tracts in `map_800.png`.

Note, these are all Python 3 scripts. Dependencies are listed in `pip-requirements.txt`.
