#!/usr/bin/env python

import praw
import re
from sys import exit
from datetime import date
import logging

log = logging.getLogger('regotw')
logging.basicConfig(level=logging.DEBUG)

from AccountDetails import UID, PASS


if __name__ == '__main__':
    live = False
    wiki_page = 'game_of_the_week'

    if live:
        subreddit = 'boardgames'
    else:
        subreddit = 'phil_s_stein'


    reddit = praw.Reddit('Game of the Week reposter for r/boardgames')
    reddit.login(username=UID, password=PASS)
    
    if live:
        gotw = bg.get_wiki_page(wiki_page)
        matches = re.findall('(\d{4}-\d{2}-\d{2}) : \[(\w+)\]\(/(\w+)\)', gotw.content_md)
        if not matches:
            log.critical('Unable to find GOTW links in wiki page {}'.format(wiki_page))
            exit(1)
    else: 
        matches = [
            ('2014-09-10', 'Agricola', '138ueo'),
            ('2012-09-27', 'Mage Knight', '140at7'),
            ('2010-01-01', 'Xyxxy: the game', 'XXX999')
        ]

    # games are [ ['YYYY-MM-DD', 'game name', 'gotw url'], ... ]
    # make first data point into python date class instance.
    games = [list(x) for x in matches]
    for game in games:
        y, m, d = game[0].split('-')
        try:
            game[0] = date(int(y), int(m), int(d))
            if game[0].month == 2 and game[0].day == 29:   # feb 29th == march 1
                game[0] = date(game[0].year, 3, 1)
        except ValueError:
            log.critical('Unable to parse date input from wiki: {}'.format(game[0]))
            exit(1)
    
    # sort by date. (It's not clear this gets us much.)
    games = sorted(games)
    log.debug('sorted games: {}'.format(games))

    today = date.today()
    try:
        two_years_ago = date(today.year-2, today.month, today.day)
    except ValueError:   # triggered for feb 29th
        two_years_ago = date(today.year-2, today.month+1, 1)

    log.debug('2 years ago: {}'.format(two_years_ago))

    for game in games:
        if game[0] < two_years_ago:
            log.debug('found GOTW older than two years: {}'.format(game[1]))
        elif game[0] == two_years_ago:
            log.debug('found two year old GOTW. Reposting {} GOTW post'.format(game[1]))
            break
        else:
            log.debug('no GOTW from two years ago. Next GOTW repost is {} on {}'.format(
                game[1], game[2]))
            exit(0)

    gotw_post = reddit.get_submission(submission_id=game[2], comment_limit=0)
    search_str = '\\[//]: # \\(GOTWS\\)\n(.+)\\[//]: # \\(GOTWE\\)\n'
    m = re.search(search_str, gotw_post.selftext, flags=re.DOTALL)
    if not m:
        log.critical('Unable to find post body or body separator flags ([//]: # (GOTWS)...')
        exit(1)

    # figure suffix for the day for header inclusion.
    if 4 <= game[0].day <= 20 or 24 <= game[0].day <= 30:
        suffix = "th"
    else:
        suffix = ["st", "nd", "rd"][game[0].day % 10 - 1]

    repost_header = '''
Note: {} was Game of the Week on /r/boardgames [two years ago today](/{}). This GoTW repost gives people of the sub a chance to discuss the game again after a bit of time has passed. Do you still play it? If so, how often does it make it to the table? Has the game held up after repeated plays? Has it moved up or down in your personal ranking? Has it been replaced by a newer, similar game? Has it replaced a game?

Below is [the original Game of the Week post](/{}) from {}:

------------------

'''.format(game[1], game[2], game[2], game[0].strftime('%B %d{}, %Y'.format(suffix)))

    repost_text = repost_header + m.group(1).encode('utf-8')
    log.debug('Reposting this GOTW text:\n{}'.format(repost_text))

    title = 'Game of the From Two Years Ago This Week: {}'.format(game[1])
    repost = reddit.submit(subreddit, title, text=repost_text)
    repost.distinguish(as_made_by='mod')

