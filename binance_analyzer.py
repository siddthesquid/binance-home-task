import pprint
from types import GeneratorType

import simplejson as json

from sidd.binance.cmdinterface import get_parser


def main():
    parser = get_parser()
    args = parser.parse_args()
    _print(args.handler(args), args.pretty)


def _print(to_print, pretty=False):
    # Sort of an ugly hack here for the time being, as we don't know whether we are getting back a dict or
    # an infinite generator
    if isinstance(to_print, GeneratorType):
        for item in to_print:
            _print(item, pretty)
    else:
        to_print = json.dumps(to_print)
        if pretty:
            pprint.PrettyPrinter(indent=2).pprint(to_print)
        else:
            print(to_print)


if __name__ == "__main__":
    main()
