# About

A Discord bot for another project on this Github, FumoCam.

## If slow to start/shutdown/restart:

There is a strange issue with discord.py and pynacl that leads it to hang in some cases. Running `poetry run pip install pynacl -I --no-binary pynacl` after the standard `poetry install` should fix any issues.

# Functions (and items to manually test):

## Farewell Messages

- Sends a farewell message to the configured channel when a Discord member leaves the guild

## Invite Logging

- When someone joins, compares last known invite mapping to invite map after they joined, and sends a message indicating what invite was used and who's invite it was, or if its a pre-mapped invite from the config file it displays a custom message instead. (This feature also works for one-use invites)

## Media Rating

- If a media file is detected in pre-configured channels, a "thumbs up" and "thumbs down" (configurable) reaction is added to the message to allow members to vote on the media. **This also works for most embedded media that isn't traditionally available through Discord API, such as Twitter**

## Suggestions

- Based on a pre-configured set of channels and prefix, a message starting with the prefix in one channel (human channel) will be reposted in another, bot-only channel in a format that shows the author, the message, attached images and adds configurable upvote/downvote emojis.
- Since the user will not be able to delete messages from another person on Discord (the bot), they are given a 30 second window in the "human" channel to press a configurable reaction emoji on a "confirmation" message. If they click it, the suggestion and confirmation are deleted, a "deletion confirmation" is sent, and shortly after deleted. If they don't click it, the confirmation is deleted after 30 seconds and the suggestion becomes permanant.

## Message Logging

- A robust message logging system that logs all server messages (including threads) to a local SQLite database
- Logs `message_id`, `utc_time`, `channel_id`, `author_id`, and `message_content`
- In a JSON object, the `extra_data` DB column can contain
  - What message this message is replying to
  - URL, file name and content type of any attachments
  - Fully reconstructable Embed data
  - ID, name, format, and URL of any stickers used
- Assesses if no data exists for a channel/server and queues a full scrape of all applicable channels
- While scraping, any incoming messages are withheld from the scrape and added after, to avoid mixed data, missing data, and race conditions
- On reboot, scans all available channels and intelligently scrapes only messages it has missed since it has been offline
