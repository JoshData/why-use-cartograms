# Fetch Census stats for each U.S. Census Tract.

# nb. There is no tract data for American Samoa (FIPS 60), Guam (FIPS 66),
#     Northern Mariana Islands (FIPS 69), and Virgin Islands (FIPS 78)?
#     So I'm skipping those state-equivalents from analysis.

import sys, os, json, io, urllib.request, csv

# 2010-2014 American Community Survey 5-Year Estimates
dataset = "http://api.census.gov/data/2014/acs5"

api_key = os.environ["API_KEY"]

fields = {
	"B01003_001E": "population",
	"B02001_002E": "white", # white alone
	
  "B06011_001E": "median_income", # Median Income in the Past 12 Months (in 2014 Inflation-Adjusted Dollars) 
  
  "B08006_001E": "all_transit", # Means of Transportation to Work - total population that works?
  "B08006_008E": "public_transit", # Public transportation (excluding taxicab)
  "B08006_014E": "bike", # Bicycle
  "B08006_015E": "walked", # Walked


  "B12001_011E": "all_female_marital", # Female Total - Sex by Marital Status for the Population 15 Years and over
  "B12001_013E": "female_married", # Female:!!Now married

  "B25024_001E": "housing_units", # Units in Structure (Housing Units?)
  "B25024_002E": "housing_units_single_detached",
  "B25024_003E": "housing_units_single_attached",
}

metadata = ["state", "county", "tract"]

all_states = ['01', '02', '04', '05', '06', '08', '09', '10', '11', '12', '13', '15', '16',
              '17', '18', '19', '20', '21', '22', '23', '24', '25', '26', '27', '28', '29',
              '30', '31', '32', '33', '34', '35', '36', '37', '38', '39', '40', '41', '42',
              '44', '45', '46', '47', '48', '49', '50', '51', '53', '54', '55', '56', '72']

def get_tract_data_for_state(state):
  # Load the data for all tracts in the given state, passed as a FIPS code.

  try:
  	# Form the URL.
    url = dataset + "?key=" + api_key + "&get=NAME," + ",".join(fields) + "&for=tract&in=state:" + state

    print(state + "...", file=sys.stderr)

    # Make HTTP request and load JSON response.
    tracts = json.load(io.TextIOWrapper(urllib.request.urlopen(url)))
    header = tracts[0]
    tracts = tracts[1:]
 
    # Return as a list of dicts:
    # { 'state': '05', 'county': '145', 'tract': '070500', 'P0010001': '6300'}
    for row in tracts:
    	item = dict(zip(header, row))
    	#for field in fields:
    	#	item[field] = float(item[field]) if item[field] else None
    	yield item

  except Exception as e:
  	raise Exception("Error %s loading tract data for state %s at %s." % (str(e), state, url))

# Loop over states, query the Census API for each state, and write stats to a CSV file.
w = csv.writer(sys.stdout)
cols = metadata + sorted(fields)
w.writerow([fields.get(c, c) for c in cols])
for state in all_states:
  for tract in get_tract_data_for_state(state):
    w.writerow([tract.get(f) for f in cols])
