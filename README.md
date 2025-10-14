# cookiecutter-rt-django

Opinionated CookieCutter template for production-ready Django applications.

## Requirements

```sh
pip install cruft ruff
```

## Usage

- Generate a new Cookiecutter template layout:
  ```sh
  cruft create https://github.com/reef-technologies/cookiecutter-rt-django
  ```

- See diff with
  ```sh
  cruft diff
  ```

- Update the project by running
  ```sh
  cruft update
  ```
  Before committing make sure to review changes listed in `docs/3rd_party/cookiecutter-rt-django/CHANGELOG.md`.

- If you have a repo which was initialized without cruft (i.e. with `cookiecutter` command), you can still link the project:
  ```sh
  cruft link https://github.com/reef-technologies/cookiecutter-rt-django
  ```

More on cruft:
<https://github.com/cruft/cruft>

## Automatic cruft updates

This template ships with a GitHub Actions workflow that will periodically (once a week) monitor changes in the template and automatically create a pull request with updates using `cruft`.

### Setup

The workflow requires permissions to create pull requests.
You can enable it by going to Repository Settings -> Actions -> General -> Allow GitHub Actions to create and approve pull requests.

### Slack notifications (optional)

The bot can send notifications to a Slack channel when a new pull request with updates is created.

To enable this, you need to set two secrets in your repository:

- `SLACK_BOT_TOKEN` (the token of your Slack app)
- `SLACK_CHANNEL_ID` (the ID of the channel where you want to receive notifications)

If you don't have a Slack app, follow the [instructions here](https://github.com/slackapi/slack-github-action?tab=readme-ov-file#technique-2-slack-api-method) to create one.

## License

This project is licensed under the terms of the [BSD-3 License](/LICENSE)

## Changelog

Breaking changes are documented in the [CHANGELOG]({{cookiecutter.repostory_name}}/docs/3rd_party/cookiecutter-rt-django/CHANGELOG.md)
