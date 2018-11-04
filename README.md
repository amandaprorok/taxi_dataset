# Taxi dataset

## About

Part of this code was used to create the results behind our "Privacy-preserving vehicle assignment for mobility-on-demand systems" paper.
This code loads the relevant data, namely the transport graph and the taxi requests.
Unfortunately, the Yellow cab data available at http://www.nyc.gov/html/tlc/html/about/trip_record_data.shtml has been updated to obfuscate the location information and, as such, this code won't work as is.

## Usage

```bash
python plot_manhattan.py \
  --log=info \
  --taxi_filename=yellow_tripdata_2016-06.csv
```

## Relevant publication

If you do end up using this code, please cite:

- A. Prorok, V. Kumar, Privacy-Preserving Vehicle Assignment for Mobility-on-Demand Systems, IEEE/RSJ International Conference on Intelligent Robots and Systems (IROS), 2017, [PDF](http://ieeexplore.ieee.org/document/8206003/)
