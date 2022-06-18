import argparse
import logging
import os
from datetime import datetime
import itertools

import requests

logger = logging.getLogger(__name__)
MSG_TEMPLATE = "*{timestamp}*\n{author}\n{changelog}"
# In case deploy is done manually we don't know what was the version of last deployment
# so printing fixed amount of commit messages
COMMITS_TO_TAKE = 5


class SlackNotifier:
    URL = "https://slack.com/api/chat.postMessage"

    def __init__(self, token: str, channel: str):
        if not channel or not token:
            raise Exception("Missing token or channel. Make sure your .env file is fine")

        self.token = token
        self.channel = channel

    def notify(self, text):
        logger.info(f"Sending message to channel {self.channel}")
        response = requests.post(
            self.URL,
            data={
                "text": text,
                "channel": self.channel,
                "token": self.token,
            },
        )
        response.raise_for_status()


def get_deployment_author():
    return os.environ.get("sender") or "Deployed manually"


def get_deployment_changelog(changelog, parse=True):
    if not parse:
        return changelog

    before_sha = os.environ.get("before")
    all_commits = [c.split(",") for c in changelog.split("\n")]
    if before_sha:
        commits = itertools.takewhile(lambda c: c[1] == before_sha, all_commits)
    else:
        commits = all_commits[:COMMITS_TO_TAKE]
    return "\n".join(c[1] for c in commits)


def get_message(changelog):
    return MSG_TEMPLATE.format(
        timestamp=datetime.now().replace(microsecond=0),
        author=get_deployment_author(),
        changelog=changelog,
    )


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-c",
        "--channel",
        action="store",
        dest="channel",
        help="Slack channel should be send notification to. Remember about preceding '#'",
    )
    parser.add_argument(
        "-m",
        "--message",
        action="store",
        dest="message",
        required=True,
        help="Message to send",
    )
    parser.add_argument(
        "-p",
        "--parse",
        action=argparse.BooleanOptionalAction,
        help="Parse message first. It's used during the deploy to parse `git log` output",
    )
    return parser.parse_args()


if __name__ == "__main__":
    parser_result = parse_arguments()
    token = os.environ.get("SLACK_TOKEN") or ""
    channel = parser_result.channel or os.environ.get("SLACK_CHANNEL") or ""
    slack_notifier = SlackNotifier(token, channel)
    changelog = get_deployment_changelog(parser_result.message, parser_result.parse)
    slack_notifier.notify(get_message(changelog))
