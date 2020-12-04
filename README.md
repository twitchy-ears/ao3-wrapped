# ao3-wrapped
A simple and probably buggy version of a "spotify wrapped" but for Archive Of Our Own, shows top tags and fics by scanning your history

So someone showed me a tweet talking about the idea of an Ao3 wrapped script, where it'll show you your top read tags and works over a year, and I was interested by the idea and so gave it a shot and cooked up something basic as I had a quiet evening.

Currently it outputs works (by amount viewed), tags, relationships, characters, fandoms, categories, warnings, ratings, number of fics, kudos left, and total words in all fics.

As an early warning running this will take *a long time*, by default it will load 100 pages of your history (~2000 fics), with a 3 second sleep between each page.  Then it will retrieve the tags from each fic read in the current year, again with a 3 second wait between each one to try and avoid the rate limiter.  So if you have read 2000 fics this year it will take ~5 minutes to load your history and then about 1 hour 40 to retrieve all the tags from those fics and process them for you.  Be very patient.

For Windows installs see the dedicated instructions at the end of the file

# Installation

This is based off the excellent [ao3_api](https://github.com/ArmindoFlores/ao3_api) however that doesn't support history yet, so I wrote [a fork of it](https://github.com/twitchy-ears/ao3_api).

This was written after work on my work machine running python3.8 and its quickly written and a bit hacky, but you'll want to do something like this on a linux machine.  As usual make modifications as required:

```
# First get a real install of the library and hence all the support libraries:
$ python3.8 -m pip install ao3_api

# Then get the local fork with history:
$ git clone https://github.com/twitchy-ears/ao3_api.git -b noisy

# Download the wrapped script itself:
$ git clone https://github.com/twitchy-ears/ao3-wrapped.git
```

# Running it

Read the --help for more options.

Since this is based on a forked version of the ao3_api library you'll need to specify you want to run that fork:

```
$ cd ao3-wrapped
$ PYTHONPATH=../ao3_api ./ao3-wrapped.py --dump-report
```

It will prompt you for your username and password, use these to log into Ao3 and retrieve your history.  It will try not to run afoul of the rate limiter while doing this but no promises.

The report will be to the console but also to a file named "<Username> <datetime>.txt" which will have all the useful output logged in it.

***IMPORTANT:*** If you have read more fic than 100 pages worth then you need to dial up ```--max-history-ages```, this is just there as a basic safeguard to constrain run time.

If you run afoul of the rate limiter then play with the following options:
```
--history-sleep
--max-history-pages
--request-window
--request-amount
--sleep
```

However the history retrieval code and the work details retrieval code *should* know how to cope with failures and retry properly.

# Output

Expect to see something that looks like this:

```
Gathering up tags/works for user Usernamein the year 2020
Retrieving up to 100 pages of history with 3 seconds between each one, please be patient.
Output will be dumped to 'Username_2020-12-04_12-16-14.txt'
Total fics this year found in history: 400
1/400: Retrieving data for '<Work [This was a good fic]>' (viewed 30 times, last: 2020-12-04)
2/400: Retrieving data for '<Work [This fic was okay]>' (viewed 3 times, last: 2020-12-04)
3/400: Retrieving data for '<Work [This fic was alright]>' (viewed 5 times, last: 2020-12-04)
..
etc

---------- RESULTS ----------


---------- Top 10 Works ----------

'This was a good fic' (https://archiveofourown/works/123456): 30
...
etc
```

# Bugs

Sometimes there will be a fic that is restricted in a way that this library cannot read it, this for me only seems to happen to orphaned works.

In this case you'll see:

```
Error: auth error on work <Work [Name of the fic here]> probably restricted, but try to refresh auth token just in case
```

It'll try and refresh your auth and just move on.  It should really retry properly

Since this relies on reading your history there are certain things it will skip, this includes locked collections because it can't retrieve tags from them.


# Windows Installation and running

Okay this is not really my speciality area but you're looking at something
like this (this was written in December 2020 and hence will become less correct over time)

## Short version:

1. Download the ao3-wrapped.zip from the Releases page

2. Unzip it in your Downloads directory

3. Open a terminal Win+R ```cmd```

4. Type this: ```cd Downloads\ao3-wrapped\ao3-wrapped```

5. Type this: ```ao3-wrapped.exe```

6. Wait for it to be done, it will dump a .txt file starting with your username in the Downloads\ao3-wrapped\ao3-wrapped directory.

## Long Version that should definitely work maybe?

1. Visit https://www.python.org/downloads/windows/

2. Look for the line: ```Download Windows x86-64 executable installer``` Under the heading: ```Python 3.8.6 - Sept. 24, 2020``` and click that link, at time of writing that means: https://www.python.org/ftp/python/3.8.6/python-3.8.6-amd64.exe

3. Run the installer, tick the "Add Python 3.8 to PATH" button then click "Install Now"

4. Click the "Disable path length limit" button at the end of the installer then click "close"

5. Win+R ```cmd```

6. Install the real ao3_api library to get its dependencies, so in the command prompt type:    
```pip install ao3_api```

7. Visit https://github.com/twitchy-ears/ao3_api/tree/noisy click the green "Code" button and select "Download zip"

8. Visit https://github.com/twitchy-ears/ao3-wrapped click the green "Code" button and select "Download zip"

9. Unzip both files in your Downloads directory (adjust following commands if your not working in a directory called "Downloads" in your home directory)

10. Back to your command prompt from step 5, steps 11, 12, and 13 are commands to type.

11. ```cd Downloads\ao3-wrapped-main\ao3-wrapped-main```

12. ```set PYTHONPATH=%HOMEDRIVE%%HOMEPATH%\Downloads\ao3_api-master\ao3_api-master```

13. ```python -x ao3-wrapped.py --dump-report```

14. Once it's done look for a text file named after your username and the date you ran the program, it'll contain the output you generated.

If you have more than 100 pages of history for this year you will need to increase the amount loaded with the ```--max-history-pages``` argument.  If for example you have 175 then use:

```python -x ao3-wrapped.py --dump-report --max-history-pages 175```

# Notes

To build your own windows package try
```
python -m pip install pyinstaller
PyInstaller -p %HOMEDRIVE%%HOMEPATH%\Downloads\ao3_api-master\ao3_api-master ao3-wrapped.py
```
