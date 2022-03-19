#!/usr/bin/env python3
"""
Transmission Torrent Cleanup
  Cleans up torrents in transmission mathching the provided regular expressions and date range.
"""

__author__ = "Kalen Peterson"
__version__ = "0.1.0"
__license__ = "MIT"

from os import environ
import argparse
from logzero import logger
import time
import re
from transmission_rpc import Client


def findTorrents(tc, searchStrings, prevDayLimit):
    """ 
    Find torrents based on provided filters
    """

    # Get all the torrents
    logger.info("Pulling all torrents from transmission")
    torrents = tc.get_torrents()

    # Find matching torrents
    logger.debug("Searching for torrents over {} days old".format(prevDayLimit))
    old_torrents = []
    for searchString in searchStrings:
        logger.info("Searching for regex {}".format(searchString))
        regex = re.compile(searchString, re.IGNORECASE)

        for torrent in torrents:
            match = regex.match(torrent.name)

            if match:
                timeDiff = ((time.time() - torrent.addedDate) / 86400)

                if timeDiff > prevDayLimit:
                    old_torrents.append(torrent)
                    logger.info("Found torrent: {}".format(match.group()))

    return old_torrents

def deleteTorrents(tc, torrents):
    """ 
    Delete a list of torrents
    """

    for torrent in torrents:
        logger.info("Deleting torrent {}".format(torrent.name))
        tc.remove_torrent(torrent.id, delete_data=True, timeout=None)
        time.sleep(10) # Wait a few seconds so we don't hammer transmission with delete requests


def main(args):
    """ Main entry point of the app """
    logger.info("Starting transmission torrent cleanup")
    logger.debug(args)
    
    # Build the Transmission Client
    tc = Client(
        protocol='https',
        host=args.transmission_host,
        port=args.transmission_port)

    # Find old Torrents
    torrents = findTorrents(
        tc,
        args.cleanup_search_strings,
        args.cleanup_prev_days)

    # Delete the Torrents
    deleteTorrents(tc, torrents)

    logger.info("Finished transmission torrent cleanup")
        

if __name__ == "__main__":
    """ This is executed when run from the command line """
    parser = argparse.ArgumentParser()

    # Transmission Args
    parser.add_argument(
        "--transmission-host",
        default=environ.get("TRANSMISSION_HOST", ""),
        help="IP or hostname of the transmission host")
    parser.add_argument(
        "--transmission-port",
        type=int,
        default=environ.get("TRANSMISSION_PORT", 9091),
        help="Transmission RPC port number (default: 9091)")
    parser.add_argument(
        "--transmission-protocol",
        default=environ.get("TRANSMISSION_PROTOCOL", "http"),
        help="Transmission RPC protocol. Can be http or https (default: http)")


    # Cleanup Args
    parser.add_argument(
        "--cleanup-prev-days",
        type=int,
        default=environ.get("CLEANUP_PREV_DAYS", 90),
        help="Number of days prior to NOW to start deleting torrents (default: 90)")
    parser.add_argument(
        "--cleanup-search-strings",
        nargs='*',
        default=environ.get("CLEANUP_SEARCH_STRINGS", []),
        help="One or more regex strings to filter torrents")
 

    # Specify output of "--version"
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s (version {version})".format(version=__version__))

    args = parser.parse_args()
    main(args)