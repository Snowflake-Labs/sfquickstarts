

## Goal

We are building a Hands-on-Lab (HoL) or workshop around following products/features
- Iceberg
- Gemini 
- Gemini Enteprise
- Cortex Agents, Cortex Analyst
- Semantic Views and models
- MCP Connection between GE and Cortex
- CoWork, Gemini Enteprise


## Reources
We have started building some materials (these are all early drafts and can/will/should change as we compelte the HoL demo):

- @blog-post.md shows the overal message and plan (we are not strictly following this but this HoL is a follow up of such effort)

- @sf-dataops-hol-repo-guide.md (I receieved from the DataOps team)

- @workshop-instructions.md (this is just a draft and every part is subject to change as we develop further, feel free to change it)


## Architecture
The workshop has two sides: 
- Snowflake which user will use DataOps to do all they want to do
- GCP which users will use Qwicklabs


## Hands on lab user experience
- go to https://go.dataops.live/snowflake-and-gemini-workshop and register for a snowflake temporary account for this lab. Click on new account, log in using username, password.
- architecture and what we are going to do and achieve with a diagram
- create a hol_role role and assign all (compact) needed priviledges including owner of a newly created db, etc. (this cell includes all for ease of understand)
- in google cloud ui, create a bucket add permission for above snowflake role
- in snowsight ui, we can go to marketplace and explore available dataset, talk about marketplace to sell/buy and free datasets with a click. then find BLS (beauru of labor stat) or
link to (link to the dataset).
- when we get dataset we want it to land in iceberg v3 in the bucket we created above
- we explore the dataset very breifly in one or two cells (to show snowflake core job)
- we create a cortex analyst and semantic view
- create a cortex agents with above analyst 
- explore to use from coco
- explore using from cowork
- create mcp server and connection 
- register in in gemini enteprise
- use it (same question as in cowork)


## Output
- should be in snowflake notebook
- all diagrams must be in DOT
- Feel free to fill the gap in steps, each step will be one or two cells (in a way that in each cell attendee understand what happens)


## Narative
it should read like a narration:

<starts from here the example

###marketplace
we get our data from the Snowflake Marketplace. Marketplace let's team augment data ... and for data providers a secure and managed place to sell/share data withe outside world.

let's build an economic dataset to track economic wellbeing of americans in each state. we need income, inflation, mortgage rate, unemployment rate, and growth rate. We track on monthly basis.

so let's go get the source data from Marketplace.

UI: left panel> marketplace> snowflake marketplace> data products> search: ... > 
```
code sell
```

We are going to create our ecomic table in iceberg format. 

###iceberg
iceberg provides ... 

one of the advantages of iceberg is it resides in customer gcs buckets, customer owns them.
let's create the bucket, assign role, and ...

code cell

ui: go to console.google> gcs> ...> create bucket, name: lastname-firstname-hol > in permission tab> add ...

code cell

ui: ...
ui: let's view the iceberg data and metadata in our gcs: go to ....


As you see we narrate very briefly, just say the core advantage of the component we choose, very telegraphic ui, related or equvalent code cell, ...

try to have one code cell in each step (like verification after creation in the same cell, etc). 
the goal is to teach through ui (but mainly for playing around) but the lab goes through running codes (mainly, except for when we do something in looker or google env). UI is just to "teach" and do "playground". We do not need to give exact instruction (put this in this field, etc).

When we want to provide insight about our choice of components (why this), we want to highly depend on "./input/blog-post.md" which we are implementing (mainly the ai part). so the reasons can come from there (summarized or edited or added), it is a good starting point.


