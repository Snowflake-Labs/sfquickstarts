author: Josh Reini
id: build-agent-powered-workflows
language: en
summary: building agent-powered workflows using Snowflake Cortex AI and Managed MCP Servers
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/ai, snowflake-site:taxonomy/snowflake-feature/cortex-analyst
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
fork repo link: https://github.com/Snowflake-Labs/MCP-HOL-BUILD-2025

# Build Agent-Powered Workflows Using Cortex AI and Managed MCP Servers
<!-- ------------------------ -->
## Overview 
As Snowflake continues to build the agentic architecture, Model Context Protocol ("MCP") has become a core element to helping standardize agents to tool communication. MCP allows agents and external systems to communicate to discover and invoke tools that are used for agentic flows, while helping deploy agents faster. 

This guide provides a hands-on experience in building and evaluating an AI agent powered by a Snowflake Managed Model Context Protocol (MCP) server. The agent is specifically designed to be a health research agent for medical researchers and healthcare professionals, giving them instant access to medical research data from the Snowflake Marketplace. 

### What You’ll Learn 
- Getting your data AI-ready
- Creating an MCP Server
- Setting up authentication for the MCP server using a personal access token
- The three layers of access control for secure deployment
- Enabling cross-region inference to allow external agents to connect

### What You’ll Need 
- A [GitHub](https://github.com/) Account 
- Access to a snowflake account. If you do not have an account, sign up for a [trial account here](signup.snowflake.com/?utm_source=&utm_medium=webinar&utm_campaign=em-gb-en-&utm_content=-evp-build-london-lab)


### What You’ll Build 
- Building an agent
- Setting up an MCP
- Connecting your agent to an MCP Server

<!-- ------------------------ -->
## Getting Started

### Setup
- Log into your Snowflake account. If you do not have an account, sign up for a [trial account here](signup.snowflake.com/?utm_source=&utm_medium=webinar&utm_campaign=em-gb-en-&utm_content=-evp-build-london-lab)
- Go to the Snowflake Marketplace.
- Find the Clinical Trials Database:
    - Search for "clinical trials".
    - Select the "clinical trials research database" that is free and instantly accessible. Choose "Get".
    - Use the dropdown to give access via the public role. Choose "Get".
- Find the PubMed Corpus:
    - Search for "PubMed" or "PubMed DB". Select the "PubMed biomedical research corpus". Choose "Get".
    - Add the public role access to the knowledge extension.


<!-- ------------------------ -->
## Create the MCP Server
Now that the data is AI-ready, the next thing we want to do is create our MCP server. The MCP server will expose these search services as tools to the agent.

- Access the lab's GitHub repository using the [this link](https://github.com/Snowflake-Labs/MCP-HOL-BUILD-2025).
- Open create_MCP_for_server.sql and copy the code.

In your Snowflake account, go to Projects and then Worksheets or [click here](https://app.snowflake.com/_deeplink/worksheets?utm_source=quickstart&utm_medium=quickstart&utm_campaign=-us-en-all&utm_content=app-build-agent-powered-workflows) to go there directly.
- Open a new worksheet, paste the code, and choose Run all.

The code will:
- Create and use a database named HEALTH_DB and the public schema.
- Create or replace the MCP server based on a specification.
- List two tools in the specification, each with a name, identifier (for the search service), type, and description. The combination of the name and description is how the agent is going to choose which tool to use when. Here, we are using Cortex Search Services as our tools. 
- Grant usage on the MCP server to the public role. This role will be able to access and use this MCP object.
- Select "Run All".

### Setup the Account Settings
Now that we've created our MCP Server, we'll move towards creating our agents. The managed MCP servers support both OAUTH authentication and PAT authentication. Once you are actually connecting and using the MCP servers, you need to know three important areas about access controls: 
1. Usage on the MCP object itself: This is what you need to both connect to the server and discover which tools are available.
2. Use on the underlying tools: This ensures that any roles that have access to particular domains or departments in your company only have access to the right services.
3. Use on the data: ou need to not only be able to call the search service but you actually need to be able to view the underlying data.

You will set up all three of these pieces to ensure access and control is set up and governed appropriately. 

- Go back to the [GitHub repository](https://github.com/Snowflake-Labs/MCP-HOL-BUILD-2025) and open alter_account_settings.sql. Copy the code.
- Open a new SQL worksheet, paste the code, and choose "Run all."

This will:
- Enable cross-region inference to access the Claude Sonnet 4-5 LLM.
- Create a permissive network policy, allowing the external agent to use its access token.


<!-- ------------------------ -->
## Run Notebook and Connect Agent
Next, we'll build the agent connect to the MCP server. Now that you've run both the SQL scripts, we can open the notebook. 

From the [GitHub repository](https://github.com/Snowflake-Labs/MCP-HOL-BUILD-2025), open the build-and-evaluate-langgraph-agents-with-mcp-tools.ipynb file.

As you are opening notebook, you'll need to fill in your Snowflake credentials and your own OpenAI key, as the agent is external.

Next we'll create a Snowpark session to connect Snowflake using the account, the PAT, and the database and schema of our MCP server. 

- To create the Snowpark session, run the cell to create your Snowpark session, connecting Snowflake using the account, PAT, database, and schema of your MCP server.
- To create the MCP client, use the MultiServerMCPClient class from the LangChain MCP adapters to create the MCP client. Pass in the URL for your Snowflake MCP server and your PAT as an authorization bearer token.

Once this cell runs, we now have our tools ready to go to add to our agent. 


<!-- ------------------------ -->
## Define and Compile Agent
For our we will be using GPT-4o as our LLM.

- Define a simple call_model function that calls the LLM with the MCP server tools binded to it (PubMed and Clinical Trials search).
- Build the graph using Langraph, defining a simple agent graph with two nodes: calling the LLM and using the tools. Compile the graph.
- Wrap the compiled graph in a simple Python class to make it synchronous.


### Test the Agent
Try out the agent by asking a simple question, such as "What is the primary indicator for a specific drug?". The agent will call the LLM, which may decide to call the MCP server for search results

What this agent is doing is calling the LLM to answer the question, and then the LLM, if it decides it is necessary, will then reach out to our MCP server to get access to search results from either clinical trials data or PubMed. 

<!-- ------------------------ -->
## Set up AI Observability
We see our agent is working, but the question is how to know how well it is performing. This is where AI observability and evaluations come in. To measure the agent's performance, you will use AI observability and evaluations.

To get started with evaluations, we first want to initialize our TruLens session. This is how we connect to Snowflake so we can store our logs, traces, and evaluations as we are evaluating our agent. To make this connection, we are going to simply import the Snowflake connector and then pass in the Snowpark session that we created earlier.

- To initialize TruLens Session: 
  - Import the Snowflake connector and passing in the Snowpark session.
- Set up Metrics: 
  - Use Claude Sonnet 4-5 to evaluate the agent on two key metrics:
    - Tool Selection:Evaluates if the agent chooses the right tool at the right time.
    - Tool Calling: Ensures the agent is using the tool correctly by passing the right parameters and query.
Note: These are client-side metrics defined using an LLM judge, which compares the agent's execution trace to a set of criteria to produce a score.

This score is going to tell us whether the agent is performing well or poorly on these specific criteria.

<!-- ------------------------ -->
## Run the First Agent Version
Register the first version of the agent using TrueGraph, which is suitable for the Langraph framework, with an application name and a version.

Next, create a test set of queries that mirrors what the agent will face in production.

Create a "run" to define the data set for evaluation. Use run.start to execute a batched run, invoking the agent against each query and logging the traces to Snowflake.
Compute Metrics: After the run is complete, compute the metrics using run.compute_metrics.


<!-- ------------------------ -->
## Analyze Performance and Identify Errors

- View the results in the Snowflake AI Observability tab by clicking Evaluations.
- Analyze the scores for Tool Calling and Tool Selection.
- Click on a query, such as "What is the primary indicator for the drug Zeljance?", to view the trace and evaluation details.

Common errors observed: 
- Tool Selection: The agent failed to make tool calls, missing the opportunity to use the tools and relying on the LLM's internal knowledge instead of grounded data.
- Tool Calling: The agent repeatedly called tools but failed to access data because it ran into issues knowing which parameters were available to search.

### Improve the Tool Descriptions 
- Go back to the [GitHub repository](https://github.com/Snowflake-Labs/MCP-HOL-BUILD-2025) and open create_MCP_server_v2.sql.
- Copy the updated code.
    - The key changes to the updated code include:
      - Mapping specific use cases as mandatory use in the tool descriptions.
      - Telling the agent to only provide the query parameter with search terms, rather than guessing other parameters.
- Paste the code into a new Snowflake worksheet.
- Create the new MCP server with a v2 tag and select run all.

### Run and Evaluate v2 of the Agent
Go back to the notebook.

- Reconnect the MCP client, changing the URL to connect to the V2 version of the MCP server.
- Rebuild the agent graph.
- Reregister the new version of the agent, ensuring you update the application version (e.g., to 'improved descriptions') so you can compare it with the old version.
- Recreate the run using the same data set.
- Execute the run and compute the metrics for the V2 agent.

<!-- ------------------------ -->
## Compare Agent Performance

Go back to the AI Observability page. You should now see two versions of the agent.

The headline metrics should show a significant jump, with Tool Calling and Tool Selection scores improving. Select both application versions and choose Compare to view a head-to-head analysis.
Click on the same query to compare the traces.
Version 1 should show a short trace with no tool calls (ungrounded).
Version 2 should show a longer trace, successfully making calls to both PubMed and clinical trial search, demonstrating that the agent is grounded in data.


<!-- ------------------------ -->
## Conclusion And Resources
Congratulations! You successfully built and evaluated AI agents using the Model Context Protocol and Snowflake's AI observability. 


### What You Learned
- Connecting and loading AI-ready data from the Snowflake Marketplace
- Created an MCP server
- Used LangGraph to set up our agent and allowed the LLM to call different tools
- Used evaluations to systematically measure the agent's performance.
