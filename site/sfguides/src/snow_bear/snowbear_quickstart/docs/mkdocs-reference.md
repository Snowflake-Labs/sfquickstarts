# MkDocs reference

Use this page as a reference for useful built-in functions to build dynamic
homepages.

## Official docs

- Material for MkDocs reference documentation
  [Material for MkDocs reference](https://squidfunk.github.io/mkdocs-material/reference/) -
  Really useful for referencing standard features and styling
- MkDocs documentation [mkdocs.org](https://www.mkdocs.org) - Can be useful with
  some core function documentation

## Pipeline build badge

!!! info

    To inform users of the current pipeline status, add this build badge to the
    homepage.

!!! abstract "Required environment variables"

    - `FROSTBYTE_CUSTOMER_NAME` - The name of the customer. Example value "ACME"
    - `FROSTBYTE_SOLUTION_TEMPLATE_NAME` - The name of the solution template.
      example "Solution Template"

!!! example

    ```jinja
    {% raw %}
    {{ build_badge() }}
    {% endraw %}
    ```

    {{ build_badge() }}

## Customer logo

!!! info

    To customize the appearance of the homepage to make it more unique during demos.

!!! abstract "Required environment variables"

    - `FROSTBYTE_CUSTOMER_LOGO_URL` - The URL to the customer logo. Example value
      "https://www.acme.com/logo.png"

!!! example

    ```jinja
    {% raw %}
    {{ customer_logo() }}
    {% endraw %}
    ```

    {{ customer_logo() }}

## Snowsight button

!!! info

    To make it easier for users to open up Snowsight UI for the account
    used to build this homepage.

!!! abstract "Required environment variables"

    - `DATAOPS_SOLE_ACCOUNT` - The account locator. Example value "abc84839.us-east-1"

!!! example

    ```jinja
    {% raw %}
    {{ snowsight_button() }}
    {{ snowsight_button(title="Open up your Snowsight") }}
    {% endraw %}
    ```

    {{ snowsight_button("Open up 403 Snowsight") }}

## Collapsible code blocks

!!! info

    To make it easier for users to read long the code blocks.

!!! example

    Add the following

    1. Before the block `/// html | div[class="collapse-code"]`
    2. After the block `///`


    /// html | div[class="collapse-code"]

    ```
    SELECT
    SUM(o.price) AS total_sales,
    o.date
    FROM frostbyte_tasty_bytes.analytics.orders_v o
    GROUP BY o.date;
    ```

    ///

## DDE button

!!! info

    To make it easier for users to open up DDE for the account
    used to build this homepage.

!!! abstract "Required environment variables"

    - `CI_PROJECT_URL` - The URL to the GitLab project. Example value
      "https://app.dataops.live/snowflake/solutions/solution-template-template"
    - `FROSTBYTE_DDE_URL` (optional) - The URL to the DDE. Default value
      "https://code.dev.dataops.live/#"
    - `CI_BUILD_REF_NAME` (optional) - The branch name. Default value "main"

!!! example

    The first parameter is the path you would like the DDE to open when clicking the
    button.


    ```jinja
    {% raw %}
    {{ dde_button("solution/") }}
    {% endraw %}
    ```

    Remember to URL encode the path if it contains special characters, for example:
    ```jinja
    {% raw %}
    {{ dde_button("tastybytes-dataops/30%20-%20vignettes/Workload%20Deep%20Dive/Data%20Science/Snowpark%20101") }}
    {% endraw %}
    ```

    {{ dde_button("solution/") }}

## Display arbitrary environment variables

!!! info

    To display arbitrary environment variables inside your homepage.

!!! example

    ```bash
    {% raw %}
    {{ getenv("DATAOPS") }}
    {% endraw %}
    ```


    ```bash
    {% raw %}
    {{ env_var("DATAOPS") }}
    {% endraw %}
    ```

## Inline admonition

!!! info

    To display inline admonitions next to code blocks.

!!! example

    Add `inline end` to the admonition name to make it inline.

    ```
        {% raw %}
        !!! info inline end

            Example content!

        /// html | div[class="collapse-code"]

        ```sql
        USE ROLE {{ DATAOPS_CATALOG_SOLUTION_PREFIX | lower }}_admin;
        USE WAREHOUSE {{ DATAOPS_CATALOG_SOLUTION_PREFIX | lower }}_de_wh;
        ```

        ///
        {% endraw %}

    ```

    !!! info inline end

        Example content!

    /// html | div[class="collapse-code"]

    ```sql
    USE ROLE {{ DATAOPS_CATALOG_SOLUTION_PREFIX | lower }}_admin;
    USE WAREHOUSE {{ DATAOPS_CATALOG_SOLUTION_PREFIX | lower }}_de_wh;
    ```

    ///

## Including and render template files

!!! info

    To include files from the repository in the homepage.

!!! example

    Add using the following syntax. Note the path is relative to the current file.

    ```markdown
    {% raw %}
    {% include("sql/example.sql") %}
    {% endraw %}
    ```

/// html | div[class="collapse-code"]

```sql
{% include("sql/example.sql") %}
```

///

## Including and files without rendering

!!! info

    To include files from the repository in the homepage without rendering.

!!! example

    Add using the following syntax. Note the path is relative to the root of the
    docs.

    ```markdown
    {% raw %}
    {{ include_raw("docs/sql/example.sql") }}
    {% endraw %}
    ```

/// html | div[class="collapse-code"]

```sql
{{ include_raw("docs/sql/example.sql") }}
```

///
