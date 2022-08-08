# Contract Countdown

A working prototype of a service that allows council officers, journalists, and local climate groups to find and monitor climate-related local authority tenders, in the UK. It uses Contracts Finder ODCS data, via [mysociety/procurement_data](https://github.com/mysociety/procurement_data).

The [original static prototype](https://github.com/mysociety/contract-countdown/tree/8072cbe4eb23c8faca48210100fefde3cef77ce5) was built as part of mySociety’s April 2022 [prototyping week for reducing local authority emissions through procurement](https://www.mysociety.org/2022/02/24/climate-month-notes-february-2022/).

## Development install

You will need [Docker](https://docs.docker.com/desktop/) installed.

Clone the repository:

    git clone git@github.com:mysociety/contract-countdown.git
    cd contract-countdown

Add a `MAPIT_URL` and `MAPIT_API_KEY` to a file at `.env`. You can [get a free MapIt API key here](https://mapit.mysociety.org). A sample `.env` file is provided in `env.sample'.

Start the Docker environment:

    docker-compose up

To load contracts data, get a bash shell inside the `web` container:

    docker-compose exec web bash

Due to a bug, you currently need to create an empty directory at `data/procurement_data`. Inside the shell, run:

    cd data
    mkdir procurement_data
    cd ../

Then, still inside the shell, run:

    ./manage.py import_tenders

The import will take a while!
