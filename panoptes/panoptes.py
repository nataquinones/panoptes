#!/usr/bin/env python

from panoptes.app import app
from argparse import ArgumentParser, RawTextHelpFormatter
import sys
import os


def main():
    __doc__ = "panoptes: monitor computational workflows in real-time"

    parser = ArgumentParser(
        description=__doc__,
        formatter_class=RawTextHelpFormatter
    )

    parser.add_argument(
        "--ip",
        dest="ip",
        help="Set the IP of the panoptes server [Default: 0.0.0.0]",
        default="0.0.0.0",
        required=False
    )

    parser.add_argument(
        "--port",
        dest="port",
        help="The port of the server [Default: 5000]",
        default="5000",
        required=False
    )
    parser.add_argument('--log',
                        metavar='path',
                        default=os.getcwd(),
                        type=str,
                        help='Specify the path for the log files to be read. (default: cwd)')

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        dest="verbose",
        default=False,
        required=False,
        help="Be Verbose"
    )

    args = parser.parse_args()

    # add to config and message about --log option
    app.config['LOG_FOLDER'] = args.log
    if args.log == os.getcwd():
        print(f"The --log argument was not provided. Using {args.log} as default.")

    app.run(host=args.ip,
            port=args.port)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        sys.stderr.write("User interrupt!\n")
        sys.exit(0)
