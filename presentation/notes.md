# Priced out of reach: speaker notes

One note per screen of [the deck](index.html), in order.

## Eleven sources, nine counties

We used four of the datathon datasets and joined them with public sources: IRS county migration, Census microdata and commute flows, California layoff notices and state income limits, the Urban Displacement Project typology, and twenty-eight years of San Francisco Planning Commission minutes.

## AI-positioned jobs pay double

AI-related classes advertise up to 1.5 times incumbent pay; exposed classes advertise below it. Because postings are in 2026 dollars and incumbents in 2023 dollars, the ratios below one are even worse in real terms.

## Two channels, two groups outside

White households hold 70.7% of capital income but are under-represented in AI jobs. Asian workers are the mirror image. Black and Hispanic workers sit at about a quarter of parity in both channels. Entry-level postings are not scarcer in exposed jobs, and worker anxiety online is falling.

## Median pay cannot rent here

This is the hinge between jobs and housing. The jobs story does not move people by firing them; it moves them by setting the price of the housing around them.

## A vacancy re-prices the home

California caps rent increases for sitting tenants but not for a vacant unit. In San Francisco one in five turnovers took a unit out of reach for a household at 80% of area median income, while almost none came back. Employers are recruiting the replacements.

## The standard map misses it

The Urban Displacement Project typology is the standard map of displacement risk. A simple logistic model predicted losses far better than its vulnerability flag. After 2018 the flag points the wrong way for price and rent growth, because pressure moved into wealthier tracts.

## Leaving trades rent for burden

Homeownership is the one thing that improves. At the IRS full cost of driving, keeping the Bay Area job usually does not work either. Units low-income households can still rent outside high-cost areas are 1.8 times farther from a clinic.

## Averages cancel; hearings rarely refuse

Lower-income leavers raise the average and younger, smaller arriving households lower it, so a county average shows neither. The Planning Commission sided with staff 97% of the time. Heavy opposition predicts split votes and extra hearings, not refusals.

## Every model fails the vulnerable first

Every model we built, in every workstream, was weakest for the most vulnerable group: renters, people of color, the cheapest units, tenant advocates. That shaped how we built and evaluated the main model.

## Will the next rent cross?

Rent control protects the sitting tenant, not the next one. Features come from all three analysis workstreams. Intended users are acquisition programs like San Francisco Small Sites, tenant groups and right-of-first-refusal outreach.

## Split by time, checked by hand

We keep re-listings from mid-2022, when we have state income limits, and units a low-income household could still afford before the turnover. We train on earlier re-listings, tune on late 2025, and score 2026 exactly once.

## The model beats the legal rule

The standard displacement map scores below a coin flip, because the affordable units most at risk are the last ones in wealthy neighborhoods, sitting just under the line. Most of the model’s power comes from that distance to the line combined with market history.

## Who the model still misses

The model still beats the rule in every group. In apartments and large-landlord buildings it predicts about half the real rate. We show the trade-off of separate lists rather than hide it.

## The model, run forward

Through 2026 the atlas shows what listings recorded; the jump in 2026 is partly because most listings were collected that year. The projection ignores rent resets after a turnover and inherits the under-prediction for apartments, so treat it as a scenario, likely on the low side.

## What did not work

Most of the model’s power is simple arithmetic about how close a unit sits to the affordability line. Use the score to order a list, not as a forecast. Some listings stand for floor plans rather than units.
