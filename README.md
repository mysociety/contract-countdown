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

(If Python complains about missing libraries, chances are the Python requirements have changed since your Docker image was last built. You can rebuild it with, eg: `docker-compose build web`.)

To load contracts data, get a bash shell inside the `web` container:

    docker-compose exec web bash

Due to a bug, you currently need to create an empty directory at `data/procurement_data`. Inside the shell, run:

    cd data
    mkdir procurement_data
    cd ../

The first time round you should run:

    ./manage.py import_councils

which will make sure there's a complete list of UK councils in the app.

Then, still inside the shell, run:

    ./manage.py import_tenders

The import will take a while!

Finally, to import the climate councillors and officers, run:

    ./manage.py import_climate_representatives

For this to work, ensure you have `comeval_councillors.csv` **and** `comeval_officers.csv` in `data/procurement_data`. These can be downloaded from [here](https://github.com/mysociety/comeval-climate-data).
