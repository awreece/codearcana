Title: A review of <em>Winning with Data</em>
Date: 2018-04-11
Tags: opinion

On the advice of a former colleague, I recently read [Winning with Data: Transform Your Culture, Empower Your People, and Shape the Future](https://smile.amazon.com/Winning-Data-Transform-Culture-Empower-ebook/dp/B01G9FLALC) by Tomasz Tunguz and Frank Bien.

This book was a bunch of just-so stories about how companies used a data-driven methodology (via Looker) to improve their business. It also mixed in some unrelated stuff; e.g. how to do pitches. I found this quite underwhelming, but here were some interesting quotes.

## Quotes

> Brutal intellectual honesty aims to slay the HIPPO, or the highest-paid person's opinion, as the determining factor of the direction of a project, team, or company. Left unmitigated, this management artifact wreaks disastrous consequences on companies.

This is particularly relevant to companies that try to bring a more data driven approach to decision making and might have to counter traditional decision making. I think this was a place where there was a lot of potential for more interesting exploration: how do you convince a team to switch to a data driven culture (e.g. the old school scouts in Moneyball).

> “What decisions would that analysis inform?”

When being asked to do some involved/length analysis, make sure the result would have real business impact.

> Upworthy's use of attention minutes, rather than the traditional cost per thousand impressions, as a metric for charging advertisers aligns the incentives of readers, journalists, and advertisers.

The use of derived measures here reminds me of the use of “risk tolerance” by the google SRE teams https://landing.google.com/sre/book/chapters/embracing-risk.html

> The Z score is determined by the desired p-value / confidence interval. Let's choose an 80 percent confidence interval. The Z score is 1.28.
>
> The standard of deviation is measured on a scale from 0 to 1. Most people use 0.5 since it is the most forgiving value and will generate the largest sample size.
>
> The margin of error is also called the confidence interval.
>
> $$ SampleSize = \frac{ZScore^2 * StandardOfDeviation * (1 -
StandardOfDeviation)}{MarginOfError^2} $$

A convenient formula to compute required sample size for a statistically
relevant study.
 
> Their analysis showed 10 slides is the optimal length for fundraising pitches:
>
> *Company Purpose*: the mission or goal of the business
>
> *Problem*: the complication with the status quo that creates the opportunity for the business to pursue
>
> *Solution*: the company's proposed idea to resolve the problem
>
> *Why Now*: why should this idea succeed now, when no one has succeeded with it before?
>
> *Market Size*: if the business were to succeed, how valuable could it be?
>
> *Product*: typically, a demonstration of the product or images of the technology
>
> *Team*: the members of the founding and executive team, often including key advisors and investors
>
> *Business Model*: an overview of the business' pricing strategy and unit economics.
>
> *Competition*: a description of the alternatives and substitutes and how the startup intends to differentiate itself
>
> *Financials*: a pro-forma profit and loss projection of the business. In Docsend's analysis, investors spend the most time on this slide to understand the long-term profitability of the business and the amount of capital required to sustain the company.
 
I think this list of 10 slides is likely to be good for nearly any pitch, including for internal presentation.
