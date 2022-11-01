#!/usr/bin/env python3

import argparse
import re
import sys
import os
import pandas
import caliperreader as cr


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


class BaseTransformer:
    def init_df(self):
        """
        Ensure we are using a common data frame structure.

        This formats into a long data frame that has two generic dimensions.
        """
        return pandas.DataFrame(columns=["path", "annotation", "dim1", "dim2", "value"])


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
        "--outdir",
        help="output directory for data frame",
        default=os.path.join(os.getcwd(), "tables"),
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

    # Show args to the user
    print("  filename: %s" % args.filename)
    print("    outdir: %s" % args.outdir)

    if not os.path.exists(args.outdir):
        os.makedirs(args.outdir)
    t = get_transformer(args.filename)

    kwargs = {"skip_rows": args.skip_rows, "annotations": args.annotations}
    df = t.to_df(args.filename, **kwargs)
    outfile = "%s.tranformed.csv" % os.path.join(
        args.outdir, os.path.basename(args.filename)
    )
    df.to_csv(outfile, index=False)


if __name__ == "__main__":
    main()
