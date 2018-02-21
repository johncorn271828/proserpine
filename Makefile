.DEFAULT_TARGET := predict
.PHONY: predict
predict: weather.csv indemnities.csv
	python predict.py
weather.csv: weather.py common.py
	python weather.py
indemnities.csv: indemnities.py common.py
	python indemnities.py
.PHONY: clean
clean:
	-rm -rf weather.csv stations.pdf departure_from_trend.pdf yield.pdf indemnities.csv
