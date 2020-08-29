#!/usr/bin/env python3

# Copyright (c) 2020, Reef Technologies, BSD 3-Clause License

import shutil


def main():
    shutil.move('.env-dev.template', '.env-dev')
    shutil.move('.env-prod.template', '.env-prod')


if __name__ == '__main__':
    main()
