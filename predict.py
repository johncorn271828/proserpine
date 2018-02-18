import os
import sys
import numpy as np
import pandas as pd
import scipy
from sklearn import preprocessing
from sklearn.kernel_ridge import KernelRidge
import matplotlib.pyplot as plt

from common import ROOT_DIR, START_YEAR, END_YEAR


class USAMaizeYieldPredictor:
    
    def __init__(
            self,
            fitter=KernelRidge(kernel="poly", degree=3, alpha=0.5),
            yield_csv_name="FF72F614-2177-381F-A4EB-D059F706EC14.csv",
            advent_1=1937, # Technological model slope changes in these years
            advent_2=1962):
        """Use RL Nielsen's technological model of maize yields to compute
        seasonal deviations from expectations. Load NOAA climatic data and be
        ready to predict."""
        self.fitter = fitter
        self.weather = pd.read_csv(os.path.join(ROOT_DIR, "weather.csv"))
        self.yields = pd.read_csv(
            os.path.join(ROOT_DIR, "raw_data", yield_csv_name))
        # Prune forecast rows
        self.yields = self.yields[self.yields["Period"] == "YEAR"] 
        self.yields = self.yields.loc[:,['Year', 'Value']]
        self.yields = self.yields.set_index(self.yields['Year'])
        self.yields = self.yields.sort_index()
        # Perform piecewise linear fit and compute departure from trend %
        era = self.yields[self.yields["Year"] < advent_1]
        (early_slope, early_intercept,
        r_value, p_value, std_err) = scipy.stats.linregress(
            era.as_matrix())
        era = self.yields[(self.yields["Year"] >= advent_1) &
                     (self.yields["Year"] < advent_2)]
        (middle_slope, middle_intercept,
         r_value, p_value, std_err) = scipy.stats.linregress(
             era.as_matrix())
        era = self.yields[self.yields["Year"] >= advent_2]
        (modern_slope, modern_intercept,
         r_value, p_value, std_err) = scipy.stats.linregress(
             era.as_matrix())
        def fit(year):
            if year < advent_1:
                return early_slope * year + early_intercept
            elif year < advent_2:
                return middle_slope * year + middle_intercept
            else:
                return modern_slope * year + modern_intercept
        self.yields["technological_trend"] = self.yields["Year"].apply(fit)
        self.yields = self.yields[(self.yields["Year"] >= START_YEAR) &
                      (self.yields["Year"] <= END_YEAR) ]
        self.yields = self.yields.drop("Year", axis=1)
        self.yields["departure_from_trend"] = (
            (self.yields["Value"] - self.yields["technological_trend"]) /
            self.yields["technological_trend"])

        
    def predict(self, year):
        """Predict the maize yield in bushels/acre for year, return as float"""
        X = self.weather.as_matrix()
        y = self.yields["departure_from_trend"].as_matrix()
        scaler = preprocessing.MinMaxScaler(feature_range=(0, 1))
        X = scaler.fit_transform(X)
        prediction_season_vector = X[year - START_YEAR]
        training_X = np.delete(X, year - START_YEAR, axis=0)
        training_y = np.delete(y, year - START_YEAR, axis=0)
        fit = self.fitter.fit(training_X, training_y)
        prediction = float(fit.predict(prediction_season_vector.reshape(1, -1)))

        return prediction    

    
    def leave_one_out_cross_validation(self):
        "Predict each year by training on all other years"
        predictions = []
        for year in range(START_YEAR, END_YEAR+1):
            predictions.append([year, self.predict(year)])
        self.predictions = pd.DataFrame(
            predictions,
            columns=["Year", "predicted_departure"])
        self.predictions = self.predictions.set_index("Year")
        self.predictions = self.predictions.join(predictor.yields)
        # Columns to evaluate the fit
        self.predictions["predicted"] = (
            self.predictions["technological_trend"] *
            (1.0 + self.predictions["predicted_departure"]))
        self.predictions["technological_trend_error"] = (
            self.predictions["technological_trend"] - self.predictions["Value"])
        self.predictions["prediction_error"] = (self.predictions["Value"] -
                                           self.predictions["predicted"])
        self.predictions["improvement"] =  (
            abs(self.predictions["technological_trend_error"]) -
            abs(self.predictions["prediction_error"]))
        self.predictions["win"] = self.predictions["improvement"] > 0
        self.report()

    def report(self):
        "IO to tell a person about the leave-one-out predicctions"
        print(self.predictions)
        print("Times outperformed technological model baseline: ")
        print(str(self.predictions["win"].sum()) +
              " / " + str(len(self.predictions)))
        regression_plot = self.predictions.plot(
            y=["departure_from_trend",
               "predicted_departure"],
            title="Predicted vs observed departure from technological model"
        ).axhline(y=0)
        for x in range(1890,2020,10):
            plt.axvline(x=x)
        plt.show()
        regression_plot.get_figure().savefig("departure_from_trend.pdf")
        value_plot = self.predictions.plot(
            y=["Value", "technological_trend", "predicted"],
            title="predicted yield (bushels/acre)"
        )
        for x in range(1890,2020,10):
            plt.axvline(x=x)
        plt.show()
        value_plot.get_figure().savefig("yield.pdf")


        
if __name__ == "__main__":
    predictor = USAMaizeYieldPredictor()
    predictor.leave_one_out_cross_validation()
