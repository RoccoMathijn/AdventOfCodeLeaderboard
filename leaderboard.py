#!/usr/bin/env python
'''
This script will grab the leaderboard from Advent of Code and post it to Slack
'''
# pylint: disable=wrong-import-order
# pylint: disable=C0301,C0103,C0209

import os
import datetime
import sys
import json
import requests

LEADERBOARD_ID = os.environ.get('LEADERBOARD_ID')
SESSION_ID = os.environ.get('SESSION_ID')
SLACK_WEBHOOK = os.environ.get('SLACK_WEBHOOK')

# If the ENV Var hasn't been set, then try to load from local config.
# Simply create secrets.py with these values defined.
# See README for more detailed directions on how to fill these variables.
if not all([LEADERBOARD_ID, SESSION_ID, SLACK_WEBHOOK]):
    from secrets import LEADERBOARD_ID, SESSION_ID, SLACK_WEBHOOK

# You should not need to change this URL
LEADERBOARD_URL = "https://adventofcode.com/{}/leaderboard/private/view/{}".format(
        datetime.datetime.today().year,
        LEADERBOARD_ID)


def formatLeaderMessage(members):
    """
    Format the message to conform to Slack's API
    """
    message = ""

    # add members with at least one star to message
    members = filter(lambda member: member[2] > 0, members) 
    medals = [':third_place_medal:', ':second_place_medal:', ':trophy:']
    for username, score, stars in members:
        if medals:
            medal = ' ' + medals.pop()
        else:
            medal = ''
        message += f"{medal}*{username}* {score} Points, {stars} Stars\n"

    message += f"\n<{LEADERBOARD_URL}|View Leaderboard Online>"

    return message


def parseMembers(members_json):
    """
    Handle member lists from AoC leaderboard
    """
    # get member name, score and stars
    members = [(m["name"],
                m["local_score"],
                m["stars"]
                ) for m in members_json.values()]

    # sort members by score, descending
    members.sort(key=lambda s: (-s[1], -s[2]))

    return members

def parseTimes(members_json):
  day_of_aoc = datetime.datetime.today().strftime("%-d")
  daily_scores = [(m["name"],m["completion_day_level"].get(day_of_aoc)) for m in members_json.values() if m["completion_day_level"].get(day_of_aoc)]
  return daily_scores

def format_part1(times):
  start_time = datetime.datetime.fromisoformat('{}-12-{} 05:00:00+00:00'.format(datetime.datetime.today().year, datetime.datetime.today().strftime("%d"))).timestamp()
  message = "First star"
  scores = [(scores[0], scores[1]["1"]["get_star_ts"]) for scores in times]
  scores_sorted = sorted(scores, key = lambda tup: tup[1])
  with_place = enumerate(scores_sorted)
  for (i, scores) in with_place:
    duration = scores[1] - start_time
    message += "\n{:0>2}) {:0>8} {}".format(i+1, str(datetime.timedelta(seconds=duration)), scores[0])
  return message

def format_part2(times):
  start_time = datetime.datetime.fromisoformat('{}-12-{} 05:00:00+00:00'.format(datetime.datetime.today().year, datetime.datetime.today().strftime("%d"))).timestamp()
  message = "Second star"
  scores = [(scores[0], scores[1]["2"]["get_star_ts"], scores[1]["1"]["get_star_ts"]) for scores in times if scores[1].get("2")]
  scores_sorted = sorted(scores, key = lambda tup: tup[1])
  with_place = enumerate(scores_sorted)
  for (i, scores) in with_place:
    duration = scores[1] - start_time
    delta = scores[1] - scores[2]
    message += "\n{:0>2}) {:0>8} {} (+{})".format(i+1, str(datetime.timedelta(seconds=duration)), scores[0], datetime.timedelta(seconds=delta))
  return message

def postMessage(message):
    """
    Post the message to to Slack's API in the proper channel
    """
    payload = json.dumps({
        "icon_emoji": ":christmas_tree:",
        "username": "Advent Of Code Leaderboard",
        "text": message
    })

    requests.post(
        SLACK_WEBHOOK,
        data=payload,
        timeout=60,
        headers={"Content-Type": "application/json"}
    )


def main():
    """
    Main program loop
    """
    # make sure all variables are filled
    if LEADERBOARD_ID == "" or SESSION_ID == "" or SLACK_WEBHOOK == "":
        print("Please update script variables before running script.\n\
                See README for details on how to do this.")
        sys.exit(1)

    # retrieve leaderboard
    r = requests.get(
        "{}.json".format(LEADERBOARD_URL),
        timeout=60,
        cookies={"session": SESSION_ID}
    )
    if r.status_code != requests.codes.ok:  # pylint: disable=no-member
        print("Error retrieving leaderboard")
        sys.exit(1)

    # get members from json
    members = parseMembers(r.json()["members"])
    times = parseTimes(r.json()["members"])

    # generate message to send to slack
    message = formatLeaderMessage(members)
    
    day = datetime.datetime.today().strftime("%-d")
    if (int(day) < 26):
        daymessage = 'Day ' + day + ':'
        part1 = format_part1(times)
        part2 = format_part2(times)
        message = message + '\n\n' + daymessage + '\n\n' + part1 + '\n\n' + part2
    
    # send message to slack
    postMessage(message)


if __name__ == "__main__":
    main()
