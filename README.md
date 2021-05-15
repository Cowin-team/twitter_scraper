# Cowin Twitter Scraper

## Installation

    bash install.sh 

## Running the script

- Set the environment variable "BEARER_TOKEN" to the twitter account API token.  Email me for credentials if you require

      export BEARER_TOKEN="Bearer AAAAsfjlsdfljsldjssdfsddddddddddddddddddddddddddddfsjslfdjsljdlfsj"`

- Run the API service

      cd src
      uwsgi --yaml app.yaml
