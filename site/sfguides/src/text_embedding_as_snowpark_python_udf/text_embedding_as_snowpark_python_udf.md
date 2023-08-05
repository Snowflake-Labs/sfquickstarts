author: Luke Merrick
id: text_embedding_as_snowpark_python_udf
summary: Text Embedding As A Snowpark Python UDF
categories: data-science-&-ml
environments: web
status: Published 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Snowpark Python, Machine Learning, Data Science, NLP 

# Text Embedding As A Snowpark Python UDF
<!-- ------------------------ -->
## Overview

Duration: 1

This first half of this guide blazes through the setup of a premade UDF so you can start playing with text embedding in Snowflake as quickly as possible!

For those who are interested in exploring a little deeper how everything works, stick around for the second half, which discusses how to make your own variant of the UDF coverd in the first half of the guide.

### Prerequisites

- Familiarity with Snowpark Python UDFs
  - The [Snowpark Developer Guide for Python](https://docs.snowflake.com/en/developer-guide/snowpark/python/index) serves as an excellent overview and reference for all things Snowpark Python
  - If you want a holistic bootcamp, consider spending an hour or two with the [Getting Started with Data Engineering and ML using Snowpark for Python Quickstart](https://quickstarts.snowflake.com/guide/getting_started_with_dataengineering_ml_using_snowpark_python/index.html#0)
- Familiarity with running Jupyter notebooks
  - Before proceeding, make sure you've got Python 3.8+ and Jupyter Lab installed in a Python environment that you feel comfortable installing more Python packages into.
- A conceptual grasp of text embedding
  - There is no need to follow ever word of technical descriptions like the [Sentence embedding Wikipedia article](https://en.wikipedia.org/wiki/Sentence_embedding), but you will get the most out of this guide if you are able to follow along plain-language material like [OpenAI documentation on Embeddings](https://platform.openai.com/docs/guides/embeddings)

### What You’ll Learn

You will learn how to install a premade text embedding Python UDF into your Snowflake environment, and (optionally) how to create your own version of a text embedding UDF.

### What You’ll Need

- A Snowflake account with [Anaconda Packages enabled by ORGADMIN](https://docs.snowflake.com/en/developer-guide/udf/python/udf-python-packages.html#using-third-party-packages-from-anaconda).
  - If you do not have a Snowflake account, or your account does not have Anaconda Packages enabled, you can register for a [free trial account](https://signup.snowflake.com/).
- A Snowflake account login with ACCOUNTADMIN role.
  - If you do not have this role in your environment, you may register for a free trial.
  - Alternatively, it is possible to
    1. Use a different role that has the ability to create database, schema, tables, stages, and user-defined functions.
    2. Use an existing database and schema in which you are able to create the aforementioned objects.
- The [SnowSQL CLI](https://docs.snowflake.com/en/user-guide/snowsql-install-config) installed and configured.
- Python 3.8+ with [Jupyter Lab](https://jupyter.org/) installed.

<!-- ------------------------ -->
## Part 1: Loading A Text Embedding Model Into Snowflake

### Follow Along In Jupyter

Remember how we said you'd need a Python 3.8+ installation with Jupyter Lab installed in it? Well, now it's time to use it! Fire up Jupyter Lab, download a copy of the [notebook for this quickstart from GitHub](https://github.com/lukemerrick/sfquickstarts/blob/master/site/sfguides/src/text_embedding_as_snowpark_python_udf/assets/notebook.ipynb) and pop it open.

Go ahead and start by installing the prerequisites.

![install prerequisites](assets/install_prerequisites.png)

### A Note About Our Embedding Model


In this guide, we will be using the [`base` size of the E5 text embedding model series (version 2)](https://huggingface.co/intfloat/e5-base-v2), which was dominating the [Massive Text Embedding Benchmark (MTEB)](https://github.com/embeddings-benchmark/mteb) leaderboard until the Alibaba DAMO Academy released the [GTE series](https://huggingface.co/thenlper/gte-large) in late July 2023. Although GTE slightly edges out E5 on the leaderboard, we see in the August 04, 2023 screenshot below above that both series of models compete favorably with OpenAI's proprietary Ada 002 model and can be considered state-of-the-art text embedding systems.

![MTEB leaderboard](assets/2023-08-04_MTEB_leaderboard.png)


### Uploading Model Weights To Snowflake.

For security reasons, Snowpark Python UDFs are not generally permitted to access the internet. This means that even if you want to use a [publicly-available text embedding model from Huggingface](https://huggingface.co/models?pipeline_tag=sentence-similarity&sort=trending), you will need to store a copy of your model weights in a Snowflake stage.

#### Downloading The Model Weights From Huggingface

Go ahead and download the E5-base-v2 model from Hugginface and save it to a tarfile on disk by running the first few cells of the notebook.

![download model](assets/download_model.png)

#### Uploading The Model Weights

Now that we have the weights downloaded, we can upload them to a Snowflake stage via the Python connector. The next block of cells in the notebook establishes a connection to Snowflake, sets up a new warehouse, database, schema, and stage for this quickstart, and uploads the model weights to our new stage. Go ahead and run those cells now -- and maybe take a coffee break, too, becuse the upload can take several minutes unless your internet connection is particularly snappy.

![upload model](assets/upload_model.png)

### Implementing A UDF To Run The Model

In the second half of this quickstart we'll revisit how to implement your own UDF for running a text embedding model as a Snowpark Python UDF, but for now let's just use the premade UDF baked into the notebook. Simply run the cell with the `%%writefile` magic to write the UDF implementation to disk.

![write udf to disk](assets/write_udf_to_disk.png)

To make sure this UDF implementation runs as expected, go ahead and execute the next block of cells.

![locally test udf](assets/locally_test_udf.png)


### Install The UDF And Run Text Embedding Via SQL!

We're almost ready to run text embedding directly on Snowflake warehouse compute. All that's left is to upload our UDF implementation file and define the UDF via a `create function` SQL query. Run the last couple cells to make this happen!

![create udf](assets/create_udf.png)


### A Note On Storing Vectors As BINARY Vs. ARRAY

For storage and computational efficiency, our text embedding UDF stores embedding vectors as BINARY blobs constructed by concatenating all of the 32-bit floating point numbers in the vector together in order. While this is how numerical computing libraries like Numpy and Pytorch "see" vectors, sometimes it may be useful to take a more JSON-like perspective and treat your embedding vectors as a Snowflake ARRAY. We could modify our UDF to make it always return an ARRAY, but for greater flexibility we can instead add a new Snowpark UDF to enable a conversion from our BINARY form to ARRAY form. In fact, all it takes is one line of JavaScript to make this possible!


Feel free to give it a shot by running the last couple cells of the notebook.

![unpacking example](assets/unpack_binary_vectors.png)


> aside negative
> 
>  Warning: Composing Python and JavaScript UDFs together in a single query on warehouses that are not [Snowpark-optimized](https://docs.snowflake.com/en/user-guide/warehouses-snowpark-optimized) may cause out-of-memory errors, since the warehouse may try to allocate memory for both UDFs at the same time. This is why our example shows running the embedding function in its own query first, then unpacking the result in a separate query.


<!-- ------------------------ -->
## Part 2: Building Your Own Text Embedding UDF
Duration: 2

<!-- ------------------------ -->
## Conclusion
Duration: 1

At the end of your Snowflake Guide, always have a clear call to action (CTA). This CTA could be a link to the docs pages, links to videos on youtube, a GitHub repo link, etc. 

If you want to learn more about Snowflake Guide formatting, checkout the official documentation here: [Formatting Guide](https://github.com/googlecodelabs/tools/blob/master/FORMAT-GUIDE.md)

### What we've covered
- creating steps and setting duration
- adding code snippets
- embedding images, videos, and surveys
- importing other markdown files