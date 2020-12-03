#!/usr/bin/python3.8

# First get all the support libraries:
# $ python3.8 -m pip install ao3_api
# 
# Then get the local fork with history:
# $ git clone https://github.com/twitchy-ears/ao3_api.git
#
# Download the wrapped script itself:
# $ git clone https://github.com/twitchy-ears/ao3-wrapped.git
#
# And run it:
# $ cd ao3-wrapped
# $ PYTHONPATH=../ao3_api ./ao3-wrapped.py

import AO3
import datetime
import time
import getpass
import os
import argparse
# import readline

parser = argparse.ArgumentParser()
parser.add_argument("-u", "--username", type=str, default=None, help="Username")
parser.add_argument("-p", "--password", type=str, default=None, help="Password")
parser.add_argument("--num-tags", type=int, default=10, help="Top N tags")
parser.add_argument("--num-works", type=int, default=10, help="Top N works")
parser.add_argument("--request-window", type=int, default=60, help="Time window for rate limiter, issue only X requests in this window")
parser.add_argument("--request-amount", type=int, default=40, help="Number of requests to make in a time window")
parser.add_argument("--sleep", type=int, default=3, help="Additional sleep between requesting each work for tags")
args = parser.parse_args()

if args.username is None:
    args.username = input("Username: ")
if args.password is None:
    args.password = getpass.getpass()

current_year = datetime.datetime.today().year

print(f"Gathering up tags/works for user {args.username} in the year {current_year}")

session = AO3.Session(args.username, args.password)
session.refresh_auth_token()

# Attempt to tune the request rates to avoid getting timed out
#AO3.utils.limit_requests(True)
AO3.utils.set_timew(args.request_window)
AO3.utils.set_rqtw(args.request_amount)

# These store the tags and works with numbers of hits against them so
# we can sort by frequency
tag_frequency = {}
work_frequency = {}

# This was here for debugging to make it only churn through a few fics
max_process = 3
curr_process = 0

# For everything in the history
for entry in session.get_history():
    curr_process += 1
    work_obj = entry[0]
    num_obj = entry[1]
    date_obj = entry[2]
    
    # if date_obj.year == current_year and curr_process <= max_process:

    # Process if in the current year
    if date_obj.year == current_year:
        try:
            # Get the work details
            work = AO3.Work(work_obj.workid)
            if work:
                # Print out title, times, date
                print(f"{work} - {num_obj} times - {date_obj.date()}", flush=True)
                # Log the times we visited this work
                work_frequency[work_obj.workid] = num_obj

                # Log the tags
                for tag in work.tags:
                    tag_str = str(tag)

                    # There must be a better way but I'm rushing this
                    try: 
                        tag_frequency[tag_str] += 1

                    # If we don't have 
                    except KeyError:
                        tag_frequency[tag_str] = 1
            else:
                print(f"{work} - {date_obj.date()}")
                print(f"Error: Couldn't retrieve work tags")

        # If we see an AuthError its probably a restricted work of
        # some kind that doesn't let us view it.
        except AO3.utils.AuthError:
            print(f"Error: auth error on work {work_obj} probably restricted, but try to refresh auth token just in case")
            session.refresh_auth_token()

        # Add an extra sleep after the work to try and avoid the rate limiter
        time.sleep(args.sleep)


print("\n\n---------- RESULTS ----------\n")

# Sort the results
sorted_tags = sorted(tag_frequency.items(), key=lambda x: x[1],reverse=True)
sorted_work = sorted(work_frequency.items(), key=lambda x: x[1],reverse=True)

print(f"\n\n---------- Top {args.num_tags} tags ----------\n")
for data in sorted_tags[:args.num_tags]:
    print(f"{data[0]}: {data[1]}")

print(f"\n\n---------- Top {args.num_works} works ----------\n")
for data in sorted_work[:args.num_works]:
    work = AO3.Work(data[0])
    print(f"{work}: {data[1]}")
    time.sleep(args.sleep) # Again, don't get rate limited
