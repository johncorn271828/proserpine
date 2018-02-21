import os
import numpy as np
import pandas as pd


from common import ROOT_DIR, START_YEAR


class USDAIndemnitiesMunger:
    """Prepare data to compute a correction term to the technological trendline 
    based on damages to crops reported to USDA. It isn't always clear whether 
    a reported damage cause is/should be reflected in the NOAA data. 

    Accuracy seems poor, but this class makes the data available at least"""

    # Pruned version of the complete list of given causes
    default_causes = [
        #'Excess Moisture/Precip/Rain',
        #'Drought',
        #'Hail',
        #'Wind/Excess Wind',
        #'Other (Snow-Lightning-Etc.)',
        'Insects',
        #'Flood',
        #'Frost',
        'Plant Disease',
        'Fire',    # Does this mean flaming fire or maize leaf curling?
        'House Burn (Pole Burn)',
        #'Heat',
        'Mycotoxin (Aflatoxin)',
        #'Cold Wet Weather',
        'Wildlife',
        #'Freeze',
        #'Cold Winter',
        'Poor Drainage',
        'Hot Wind',          # LOL?
        'Failure Irrig Supply',
        #'Hurricane/Tropical Depression',
        'Fruit Set Failure',
        'Volcanic Eruption',
        #'Tornado',
        'Failure Irrig Equip',
        'Earthquake',
        #'Insufficient Chilling Hours', #Should be accounted for by TMIN
        #'Cyclone',
        #'Excess Sun',   # ???
        'Force Fire',   # Ditto?
        #'Area Plan Crops Only',
        #'Decline in Price',
        'Mycotoxin',
        'Failure of Irrigation Supply',
        'GRP/Grip Crops',
        #'Wind/Excess Win',
        #'Excess Moisture/Precipitation/Rain',
        #'Other (Snow, Lightening, Etc.)',     # (sic)
        'Failure of Irrigation Equipment',
        'Inability to Prepare Land for Irrigation',
        'Federal or State Ordered Destruction',
        #'Other (Snow, Lightning, Etc.)'
        #'Area Protection Crops Only',
        #'ARPI/SCO/STAX Crops Only'
    ]


    @staticmethod
    def year_to_fname(year):
        """USDA's naming scheme for indemnity records"""
        if year < 1989:
            return "COLINDHS.TXT"
        else:
            return {
                1989 : "COLIND89.TXT",
                1990 : "COLIND90.TXT",
                1991 : "COLIND91.TXT",
                1992 : "COLIND92.TXT",
                1993 : "COLIND93.TXT",
                1994 : "COLIND94.TXT",
                1995 : "COLIND95.TXT",
                1996 : "COLIND96.TXT",
                1997 : "COLIND97.TXT",
                1998 : "COLIND98.TXT",
                1999 : "COLIND99.TXT",
                2000 : "COLIND00.TXT",
                2001 : "colind01.txt",
                2002 : "colind02.txt",
                2003 : "colind03.txt",
                2004 : "colind04.txt",
                2005 : "colind05.txt",
                2006 : "colind06.txt",
                2007 : "colind07.txt",
                2008 : "colind08.txt",
                2009 : "colind09.txt",
                2010 : "colind10.txt",
                2011 : "colind11.txt",
                2012 : "colind12.txt",
                2013 : "colind13.txt",
                2014 : "colind14.txt",
                2015 : "colind15.txt",
                2016 : "colind16.txt",
                2017 : "colind17.txt",
                2018 : "colind18.txt"
            }[year]


    @classmethod
    def get_report(cls, year):
        fname = cls.year_to_fname(year)
        report = pd.read_csv(
            os.path.join(ROOT_DIR, "raw_data", fname),
            sep="|",
            names = (["Commodity Year",
                     "Location State Code",
                     "Location State Abbreviation",
                     "Location County Code",
                     "Location County Name",
                     "Commodity Code",
                     "Commodity Name",
                     "Insurance Plan Code",
                     "Insurance Plan Abbreviation",
                     "Stage Code",
                     "Damage Cause Code",
                     "Damage Cause Description"] +
                     ([] if year < 2001 else ["Determined Acres"]) +
                     ["Indemnity Amount",
                      "(empty)"]),
                header=None,
                dtype={"Indemnity Amount" : np.float64,
                       "Insurance Plan Abbreviation" : np.object_})
        report = report.drop(
            ["Location County Code",
             "Location State Code",
             "Commodity Code",
             "Insurance Plan Code",
             "Stage Code",
             "Damage Cause Code",
             "(empty)"],
            axis=1)
        
        return report


    @classmethod
    def munge(cls, correction_term_damage_causes=default_causes):
        """Read indemnities from USDA data to estimate a non-weather related 
        loss correction tern to Nielsen model before calculating departure from 
        trend. The data starts in 1948."""
        reports = pd.DataFrame()
        for year in range(1988, 2017+1): # 1948-88 all in one file
            report = cls.get_report(year)
            reports = reports.append(report)
        reports = reports.drop("Determined Acres", axis=1)
        reports["Commodity Year"] = reports["Commodity Year"].astype(
            np.int64)
        reports["Commodity Name"] = reports[
            "Commodity Name"].str.strip()
        reports = reports[
            reports["Commodity Name"] == "CORN"]
        reports["Damage Cause Description"] = reports[
            "Damage Cause Description"].str.strip()
        reports["Insurance Plan Abbreviation"] = reports[
            "Insurance Plan Abbreviation"].str.strip()
        reports["Location County Name"] = reports[
            "Location County Name"].str.strip()
        reports["Location State Abbreviation"] = reports[
            "Location State Abbreviation"].str.strip()
        reports = reports[
            reports["Damage Cause Description"].isin(
            correction_term_damage_causes)]
        # Compute avg lost bushels per acre
        per_bushel_prices = pd.read_csv(
            os.path.join(ROOT_DIR, "raw_data",
                         "FDE80B2D-1155-391B-B0D9-2ECC1E988562.csv"),
            dtype={"Year" : np.int64, "Value" : np.float64})
        per_bushel_prices = per_bushel_prices[
            per_bushel_prices["Period"] == "MARKETING YEAR"]
        per_bushel_prices = per_bushel_prices.loc[:,["Year", "Value"]]
        per_bushel_prices = per_bushel_prices.rename(
            index=str, columns={"Value" : "per_bushel_price"})
        per_bushel_prices = per_bushel_prices.set_index(
            per_bushel_prices["Year"])
        per_bushel_prices.sort_index()
        acres_planted = pd.read_csv(
            os.path.join(ROOT_DIR, "raw_data",
                         "0BA4DA4C-05B8-3321-B35B-C145F4AA2925.csv"),
            dtype={"Year" : np.int64})
        acres_planted["Value"] = acres_planted["Value"].apply(
            lambda s : float(s.replace(",", "")))
        acres_planted["Value"] = acres_planted["Value"].astype(np.float64)
        acres_planted = acres_planted.loc[:,["Year", "Value"]]
        acres_planted = acres_planted.rename(
            index=str, columns={"Value" : "acres_planted"})
        acres_planted = acres_planted.set_index(
            acres_planted["Year"])
        acres_planted.sort_index()
        indemnities = per_bushel_prices.merge(acres_planted, on="Year")
        def total_indemnities(year):
            return reports[reports["Commodity Year"] == year][
                "Indemnity Amount"].sum()
        indemnities["total_indemnities"] = indemnities["Year"]
        indemnities["total_indemnities"] = indemnities[
            "total_indemnities"].apply(total_indemnities)
        indemnities = indemnities.set_index("Year")
        indemnities = indemnities[indemnities.index >= START_YEAR]
        indemnities["bushels_lost"] = (
            indemnities["total_indemnities"] /
            indemnities["per_bushel_price"])
        indemnities["bushels_lost_per_acre"] = (
            indemnities["bushels_lost"] /
            indemnities["acres_planted"])
        #The old numbers are small. Just copy zeroes for very old times
        unknown_indemnities = []
        for year in range(START_YEAR, 1926):
            unknown_indemnities.append(
                [year,
                 np.nan,
                 np.nan,
                 np.nan,
                 np.nan,
                 0])
        unknown_indemnities.append(
            [2017,
             np.nan,
             np.nan,
             np.nan,
             np.nan,
             indemnities[
                 indemnities.index > 2012]["bushels_lost_per_acre"].mean()
            ]
        )
        columns = ["Year"] + list(indemnities.columns.values)
        unknown_indemnities = pd.DataFrame(unknown_indemnities,
                                           columns=columns)
        unknown_indemnities = unknown_indemnities.set_index("Year")
        indemnities = indemnities.append(unknown_indemnities)
        indemnities = indemnities.sort_index()
        indemnities.to_csv("indemnities.csv")
        

if __name__ == "__main__":
    USDAIndemnitiesMunger.munge()
