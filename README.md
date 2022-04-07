# Contract Countdown

A prototype built as part of mySociety’s April 2022 [prototyping week for reducing local authority emissions through procurement](https://www.mysociety.org/2022/02/24/climate-month-notes-february-2022/).

## Use it online

Visit <https://mysociety.github.io/contract-countdown>.

All modern browsers are supported. Internet Explorer is not. See `.browserlistrc` for details.

## Running locally

Requirements:

- [Ruby](https://www.ruby-lang.org/en/documentation/installation/)
- [Bundler](https://bundler.io/#getting-started)

Install all dependencies and get a local server running immediately, in one command:

    script/server

The site will be available at both <http://localhost:4000> and <http://0.0.0.0:4000>.

If you want to serve locally over SSL (recommended) then generate self-signed SSL certificates with:

    script/generate-ssl-certificates

Once the SSL certificates are in place, `script/server` will serve the site over HTTPS, at both <https://localhost:4000> and <https://0.0.0.0:4000>. (You will need to tell your web browser to accept the self-signed certificate.)

You can build the site to `_site` (without serving it) with:

    script/build

## Data

`_data/uk_contracts_finder.csv` was generated from [Open Data Services’ SQLite copy of the UK Contacts Finder database](https://ocds-downloads.opendata.coop/source/uk_contracts_finder), with the following SQL query:

```sql
select
  tender._link_release as release_id,
  tender.title as tender_title,
  tender.description as tender_description,
  tender_items.classification_id,
  tender_items.classification_description,
  buyer.name as buyer_name,
  awards.value_amount,
  printf("%,d", awards.value_amount) as value_human,
  awards.value_currency,
  awards.contractPeriod_startDate,
  awards.contractPeriod_endDate,
  Cast ((
    JulianDay(awards.contractPeriod_endDate) - JulianDay(awards.contractPeriod_startDate)
  ) As Integer) as contract_length_days,
  Cast ((
    ( JulianDay(awards.contractPeriod_endDate) - JulianDay(awards.contractPeriod_startDate) ) / 30
  ) As Integer) as contract_length_months,
  Cast ((
    JulianDay(awards.contractPeriod_endDate) - JulianDay('now')
  ) As Integer) as contract_expires_days_from_now,
  Cast ((
    ( JulianDay(awards.contractPeriod_endDate) - JulianDay('now') ) / 30
  ) As Integer) as contract_expires_months_from_now,
  (
    JulianDay(awards.contractPeriod_endDate) - JulianDay('now') ) / ( JulianDay(awards.contractPeriod_endDate) - JulianDay(awards.contractPeriod_startDate)
  ) as contract_time_remaining_fraction
from
  tender,
  tender_items,
  buyer,
  awards
where
  buyer._link_release = tender._link_release
  and awards._link_release = tender._link_release
  and tender_items._link_release = tender._link_release
  and buyer.name LIKE '%council%'
  and (
    tender_items.classification_id like '09%' -- Fuel and energy
    or tender_items.classification_id like '555%' -- Catering
    or tender_items.classification_id = '90000000' -- Sewage, refuse, cleaning and environmental
    or tender_items.classification_id like '904%' -- Sewage
    or tender_items.classification_id like '905%' -- Refuse and waste
  )
  and date(awards.contractPeriod_startDate) < date('now')
  and date(awards.contractPeriod_endDate) > date('now')
order by
  contract_expires_days_from_now ASC, awards.contractPeriod_startDate ASC
```