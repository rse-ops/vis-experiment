#!/usr/bin/env python3


import argparse
import re
import sys
import os
import pandas
import hatchet as ht
import caliperreader as cr
from grafanalib.core import Dashboard
from grafanalib._gen import DashboardEncoder
from glob import glob
import json


from grafanalib.core import (
    Dashboard,
    Graph,
    OPS_FORMAT,
    Row,
    single_y_axis,
    Target,
    TimeRange,
    YAxes,
    YAxis,
)


here = os.path.dirname(os.path.abspath(__file__))
default_outdir = os.path.join(here, "dashboards")


def read_file(filename):
    """
    Read content from file
    """
    with open(filename, "r") as fd:
        content = fd.read()
    return content


def get_transformer(filename):
    if filename.endswith("cali"):
        return CaliperTransformer()
    return TabularTransformer()


def write_json(obj, outfile):
    with open(outfile, "w") as fd:
        fd.write(json.dumps(obj, indent=4))


class BaseTransformer:
    def init_df(self):
        """
        Ensure we are using a common data frame structure.

        This formats into a long data frame that has two generic dimensions.
        """
        return pandas.DataFrame(columns=["path", "annotation", "dim1", "dim2", "value"])

    def get_flamegraph(self, *args, **kwargs):
        raise NotImplementedError

    def save_json_dashboard(self, filename, outfile, **kwargs):
        """
        Generate grafana json dashboard
        """
        df = self.to_df(filename, **kwargs)


def get_dashboard_json(dashboard, overwrite=False, message="Updated by grafanlib"):
    """
    get_dashboard_json generates JSON from grafanalib Dashboard object
    :param dashboard - Dashboard() created via grafanalib
    dashboard = Dashboard(
           title="Python generated dashboard",
             rows=[
                 Row(panels=[
                    Graph(
                       title="Prometheus http requests",
                       dataSource='default',
                       targets=[
                  Target(
                    expr='rate(prometheus_http_requests_total[5m])',
                    legendFormat="{{ handler }}",
                    refId='A',
                  ),
              ],
              yAxes=single_y_axis(format=OPS_FORMAT),
          ),
        ]),
    ]

    # grafanalib generates json which need to pack to "dashboard" root element
    #return json.dumps(
    #    {
    #       "dashboard": dashboard.to_json_data(),
    #       "overwrite": overwrite,
    #       "message": message
    #   }, sort_keys=True, indent=2, cls=DashboardEncoder)
    """
    return


class TabularTransformer(BaseTransformer):
    def get_separator(self, filename):
        """
        Ensure we read a file based on an extension we know
        """
        _, ext = os.path.splitext(filename)
        ext = ext.lower()
        if ext not in [".tsv", ".csv"]:
            sys.exit(f"Extension {ext} is not yet supported! Please open an issue.")
        if ext == ".csv":
            return ","
        if ext == ".tsv":
            return "\t"

    def to_df(self, filename, skip_rows=0, index_col=None, annotations=None, **kwargs):
        """
        Transform pandas to long data frame.
        """
        df = self.init_df()
        sep = self.get_separator(filename)
        annotations = annotations or ""

        records = pandas.read_csv(
            filename, sep=sep, engine="python", skiprows=skip_rows, index_col=index_col
        )
        # We hope file ending is known separator

        idx = 0
        for row in records.iterrows():
            metric = row[0]
            for key, value in row[1].items():
                key = key.strip()
                if isinstance(value, str):
                    value = value.strip()
                if not key and value in [None, ""]:
                    continue
                df.loc[idx, :] = [filename, annotations, metric, key, value]
                idx += 1
        return df


class CaliperTransformer(BaseTransformer):
    def get_flamegraph(self, filename_glob, **kwargs):
        """
        Get a flamegraph structure in the form of a pandas dataframe.
        """
        filenames = glob(filename_glob, recursive=True)
        fg = {}
        fg = {"children": [], "name": "root"}

        def add_node(node, parent_pointer):
            name, value = get_node_flamegraph_entry(gf, node, metric)
            new_node = {"name": name, "value": value}
            if node.children:
                new_node["children"] = []
            parent_pointer["children"].append(new_node)
            return new_node

        for filename in filenames:

            # This currently generates a flamegraph for one file - we could extend this to multiple
            reader = cr.CaliperReader()
            reader.read(filename)
            gf = ht.GraphFrame.from_caliperreader(reader)
            metric = kwargs.get("metric") or gf.default_metric
            parent_pointer = fg

            # This is how hatchet generates the graph data (assumed one root?)
            for root in gf.graph.roots:

                # Keep going until no mode to parse (assume no shared children)
                nodes = [(root, parent_pointer)]
                while nodes:
                    node, parent_pointer = nodes.pop(0)
                    new_node = add_node(node, parent_pointer)
                    for child in node.children:
                        nodes.append((child, new_node))

        # Get total value for root
        total_value = 0
        for child in fg.get("children", []):
            total_value += child["value"]

        fg["value"] = total_value
        return fg


def get_node_flamegraph_entry(
    gf, node, metric, name="name", rank=0, thread=0, threshold=0.0
):
    """
    Get the path and value for a node to add to the flamegraph
    """
    callpath = node.path()
    index_names = gf.dataframe.index.names
    entry_name = ""

    for i in range(0, len(callpath) - 1):
        if "rank" in index_names and "thread" in index_names:
            df_index = (callpath[i], rank, thread)
        elif "rank" in index_names:
            df_index = (callpath[i], rank)
        elif "thread" in index_names:
            df_index = (callpath[i], thread)
        else:
            df_index = callpath[i]
        entry_name += str(gf.dataframe.loc[df_index, "name"]) + "; "

    if "rank" in index_names and "thread" in index_names:
        df_index = (callpath[-1], rank, thread)
    elif "rank" in index_names:
        df_index = (callpath[-1], rank)
    elif "thread" in gf.dataframe.index.names:
        df_index = (callpath[-1], thread)
    else:
        df_index = callpath[-1]
    entry_name += gf.dataframe.loc[df_index, "name"] + "; "

    if "rank" in index_names and "thread" in index_names:
        df_index = (node, rank, thread)
    elif "rank" in index_names:
        df_index = (node, rank)
    elif "thread" in index_names:
        df_index = (node, thread)
    else:
        df_index = node
    value = gf.dataframe.loc[df_index, metric]
    return entry_name, value

    def to_df(self, filename, **kwargs):
        """
        Transform caliper to pandas data frame.
        """
        reader = cr.CaliperReader()
        reader.read(filename)
        df = self.init_df()

        idx = 0
        for rec in reader.records:
            path = rec.get("path", "UNKNOWN")
            labels = rec.get("annotation", "")
            if isinstance(path, list):
                path = os.sep.join(path)
            if isinstance(labels, list):
                labels = "|".join(labels)
            for key, value in rec.items():
                if key in ["path", "annotation"]:
                    continue
                key = reader.attribute(key).get("attribute.alias")
                df.loc[idx, :] = [path, labels, key, None, value]
                idx += 1
        return df


def get_parser():
    parser = argparse.ArgumentParser(
        description="Caliper To Pandas Data Frame Transformer",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "filename", help="input filename .cali (caliper file) or tabular to transform"
    )
    parser.add_argument(
        "--filename-glob",
        help="glob to match multiple files (e.g., *.cali) for caliper files for hatchet flamegraph",
        default="*.cali",
    )
    parser.add_argument(
        "--csv",
        help="save to tabular format",
        default=False,
        action="store_true",
    )
    parser.add_argument(
        "--flamegraph",
        help="generate hatchet flame graph",
        default=False,
        action="store_true",
    )
    parser.add_argument(
        "--outdir",
        help="output directory for data frame",
        default=os.path.join(os.getcwd(), "dashboards"),
    )
    parser.add_argument(
        "--skip-rows",
        help="Number of rows to skip for tabular data",
        default=0,
        type=int,
    )
    parser.add_argument(
        "--annotations", help="pipe (|) separated list of annotations (no spaces)"
    )
    return parser


def main():

    parser = get_parser()

    # If an error occurs while parsing the arguments, the interpreter will exit with value 2
    args, extra = parser.parse_known_args()

    # If no custom output directory provided, switch between tables/dashboard
    if args.csv and args.outdir == default_outdir:
        args.outdir = os.path.join(here, "tables")
    if args.flamegraph and args.outdir == default_outdir:
        args.outdir = os.path.join(here, "flamegraph")

    # Show args to the user
    print("  filename: %s" % args.filename)
    print("    outdir: %s" % args.outdir)

    if not os.path.exists(args.outdir):
        os.makedirs(args.outdir)
    t = get_transformer(args.filename)

    kwargs = {"skip_rows": args.skip_rows, "annotations": args.annotations}
    if args.csv:
        df = t.to_df(args.filename, **kwargs)
        outfile = "%s.tranformed.csv" % os.path.join(
            args.outdir, os.path.basename(args.filename)
        )
        df.to_csv(outfile, index=False)
        return

    elif args.flamegraph:
        fg = t.get_flamegraph(args.filename_glob)
        outfile = os.path.join(args.outdir, "combined.flamegraph.json")
        write_json(fg, outfile)
        return

    # Otherwise generate a dashboard json
    outfile = "%s.tranformed.json" % os.path.join(
        args.outdir, os.path.basename(args.filename)
    )
    t.save_json_dashboard(args.filename, **kwargs)


if __name__ == "__main__":
    main()
