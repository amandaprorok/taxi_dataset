# Taxi dataset

## About

Part of this code was used to create the results behind our "Privacy-preserving vehicle assignment for mobility-on-demand systems" paper.
This code loads the relevant data, namely the transport graph and the taxi requests.
Unfortunately, the Yellow Cab data available at http://www.nyc.gov/html/tlc/html/about/trip_record_data.shtml has been updated to obfuscate location information and, as such, this code won't work as is.

## Relevant publication

If you use this code, please cite:

- A. Prorok, V. Kumar, Privacy-Preserving Vehicle Assignment for Mobility-on-Demand Systems, IEEE/RSJ International Conference on Intelligent Robots and Systems (IROS), 2017, [PDF](http://ieeexplore.ieee.org/document/8206003/)

## Usage

```bash
$ python plot_manhattan.py \
    --log=info \
    --taxi_filename=yellow_tripdata_2016-06.csv

INFO:root:Trying to load map from "/tmp/cae984584e27feb27bea9eb399e71402.graphml"
INFO:root:Trying to load preprocessed taxi data from "/tmp/7f97dc9cf54747cba17ac51a97a0072b_1000000.bin"
INFO:root:Loading taxi data from "yellow_tripdata_2016-06.csv"
100%|████████████████████████████████████████████████████████████████████| 11135470/11135470 [05:48<00:00, 31954.66it/s]
INFO:root:Saving processed taxi data to "/tmp/7f97dc9cf54747cba17ac51a97a0072b_1000000.bin"
INFO:root:Trying to load edge times from "/tmp/edge_times_bf5a52316baa206ded93dd4834a92a85.pickle"
INFO:root:Computing all routes to calculate edge time
INFO:root:Computing edge statistics
100%|███████████████████████████████████████████████████████████████████████| 1000000/1000000 [04:19<00:00, 3848.73it/s]
INFO:root:Average speed: 16.32 +- 5.64 km/h
```

which should display a plot similar to the following:

![Screenshot](https://raw.githubusercontent.com/amandaprorok/taxi_dataset/master/img/screenshot.png)
