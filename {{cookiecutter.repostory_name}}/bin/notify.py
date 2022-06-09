import argparse
import os
from datetime import datetime

import requests

msg_template = "*{timestamp}*\n{author}\n{changelog}"


class SlackNotifier:
    url = "https://slack.com/api/chat.postMessage"

    def __init__(self, token, channel):
        if not channel or not token:
            raise Exception("Missing token or channel")

        self.token = token
        self.channel = channel

    def notify(self, text):
        print(f"Sending message to channel {self.channel}")
        r = requests.post(
            self.url,
            data={
                "text": text,
                "channel": self.channel,
                "token": self.token,
            },
        )
        r.raise_for_status()


def get_deployment_author():
    return os.environ.get("sender") or "Deployed manually"


def get_deployment_changelog():
    # for now it's just message of last commit when deployed with github action
    return os.environ.get("commit_msg") or ""


def get_message():
    return msg_template.format(
        timestamp=datetime.now().replace(microsecond=0),
        author=get_deployment_author(),
        changelog=get_deployment_changelog(),
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
        default=get_message(),
        dest="message",
        help="Message to send",
    )
    return parser.parse_args()


if __name__ == "__main__":
    parser_result = parse_arguments()
    token = os.environ.get("SLACK_TOKEN")
    channel = parser_result.channel or os.environ.get("SLACK_CHANNEL")
    slack_notifier = SlackNotifier(token, channel)
    slack_notifier.notify(parser_result.message)
