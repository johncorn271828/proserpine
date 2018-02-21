import os
import sys
from pprint import pprint
import numpy as np
import pandas as pd
import urllib.request
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap


from common import ROOT_DIR, START_YEAR, END_YEAR


class GhcndMunger:
    """Compute periodic statistics from NOAA's Global Historical Climate
    Network Daily files and write to csv"""

    # Cherrypick a collection of weather stations. Originally I downloaded
    # all the ghcd data, grepped for stations with 1890 through 2017 data,
    # and kept the ones with almost all the measurements.
    default_station_ids = [ #     STATE                         NAME 
        #"CA001100120",      #     BC                     AGASSIZ CDA 
        "USW00023271",      #     CA                SACRAMENTO 5 ESE 
        "USW00093820",      #     KY          LEXINGTON BLUEGRASS AP 
        #"USC00200032",      #     MI                    ADRIAN 2 NNE 
        "USC00200146",      #     MI                            ALMA 
        #"USC00211891",      #     MN            CROOKSTON NW EXP STN 
        "USC00215638",      #     MN  MORRIS W CNTRL RSCH & OUTREACH 
        #"USW00013872",      #     NC                       ASHEVILLE 
        #"USW00013724",      #     NJ                   ATLANTIC CITY 
        "USW00024128",      #     NV              WINNEMUCCA MUNI AP 
        "USW00094728",      #     NY           NEW YORK CNTRL PK TWR 
        #"CA006149625",      #     ON                       WOODSTOCK 
        "CA006105976",      #     ON                      OTTAWA CDA 
        "USW00014936",      #     SD                   HURON RGNL AP 
        "USW00024157",      #     WA                 SPOKANE INTL AP 
        "USW00014898"]      #     WI                       GREEN BAY


    def __init__(self):
        """Prepare a wide schema for reading fixed width .dly files"""
        # The fixed-width data in the .dly files begin with these four elements
        self.dly_schema_names = ["ID", "YEAR", "MONTH", "ELEMENT"]
        self.dly_schema_indices = [(0,11), (11,15), (15,17), (17,21)]
        # After that, there are 4 components times 31 days. Append these numbered
        # column names to the schema above
        column_index = 21
        for i in range(1,32):
            self.dly_schema_names.append("VALUE" + str(i))
            self.dly_schema_indices.append((column_index, column_index+5))
            column_index += 5

            self.dly_schema_names.append("MFLAG" + str(i))
            self.dly_schema_indices.append((column_index, column_index+1))
            column_index += 1

            self.dly_schema_names.append("QFLAG" + str(i))
            self.dly_schema_indices.append((column_index, column_index+1))
            column_index += 1

            self.dly_schema_names.append("SFLAG" + str(i))
            self.dly_schema_indices.append((column_index, column_index+1))
            column_index += 1
        self.measurements = dict()


    def get_measurements(self, station_id):
        """Obtain the relevant DataFrame representation of one of the NOAA daily
        measurement files."""
        if station_id in self.measurements:
            return self.measurements[station_id]
        dly_path = os.path.join(ROOT_DIR, "raw_data", station_id + ".dly")
        if not os.path.isfile(dly_path):
            try:
                url = ("https://www1.ncdc.noaa.gov/pub/data/ghcn/daily/all/" +
                       station_id + ".dly")
                with urllib.request.urlopen(url) as response, \
                     open(dly_path, "wb") as out_file:
                    data = response.read() # a `bytes` object
                    out_file.write(data)
            except:
                print("Error downloading " + url)
                sys.exit(0)
        measurements = pd.read_fwf(
            dly_path,
            names=self.dly_schema_names,
            colspecs=self.dly_schema_indices)
        # Discard everything except for temperature and precipitation total
        measurements = measurements[(measurements["ELEMENT"]=="PRCP") |
                                    (measurements["ELEMENT"]=="TMAX") |
                                    (measurements["ELEMENT"]=="TMIN")]
        measurements = measurements[(measurements["YEAR"] >= START_YEAR) &
                  (measurements["YEAR"] <= END_YEAR)]
        # Change from rows being months to rows being days
        measurements["dly_file_index"] = measurements.index
        measurements = pd.wide_to_long(measurements,
                                       ["VALUE", "MFLAG", "QFLAG", "SFLAG"],
                                       i="dly_file_index",
                                       j="DAY")
        measurements = measurements.reset_index(level=["DAY"])
        measurements["DAY"] = measurements["DAY"].astype(np.int64)
        measurements = measurements[measurements["VALUE"] != -9999]
        # Remove days with bad quality flag
        measurements = measurements[measurements["QFLAG"].isnull()]
        # Filter on source flag. According to docs: "NOTE: "S" values are derived
        # from hourly synoptic reports exchanged on the Global Telecommunications
        # System (GTS). Daily values derived in this fashion may differ
        # significantly from "true" daily data, particularly for precipitation
        # (i.e., use with caution)."
        measurements["SFLAG"] = measurements["SFLAG"].astype(str)
        measurements = measurements[measurements["SFLAG"] != "S"]
        # Drop unused columns
        measurements = measurements.drop("MFLAG", axis=1)
        measurements = measurements.drop("QFLAG", axis=1)
        measurements = measurements.drop("SFLAG", axis=1)
        # Memoize
        self.measurements[station_id] = measurements

        return measurements


    def plot_stations(self, station_ids=default_station_ids):
        "Draw a map of stations."
        stations = pd.read_fwf(
            os.path.join(ROOT_DIR, "raw_data", "ghcnd-stations.txt"),
            header=None,
            names=[     "ID", "LATITUDE", "LONGITUDE", "ELEVATION", "STATE", "NAME", "GSN FLAG", "HCN/CRN FLAG", "WMO ID"],
            colspecs=[(0,11),    (12,20),     (21,30),     (31,37), (38,40), (41,71),   (72,75),        (76,79), (80,85)])
        stations = stations[
            stations["ID"].isin(station_ids)]

        fig=plt.figure()
        ax=fig.add_axes([0.1,0.1,0.8,0.8])
        m = Basemap(projection="mill",\
                    lon_0=0)
        m.drawcoastlines()
        m.drawcountries()
        lons = stations["LONGITUDE"].tolist()
        lats = stations["LATITUDE"].tolist()
        x, y = m(lons, lats)
        m.scatter(x,y,marker=".", color="red")
        ax.set_title("Weather stations")
        plt.savefig("stations.pdf")
        plt.show()    

                
    def munge(self, start_month=2, end_month=11, enough_days=15,
              station_ids=default_station_ids):
        """Compute monthly averages of TMIN, TMAX and PRCP and return them in a 
        DataFrame."""
        # pandas doesn't have wide_to_long, so generate a big wide schema.
        # (This is naming the columns of what will be X.)
        season_schema = ["year"]
        for station_id in station_ids:
            for month in range(start_month, end_month+1):
                season_schema += [
                "TMAXavg_" + str(station_id) + "_month" + str(month),
                "TMAXmin_" + str(station_id) + "_month" + str(month),
                "TMAXmax_" + str(station_id) + "_month" + str(month),
                "TMINavg_" + str(station_id) + "_month" + str(month),
                "TMINmin_" + str(station_id) + "_month" + str(month),
                "TMINmax_" + str(station_id) + "_month" + str(month),
                "PRCPavg_" + str(station_id) + "_month" + str(month),
                "PRCPmax_" + str(station_id) + "_month" + str(month)]
        seasons = []
        bad_months = {station_id : 0 for station_id in station_ids}
        for year in range(START_YEAR, END_YEAR+1):
            print(str(year) + " ... ", end = ""); sys.stdout.flush()
            season = [year]
            for station_id in station_ids:
                measurements = self.get_measurements(station_id)
                for month in range(start_month, end_month+1):
                    tmaxs = measurements[(measurements["MONTH"] == month) &
                                         (measurements["YEAR"] == year) &
                                         (measurements["ELEMENT"] == "TMAX") ]
                    if(len(tmaxs) < enough_days):
                        print(":( ", end="")
                        bad_months[station_id] += 1
                        tmaxs = measurements[(measurements["MONTH"] == month) &
                                             (measurements["ELEMENT"] == "TMAX")]
                    tmins = measurements[(measurements["MONTH"] == month) &
                                         (measurements["YEAR"] == year) &
                                         (measurements["ELEMENT"] == "TMIN") ]
                    if(len(tmins) < enough_days):
                        print(":( ", end="")
                        bad_months[station_id] += 1
                        tmins = measurements[(measurements["MONTH"] == month) &
                                             (measurements["ELEMENT"] == "TMIN")]
                    prcps = measurements[(measurements["MONTH"] == month) &
                                         (measurements["YEAR"] == year) &
                                         (measurements["ELEMENT"] == "PRCP")]
                    if(len(prcps) < enough_days):
                        print(":( ", end="")
                        bad_months[station_id] += 1
                        prcps = measurements[(measurements["MONTH"] == month) &
                                             (measurements["ELEMENT"] == "PRCP")]
                    season += [tmaxs["VALUE"].mean(),
                               tmaxs["VALUE"].min(),
                               tmaxs["VALUE"].max(),
                               tmins["VALUE"].mean(),
                               tmins["VALUE"].min(),
                               tmins["VALUE"].max(),
                               prcps["VALUE"].mean(),
                               prcps["VALUE"].max()]
            seasons.append(season)
            print("")
        print("Bad months: ")
        pprint(bad_months)
        seasons = pd.DataFrame(seasons, columns=season_schema)
        #seasons = seasons.fillna(0)
        seasons = seasons.set_index("year")
        seasons.to_csv("weather.csv")
        
        return seasons


if __name__ == "__main__":
    m = GhcndMunger()
    m.plot_stations()
    m.munge()
