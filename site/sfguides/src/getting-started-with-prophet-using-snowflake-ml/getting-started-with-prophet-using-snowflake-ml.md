author: Ranjeeta Pegu
id: getting-started-with-prophet-using-snowflake-ml
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/platform, snowflake-site:taxonomy/product/applications-and-collaboration
language: en
summary: This is a sample Snowflake Guide to get started with Prophet 
environments: web
status: Published 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
fork repo link: https://github.com/Snowflake-Labs/sfguide-getting-started-with-prophet-using-snowflake-ml





# Getting Started with Prophet Model using Snowflake ML
<!-- ------------------------ -->
## Overview 


This guide shows how to create and log a Prophet forecasting model using Snowflake ML. 

Snowflake also lets you log models beyond the [built-in](https://docs.snowflake.com/en/developer-guide/snowflake-ml/model-registry/built-in-models/overview) types like Prophet model , as long as they’re serializable and extend the CustomModel class from snowflake.ml.model.

You can get more information [here](https://docs.snowflake.com/en/developer-guide/snowflake-ml/model-registry/bring-your-own-model-types)

### What is Prophet
The Prophet model is a time series forecasting tool developed by Facebook, designed to handle seasonality, holidays, and trend changes in data. It’s especially useful for business time series (like sales or traffic) and is robust to missing data and outliers.

### Prerequisites
- Access to [snowflake account](https://signup.snowflake.com/?utm_source=snowflake-devrel&utm_medium=developer-guides&utm_cta=developer-guides) with ACCOUNTADMIN role

### What You’ll Learn 
- How to build a time series forecasting model using Facebook Prophet

- How to wrap the model using Snowflake’s CustomModel class

- How to log and register the model in Snowflake ML

- How to run predictions using the logged model directly in Snowflake


### What You’ll Build 
- A Prophet model for time series forecasting, developed in a Snowflake Notebook

- Model training and inference running directly in a Snowflake warehouse

- The model logged and registered in the Snowflake ML registry for future use

<!-- ------------------------ -->
## Setup

**Step 1.** In Snowsight, [create a SQL Worksheet](https://docs.snowflake.com/en/user-guide/ui-snowsight-worksheets-gs?_fsi=THrZMtDg,%20THrZMtDg&_fsi=THrZMtDg,%20THrZMtDg#create-worksheets-from-a-sql-file) and open [setup.sql](https://github.com/Snowflake-Labs/sfguide-getting-started-with-prophet-using-snowflake-ml/blob/main/setup.sql) to execute all statements in order from top to bottom.

**Step 2.** Download the [SNF_PROPHET_FORECAST_MODEL.ipynb](https://github.com/Snowflake-Labs/sfguide-getting-started-with-prophet-using-snowflake-ml/blob/main/SNF_PROPHET_FORECAST_MODEL.ipynb) and [PROPHET_PREDICTION.ipynb](https://github.com/Snowflake-Labs/sfguide-getting-started-with-prophet-using-snowflake-ml/blob/main/PROPHET_PREDICTION.ipynb)

**Step 3.**  In Snowsight , switch to the FR_SCIENTIST role and import the notebook file downloaded in step 2. Use Database as ML_MODELS , schema as DS and warehouse as ML_FS_WH


<!-- ------------------------ -->
## Run Notebook
1. **Set up environment and import libraries**  
   After importing the necessary libraries and setting up the environment, create synthetic data.

2. **Train the model on synthetic data**  
   Train the Prophet model using the synthetic dataset.

3. **Pickle the trained model and upload it to the stage**  
   Serialize the trained model using `pickle` and upload it to a Snowflake stage.

```pickle.dump(my_forcast_model, open('ProphetModel.pkl', 'wb'))

## Uplad the model into stage
session.file.put("ProphetModel.pkl", f"@{stage_nm}/", auto_compress=False)
```
- Create the custom model 
```
# Initialize ModelContext with keyword arguments
# my_model can be any supported model type
# my_file_path is a local pickle file path

mc = custom_model.ModelContext(
    artifacts={
        'config': 'ProphetModel.pkl'
    }
)


# Define a custom model class that utilizes the context
class MyProphetModel(custom_model.CustomModel):

    def __init__(self,context:custom_model.ModelContext) -> None:
        super().__init__(context)
        ## use 'file_path to load the piecked object
        with open(self.context['config'],'rb') as f:
            self.model =pickle.load(f)
    @custom_model.inference_api
    def predict(self,X:pd.DataFrame) -> pd.DataFrame:
        X_copy = X.copy()
        X_copy['ds']=pd.to_datetime(X_copy['ds'])# ensure correrct datetime
        forecast = self.model.predict(X_copy)
        res_df = forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]]
        return res_df
```

- Model registry 
```reg = Registry(session,database_name = db,schema_name= schema)

custom_mv = reg.log_model(
   forecast_model,
    model_name="Prophet_forcast_model",
    version_name="v1",
    conda_dependencies=["prophet"],
    sample_input_data= df_1,
    options={'relax_version': False},
    comment = 'My Prophet forcast experiment using the CustomModel API'
)
```
- Inference Notebook
use the [PROHPET_PREDICTION](https://github.com/Snowflake-Labs/sfguide-getting-started-with-prophet-using-snowflake-ml/blob/main/PROPHET_PREDICTION.ipynb) notebook

```
reg = Registry(session,database_name = db,schema_name= schema)
model_name='PROPHET_FORCAST_MODEL'
version = 'V1'
mv = reg.get_model('PROPHET_FORCAST_MODEL').version('VERSION_2')
predicted_sales = mv.run(forecast_dates)
```

<!-- ------------------------ -->
## Conclusion And Resources

Congratulations! You’ve successfully built a Prophet forecasting model in a Snowflake Notebook and logged the trained model to the Snowflake ML registry, making it ready for inference and future use.

### What You Learned
- How to build a time series forecasting model using Facebook Prophet

- How to develop and run the model directly in a Snowflake Notebook

- How to wrap the model using Snowflake’s CustomModel class

- How to log and register the model in the Snowflake ML registry

- How to run predictions on new data using the registered model within Snowflake

### Related Resources
- [GitHub Repo](https://github.com/Snowflake-Labs/sfguide-getting-started-with-prophet-using-snowflake-ml)
- [Snowflake Logging Custom Models](https://docs.snowflake.com/en/developer-guide/snowflake-ml/model-registry/bring-your-own-model-types)
- [Snowflake ML](/en/data-cloud/snowflake-ml/)
- [Prophet Forecast Model](https://facebook.github.io/prophet/docs/quick_start.html)