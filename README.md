# Proserpine #
* An algorithm for predicting crop yields *


## Abstract ##
An attempt is made to predict crop yields (the bushels of grain produced per acre of land) from seasonal weather data. Using USDA reports for national average crop yields and NOAA's Global Historical Climate Network database for meteorological measurements, varous machine learning algorithms were applied to predict the maize yield of each year. "Leave one out" model validation is used, in which the performance of a given algorithm for a particular growing season is evaluated by furnishing the algorithm with complete weather and yield data of every other year for training, then comparing its prediction for the given year to the USDA record as if the algorithm were predicting a new year. Kernel ridge regression gives the best results, correctly predicting the direction of departure of maize yields from historical trendlines for 87 out of 128 seasons studied.


## Introduction ##
This project was inspired by a question my mom asked me about how I thought the Old Farmer's Alamanac could supposedly provide useful predictions about weather and crops months in advance. Setting aside the performance of that particular horoscope, it is natural to speculate whether the upcoming growing season will in some way resemble a particular past season. This is the idea behind the groundhog seeing its shadow and similar traditions, and we know now that there are phenomena like El Nino and La Nina that allow climatic measurements at one time of year to provide a degree of predictive power about the weather later that year. Since the prediction of future weather from current weather has a lot of people working on it, I started thinking about how one might go about predicting crop yields from weather data. People have been interested in this for a long time [1]. If we could combine weather predicting software with yield predicting software, we might be able to at least generate good advice about whether it is appropriate to plant more or less of a crop than usual, even if you can't accurately guess the yield value with all the technological and other noise in the data.

For now, let's focus our discussion on corn; setting aside the corny puns about my surname being Corn, there's a veritable cornucopia of corn literature out there. The second distracting homograph in this context is that the algorithm that seems to work the best is called "kernel ridge regression" where kernel refers to the nullspace of an algebraic operator and not the fruit of the maize plant. But if we can get through the linguistic dualities and just stop punning, there's a kernel of truth to be found.

Glancing at yield data [2], it becomes clear that the growth in yields over time will make separating the effect of weather from technology difficult. There was understandable interest after the 2012 growing season [3]. That year's maize crop suffered a combination of an accelerated planting season and a long drought, which emphasizes how useful it would be to accurately predict a harvest months from now with today's weather. [3] took an approach of fitting a trend line to recent national yield averages and measuring deviation from the trend to quantify the effect of weather on a harvest. They successfully correlated quantities like average July temperature across 8-state regions to develop a weather correction term to the technological trend line.

Thinking a little further about maize physiology, quantities averaged over a large region and a long span of time might not be particularly informative about the weather events that affect a plant's life. Early season frosts can have a very different impact on a plant depending on a swing of just a few degrees on a particular night [4]. The effects of high temperatures on corn plants depends on the intensity of the heat and the duration, and high nighttime temperatures can also play a large role [5]. [6] quantifies the effect of drought on yield by counting days under moisture stress, which is not necessarily correlated with seasonal rainfall totals. The response to drought is also dependent on the developmental stage at which the plant is subjected to moisture stress [7]. Similarly, one can separately study the effects of early [8] and mid [9] season flooding. The flood damage takes place in a 24-48 hour span of time, an effect that could completely disappear if you only look at the monthly rainfall totals of a dry month with a traumatic flood on the last day.

All this suggests that there might be a way to use more fine-grained weather data to predict yields. The National Oceanic Atmospheric Administration has a large database of weather measurements called the Global Historical Climate Network [10]. I'd like to try various machine learning algorithms on that data to calculate a correction and outperform the technological trend line.


## Results ##
After searching through the 26GB or so of measurement data, I found a dozen or so weather stations in the US and Canada with precipitation and min/max temperature data going back to 1890:

![Alt text](stations.pdf "")

More training data (ie more harvests to learn from) should make the fit more accurate. The USDA has data going back to 1866 [11] but the NOAA data is rather sparse until about 1890 [12].

The historical trendline going back that far isn't exactly straight. [13] gives a piecewise linear fit to the technological trend, and identifies various famous/infamous harvest seasons on the plot of departures from the trend.

After adopting the piecewise technological model of [13], I tried various methods for munging all the measurements into informative training data. The first approach I tried was to calculate montly statistics like the authors of [3], and was immediately able to outperform the technological trendline. Next I attempted to flag days at which a plant was subjected to sudden stresses like floods, heat waves, etc, then count the bad days. I also tried averaging the weather data over spans of time smaller than a month, but didn't see an improvement. So far, the best results I've seen are from training on monthly averages of daily maximum and minimum temperatures, monthly maximum and minimum temperatures, precipitation totals, and daily precipitation maxima. More experiments projecting the available data onto training vectors and performing cross validation is needed, and I'll keep trying.

Using Kernel Ridge Regression with a degree 3 polynomial kernel and "leave one out" cross validation, this model correctly predicts the direction of the deviation from the technological trendline in 87 out of 128 years. So, you'd have a hard time winning that many coin flips, but it isn't perfect:

![Alt text](departure_from_trend.pdf "")
![Alt text](yield.pdf "")


## Future work ##
If there were some way to filter out more noise, the quality of the model could be drastically improved. Right now, the algorithm has no way of distinguishing two growing seasons with identical weather but a plague of locusts in one. If the locust season is encountered in the training data, it will unfairly stereotype new test data. If the locust and non-locust year are both in the training data, the algorithm will assume small differences between the two years amount to vast effects on yield. Any sort of quantitative model or even a qualitative history of pests, labor disruptions, or any other events that could affect yields could help me massage the trendline to make the fit converge better. Maybe the IRS has this kind of information, but I haven't found it.

For the next iteration of this project, I'd like to use more of the weather station data. It probably makes sense to break the growing area up into a grid, choose stations within the squares, and average the data of many stations instead of cherry picking a chosen few with near-complete data. I've experimented with a number of the predictors built into sklearn, but haven't expended much effort optimizing the hyper parameters. It may also be worthwhile to spend more time trying to train with some representation of short term weather effects as in [4,5,6,7,8,9].

## Running the software ##
To run this, you'll need the standard panoply of python data science libraries. I recommend Anaconda [14]. I've provided a GNU Makefile if you're into that sort of thing. You'll need to `pip install basemap scikit-learn pandas numpy matplotlib` if you haven't already. Munging the data takes a few minutes, but once the `weather.csv` file is generated, you can alter predictor parameters and see the effect fairly quickly.

Comments and PRs welcome!


## References ##
[1] http://www.isws.illinois.edu/pubdoc/cr/iswscr-51.pdf
[2] http://usda.mannlib.cornell.edu/usda/current/htrcp/htrcp-04-13-2017.txt
[3] http://usda.mannlib.cornell.edu/usda/ers/FDS/2010s/2013/FDS-07-26-2013.pdf
[4] https://www.agry.purdue.edu/ext/corn/news/articles.02/frost_freeze-0520.html
[5] http://www.cornandsoybeandigest.com/corn/high-temperature-effects-corn-soybeans
[6] http://agrigold.com/Universal/Articles/The-Effects-on-Drought-on-Corn-Yield/
[7] https://dirp3.pids.gov.ph/ACIAR/relatedresources/Impact%20of%20drought%20on%20corn%20productivity.pdf
[8] http://corn.agronomy.wisc.edu/Management/L038.aspx
[9] https://crops.extension.iastate.edu/cropnews/2010/08/mid-season-flooding-impact-corn-ear-fill
[10] https://www.ncdc.noaa.gov/data-access/land-based-station-data/land-based-datasets/global-historical-climatology-network-ghcn
[11] https://quickstats.nass.usda.gov/
[12] https://www.ncdc.noaa.gov/ghcn-daily-description
[13] https://www.agry.purdue.edu/ext/corn/news/timeless/yieldtrends.html
[14] https://conda.io/docs/user-guide/install/download.html