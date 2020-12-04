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
#import datetime
from datetime import datetime
import time
import getpass
import os
import sys
import argparse
# import pickle
# import readline

parser = argparse.ArgumentParser()
parser.add_argument("-u", "--username", type=str, default=None, help="Username")
parser.add_argument("-p", "--password", type=str, default=None, help="Password")
parser.add_argument("--top-number", type=int, default=10, help="Top N of everything (tags, stories, relationships, etc), default=10")
parser.add_argument("--request-window", type=int, default=60, help="Time window for rate limiter, issue only X requests in this window, default=60")
parser.add_argument("--request-amount", type=int, default=40, help="Number of requests to make in a time window, default=40")
parser.add_argument("--sleep", type=int, default=3, help="Additional sleep between requesting each work for tags, default=3")
parser.add_argument("--history-sleep", type=int, default=3, help="Additional sleep between loading history pages, default=3")
parser.add_argument("--max-history-pages", type=int, default=100, help="Maximum number of pages of history to load, default=100")
parser.add_argument("--rate-limit-pause", type=int, default=180, help="Seconds to wait if rate limited while retrieving tags")
parser.add_argument("--dump-report", action="store_true", default=False, help="Dump report out to a text file")

args = parser.parse_args()

def retrieve_work(workid, session):
    work = None

    while work is None:
        try: 
            work = AO3.Work(workid, session)
        except AO3.utils.HTTPError:
            print(f"Being rate limited, sleeping for {args.rate_limit_pause} seconds then trying again")
            time.sleep(args.rate_limit_pause)
    return work

def thing_counter(thing, place):
    try: 
        place[thing] += 1
        
    # If we don't have 
    except KeyError:
        place[thing] = 1

def meta_thing_counter(place, source):
    for data in source:
        thing_counter(str(data), place)

def top_number_of_thing(thing, label, report_file):
    sorted_data = sorted(thing.items(), key=lambda x: x[1],reverse=True)
    print(f"\n\n---------- Top {args.top_number} {label} ----------\n")
    for data in sorted_data[:args.top_number]:
        print(f"{data[0]}: {data[1]}")

    if report_file is not None:
        with open(report_file, 'a') as f:
            print(f"\n\n---------- Top {args.top_number} {label} ----------\n", file=f)
            for data in sorted_data[:args.top_number]:
                print(f"{data[0]}: {data[1]}", file=f)


if args.username is None:
    args.username = input("Username: ")
if args.password is None:
    args.password = getpass.getpass()

current_year = datetime.today().year

print(f"Gathering up tags/works for user {args.username} in the year {current_year}")
print(f"Retrieving up to {args.max_history_pages} pages of history with {args.history_sleep} seconds between each one, please be patient.")

# If we're outputting a report set that up
report_file = None
if args.dump_report is True:
    time_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    report_file = f"{args.username}_{time_str}.txt"
    if os.path.exists(report_file):
        print(f"Error: report file '{report_file}' already exists")
        exit(1)
    else:
        with open(report_file, 'a') as f:
            print(f"Welcome to your Ao3 Wrapped report for {current_year}, generated at {time_str}", file=f)

if report_file is not None:
    print(f"Output will be dumped to '{report_file}'")


# Login to Ao3
session = AO3.Session(args.username, args.password)
session.refresh_auth_token()

    
#works_cache = {}
#if os.path.exists(args.work_cache_file) and os.stat(args.work_cache_file).st_size > 0:
#    fileio = open(args.work_cache_file, 'rb')
#    works_cache = pickle.load(fileio)
#    fileio.close()

# Attempt to tune the request rates to avoid getting timed out
#AO3.utils.limit_requests(True)
AO3.utils.set_timew(args.request_window)
AO3.utils.set_rqtw(args.request_amount)

# These store the tags and works with numbers of hits against them so
# we can sort by frequency
work_frequency = {}
tag_frequency = {}
relationship_frequency = {}
character_frequency = {}
fandom_frequency = {}
category_frequency = {}
warning_frequency = {}
rating_frequency = {}
total_words = 0

# This was here for debugging to make it only churn through a few fics
max_process = 3
curr_process = 0

# Fetch the history for the session
session.get_history(args.history_sleep,
                    args.max_history_pages,
                    args.rate_limit_pause)

# Now count up how many are in this year
fics_this_year = 0
for entry in session.get_history(0, args.max_history_pages, args.rate_limit_pause):
    date_obj = entry[2]
    if date_obj.year == current_year:
        fics_this_year += 1

print(f"Total fics this year found in history: {fics_this_year}")


# For everything in the history
for entry in session.get_history(0, args.max_history_pages, args.rate_limit_pause):
    curr_process += 1
    work_obj = entry[0]
    num_obj = entry[1]
    date_obj = entry[2]
    
    # if date_obj.year == current_year and curr_process <= max_process:

    # Process if in the current year
    if date_obj.year == current_year:
        try:
            # Get the work details
            work = retrieve_work(work_obj.workid, session)
                
            if work:
                # Print out title, times, date
                print(f"{curr_process}/{fics_this_year}: Retrieving data for '{work}' (viewed {num_obj} times, last: {date_obj.date()})", flush=True)

                # Log the times we visited this work
                work_str = "'{0}' ({1})".format(work.title, work.url)
                work_frequency[work_str] = num_obj

                # Count words
                total_words += work.words

                # Store the rating
                thing_counter(work.rating, rating_frequency)

                # Store just about everything else
                meta_thing_counter(tag_frequency, work.tags)
                meta_thing_counter(relationship_frequency, work.relationships)
                meta_thing_counter(character_frequency, work.characters)
                meta_thing_counter(fandom_frequency, work.fandoms)
                meta_thing_counter(category_frequency, work.categories)
                meta_thing_counter(warning_frequency, work.warnings)
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

top_number_of_thing(work_frequency, 'Works', report_file)
top_number_of_thing(tag_frequency, 'Tags', report_file)
top_number_of_thing(relationship_frequency, 'Relationships', report_file)
top_number_of_thing(character_frequency, 'Characters', report_file)
top_number_of_thing(fandom_frequency, 'Fandoms', report_file)
top_number_of_thing(category_frequency, 'Categories', report_file)
top_number_of_thing(warning_frequency, 'Warnings', report_file)
top_number_of_thing(rating_frequency, 'Ratings', report_file)

print(f"\n\n---------- Total Words Read ----------\n{total_words}")
with open(report_file, 'a') as f:
    print(f"\n\n---------- Total Words Read ----------\n{total_words}", file=f)

# Sort the results
#sorted_tags = sorted(tag_frequency.items(), key=lambda x: x[1],reverse=True)
#sorted_work = sorted(work_frequency.items(), key=lambda x: x[1],reverse=True)
#
#print(f"\n\n---------- Top {args.num_tags} tags ----------\n")
#for data in sorted_tags[:args.num_tags]:
#    print(f"{data[0]}: {data[1]}")
#
#print(f"\n\n---------- Top {args.num_works} works ----------\n")
#for data in sorted_work[:args.num_works]:
#    #work = retrieve_work(data[0])
#    print(f"{work[0]}: {data[1]}")
#    #time.sleep(args.sleep) # Again, don't get rate limited


# Cannot cache the beautiful soup
#sys.setrecursionlimit(500000)
#fileio = open(args.work_cache_file, 'wb')
#pickle.dump(works_cache, fileio)
#fileio.close()

print(f"\nDONE!  Happy {current_year}")
