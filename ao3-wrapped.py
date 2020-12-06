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
import atexit
import pickle
# import readline

parser = argparse.ArgumentParser()
parser.add_argument("-u", "--username", type=str, default=None, help="Username")
parser.add_argument("-p", "--password", type=str, default=None, help="Password")
parser.add_argument("--year", type=int, default=None, help="Set the year, otherwise current")
parser.add_argument("--top-number", type=int, default=10, help="Top N of everything (tags, stories, relationships, etc), default=10")
parser.add_argument("--only-kudos", action="store_true", default=False, help="Only process fics you have left kudos for")
parser.add_argument("--request-window", type=int, default=60, help="Time window for rate limiter, issue only X requests in this window, default=60")
parser.add_argument("--request-amount", type=int, default=40, help="Number of requests to make in a time window, default=40")
parser.add_argument("--sleep", type=int, default=3, help="Additional sleep between requesting each work for tags, default=3")
parser.add_argument("--history-sleep", type=int, default=3, help="Additional sleep between loading history pages, default=3")
parser.add_argument("--start-history-page", type=int, default=1, help="Start reading on this history page, default 1, can be used with --max-history-pages and --year to select a range")
parser.add_argument("--max-history-page", type=int, default=100, help="Maximum number of pages of history to load, default=100")
parser.add_argument("--rate-limit-pause", type=int, default=180, help="Seconds to wait if rate limited while retrieving tags")
parser.add_argument("--no-dump-report", action="store_true", default=False, help="Dump report out to a text file")
parser.add_argument("--just-dump-history", action="store_true", default=False, help="Just dump out the history page contents")
parser.add_argument("--state-file", type=str, default="current-state.pickle", help="File that stores current counter states so that if the run fails half way through it can pick back up again, default 'current-state.pickle'")

args = parser.parse_args()
args.start_history_page -= 1 # This thing is zero indexed
args.max_history_page -= 1  # This thing is zero indexed
number_of_pages_of_history = (args.max_history_page - args.start_history_page) + 1

def retrieve_work(workid):
    work = None

    while work is None:
        try:
            work = AO3.Work(workid, None, True)                
        except AO3.utils.HTTPError:
            print(f"Being rate limited, sleeping for {args.rate_limit_pause} seconds then trying again")
            time.sleep(args.rate_limit_pause)
    return work

def session_create(username, password):
    session = None
    while session is None:
        try:
            session = AO3.Session(username, password)
        except AO3.utils.HTTPError:
            print(f"Being rate limited, sleeping for {args.rate_limit_pause} seconds then trying again")
            time.sleep(args.rate_limit_pause)
    return session


def session_refresh(session):
    succeeded = None
    while succeeded is None:
        try:
            session.refresh_auth_token()
            succeeded = True

        except AO3.utils.HTTPError:
            print(f"Being rate limited, sleeping for {args.rate_limit_pause} seconds then trying again")
            time.sleep(args.rate_limit_pause)

    return session


def left_kudos_p(work, username):
    small_kudos = work._soup.find('p', {'class': 'kudos'})
    if small_kudos is not None: 
        for a in small_kudos.find_all("a"):
            if a.attrs["href"] == f"/users/{username}":
                # print(f"User '{username}' has left kudos on work {work.title} | {work.url}")
                return True;

    big_kudos = work._soup.find('span', {'class': 'kudos_expanded hidden'})
    if big_kudos is not None:
        for a in big_kudos.find_all("a"):
            if a.attrs["href"] == f"/users/{username}":
                # print(f"User '{username}' has left kudos on work {work.title} | {work.url}")
                return True;

    return False;
    

def thing_counter(thing, place):
    try: 
        place[thing] += 1
        
    # If we don't have 
    except KeyError:
        place[thing] = 1

def meta_thing_counter(place, source):
    for data in source:
        thing_counter(str(data), place)

def output_terminal_and_file(thing, report_file):
    print(thing)
    if report_file is not None:
        with open(report_file, 'a', encoding="utf-8") as f:
            print(thing, file=f)
        
        
def top_number_of_thing(thing, label, report_file):
    sorted_data = sorted(thing.items(), key=lambda x: x[1],reverse=True)
    output_terminal_and_file(f"\n\n---------- Top {args.top_number} {label} ----------\n", report_file)
    for data in sorted_data[:args.top_number]:
        output_terminal_and_file(f"{data[0]}: {data[1]}", report_file)


if args.username is None:
    args.username = input("Username: ")
if args.password is None:
    args.password = getpass.getpass()

current_year = datetime.today().year
if args.year:
    current_year = args.year

print(f"Gathering up tags/works for user {args.username} in the year {current_year}")
print(f"Retrieving up to {number_of_pages_of_history} pages of history with {args.history_sleep} seconds between each one, please be patient.")

# If we're outputting a report set that up
report_file = None
if args.no_dump_report is False or args.just_dump_history is True:
    time_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    report_file = f"{args.username}_{time_str}.txt"
    if os.path.exists(report_file):
        print(f"Error: report file '{report_file}' already exists")
        sys.exit(1)
    else:
        with open(report_file, 'a') as f:
            print(f"Welcome to your Ao3 Wrapped report for {current_year}, generated at {time_str}", file=f)

if report_file is not None:
    print(f"Output will be dumped to '{report_file}'")


# Login to Ao3
session = session_create(args.username, args.password)
session_refresh(session)

# Attempt to tune the request rates to avoid getting timed out
AO3.utils.set_timew(args.request_window)
AO3.utils.set_rqtw(args.request_amount)

# These store the tags and works with numbers of hits against them so
# we can sort by frequency
workids_seen = []
work_frequency = {}
tag_frequency = {}
author_frequency = {}
relationship_frequency = {}
character_frequency = {}
fandom_frequency = {}
category_frequency = {}
warning_frequency = {}
rating_frequency = {}
total_words = 0
left_kudos = 0

# This was here for debugging to make it only churn through a few fics
max_process = 3
curr_process = 0


def store_state():
    global workids_seen
    global work_frequency
    global tag_frequency
    global author_frequency
    global relationship_frequency
    global character_frequency
    global fandom_frequency
    global category_frequency
    global warning_frequency
    global rating_frequency
    global total_words
    global left_kudos
    #global curr_process

    sys.setrecursionlimit(10000)
    
    print(f"Something went wrong, dumping state to '{args.state_file}'")
    if os.path.exists(args.state_file):
        print(f"Removing existing state file...")
        os.unlink(args.state_file)
    with open(args.state_file, 'wb') as f:
        pickle.dump(workids_seen, f)
        pickle.dump(work_frequency, f)
        pickle.dump(tag_frequency, f)
        pickle.dump(author_frequency, f)
        pickle.dump(relationship_frequency, f)
        pickle.dump(character_frequency, f)
        pickle.dump(fandom_frequency, f)
        pickle.dump(category_frequency, f)
        pickle.dump(warning_frequency, f)
        pickle.dump(rating_frequency, f)
        pickle.dump(total_words, f)
        pickle.dump(left_kudos, f)
        #pickle.dump(curr_process, f)

def restore_state():
    global workids_seen
    global work_frequency
    global tag_frequency
    global author_frequency
    global relationship_frequency
    global character_frequency
    global fandom_frequency
    global category_frequency
    global warning_frequency
    global rating_frequency
    global total_words
    global left_kudos
    #global curr_process

    if os.path.exists(args.state_file):
        print(f"Restoring state from '{args.state_file}'")
        with open(args.state_file, 'rb') as f:
            workids_seen = pickle.load(f)
            work_frequency = pickle.load(f)
            tag_frequency = pickle.load(f)
            author_frequency = pickle.load(f)
            relationship_frequency = pickle.load(f)
            character_frequency = pickle.load(f)
            fandom_frequency = pickle.load(f)
            category_frequency = pickle.load(f)
            warning_frequency = pickle.load(f)
            rating_frequency = pickle.load(f)
            total_words = pickle.load(f)
            left_kudos = pickle.load(f)
            #curr_process = pickle.load(f)


# Fetch the history for the session
session.get_history(args.history_sleep,
                    args.start_history_page,
                    args.max_history_page,
                    args.rate_limit_pause)

# Now count up how many are in this year
fics_this_year = 0
for entry in session.get_history(0, args.start_history_page, args.max_history_page, args.rate_limit_pause):
    work_obj = entry[0]
    num_obj = entry[1]
    date_obj = entry[2]
    if date_obj.year == current_year:
        if args.just_dump_history is True:
            print(f"{work_obj} - {num_obj} - {date_obj.date()}")
        fics_this_year += 1

print(f"Total fics this year found in history: {fics_this_year}")

# If we're exiting early then just bail out
if args.just_dump_history is True:
    sys.exit(0)

# Before we exit dump state
atexit.register(store_state)

skip_to_fic = None
if os.path.exists(args.state_file):
    restore_state()

# For everything in the history
for entry in session.get_history(0, args.start_history_page, args.max_history_page, args.rate_limit_pause):
    curr_process += 1

    work_obj = entry[0]
    num_obj = entry[1]
    date_obj = entry[2]
    
    # if date_obj.year == current_year and curr_process <= max_process:

    # Process if in the current year
    if date_obj.year == current_year:
        processed_something = False # Controls sleep
        
        try:
            # If we're doing a skip because of a restore then bail
            if work_obj.workid in workids_seen:
                print(f"{curr_process}/{fics_this_year}: Skipping data for '{work_obj}' (viewed {num_obj} times, last: {date_obj.date()}) - restoring", flush=True)
                raise Exception("restore skipping")

            # print(f"{work_obj.workid} not in {workids_seen}")
            
            
            # Get the work details
            work = retrieve_work(work_obj.workid)

            if work:
                processed_something = True # We got something so sleep
            
                # check for kudos
                has_left_kudos = False
                if left_kudos_p(work, args.username):
                    left_kudos += 1
                    has_left_kudos = True

                if args.only_kudos is True and has_left_kudos is not True:
                    print(f"{curr_process}/{fics_this_year}: Skipping data for '{work}' (viewed {num_obj} times, last: {date_obj.date()}, word-count: {work.words}) - no kudos", flush=True)
                    raise Exception("no kudos left")
                
                # Print out title, times, date
                print(f"{curr_process}/{fics_this_year}: Retrieving data for '{work}' (viewed {num_obj} times, last: {date_obj.date()}, word-count: {work.words})", flush=True)

                # Log the times we visited this work
                work_str = "'{0}' ({1})".format(work.title, work.url)
                work_frequency[work_str] = num_obj

                # Count words
                total_words += work.words

                # kudos
                if left_kudos_p(work, args.username):
                    left_kudos += 1
                    
                # Store the rating
                thing_counter(str(work.rating), rating_frequency)

                # Store just about everything else
                meta_thing_counter(tag_frequency, work.tags)
                meta_thing_counter(author_frequency, map(lambda x: x.username, work.authors))
                meta_thing_counter(relationship_frequency, work.relationships)
                meta_thing_counter(character_frequency, work.characters)
                meta_thing_counter(fandom_frequency, work.fandoms)
                meta_thing_counter(category_frequency, work.categories)
                meta_thing_counter(warning_frequency, work.warnings)

                workids_seen.append(work_obj.workid)

            else:
                print(f"{work} - {date_obj.date()}")
                print(f"Error: Couldn't retrieve work data")

        # If we see an AuthError its probably a restricted work of
        # some kind that doesn't let us view it.
        except AO3.utils.AuthError:
            print(f"Error: auth error on work {work_obj} probably restricted")
            #session_refresh(session)
            
        except Exception as e:
            if e == 'no kudos left':
                pass
            elif e == 'restore skipping':
                pass

        # Add an extra sleep after the work to try and avoid the rate limiter
        if processed_something is True:
            time.sleep(args.sleep)

    elif args.year is not None:
        print(f"{curr_process}/{fics_this_year}: Ignoring, not in {current_year}: {work_obj} - {num_obj} - {date_obj.date()}")

print("\n\n---------- RESULTS ----------\n")

top_number_of_thing(work_frequency, 'Works', report_file)
top_number_of_thing(tag_frequency, 'Tags', report_file)
top_number_of_thing(author_frequency, 'Authors', report_file)
top_number_of_thing(relationship_frequency, 'Relationships', report_file)
top_number_of_thing(character_frequency, 'Characters', report_file)
top_number_of_thing(fandom_frequency, 'Fandoms', report_file)
top_number_of_thing(category_frequency, 'Categories', report_file)
top_number_of_thing(warning_frequency, 'Warnings', report_file)
top_number_of_thing(rating_frequency, 'Ratings', report_file)


output_terminal_and_file(f"\n\n---------- Fics This Year ----------\n{fics_this_year}", report_file)

output_terminal_and_file(f"\n\n---------- Left Kudos ----------\n{left_kudos}", report_file)

output_terminal_and_file(f"\n\n---------- Total Words Read ----------\n{total_words}", report_file)

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

# Successful process, in which case we don't need to store state,
# remove any we have already stored.
atexit.unregister(store_state)
if os.path.exists(args.state_file):
    os.unlink(args.state_file)
