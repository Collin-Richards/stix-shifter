import argparse
import sys
from stix_shifter.stix_translation import stix_translation
from stix_shifter.stix_transmission import stix_transmission
import json


TRANSLATE = 'translate'
TRANSMIT = 'transmit'


def __main__():
    """
    Stix-shifter can either be called to either translate or transmit.
    In the case of translation, stix-shifter either translates a stix pattern to a datasource query, 
    or converts data source query results into JSON of STIX observations. 
    Arguments will take the form of...
    "translate" <module> <translate_type (query or results)> <data (STIX pattern or query results)> <options>
    The module and translate_type will determine what module and method gets executed.
    Option arguments comes in as:
      "{
          "select_fields": <string array of fields in the datasource select statement> (In the case of QRadar),
          "mapping": <mapping hash for either stix pattern to datasource or mapping hash for data results to stix observation objects>,
          "result_limit": <integer limit number for max results in the data source query>,
          "timerange": <integer time range for LAST x MINUTES used in the data source query when START STOP qualifiers are absent>
       }"
    In the case of transmission, stix-shifter connects to a datasource to execute queries, status updates, and result retrieval.
    Arguments will take the form of...
    "transmit" <module> '{"host": <host IP>, "port": <port>, "cert": <certificate>}', '{"auth": <authentication>}',
        <
            query <query string>,
            status <search id>,
            results <search id> <offset> <length>,
            ping,
            is_async
        >
    """

    # process arguments
    parent_parser = argparse.ArgumentParser(description='stix_shifter')
    parent_subparsers = parent_parser.add_subparsers(dest='command')

    # translate parser
    translate_parser = parent_subparsers.add_parser(
        TRANSLATE, help='Translate a query or result set using a specific translation module')

    # positional arguments
    translate_parser.add_argument(
        'module', choices=stix_translation.TRANSLATION_MODULES, help='what translation module to use')
    translate_parser.add_argument('translate_type', choices=[
        stix_translation.RESULTS, stix_translation.QUERY], help='what translation action to perform')
    translate_parser.add_argument(
        'data_source', help='STIX identity object representing a datasource')
    translate_parser.add_argument(
        'data', type=str, help='the data to be translated')
    translate_parser.add_argument('options', nargs='?', help='options that can be passed in')

    # optional arguments
    translate_parser.add_argument('-x', '--stix-validator', action='store_true',
                                  help='run stix2 validator against the converted results')
    translate_parser.add_argument('-m', '--data-mapper',
                                  help='module to use for the data mapper')

    # transmit parser
    transmit_parser = parent_subparsers.add_parser(
        TRANSMIT, help='Connect to a datasource and exectue a query...')

    # positional arguments
    transmit_parser.add_argument(
        'module', choices=stix_transmission.TRANSMISSION_MODULES,
        help='choose which connection module to use'
    )
    transmit_parser.add_argument(
        'connection',
        type=str,
        help='Data source connection with host, port, and certificate'
    )
    transmit_parser.add_argument(
        'configuration',
        type=str,
        help='Data source authentication'
    )

    # operation subparser
    operation_subparser = transmit_parser.add_subparsers(title="operation", dest="operation_command")
    operation_subparser.add_parser(stix_transmission.PING, help="Pings the data source")
    query_operation_parser = operation_subparser.add_parser(stix_transmission.QUERY, help="Executes a query on the data source")
    query_operation_parser.add_argument('query_string', help='native datasource query string')
    results_operation_parser = operation_subparser.add_parser(stix_transmission.RESULTS, help="Fetches the results of the data source query")
    results_operation_parser.add_argument('search_id', help='uuid of executed query')
    results_operation_parser.add_argument('offset', help='offset of results')
    results_operation_parser.add_argument('length', help='length of results')
    status_operation_parser = operation_subparser.add_parser(stix_transmission.STATUS, help="Gets the current status of the query")
    status_operation_parser.add_argument('search_id', help='uuid of executed query')
    operation_subparser.add_parser(stix_transmission.IS_ASYNC, help='Checks if the query operation is asynchronous')

    args = parent_parser.parse_args()

    if args.command is None:
        parent_parser.print_help(sys.stderr)
        sys.exit(1)


    if args.command == TRANSLATE:
        options = json.loads(args.options) if bool(args.options) else {}
        if args.stix_validator:
            options['stix_validator'] = args.stix_validator
        if args.data_mapper:
            options['data_mapper'] = args.data_mapper

        translation = stix_translation.StixTranslation()
        result = translation.translate(
            args.module, args.translate_type, args.data_source, args.data, options=options)
    elif args.command == TRANSMIT:
        result = transmit(args) # stix_transmission

    print(result)
    exit(0)


def transmit(args):
    """
    Connects to datasource and executes a query, grabs status update or query results
    :param args:
    args: <module> '{"host": <host IP>, "port": <port>, "cert": <certificate>}', '{"auth": <authentication>}',
    <
        query <query string>,
        status <search id>,
        results <search id> <offset> <length>,
        ping,
        is_async
    >
    """
    connection_dict = json.loads(args.connection)
    configuration_dict = json.loads(args.configuration)
    transmission = stix_transmission.StixTransmission(args.module, connection_dict, configuration_dict)

    operation_command = args.operation_command
    if operation_command == stix_transmission.QUERY:
        query = args.query_string
        result = transmission.query(query)
    elif operation_command == stix_transmission.STATUS:
        search_id = args.search_id
        result = transmission.status(search_id)
    elif operation_command == stix_transmission.RESULTS:
        search_id = args.search_id
        offset = args.offset
        length = args.length
        result = transmission.results(search_id, offset, length)
    elif operation_command == stix_transmission.DELETE:
        search_id = args.search_id
        result = transmission.delete(search_id)
    elif operation_command == stix_transmission.PING:
        result = transmission.ping()
    elif operation_command == stix_transmission.IS_ASYNC:
        result = transmission.is_async()
    else:
        raise NotImplementedError
    return result


if __name__ == "__main__":
    __main__()