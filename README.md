# mastodon-scripts

Some scripts using the mastodon api.

The scripts need a valid config file with your twitter API keys (get them at developer.twitter.com.) in a config.ini file (see config_sample.ini for an example).

- export_all_toots.py : Exports all toots from one or several users in xlsx format.

## Requirements

- pandas

## Installation of the virtualenv with pipenv (recommended)

```
pipenv install
```

You can then launch any script with

```
pipenv run python export_all_tweets.py -h
```
