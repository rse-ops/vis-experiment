# Visualization (vis) Experiment

**this project does not have a name yet**

This is an experiment to transform Caliper data and csv output (from a [rajaperf tutorial](https://github.com/rse-ops/rajaperf-tutorials)) 
into a visualization. The strategy we take will be the following:

1. Transform into long tabular format
2. Experiment with different visualizations for it


## Usage

### 1. Install

Install dependencies in a virtual environment:

```bash
$ python -m venv env
$ source env/bin/activate
```

### 2. Transform into Dashboards

**under development**

For caliper we can read the files with [caliper-reader](https://software.llnl.gov/Caliper/pythonreader.html) OR read in .csv output to do the same. We will likely want to read them into some equivalent data structure (e.g., pandas flat table). Here is how to do the transform for caliper files (and other csv) into output directory [tables](tables) (default for `--outdir`). There are several output formats available, and
for grafana we will want dashboards (the default):

#### Flamegraphs

Let's try generating a flamegraph for a particular .cali (caliper data) file! This can be viewed with standard JavaScript (and eventually a Grafana dashboard, if we go in that direction).

```
Hatchet.flamegraph -> data export -> https://github.com/spiermar/d3-flame-graph -> https://github.com/samber/grafana-flamegraph-panel -> grafana
```

We can generate for all plots like:

```console
$ python transform.py *.cali --flamegraph
```

#### Long Tables

To generate long tables (csv)

```console
$ for filename in $(ls *.cali); do
    python transform.py ${filename} --csv
done
```

And for the standard csv:

```bash
$ for filename in $(ls *.csv); do
    python transform.py ${filename} --skip-rows=2 --csv
done
```

#### Dashboards

I first tried [loading csv from a path](https://grafana.github.io/grafana-csv-datasource/)
but I think it's unlikely that users will want to do this and then know how to query data.
So instead, we can use a Python library [grafanalib](generate-dashboard -o frontend.json example.dashboard.py)
to generate our dashboards.

```bash
python transform.py 
```


### 3. Testing Grafana


First build the container with the plugins we need:

```bash
$ docker build -t grafana .
```

Then run it, binding our data directory for access.

```bash
$ docker run --rm -v $PWD/tables:/data -p 3000:3000 grafana
```

TODO:

1. generate dashboards from python
2. Generate data files
3. install plugin and go?

Add a JSON data source#

    In the side menu, click the Configuration tab (cog icon)
    Click Add data source in the top-right corner of the Data Sources tab
    Enter "JSON" in the search box to find the JSON API data source
    Click the search result that says "JSON API"

The data source has been added, but it needs some more configuration before you can use it.

License
-------

Copyright (c) 2017-2021, Lawrence Livermore National Security, LLC. 
Produced at the Lawrence Livermore National Laboratory.

RADIUSS Docker is licensed under the MIT license [LICENSE](./LICENSE).

Copyrights and patents in the RADIUSS Docker project are retained by
contributors. No copyright assignment is required to contribute to RADIUSS
Docker.

This work was produced under the auspices of the U.S. Department of
Energy by Lawrence Livermore National Laboratory under Contract
DE-AC52-07NA27344.
