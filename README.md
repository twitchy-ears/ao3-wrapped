# ao3-wrapped
A simple and probably buggy version of a "spotify wrapped" but for Archive Of Our Own, shows top tags and fics by scanning your history

So someone showed me a tweet talking about the idea of an Ao3 wrapped script, where it'll show you your top read tags and works over a year, and I was interested by the idea and so gave it a shot and cooked up something basic as I had a quiet evening

# Installation

This is based off the excellent [ao3_api](https://github.com/ArmindoFlores/ao3_api) however that doesn't support history yet, so I wrote [a fork of it](https://github.com/twitchy-ears/ao3_api).

This was written after work on my work machine running python3.8 and its quickly written and a bit hacky, but you'll want to do something like this on a linux machine.  As usual make modifications as required:

```
# First get a real install of the library and hence all the support libraries:
$ python3.8 -m pip install ao3_api

# Then get the local fork with history:
$ git clone https://github.com/twitchy-ears/ao3_api.git

# Download the wrapped script itself:
$ git clone https://github.com/twitchy-ears/ao3-wrapped.git
```

# Running it

Since this is based on a forked version of the ao3_api library you'll need to specify you want to run that fork:

```
$ cd ao3-wrapped
$ PYTHONPATH=../ao3_api ./ao3-wrapped.py
```

It will prompt you for your username and password, use these to log into Ao3 and retrieve your history.  It will try not to run afoul of the rate limiter while doing this but no promises, if you have a lot of history this is possible, you may need to tweak the `--request-window`, `--request-amount`, and `--sleep` arguments to be sure you're giving everything time to go slow enough, these lean on the underlying ao3_api library so depends how that's implementing them I've not checked in heavy detail.

# Output

Expect to see something that looks like this:

```
Gathering up tags/works for user UserNameGoesHere in the year 2020
<Work [This was a good fic]> - 30 times - 2020-12-03
<Work [This fic was okay]> - 3 times - 2020-11-30
<Work [This fic was alright]> - 5 times - 2020-11-12
...
etc

---------- RESULTS ----------



---------- Top 10 tags ----------

Fluff: 250
Angry Politics!: 100
Emotional Hurt/Comfort: 60
Angst: 50
Hurt/Comfort: 40
etc.

---------- Top 10 works ----------


<Work [This was a good fic]>: 30
<Work [Also this one]>: 25
<Work [This was groovy]>: 20
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
