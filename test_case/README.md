# This is a test case for Ypsilanti, Michigan, USA
To ensure data privacy, this test case is developed from the Ypsilanti case study outlined in Section 6 (similar to Instance 3 and 4 with doubled ridership, see settings.yaml) and Appendix C.

## stops.csv
The stops are collected from AAATA's official GTFS (in the year of 2016)

## hubs.csv
The details can be found in Appendix C within the paper.

## demographic.json
The details can be found in Appendix C within the paper.

## core-trips.csv
This data is synthetic, as the original data cannot be disclosed to the public.

## latent-trips.csv
This data is synthetic, as the original data cannot be disclosed to the public.

## dist_km.pickle / time_min.pickle
The files are omitted from the repository due to their considerable sizes but can be generated easily using Haversine distance with a constant vehicle speed (e.g., 0.5 km/min) or more advanced tools like Graphhopper. However, for the experiments in the paper, these files were provided by the authors' collaborators and are not intended for public distribution.