.DEFAULT_TARGET := predict
.PHONY: predict
predict: weather.csv
	python predict.py
weather.csv: munge.py common.py
	python munge.py
.PHONY: clean
clean:
	-rm -rf weather.csv stations.pdf departure_from_trend.pdf yield.pdf
