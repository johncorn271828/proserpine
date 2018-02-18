import os
import pandas as pd

ROOT_DIR = os.path.dirname(os.path.realpath(__file__))
pd.set_option('display.width', 280)
pd.set_option("display.max_rows", 200)

# USDA data goes back to 1866, but the selection of weather stations is poor.
# NOAA points out that many are available by 1890: https://www.ncdc.noaa.gov/ghcn-daily-description
START_YEAR = 1890
END_YEAR = 2017
