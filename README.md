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

### 2. Transform

For caliper we can read the files with [caliper-reader](https://software.llnl.gov/Caliper/pythonreader.html) OR read in .csv output to do the same. We will likely want to read them into some equivalent data structure (e.g., pandas flat table). Here is how to do the transform for caliper files (and other csv) into output directory [tables](tables) (default for `--outdir`)

```bash
$ for filename in $(ls *.cali); do
    python transform-to-long.py ${filename}
done
```

And for the standard csv:

```bash
$ for filename in $(ls *.csv); do
    python transform-to-long.py ${filename} --skip-rows=2
done
```

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
