# cookiecutter-rt-django

Opinionated CookieCutter template for production-ready Django applications.

## Requirements

```sh
pip install cruft
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

## License

This project is licensed under the terms of the [BSD-3 License](/LICENSE)

## Changelog

Breaking changes are documented in the [CHANGELOG]({{cookiecutter.repostory_name}}/docs/3rd_party/cookiecutter-rt-django/CHANGELOG.md)
