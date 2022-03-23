Title: An Ideal Platform Experience
Tags: platform
Date: 2022-03-23

I've thought a while about the vision for Platform orgs. In short, my opinion
is that 
Platform orgs should prioritize making an incredible user experience.
Unfortunately, they frequently target making a very customizable experience at
the expense of making an enjoyable one -- they target making AWS when they
should make something easier than Heroku. 

The net result of this focus is that
sometimes product engineers find themselves needing (and missing) systems
domain expertise to configure and deploy their code. Eventually, these orgs 
usually reach towards  embedded devops engineers who act as a professional 
services org and fill 
the gap between product engineers and tools that require too much context to
be used by the product engineers.

I believe that Platform orgs can avoid all this pain if they focus at the 
beginning on making an incrediable developer experience and use that as their
north star. With a sufficiently good focus on developer experience, maybe there
is no need for pure devops?

Below is an alternative potential vision for how
to make a great platform experience.

##  Edit code

Ernie the Engineer picks up a new issue from the ticket tracking system to work on. 

Ernie creates a new branch on their local machine, write some code, and then want to run their code. They click a button in their IDE to create an ephemeral environment deployed into staging with all the dependencies of their service, attach their IDE as a remote debugger to their code while streaming the logs back to the IDE, and open their browser pointing to their new service. Since they are attached as with a remote debugger, they can quickly edit code and have it be automatically redeployed to the remote environment.

They play around with the code to get it working, add some tests, and then push a new button in their IDE to create a draft code review by pushing their code to a new branch and opening the draft in their browser. The code review tool has suggested a template for the description and suggested some authors based on what files Ernie was editing. Ernie writes the description, links to the issue from the ticket tracking system, and then publishes the code for review by other engineers.

Immediately after hitting publish, the code review system quietly starts to perform tests in the background. First it builds a packaged artifact and runs unit tests, then deploys the packaged artifact to a new ephemeral environment(s) and runs a set of integration tests (and in some cases, performance tests). If something goes wrong with the build or the tests, a short snippet of the error is posted and a link to the testing tool to get more information (or re-run the test with a debugger attached) is posted on the code review. When all the tests pass, a badge appears on the code review so all reviewers can see that fact.

After gathering feedback and updating the code, Ernie has the approval to merge their code. They click a button on the code review tool that adds their change to a "submit queue", where all new changes are serially rebased onto `main` and (if cleanly rebased) re-built and re-tested before being committed to `main`. If anything goes wrong, Ernie gets an email/slack notification with a link to get more information (or re-run the test with a debugger attached). When the commit lands on `main`, the review is automatically closed.

Once the code is committed to `main`, the packaged artifact from the submit queue is rolled out to production by deploying new copies of the service and shifting traffic from the old to the new. This process is done incrementally -- monitoring key metrics for the service and rolling back automatically if there is a drop in performance. If something does go wrong, a message is sent to the team's slack channel with a short snippet from the logs, a screenshot of the monitoring dashboard, and a link to learn more (or open up a remote debugger with the core dump loaded). 

When the code is all deployed to production, Ernie is free to delete their old branches from the local computer and all ephemeral environments are automatically cleaned up after not being used. 

## Adding a new dependency

Later, Ernie wants to add a dependency on another service (i.e. have their service make an RPC call to another service). 

They follow the same steps as above but then hit an error when trying to run the code: the message clearly says that the service is not authorized to make the RPC call and Ernie needs to add this authorization in the service portal with a helpful link. Ernie clicks the link and encounters a form pre-populated with the names of both services and the RPC endpoint(s) being hit, an optional text box to describe why, and the ability to describe how the testing system should handle the dependency for ephemeral environments (is it ok to have all ephemeral environments share a stable copy of the dependency, or should a new ephemeral copy of the dependency be created every time an ephemeral environment is created). Ernie isn't sure, so they trust the default of sharing a stable copy of the dependency. Ernie also knows that they will need to make additional RPC calls in the future so use the pre-populated list of endpoints to add them all. After Ernie hits submit on the form, a message is pushed to the team channel of the change Ernie made and they are able to finish developing their code as normal.

(Note: Ernie didn't need any additional review of this change to the service config because their team chose to prioritize speed of development and the service they are making an RPC call to has no security restrictions. If either of these were different, Ernie would have instead gotten a link to a draft code review of some infrastructure configuration files where they could get others to approve the change.)

## Creating a new service

Tina the Tech Lead goes to the service registry to create a new service. 

She goes to a new form where she types in the name of the new service and what language the service is in. The form asks for additional information (e.g. the repository, path, etc) but it is pre-populated with reasonable defaults based on the name of the service. The form asks if it should create a new group for operating this service or if it should share the same group as an additional service. If she wants to create a new group, Tina is asked to pick the name of the group (with a reasonable default chosen based on the name of the service) and add any members she chooses. Tina has the option to add custom metrics/SLOs for the service (with reasonable defaults based on her choice language) and add databases or caches. Lastly, Tina has the option to choose if this is an automatically scaled service or if she wants to manually configure the number and type of instances on which the service is deployed.

After Tina hits submit, the service registry displays a dashboard with her service, the ability to configure it (add custom metrics, add databases or cached, authorize RPC calls, and modify maintainers), and a list of all environments (currently just production and maybe staging, but eventually also all active ephemeral environments). For each environment, she can see the cost per day, some high level counters of the traffic it is receiving, and a link to get more information (e.g. the monitoring dashboard, number of instances, a list of recent deployments). Behind the scenes, the service registry has created a pager duty group, several email groups (e.g. NAME-maintainers@company.com, NAME-announce@company.com, etc), created or deployed all databases and caches, etc.
