#!/usr/bin/env python3
"""
Set DataDog Downtimes

DESCRIPTION:
Supports delete, get, create/schedule of a downtime via DD API (using datadog python lib/module).
Requires DATADOG_APP_KEY and DATADOG_API_KEY environment variables are set before execution.

https://docs.datadoghq.com/api/?lang=python#api-reference

USAGE:
See -h or --help
Note there is a "raw" option for each subcommand to output ONLY raw JSON if you wish to parse the response.


EXAMPLES:
- CREATE
    Set downtime for Voice Platform services in Production for 60 minutes from time command is run.
    `dd-downtime.py create -s 'environment:prd1,service:voice-platform' -t 60 -m 'Performing upgrade of VP software'`
- DELETE (by ID or scope)
    Delete downtime with ID 1111111
    `dd-downtime.py delete -i 1111111`
    Delete downtime by scope 'environment:prd1,service:voice-platform'
    `dd-downtime.py delete -s 'environment:prd1,service:voice-platform'`
- GET/LIST
    Get particular downtime with ID 1111111
    `dd-downtime.py get -i 1111111`

"""

import argparse
import os
import time
import json
import sys
from datetime import datetime
from datadog import initialize, api


DEFAULT_DOWNTIME_MESSAGE = "Downtime scheduled by CEPSRE"


def main():
    """ main()"""
    parser = argparse.ArgumentParser(
        prog="dd-downtime.py",
        description="Set Datadog downtimes for monitors via DD API.  Supports get, create, delete downtimes.  "
        "Requires DATADOG_APP_KEY and DATADOG_API_KEY environment variables.",
    )
    subparsers = parser.add_subparsers(
        help="The API action to perform", dest="action", required=True
    )
    parser_create = subparsers.add_parser(
        "create",
        help="Create / Schedule Datadog downtime",
    )
    parser_create.add_argument(
        "--scope",
        "-s",
        required=True,
        metavar="scope",
        dest="scope",
        type=str,
        help="Existing datadog scope tag(s) - e.g. 'environment:prd1,service:voice-platform' (required)",
    )
    parser_create.add_argument(
        "--time",
        "-t",
        required=True,
        type=int,
        metavar="minutes",
        dest="minutes",
        help="Downtime 'time' to set in minutes (required)",
    )
    parser_create.add_argument(
        "--message",
        "-m",
        metavar="message",
        dest="message",
        type=str,
        help="The message that appears in the downtime defined in Datadog (optional)",
    )
    parser_create.add_argument(
        "-r",
        "--raw",
        action="store_true",
        dest="raw",
        default=False,
        help="Limit output to raw json output from API response.  Useful if you wish to parse the response.",
    )

    parser_update = subparsers.add_parser(
        "update",
        help="Update existing Datadog downtime",
    )
    parser_update.add_argument(
        "--id",
        "-i",
        required=True,
        metavar="id",
        type=int,
        dest="downtime_id",
        help="Existing datadog downtime ID to update (required)",
    )
    parser_update.add_argument(
        "--scope",
        "-s",
        metavar="scope",
        dest="scope",
        type=str,
        help="Update existing datadog scope tag(s) to these values - e.g. 'environment:prd1,service:voice-platform'",
    )
    parser_update.add_argument(
        "--time",
        "-t",
        type=int,
        metavar="minutes",
        dest="minutes",
        help="Extends (Adds) the specified minutes to the current downtime (extend the downtime by x minutes)",
    )
    parser_update.add_argument(
        "--message",
        "-m",
        metavar="message",
        dest="message",
        type=str,
        help="Update the message that appears in the downtime defined in Datadog",
    )
    parser_update.add_argument(
        "-r",
        "--raw",
        action="store_true",
        dest="raw",
        default=False,
        help="Limit output to raw json output from API response.  Useful if you wish to parse the response.",
    )
    parser_delete = subparsers.add_parser(
        "delete",
        help="Delete Datadog specified downtime",
    )
    parser_delete.add_argument(
        "-r",
        "--raw",
        action="store_true",
        dest="raw",
        default=False,
        help="Limit output to raw json output from API response.  Useful if you wish to parse the response.",
    )
    group = parser_delete.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--scope",
        "-s",
        metavar="scope",
        dest="scope",
        type=str,
        help="Existing datadog scope tag(s) - e.g. 'environment:prd1,service:voice-platform'",
    )
    group.add_argument(
        "--id",
        "-i",
        metavar="id",
        type=int,
        dest="downtime_id",
        help="Existing datadog downtime ID",
    )

    parser_get = subparsers.add_parser(
        "get",
        help="Get/List specified Datadog downtime",
    )
    parser_get.add_argument(
        "--id",
        "-i",
        required=True,
        metavar="id",
        type=int,
        dest="downtime_id",
        help="Existing datadog downtime ID",
    )
    parser_get.add_argument(
        "-r",
        "--raw",
        action="store_true",
        dest="raw",
        default=False,
        help="Limit output to raw json output from API response.  Useful if you wish to parse the response.",
    )
    parser.add_argument("-v", "--version", action="version", version="1.0")
    args = parser.parse_args()
    action = args.action

    try:
        authenticate()
        if action == "create":
            start_time = int(time.time())
            end_time = int(time.time() + (args.minutes * 60))
            message = DEFAULT_DOWNTIME_MESSAGE if args.message is None else args.message
            display_response(
                api.Downtime.create(
                    scope=args.scope,
                    start=start_time,
                    end=end_time,
                    message=message,
                ),
                args,
            )
        elif action == "update":
            body = {}
            if args.scope:
                body["scope"] = args.scope
            if args.minutes:
                # extend end downtime by x minutes
                end = int(api.Downtime.get(args.downtime_id).get("end"))
                body["end"] = int(end + (args.minutes * 60))
            if args.message:
                body["message"] = args.message
            if not body:
                raise ValueError(
                    "\033[31mYou must specify at least one param to update!\033[0m"
                )
            display_response(
                api.Downtime.update(args.downtime_id, **body),
                args,
            )
        elif action == "delete":
            if args.scope:
                display_response(
                    api.Downtime.cancel_downtime_by_scope(scope=args.scope), args
                )
            else:
                display_response(api.Downtime.delete(args.downtime_id), args)
        else:
            display_response(api.Downtime.get(args.downtime_id), args)

    except ValueError:
        raise
    except DataDogAPIError:
        raise


def authenticate():
    """Checks API keys and prepares API auth"""
    # https://github.com/DataDog/datadogpy#environment-variables
    if "DATADOG_API_KEY" not in os.environ or "DATADOG_APP_KEY" not in os.environ:
        raise ValueError(
            "\033[31mDATADOG_API_KEY and DATADOG_APP_KEY env variables not set!\033[0m"
        )
    initialize()


def convert_time(posix_time):
    """ Convert unix/posix time and returns in human readable in UTC """
    # TODO - could convert to local time using fromtimestamp()
    return f"{datetime.utcfromtimestamp(posix_time).strftime('%m-%d-%Y %H:%M:%S')} UTC"


def display_response(response, args):
    """ Display formatted response """
    if not args.raw:
        print(f"\033[33m'{args.action}' DataDog Downtime\033[0m")

    if response is not None:
        if "errors" in response:
            raise DataDogAPIError(args, response)

    # delete will return no response on success
    if args.action == "delete" and response is None:
        if args.downtime_id is not None:
            print(f"\033[32mDowntime with ID [{args.downtime_id}] was deleted.\033[0m")
        if args.scope is not None:
            print(f"\033[32mDowntime with scope [{args.scope}] was deleted.\033[0m")
    else:
        if not args.raw:
            quick_info = {}
            if response.get("active"):
                quick_info["active"] = response.get("active")
            if response.get("id"):
                quick_info["id"] = response.get("id")
            if response.get("start"):
                quick_info["start"] = convert_time(int(response.get("start")))
            if response.get("end"):
                quick_info["end"] = convert_time(int(response.get("end")))
            if response.get("scope"):
                quick_info["scope"] = response.get("scope")
            print(f"\033[32mSummary: {json.dumps(quick_info, indent=2)}\033[0m")
        json.dump(response, sys.stdout)


class DataDogAPIError(SystemExit):
    """
    Custom exception for any datadog error returned by the API
    I am using SystemExit since we are not interested in the stack trace -
    just exiting and displaying the error returned by the API
    """

    def __init__(self, args, response):
        SystemExit.__init__(
            self,
            f"\n\033[31mAn error was returned by Datadog API. Action {args.action} did not succeed!\033[0m"
            if not args.raw
            else "",
        )
        json.dump(response, sys.stdout)


if __name__ == "__main__":
    main()
