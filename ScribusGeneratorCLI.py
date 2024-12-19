#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""

=================
Automatic document generation for Scribus.
=================

This fork based on the great job of Ekkehard Will and Berteh!
https://github.com/codfish-zz/ScribusGenerator

Major changes in this fork
# v3.2 (2024-12-19): Support JPG generating with xvfb-run in command line. 
# v3.1 (2024-12-17): Support PDF generating with xvfb-run in command line. 

For further information (manual, description, etc.) please visit:
http://berteh.github.io/ScribusGenerator/

# v3.0 (2022-01-12): Port to Python3 for Scribut 1.5.6+, some features (count, fill)
# v2.0 (2015-12-02): Added features (merge, range, clean, save/load)
# v1.9 (2015-08-03): Initial command-line support (SLA only, use GUI version to generate PDF)

This script is the Command Line ScribusGenerator

=================
The MIT License
=================

Copyright (c) 
2010-2014 Ekkehard Will (www.ekkehardwill.de)
2014-2022 Berteh (https://github.com/berteh/)
2024 codfish-zz (https://github.com/codfish-zz/)

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions: The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

import argparse
import os
import traceback
from ScribusGeneratorBackend import CONST, ScribusGenerator, GeneratorDataObject


parser = argparse.ArgumentParser(
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description="""Generate Scribus (SLA) or PDF documents automatically from external (csv) data.
Mail-Merge-like extension to Scribus.""",
    usage="%(prog)s [options] infiles+",
    epilog="""requirements
    This program requires Python 3.0+

Examples:

%(prog)s my-template.sla
    Generates Scribus (SLA) files for each line of 'my-template.csv'
    by substituting the provides values into 'my-template.sla' to the 
    current directory.

%(prog)s --outDir "/home/user/tmp" example/Business_Card.sla
    Generates Scribus files for each line of example/Business_Card.csv
    in the "/home/user/tmp" subdirectory.

%(prog)s --outName "card-%%VAR_COUNT%%-%%VAR_email%%"  */*.sla
    Generates Scribus files for each sla file in any subdirectory
    that has a csv file with a similar name in the same directory.
    Generated files will have a name constructed from the entry position
    and "email" field, and are stored in their respective sla file directory.

%(prog)s --single -c translations.csv -n doc_  lang/*.sla
    Generates a single Scribus file for each sla file in the lang/ subdirectory
    using all rows of the translations.csv data file.
    Generated files will have a name constructed from the "doc_" prefix
    and the input sla file name.

%(prog)s sample.sla --dataFile data.csv --outName result --formatJpg
    Generates result.jpg for sample.sla using all rows of the data.csv.

%(prog)s sample.sla --dataFile data.csv --outName result --formatPdf
    Generates result.pdf for sample.sla using all rows of the data.csv.

%(prog)s sample.sla --dataFile data.csv --outName result --formatAll
    Generates all type of result files for sample.sla using all rows of the data.csv.

More information: https://github.com/codfish-zz/ScribusGenerator/
""",
)

parser.add_argument(
    "infiles",
    nargs="+",
    help="SLA file(s) to use as template(s) for the generation, wildcards are supported",
)

parser.add_argument(
    "-c",
    "--dataFile",
    default=None,
    help="""CSV/JSON data file containing the data to substitute in each template during generation. 
    Default is scribus source file(s) name with "csv" extension instead of "sla". 
    If csv file is not found, generation from this particular template is skipped.""",
)

parser.add_argument(
    "-d",
    "--csvDelimiter",
    default=CONST.CSV_SEP,
    help='CSV field delimiter character. Default is comma: ","',
)

parser.add_argument(
    "-e",
    "--csvEncoding",
    default=CONST.CSV_ENCODING,
    help="Encoding of the CSV file (default: utf-8)",
)

parser.add_argument(
    "-l",
    "--load",
    action="store_true",
    default=False,
    help="Load generator settings from (each) Scribus input file(s), overloads all options.",
)

parser.add_argument(
    "-m",
    "--merge",
    "--single",
    action="store_true",
    default=False,
    help="Generate a single output file that combines all data rows, for each source file.",
)

parser.add_argument(
    "-n",
    "--outName",
    default=CONST.EMPTY,
    help="""Name of the generated files, with no extension. 
    Default is a simple incremental index. 
    Using SG variables is allowed to define the name of generated documents. 
    Use %VAR_COUNT% as a unique counter defined automatically from the data entry position.""",
)

parser.add_argument(
    "-o",
    "--outDir",
    default=None,
    help="Directory where generated files are stored. Default is the directory of the scribus source file.",
)

parser.add_argument(
    "-q",
    "--imgQuality",
    type=int,
    default=CONST.IMG_QUALITY,
    help="Quality of the generated image file: minimum 1, maximum 100.",
)

parser.add_argument(
    "-s",
    "--save",
    action="store_true",
    default=False,
    help="Save current generator settings in (each) Scribus input file(s).",
)

parser.add_argument(
    "-from",
    "--firstrow",
    default=CONST.EMPTY,
    dest="firstRow",
    help="Starting row of data to merge (not counting the header row), first row by default.",
)

parser.add_argument(
    "-to",
    "--lastrow",
    default=CONST.EMPTY,
    dest="lastRow",
    help="Last row of data to merge (not counting the header row), last row by default.",
)

parser.add_argument(
    "-fa",
    "--formatAll",
    action="store_true",
    default=False,
    help="Generate all types of result files. (scribus SLA, Image and PDF)",
)

parser.add_argument(
    "-fj",
    "--formatJpg",
    action="store_true",
    default=False,
    help="Generate result file in JPG format.",
)

parser.add_argument(
    "-fp",
    "--formatPdf",
    action="store_true",
    default=False,
    help="Generate result file in PDF format.",
)


def ife(condition, if_result, else_result):
    """Utility if-then-else syntactic sugar"""
    if condition:
        return if_result

    return else_result


def main():
    # Defaults
    outDir = os.getcwd()
    format = CONST.FORMAT_SLA

    args = parser.parse_args()

    # Create outDir if needed
    if args.outDir is not None:
        outDir = args.outDir
        os.makedirs(outDir, exist_ok=True)

    if args.formatJpg:
        format = CONST.FORMAT_JPG
    elif args.formatPdf:
        format = CONST.FORMAT_PDF
    elif args.formatAll:
        format = CONST.FORMAT_ALL

    # Collect the settings
    dataObject = GeneratorDataObject(
        dataSourceFile=ife(not (args.dataFile is None), args.dataFile, CONST.EMPTY),
        outputDirectory=outDir,
        outputFileName=args.outName,
        outputFormat=format,
        imgQuality=args.imgQuality,
        keepGeneratedScribusFiles=CONST.TRUE,
        csvSeparator=args.csvDelimiter,
        csvEncoding=args.csvEncoding,
        singleOutput=args.merge,
        firstRow=args.firstRow,
        lastRow=args.lastRow,
        saveSettings=args.save,
    )

    generator = ScribusGenerator(dataObject)

    log = generator.get_log()
    log.debug(
        "ScribusGenerator is starting generation for %s template(s)."
        % (str(len(args.infiles)))
    )

    for infile in args.infiles:
        dataObject.setScribusSourceFile(infile)

        if args.load:
            saved = generator.get_saved_settings()

            if saved:
                dataObject.loadFromString(saved)
                log.info("Settings loaded from %s:" % (os.path.split(infile)[1]))

            else:
                log.warning(
                    "Could not load settings from %s. using arguments and defaults instead"
                    % (os.path.split(infile)[1])
                )

        if dataObject.getDataSourceFile() is CONST.EMPTY:
            # Default data file is <template-sla>.csv
            dataObject.setDataSourceFile(os.path.splitext(infile)[0] + ".csv")

        if not (
            os.path.exists(dataObject.getDataSourceFile())
            and os.path.isfile(dataObject.getDataSourceFile())
        ):
            log.warning(
                "Data file [%s] for [%s] not found, skip this template."
                % (dataObject.getDataSourceFile(), os.path.split(infile)[1])
            )
            continue

        # Default outDir is template dir
        if dataObject.getOutputDirectory() is CONST.EMPTY:
            dataObject.setOutputDirectory(os.path.split(infile)[0])

            if not os.path.exists(dataObject.getOutputDirectory()):
                log.info(
                    "Creating output directory: %s" % (dataObject.getOutputDirectory())
                )
                os.makedirs(dataObject.getOutputDirectory())

        if dataObject.getSingleOutput() and (len(args.infiles) > 1):
            dataObject.setOutputFileName(args.outName + "__" + os.path.split(infile)[1])

        log.info(
            "Generating all files for %s in directory %s"
            % (os.path.split(infile)[1], dataObject.getOutputDirectory())
        )

        try:
            generator.run()
            log.info("Scribus Generation completed. Congrats!")
        except ValueError as e:
            log.error(
                "\nError: Could not replace variable with value, please check your data file. Details: %s\n\n"
                % e
            )
            traceback.print_exc()
        except IndexError as e:
            log.error(
                "\nError: Could not find the value for variable, please check your data file. Details: %s\n\n"
                % e
            )
            traceback.print_exc
        except Exception:
            log.error("\nError: " + traceback.format_exc())
            traceback.print_exc


if __name__ == "__main__":
    main()
