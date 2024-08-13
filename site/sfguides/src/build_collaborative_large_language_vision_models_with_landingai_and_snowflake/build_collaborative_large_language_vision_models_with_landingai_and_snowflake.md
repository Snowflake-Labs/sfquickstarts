author: Naveen Thomas
id: build_collaborative_large_language_vision_models_with_landingai_and_snowflake
summary: This guide shows how to use LandingLens and Snowflake to create a computer vision model that detects pneumonia in X-ray images.
categories: data-science, genai, LLM, LVM, landingai
environments: web
status: Published
tags: Getting Started, Data Science, Data Engineering, LandingAI, LVM

# Computer Vision Models with LandingLens on Snowflake

## Overview
Duration: 1

In this quickstart, we'll use LandingLens — a Native App available in the Snowflake Marketplace — to create a computer vision model that detects pneumonia in X-ray images. After completing this quickstart, users can use the concepts and procedures from this quickstart to build Object Detection, Segmentation, and Classifications models in LandingLens. 

### What Is LandLens?
LandingLens is a cloud-based Visual AI platform. LandingLens empowers users to create and train Visual AI models even if you don't have a background in AI, machine learning, or computer vision. LandingLens guides you through the process of uploading images, labeling them, training models, comparing model performance, and deploying models.

To users who are familiar with machine learning, LandingLens offers advanced tools to customize the model training process. LandingLens supports advanced deployment options including cloud deployment as well as [Docker](https://support.landing.ai/landinglens/docs/docker-deploy) and [LandingEdge](https://support.landing.ai/landinglens/docs/landingedge-overview), LandingAI’s edge-deployment solution.

### What You'll Learn

- How to install LandingLens from the Snowflake Marketplace
- How to load sample data from a Snowflake stage
- How to build a Classification computer vision model in LandingLens


### What You’ll Need
- A [Snowflake](https://signup.snowflake.com/?utm_cta=quickstarts_) account
- Snowflake privileges on your user to [Install a Native Application](https://other-docs.snowflake.com/en/native-apps/consumer-installing#set-up-required-privileges)
- A warehouse to *install* LandingLens (the warehouse can be any size and can have auto-suspend enabled)
- A warehouse to *run* LandingLens


### What You’ll Build
- A computer vision Classification model to detect pneumonia

<!-- ------------------------ -->

## Install the LandingLens Native App in Your Account
Duration: 30

1. Open the [LandingLens app listing](https://app.snowflake.com/marketplace/listing/GZTYZ12K65CU/landingai-landinglens-visual-ai-platform) in the Snowflake Marketplace and click **Get**.
   <img src="assets/LL_VisualAIPlatform.png" alt="LandingLens listing in the Snowflake Marketplace" width="800">
   
2. Select the **Warehouse** to use for the installation process. The warehouse is only used to install the app, and can be any size (including X-Small).
3. If you want to change the name of the application, click **Options** and enter a name in **Application Name**.
4. Click **Try for Free**. This starts a 30 day free trial of LandingLens.
   <img src="assets/tryForFree.png" alt="Try Landinglens for Free" width="800">

5. Go to **Snowsight** > **Data Products** > **Apps**. Double-click the LandingLens app listing. (Although the app is listed in the Installed Apps section, it is not installed yet.)
   <img src="assets/LLSF_install_2.png" alt="Installed Apps" width="800">

6. A new page opens. It has a series of steps that guide you through the installation process.
7. In **Step 1**, click **Grant**. These permissions allow LandingLens to create compute pools and perform other tasks in your account.
   <img src="assets/LLSF_install_3.png" alt="Grant account privileges" width="800">
   
8. In **Step 2**, click **Review**. Review the allowed endpoints on the pop-up and click **Connect**. This allows LandingLens to access the World Wide Web (WWW).
9. Scroll to the top of the page and click **Activate**.
   <img src="assets/LLSF_install_5.png" alt="Activate" width="800">
   
10. LandingLens opens in your Apps. Click **Launch App**.
      <img src="assets/LLSF_install_7.png" alt="Launch the app installer" width="800">
   
11. The installer opens in the **APP_WIZARD** tab.
12. Click **Install/Upgrade/Resume**. The installer installs all the required services for the LandingLens app. This process takes about 20 to 30 minutes. Do NOT close the tab during the installation process, because it will stop the process.
      <img src="assets/LLSF_install_8.png" alt="Launch the app installer" width="800">
   
13. Once the installation process is complete, all services have the status DONE or READY (green checkmark) and the URL to access LandingLens displays. Copy and paste the URL.  
      <img src="assets/LLSF_install_9.png" alt="Copy the URL for the LandingLens app" width="800">
14. Paste the URL into a new tab to open the LandingLens app. We recommend bookmarking this URL. you can log in to the app using the Snowflake credentials you used to install the app. Only users with the correct privileges in the account can access the LandingLens app.
   <img src="assets/lai_landinglens_app.png" alt="LAI Lens app" width="800">
   
    
<!-- ------------------------ -->

## Get Sample Images
Duration: 15

Now that you've installed the LandingLens app, you are ready to get the sample images. LandingAI provides a set of sample images as an "app" that can be downloaded from the Snowflake Marketplace. You will use these images to train a computer vision model in LandingLens that detects pneumonia.

To get the sample images, follow these instructions:

1. Open the [Sample Dataset for LandingLens: LifeSciences Pneumonia listing](https://app.snowflake.com/marketplace/listing/GZTYZ12K65CA/landingai-sample-dataset-for-landinglens-lifesciences-pneumonia) in the Snowflake Marketplace and click **Get**.
   <img src="assets/LL_pneumonia_1.png" alt="Sample dataset listing in the Snowflake Marketplace" width="800">
2. Go to **Snowsight** > **Data Products** > **Apps**. Click the **Sample Dataset for LandingLens: LifeSciences Pneumonia** app listing.
   <img src="assets/LL_pneumonia_2.png" alt="Open the app" width="800">
3. Click the **Shield** icon in the top right corner of this app page.
4. Click **Review** and allow the CREATE DATABASE privilege, which grants the app to create a database to load the sample data.
   <img src="assets/LL_pneumonia_3.png" alt="Grant privileges" width="800">
5. Open the **LLENS_DATA_APP** tab.
6. Click **Create Sample Dataset** to load the dataset into your Snowflake account.
   <img src="assets/LL_pneumonia_4.png" alt="Create the database" width="800">
7. Make a note of the location of the images; you will use these later.
      - **Database**: llens_sample_ds_lifesciences
      - **Schema**: pneumonia
      - **Stage**: dataset


<!-- ------------------------ -->
## Build a Pneumonia Detection Project

Duration: 20

Now that you've loaded the sample dataset into your Snowflake account, you're ready to create a computer vision model using those images in LandingLens.

### Load the Images into LandingLens
1. Open LandingLens in Snowflake (use the URL generated when you installed the app).
2. Click **Start First Project** and name your project.
3. Click **Classification**.
4. Click **Sync Snowflake Data**.
   <img src="assets/LL_pneumonia_load_1.png" alt="Sync images from Snowflake" width="800">
5. Enter the location that you saved the sample dataset to earlier. The location should be:
      - **Database**: llens_sample_ds_lifesciences
      - **Schema**: pneumonia
      - **Stage**: dataset
6. You will get a message saying that you don't have access to that location. To fix this, copy the SQL commands at the bottom of the pop-up and run them in a Snowflake worksheet in a different browser tab.
7. Turn on **Classify images based on folder names**.
8. Click the directory path (**⌄ /**) in the **Specify the path to an existing folder** field. 
9. Select the **data** directory.
10. Click **Sync**.
   <img src="assets/LL_pneumonia_load_2.png" alt="Select the snowflake stage to load images from" width="800">
11. All images in the stage are loaded to the LandingLens project. (Refresh the page to see the images.) The project now has 100 images; 50 images have the class "normal", and 50 have the class "pneumonia".
    <img src="assets/LL_pneumonia_load_3.png" alt="Select the snowflake stage to load images from" width="800">

### Train a Classification Model
Now that all of the images are in the LandingLens project and have classes assigned to them, train a computer vision model. When you train a model, you give the labeled images to a deep learning algorithm. This allows the algorithm to "learn" what to look for in images.

To train a model, click **Train**.
<img src="assets/LL_pneumonia_train_1.png" alt="train the model" width="800">

The right side panel opens and shows the model training progress. This process can take a few minutes.

[image]

Once training finishes, you will see the model's predictions and performance information. You can click the model tile in the side panel to see more detailed information. In most real-world use cases, you might need to upload and label more images to improve performance. In this example, the model should be performing well, so we will go to the next step, which is deploying the model.

[image]

If you want to see more detailed model performance data, click the **Models** tab open the model.

In this example, the trained model should be already performing well. 

<img src="lai_landinglens_models.png" alt="LAI models page">

### Deploying the model to an endpoint

Once you are satisfied with the model performance, you can deploy it to an endpoint. To do that, click on the "Deploy" button in the models tab. Select "Cloud deployment", give the new endpoint a name and hit "Deploy".

<img src="lai_landinglens_model_deploy.png" alt="LAI deploying a model">


Once the model is deployed, you will be redirected to the "Deploy" tab, with your new endpoint already selected. In this tab, you will need to get the endpoint URL, which you can use to make predictions with the model.

<img src="lai_landinglens_deployment_tab.png" alt="LAI model tab">

LandingLens provide several ways to run inferences using your trained model. You can use the Python library to integrate the model with your applications with very few lines of code. You can find the documentation for the Python library [here](https://landing-ai.github.io/landingai-python/inferences/snowflake-native-app/).

You can also use LandingEdge ([documentation here](https://support.landing.ai/docs/landingedge-overview)) or Docker deployment ([documentation here](https://support.landing.ai/docs/docker-deploy)) to run inferences on the edge or on your own infrastructure.

<!-- TODO: Uncomment this section once the endpoint function will be available.

Another alternative is using our built-in Snowflake functions to make predictions directly from Snowflake. For example:

```sql
SELECT
    -- Replace "ac104c43-c6eb-4d1a-8a94-cfaf3dae8f70" below with the deployed cloud endpoint ID
    LANDING_APP_NAME.code.run_inference(file_url_column, 'ac104c43-c6eb-4d1a-8a94-cfaf3dae8f70') as inference
FROM table_with_image_files
WHERE
    some_condition = true;
```
-->

For permissions needed to use LandingEdge, Docker deployment and Snowflake functions, please check the "Settings" tab in the LandingLens installer.


<!-- ------------------------ -->
## Conclusion And Resources
Duration: 2

Thanks to RelationalAI’s Native App on Snowflake, we built a recommendation system with just a few steps. Although the dataset used was a small graph with thousands of nodes and edges, our solution can scale to real world datasets due to our cloud-native architecture that separates compute from storage.

In this Quickstart you learned

- How to find and install the RelationalAI Native App from the Snowflake Marketplace
- How to build a knowledge graph on top of your Snowflake data without having to extract data from Snowflake
- How to create a recommender system using graph algorithms on the MovieLens 100k dataset.

### Related Resources
- To learn about more about RelationalAI and view full documentation, visit [https://relational.ai](https://relational.ai)
- To see a brief summary of the recommender system you just built, see [Blogpost](https://medium.com/@haythemtellili/recommender-systems-with-relationalais-snowflake-native-app-68d9c76bb07f)
- [Snowflake Marketplace](https://app.snowflake.com/marketplace)
- More info on [Snowflake Native Apps](https://docs.snowflake.com/en/developer-guide/native-apps/native-apps-about)
