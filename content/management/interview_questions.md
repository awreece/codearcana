Title: 5 graceful questions to avoid a toxic engineering team
Date: 2018-04-17
Tags: opinion, interviewing

While interviewing at a potential company, the engineer evaluating you asks the
obligatory "Any questions for me?". What do you ask?

Some might be tempted to follow a checklist like the
[Joel Test](https://www.joelonsoftware.com/2000/08/09/the-joel-test-12-steps-to-better-code/)[^1],
but I prefer to ask questions that allow me to be more diplomatic when probing
a company's values:

[^1]: I have a preference for this [updated Joel Test](https://myers.io/2017/04/04/the-joel-test-for-2017/), but I still don't find it perfect (in particular, I think it assumes the organization is a certain size).

## Can you show me a non-trivial code review?

In my favorite opening question, I immediately seem innocent and
curious while asking the engineer to show me something they are proud of. 
I maintain this demeanor while asking all future questions -- the interviewer
will be evaluating me on my questions, so I want to sound friendly with no
ulterior motives.

But this question jumps directly to the heart of the engineering culture:

 - How are disputes settled, e.g. about code style? Does the "highest paid
   person's opinion" win? Are people friendly or are does the company allow
   ["brilliant jerks"](http://www.brendangregg.com/blog/2017-11-13/brilliant-jerks.html)?
 - How are the tests? Are they automated in a CI system? Are flaky tests tracked?
   Does the review add more tests? Was it expected to? 
 - Does someone maintain the health of the build and test system?

I normally like to ask this question of a junior engineer who is less likely to
override the company culture with their own personality. I do need to be careful
when asking follow up questions because I do not want to come off
as critical.

## How was your on-boarding?

In this question, I want to seem supportive and eager to start. I want to know:

 - Were you thrown in the fire or was there a training process? Was there good
   documentation and tools?
 - How long were you mentored? What was the ongoing relationship between you
   and your manager?
 - Are there non-HR trainings available for senior people?

Again, this question is most effective when you can ask a junior person who 
recently was on-boarded. It is important to not come off as entitled when
asking this question.
 
## What is the weirdest bug that you have worked on in the past year?

In this question, my goal is to elicit a good war story so I can evaluate:

 - How was it addressed in the short term? In the long term?
 - Do people actually debug issues or do they just work around them?
 - Do people root-cause non-reproducible issues?

This question is better to ask of a senior person who is likely to have seen
a spectrum of issues and the long-term consequences of fixes to them.

## Can you talk about the last engineer who got promoted (not to management)?

The goal of this question is to understand what qualities the company actually
values.

 - Were they friendly and helpful when working with other engineers?
 - How did they start working on their projects? Is project assignment political?
 - Is there a culture of recognizing talented individual contributors?

Again, I like to ask a senior engineer this question because they are more
likely to have seen the history of the engineer in question. This question does
not work with exceptionally small companies that have not promoted engineers.

## Can you show me how you track the status of your next release?

Here I want to understand the health of the engineering organization.

 - How do you measure the health of your engineering organization?
 - How do you decide what projects to prioritize?
 - How does the culture change near the end of the release?

This question is most effective when asked of a senior engineer or even a
manager who would be thinking about release health. Be careful when asking
this question of exceptionally small companies -- they might not have a release
dashboard and you do not want to shame them.

## Key takeaways

Keep a friendly and playful spirit and under no circumstances allow 
the interviewer to feel bad; remember they are evaluating you for culture
fit too!

The goal is answer important questions about the company culture without being 
offensive. These questions allow you to gracefully probe the values of an
engineering organization.

