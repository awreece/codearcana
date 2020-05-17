Title: A review of <em>Drift Into Failure</em>
Date: 2016-03-02
Tags: reviews

On the advice of a former colleague, I recently read [_Drift into Failure: From Hunting Broken Components to Understanding Complex Systems_](http://smile.amazon.com/Drift-into-Failure-Components-Understanding-ebook/dp/B009KOKXKY) by Sidney Dekker. 

## An overview of _Drift into Failure_

By examining several recent disasters (ranging from the Challenger explosion to the housing market collapse of 2008), Dekker contends that root cause analysis is an inherently flawed strategy for understanding failures of large complicated systems (e.g. the NASA bureaucracy or Wall Street). Dekker believes that a single faulty component cannot be held to blame for these failures. Competing pressures (e.g. budget, publicity) can allow complicated systems to tolerate increasing levels of risk over time, leading to a slow "drift into failure" where no one component can be held truly responsible.

Dekker eventually proposes several ways to avoid this drift. He says that "high reliability organizations" tend to exhibit the following 4 characteristics:

> - Senior management commitment to safety
> - Shared care and concern for hazards and a willingness to learn and understand how they impact people
> - Realistic and flexible norms and rules about hazards
> - Continual reflection on practice through monitoring, analysis, and feedback systems

The last point is the most nuanced. Since organizations will evolve over time, it is important that they continually reflect on how they are changing to ensure they evolve in the best direction for the long term health of the organization.

This kind of reflection is _hard_ for most organizations and Dekker offers some interesting suggestions for how to do it. First, he emphasizes that senior management must support this kind reflection and commitment. He then suggests:

> Rotating personnel from different places (but similar operations) for shorter periods can in principle be done in a variety of worlds. It represents an important lever for assuring the kind of diversity that can make small steps visible and open for discussion.

During these discussions, Dekker says:

> The questions we should reflect on (even if we may not get clear answers) are two-fold: why did this happen, and why are we surprised that it happened? The first question is about the workings of the complex system and its environment. The second is about our (lack of) understanding of those workings.

In addition, Dekker recommends that organizations give authority to all levels of an organization. He cites the example of the nuclear aircraft carrier:

> Even the lowest ranking individual on the deck of an aircraft carrier has the authority (and in indeed the duty) to suspend immediately any take-off or landing that might pose unnecessary risk.

Lastly, he suggests that systems can use this tendency to evolve to push themselves towards safety. Rather than compliance and regulation, he suggests that

> complex systems should have a co-evolver/counter evolver.

This is an entity that is aware of the complexity of the organization (and will evolve with it) and strives to push the organization in a different direction than it would locally optimize for. Dekker doesn't mention it, but I think Netflix's [Chaos Monkey](http://techblog.netflix.com/2012/07/chaos-monkey-released-into-wild.html) is the perfect example of this.

## A wrap up

Overall, the book was fascinating but hard to read. Unfortunately, Dekker uses very complex language that usually muddles his argument rather than refining it. This confusion was exacerbated by the fact that he only starts proposing solutions in the last chapter. I ended up writing this review because I wanted to share the ideas of the book with other people but wasn't convinced they would read through it.

## Do startups have a moral imperative not to fail?

One of the things that really struck me in the book was that it implicitly assumed that these systems had a moral imperative not to fail. For a mine or airline, where human lives are at stake, that case is "easier" to argue; however, I feel like that is not a core tenet of many web startups. In some sense, the motto "move fast break things" seems like a deliberate acknowledgment that there is no moral imperative to avoid failure.
