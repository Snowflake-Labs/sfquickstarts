id: getting_started_with_snowflake_notebooks
summary: This guide provides the instructions on how to get started with your first Snowflake Notebook.
categories: featured,getting-started
environments: web
status: Published
feedback link: <https://github.com/Snowflake-Labs/sfguides/issues>
tags: Getting Started, Snowflake Notebooks
authors: Vino Duraisamy, Doris Lee

# A Getting Started Guide With Snowflake Notebooks
<!-- ------------------------ -->
## Overview

Duration: 5

[Snowflake Notebooks](https://docs.snowflake.com/user-guide/ui-snowsight/notebooks) offer an interactive, cell-based programming environment for Python and SQL. With a Snowflake Notebook, you can perform exploratory data analysis, experiment with feature engineering for machine learning, and perform other data science tasks within Snowflake.

You can write and execute code, visualize results, and tell the story of your analysis all in one place.

* Explore and experiment with data already in Snowflake, or upload new data to Snowflake from local files, external cloud storage, or datasets from the Snowflake Marketplace.
* Write SQL or Python code and quickly compare results with cell-by-cell development and execution.
* Interactively visualize your data using embedded Streamlit visualizations and other libraries like Altair, Matplotlib, or seaborn.
* Contextualize results and make notes about different results with Markdown cells.
* Keep your data fresh by relying on the default behavior to run a cell and all modified cells preceding it or debug your notebook by running it cell-by-cesll.
* Run your notebook on a schedule. See [Schedule your Snowflake Notebook to run](https://docs.snowflake.com/user-guide/ui-snowsight/notebooks-schedule).
* Make use of the role-based access control and other data governance functionality available in Snowflake to allow other users with the same role to view and collaborate on the notebook.

![Notebook](assets/sf-notebooks-welcome.gif)

In this guide, we will learn how to get started with your first notebook project!

### Prerequisites

- A [Snowflake](https://signup.snowflake.com/) account. Sign up for a [30-day free trial](https://signup.snowflake.com/) account, if required.
- Access to download an IPython Notebook from [Snowflake notebooks demo repo](https://github.com/Snowflake-Labs/snowflake-demo-notebooks/tree/main)

### What will you build?

Here is a summary of what you will be able to learn in each step by following this quickstart:

- **Adding Python Packages**: How to use pre-installed libraries in Notebooks as well as adding additional packages from package picker
- **Switching between SQL and Python cells**: How to switch between SQL and Python cells in the same notebook
TODO: (fix the error that says worksheet in the ipynb markdown)
- **Visualize your Data**: How to use Altair and Matplotlib to visualize your data
- **Working with Snowpark**: How to use Snowpark API to process data at scale within the Notebook
- **Using Python Variables in SQL cells**: How to use Jinja syntax `{{.}}` to refer to Python variables within SQL queries, to reference previous cell outputs in your SQL query and more.
- **Creating an Interactive app with Streamlit**: How to build a simple interactive Streamlit app
- **Keyboard Shortcuts in Notebooks**: How to use Keyboard shortcuts in Notebooks to developer faster

<!-- ------------------------ -->
## Setup

Duration: 5

You can create a Snowflake Notebook directly from the Snowsight UI or upload an existing IPython Notebook to Snowflake.

In this example, we will upload an existing notebook from [Snowflake Notebooks demo repo](https://github.com/Snowflake-Labs/snowflake-demo-notebooks/tree/main) into a Snowflake account.

## Load demo notebooks to Snowflake

The notebook files are available for download as `.ipynb` files in the demo repository. To load the demo notebooks into your Snowflake Notebook, follow these steps: 

1. On Github, click into each folder containing the tutorial and the corresponding `.ipynb file`, such as [this](https://github.com/Snowflake-Labs/notebook-demo/blob/main/My%20First%20Notebook%20Project/My%20First%20Notebook%20Project.ipynb). Download the file by clicking on the `Download raw file` from the top right.

2. Go to the Snowflake web interface, [Snowsight](https://app.snowflake.com), on your browser.

3. Navigate to `Project` > `Notebooks` from the left menu bar. 

4. Import the .ipynb file you've download into your Snowflake Notebook by using the `Import from .ipynb` button located on the top right of the Notebooks page.

![Import](assets/snowflake_notebook.png)

5. Select the file from your local directory and press `Open`.

6. A `Create Notebook` dialog will show up. Select a database, schema, and warehouse for the Notebook and click `Create`.

<!-- ------------------------ -->
## Running Snowflake Notebooks

Duration: 5

Let's walk through the first demo notebook in Snowflake now.

### Adding Python Packages

Notebooks comes pre-installed with common Python libraries for data science 🧪 and machine learning 🧠, such as numpy, pandas, matplotlib, and more!

If you are looking to use other packages, click on the Packages dropdown on the top right to add additional packages to your notebook.

For the purpose of this demo, let's add the matplotlib and scipy package from the package picker.

![PackagePicker](assets/package_picker.png)

### Switching between SQL and Python cells

We often work with SQL query and different Python packages in the data exploration phase. How to switch between SQL and Python cells in the same notebook?

While creating a new cell, you can select between `SQL`, `Python` and `Markdown` cells to select an appropriate one you need.

Every cell at the top left has a drop down list that shows the type of cell along with the cell number as well.

![CellType](assets/cell_type.png)

### Accessing cell outputs as variables in Python

You can give cells a custom name (as opposed to the default cell#) and refer to the cell output in subsequent cells as well.

For example, you can refer to the output of the SQL query in `cell5` in a `Python variable` called `cell5` in subsequent cells.

![CellType](assets/cell_output.png)

### Visualize your data

You can use different visualization libraries such as Altair, Streamlit, Matplotlib, etc to plot your data.

Let's use Altair to easily visualize our data distribution as a histogram.

![Histogram](assets/histogram.png)

To learn more on how to install different visualization libraries and visualize your data, refer to the [documentation](https://docs.snowflake.com/en/user-guide/ui-snowsight/notebooks-visualize-data)

### Working with Data using Snowpark

In addition to using your favorite Python data science libraries, you can also use the [Snowpark API](https://docs.snowflake.com/en/developer-guide/snowpark/index) to query and process your data at scale within the Notebook. 

First, you can get your session variable directly through the active notebook session.The session variable is the entrypoint that gives you access to using Snowflake's Python API.

```python
    from snowflake.snowpark.context import get_active_session
    session = get_active_session()

    session.write_pandas(df,"SNOW_CATALOG",auto_create_table=True, table_type="temp")
```

### Using Python variables in SQL cells

You can use the Jinja syntax `{{..}}` to refer to Python variables within your SQL queries as follows. 

```python
threshold = 5
```

```sql
-- Reference Python variable in SQL
SELECT * FROM SNOW_CATALOG where RATING > {{threshold}}
```

Likewise, you can reference a Pandas dataframe within your SQL statment:

```sql
-- Filtering from a Pandas dataframe
SELECT * FROM {{my_df}} where VAR = 6
```

### Simplifying your subqueries

Let's start with the output of `cell21` in this notebook. Here is how it looks!

```sql
    SELECT * FROM SNOW_CATALOG;
```

![Cell21_Output](assets/cell_21.png)

You can simplify long subqueries with [CTEs](https://docs.snowflake.com/en/user-guide/queries-cte) by combining what we've learned with Python and SQL cell result referencing. 

For example, if we want to compute the average rating of all products with ratings above 5. We would typically have to write something like the following:

```sql
    WITH RatingsAboveFive AS (
    SELECT RATING
    FROM SNOW_CATALOG
    WHERE RATING > 5
)
SELECT AVG(RATING) AS AVG_RATING_ABOVE_FIVE
FROM RatingsAboveFive;
```

With Snowflake Notebooks, the query is much simpler! You can get the same result by filtering a SQL table from another SQL cell by referencing it with Jinja, e.g., `{{my_cell}}`. 

```sql  
    SELECT AVG(RATING) FROM {{cell21}}
    WHERE RATING > 5
```

<!-- ------------------------ -->
## Snowflake Arctic

Duration: 5

### Prompt Engineering
Being able to pull out the summary is good, but it would be great if we specifically pull out the product name, what part of the product was defective, and limit the summary to 200 words. 

Let’s see how we can accomplish this using the **snowflake.cortex.complete** function.

```sql
SET prompt = 
'### 
Summarize this transcript in less than 200 words. 
Put the product name, defect and summary in JSON format. 
###';

select snowflake.cortex.complete('snowflake-arctic',concat('[INST]',$prompt,transcript,'[/INST]')) as summary
from call_transcripts where language = 'English' limit 1;
```

Here we’re selecting the Snowflake Arctic model and giving it a prompt telling it how to customize the output. Sample response:

```json
{
    "product": "XtremeX helmets",
    "defect": "broken buckles",
    "summary": "Mountain Ski Adventures received a batch of XtremeX helmets with broken buckles. The agent apologized and offered a replacement or refund. The customer preferred a replacement, and the agent expedited a new shipment of ten helmets with functioning buckles to arrive within 3-5 business days."
}
```

<!-- ------------------------ -->
## Streamlit Application

Duration: 9

To put it all together, let's create a Streamlit application in Snowflake.

### Setup

**Step 1.** Click on **Streamlit** on the left navigation menu

**Step 2.** Click on **+ Streamlit App** on the top right

**Step 3.** Enter **App name**

**Step 4.** Select **Warehouse** (X-Small) and **App location** (Database and Schema) where you'd like to create the Streamlit applicaton

**Step 5.** Click on **Create**

- At this point, you will be provided code for an example Streamlit application

**Step 6.** Replace the entire sample application code on the left with the following code snippet.

```python
import streamlit as st
from snowflake.snowpark.context import get_active_session

st.set_page_config(layout='wide')
session = get_active_session()

def summarize():
    with st.container():
        st.header("JSON Summary With Snowflake Arctic")
        entered_text = st.text_area("Enter text",label_visibility="hidden",height=400,placeholder='For example: customer call transcript')    
        if entered_text:
            entered_text = entered_text.replace("'", "\\'")
            prompt = f"Summarize this transcript in less than 200 words. Put the product name, defect if any, and summary in JSON format: {entered_text}"
            cortex_prompt = "'[INST] " + prompt + " [/INST]'"
            cortex_response = session.sql(f"select snowflake.cortex.complete('snowflake-arctic', {cortex_prompt}) as response").to_pandas().iloc[0]['RESPONSE']
            st.json(cortex_response)

def translate():
    supported_languages = {'German':'de','French':'fr','Korean':'ko','Portuguese':'pt','English':'en','Italian':'it','Russian':'ru','Swedish':'sv','Spanish':'es','Japanese':'ja','Polish':'pl'}
    with st.container():
        st.header("Translate With Snowflake Cortex")
        col1,col2 = st.columns(2)
        with col1:
            from_language = st.selectbox('From',dict(sorted(supported_languages.items())))
        with col2:
            to_language = st.selectbox('To',dict(sorted(supported_languages.items())))
        entered_text = st.text_area("Enter text",label_visibility="hidden",height=300,placeholder='For example: call customer transcript')
        if entered_text:
          entered_text = entered_text.replace("'", "\\'")
          cortex_response = session.sql(f"select snowflake.cortex.translate('{entered_text}','{supported_languages[from_language]}','{supported_languages[to_language]}') as response").to_pandas().iloc[0]['RESPONSE']
          st.write(cortex_response)

def sentiment_analysis():
    with st.container():
        st.header("Sentiment Analysis With Snowflake Cortex")
        entered_text = st.text_area("Enter text",label_visibility="hidden",height=400,placeholder='For example: customer call transcript')
        if entered_text:
          entered_text = entered_text.replace("'", "\\'")
          cortex_response = session.sql(f"select snowflake.cortex.sentiment('{entered_text}') as sentiment").to_pandas()
          st.caption("Score is between -1 and 1; -1 = Most negative, 1 = Positive, 0 = Neutral")  
          st.write(cortex_response)

page_names_to_funcs = {
    "JSON Summary": summarize,
    "Translate": translate,
    "Sentiment Analysis": sentiment_analysis,
}

selected_page = st.sidebar.selectbox("Select", page_names_to_funcs.keys())
page_names_to_funcs[selected_page]()
```

### Run

To run the application, click on **Run** located at the top right corner. If all goes well, you should see the application running as shown below.

![App](assets/snowflake_arctic.gif)

> aside positive
> Note: Besides Snowflake Arctic you can also use [other supported LLMs in Snowflake](https://docs.snowflake.com/en/user-guide/snowflake-cortex/llm-functions#availability) with `snowflake.cortex.complete` function.

<!-- ------------------------ -->
## Conclusion And Resources

Duration: 1

Congratulations! You've successfully completed the Getting Started with Snowflake Notebooks quickstart guide. 

### What You Learned

- **Adding Python Packages**: How to use pre-installed libraries in Notebooks as well as adding additional packages from package picker
- **Switching between SQL and Python cells**: How to switch between SQL and Python cells in the same notebook
TODO: (fix the error that says worksheet in the ipynb markdown)
- **Visualize your Data**: How to use Altair and Matplotlib to visualize your data
- **Working with Snowpark**: How to use Snowpark API to process data at scale within the Notebook
- **Using Python Variables in SQL cells**: How to use Jinja syntax `{{.}}` to refer to Python variables within SQL queries, to reference previous cell outputs in your SQL query and more.
- **Creating an Interactive app with Streamlit**: How to build a simple interactive Streamlit app
- **Keyboard Shortcuts in Notebooks**: How to use Keyboard shortcuts in Notebooks to developer faster

### Related Resources

Here are some resources to learn more about Snowflake Notebooks:

* [Documentation](https://docs.snowflake.com/LIMITEDACCESS/snowsight-notebooks/ui-snowsight-notebooks-about)
* [YouTube Playlist](https://www.youtube.com/playlist?list=PLavJpcg8cl1Efw8x_fBKmfA2AMwjUaeBI)
* [Solution Center](https://developers.snowflake.com/solutions/?_sft_technology=notebooks)

