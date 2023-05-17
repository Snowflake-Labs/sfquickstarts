author: gflomo@hex.tech
id: hex-churn-model
summary: This lab will walk you through how to use Snowflake and Hex.
categories: data-science-&-ml,partner-integrations
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Hex, Notebooks, Partner Connect

# Don't let your customers slip away: A guide to churn modeling using Snowflake and Hex



## Lab Overview 
In this demo, we will play the role of a data scientist at a telecom company that wants to identify users who are at high risk of churning. To accomplish this, we need to build a model that can learn how to identify such users. We will demonstrate how to use Hex in conjunction with Snowflake/Snowpark to build a Random Forest Classifier to help us with this task.

### Prerequisites
* Familiarity with basic Python and SQL
* Familiarity with training ML models
* Familiarity with data science notebooks



### What You'll Learn
* How to import/export data between Hex and Snowflake
* How to train a Random Forest model and deploy to Snowflake using UDFs
* How to visualize the predicted results from the forecasting model
* How to convert a Hex project into an interactive web app and make predictions on new users






<!-- ------------------------ -->
## Creating a Snowflake account
Go to the [Snowflake](https://signup.snowflake.com/) sign-up page and register for a free account. After registration, you will receive an email containing a link that will take you to Snowflake, where you can sign in.

## Setting up partner connect
After logging into your Snowflake account, you will land on the `Learn` page. To connect with Hex, navigate to the `Admin` tab on the left and click on `Partner connect`. In the search bar at the top, type `Hex` and the Hex partner connect tile will appear. Clicking on the tile will bring up a new screen, and click the `connect button` in the lower right corner. A new screen will confirm that your account has been created, from which you can click `Activate`.

![](assets/pc.gif)


### Creating a workspace
After activating your account, you'll be directed to Hex and prompted to create a new workspace and give it a name. Once you've named your workspace, you'll be taken to the projects page where you can create new projects, import existing projects (Hex or Jupyter), and navigate to other sections of your workspace.


## Getting Started with Hex
Now we can move back over to Hex and get started on our project. The first thing you'll need to do is download the Hex project that contains all of the code to train our model.

<button>

[Download Hex project](https://static.hex.site/SFS_Churn_model_yaml.yaml)

</button>

![](assets/import.gif)

Now that you've got your project imported, you will find yourself in the [Logic view](https://learn.hex.tech/docs/develop-logic/logic-view-overview) of a Hex project. The Logic view is a notebook-like interface made up of cells such as code cells, markdown cells, input parameters and more! On the far left side, you'll see a control panel that will allow you to do things like upload files, import data connections, or search your project. Before we dive into the code, we'll need to:

1. Change our compute profile to run Python 3.8
2. Import our Snowflake data connection

Which we can do all from the left control panel. To change the compute profile, click on the Environments tab represented by a cube. At the top of this section you'll see the compute profile portion at the top. Click on the Image dropdown and select Python 3.8.

![](assets/3.8.gif)

Next we can import our data connection by heading over to the Data sources tab represented by a database icon with a lightning bolt. You should see two data connections -  [Demo] Hex public data and Snowflake. Import both connections. 

![](assets/DC.gif)

One nice feature of Hex is the [reactive execution model](https://learn.hex.tech/docs/develop-logic/compute-model/reactive-execution). This means that when you run a cell, all related cells are also executed so that your projects are always in a clean state. However, to ensure we don’t get ahead of ourselves, were going to turn this feature off. In the top right corner of your screen, you’ll see a Run mode dropdown. If this is set to Auto, select the dropdown and change it to cell only.

![](assets/mode.gif)


## Reading and writing data 
To predict customer churn, we first need data to train our model. In the SQL cell labeled **Pull churn results** assign `[Demo] Hex public data` as the data connection source and run the cell.

```SQL
select * from "DEMO_DATA"."DEMOS"."TELECOM_CHURN"
```

At the bottom of this cell, you will see a green output variable labeled `dataframe`. This is a Pandas dataframe, and we are going to write it back into our `Snowflake` data connection. To do so, input the following configurations to the writeback cell (labeled: **Writeback to snowflake)**

- **Source**: dataframe
- **Connection**: Snowflake
- **Database**: PC_HEX_DB
- **Schema**: Public
- **Table**: *Static* and name it CHURN

Once the config is set, enable `Logic session` as the writeback mode (in the upper right of the cell) and run the cell.

In the SQL cell labeled **Churn data**, change the data source to `Snowflake` and execute the cell. You will see a green output variable at the bottom. Double-click on it and rename it to `data`.
## Data preparation 
Now that we have our data in Hex, we want to make sure the it’s clean enough for our machine learning algorithm. To ensure this, we’ll first check for any null values.

```python
data.isnull().sum()
```
Now that we have checked for null values, let's look at the distribution of each variable.

```python
# create a 15x5 figure
plt.figure(figsize=(15, 5))

# create a new plot for each variable in our dataframe
for i, (k, v) in enumerate(data.items(), 1):
    plt.subplot(3, 5, i)  # create subplots
    plt.hist(v, bins = 50)
    plt.title(f'{k}')

plt.tight_layout()
plt.show();
```

![](assets/chart.png)

The charts' results allow us to visualize each variables distribution, which can help us identify early signs of skewness, among other things. We can see that all of our continuous variables follow a fairly normal distribution, and further transformations won't be necessary. The `DataUsage` column appears a little off because many customers use 0GB of data, but there are also a lot of users who didn't have data plans in the first place, so this isn't considered an anomaly.
## Understanding churn rate
If you take a look at our visuals, you may notice that the churn chart looks a little odd. Specifically, it looks like there are a lot more users who haven’t churned than who have.  

We take a closer look at this by visualizing in a chart cell.

![](assets/imbal.png)
As you can see, the majority of observations are in support of user who haven’t yet churned. Specifically, 85% of user haven’t churned while the other 15% has. In machine learning, a class imbalance such as this can cause issues when evaluating the model since it’s not getting equal attention from each class. In the next section we will go over a method to combat the imbalance problem.
## Model training
In order to predict the churn outcomes for customers not in our dataset, we’ll need to train a model that can identify users who are at risk of churning from the history of users who have. However, it was mentioned in the last section that there is an imbalance in the class distribution that will cause problems for our model if not handled properly. One way to handle this is to create new data points such that the classes balance out. This is also known as upsampling. 

For this, we’ll be using the `SMOTE` algorithm from the `imblearn` package. Run the code cell labeled **Feature separation and upsampling**.

```python
# Extract the training features
features_names = [col for col in data.columns if col not in ['Churn']]
features = data[features_names]
print(f"Size of data before upsampling {features.shape[0]}")

# extract the target
target = data['Churn']

# upsample the minority class in the dataset
upsampler = SMOTE(random_state = 111)
features, target = upsampler.fit_resample(features, target)
print(f"Size of data after upsampling {features.shape[0]}")
```
Now that we have balanced our dataset, we can prepare our model for training. The model we have chosen for this project is a Random Forest classifier. A random forest creates an ensemble of smaller models that all make predictions on the same data. The prediction with the most votes is the prediction the model chooses.

Instead of coding this ourselves, Hex provides an AI assistant built into the product that is eager to help us out. In the code cell labeled "Model training," paste the following prompt.

`instantiate a random forest object and a standard scaler object. scale the features and then split into a training and testing set. fit the model on the training features.` 

*If Magic isn't showing up for you, there's a chance it's not enabled yet. To enable it,  select the magic toggle in your workspace settings under preferences. See [docs for more](https://learn.hex.tech/docs/develop-logic/hex-magic) info*

![](assets/magic.gif)

The output should look something like this 👇🏾

```python
# import necessary libraries
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split

# instantiate a random forest object
rf = RandomForestClassifier()

# instantiate a standard scaler object
scaler = StandardScaler()

# scale the features
features_scaled = scaler.fit_transform(features)

# split into a training and testing set
X_train, X_test, y_train, y_test = train_test_split(
    features_scaled, target, test_size=0.2, random_state=42
)

# fit the model on the training features
rf.fit(X_train, y_train)
```

It's okay if your output doesn't look exactly like this. However, if you are having issues getting it to work, you can simply copy this code cell.

In the next section, we will look at how well our model performed as well as which features played the most important role when predicting the churn outcome.
## Model evaluation and feature importance
In order to understand how well our model performs at identifying users at risk of churning, we’ll need to evaluate how well it does predicting churn outcomes. Specifically, we’ll be looking at the recall score, which tells us *of all the customers that will churn, how many can it identify.*

Run the code cell labeled **Evaluate model** on *accuracy and recall.*

```python
# run the model on the testing set
predictions = rf.predict(X_test)

# scores
accuracy = round(accuracy_score(y_test, predictions), 3) # How often does it get the right answer
recall = round(recall_score(y_test, predictions), 3) # How many churners were identified correctly
```
This will calculate an accuracy and recall score for us which we'll display in a [single value cell](https://learn.hex.tech/docs/logic-cell-types/display-cells/single-value-cells#single-value-cell-configuration).

### Feature importance

Next, we want to understand which features were deemed most important by the model when making predictions. Lucky for us, our model keeps track of the most important features, and we can access them using the `feature_importances_` attribute. However, this will only show us the score, and we won't know which column the score refers to. To address this, we'll create a dataframe with the combined feature names and scores.

```python
importances = pd.DataFrame(
    list(zip(features.columns, rf.feature_importances_)),
    columns=["feature", "importance"],
)
```
Let’s visualize the most important features. 
![](assets/important.png)

## Predicting churn for a new user 
Now is the moment we've all been waiting for: predicting the churn outcome for a new user. In this section, you should see an array of input parameters already in the project. Each of these inputs allow you to adjust a different feature that goes into predicting customer churn, which will simulate a new user. But we’ll still need to pass this data to our model, so how can we do that?

![](assets/input.png)

Each input parameter has its own variable as its output, and these variables can be referenced in a Python cell. The model expects the inputs it receives to be in a specific order otherwise it will get confused about what the features mean. Keeping this in mind, execute the Python cell labeled ***Create the user vector***.

```python
inputs = [
	    account_weeks,
	    1 if renewed_contract else 0, # This value is a bool and we need to convert to numbers
	    1 if has_data_plan else 0, # This value is a bool and we need to convert to numbers
	    data_usage,
	    customer_service_calls,
	    mins_per_month,
	    daytime_calls,
	    monthly_charge,
	    overage_fee,
	    roam_mins,
]
```
This creates a list where each element represents a feature that our model can understand. However, before our model can accept these features, we need to transform our array. To do this, we will convert our list into a numpy array and reshape it so that there is only one row and one column for all features.

```python
user_vector = np.array(inputs).reshape(1, -1)
```

As a last step, we’ll need to scale our features within the original range that was used during the training phase. We already have a scaler fit on our original data and we can use the same one to scale these features.

```python
user_vector_scaled = scaler.transform(user_vector)
```

The final cell should look like this:
```python
# get model inputs
inputs = [
	    account_weeks,
	    1 if renewed_contract else 0, # This value is a bool and we need to convert to numbers
	    1 if has_data_plan else 0, # This value is a bool and we need to convert to numbers
	    data_usage,
	    customer_service_calls,
	    mins_per_month,
	    daytime_calls,
	    monthly_charge,
	    overage_fee,
	    roam_mins,
]

# reshape and scale the user vector
user_vector = np.array(inputs).reshape(1, -1)
user_vector_scaled = scaler.transform(user_vector)
```

We are now ready to make predictions. In the last code cell labeled ***Make predictions and get results***, we will pass our user vector to the model's predict function, which will output its prediction. We will also obtain the probability for that prediction, allowing us to say: ***"The model is 65% confident that this user will churn."***
```python
# get the predicted value
value = rf.predict(user_vector)[0]

# convert prediction into a string
prediction = 'churn' if value == 1 else 'not churn'

# get the prediction confidence
probability_of_prediction = np.round(max(rf.predict_proba(user_vector)[0]) * 100, 4)
```
To display the results in our project, we can do so in a markdown cell. In this cell, we’ll use Jinja to provide the variables that we want to display on screen. 

```markdown
{% if predict %}
#### The model is {{probability_of_prediction}}% confident that this user will {{prediction}}
{% else %}
#### No prediction has been made yet
{% endif %}
```



## Making Hex apps
At this stage of the project, we have completed building out our logic and are ready to share it with the world. To make the end product more user-friendly, we can use the app builder to simplify our logic. The app builder enables us to rearrange and organize the cells in our logic to hide the irrelevant parts and only show what matters.

![](assets/app.gif)

Once you've arranged your cells and are satisfied with how it looks, use the share button to determine who can see this project and what level of access they have. Once shared, hit the publish button and your app will go live.

![](assets/share.gif)

## Conclusion
Congratulations on on making it to the end of this Lab! You can view the published version of this [project here](https://app.hex.tech/hex-public/app/3987c3db-976e-41c9-a7b0-dec571159260/10/d8ffce15-67ec-4704-96ad-656baad8187f)! 

### What we've covered
- Use Snowflake’s “Partner Connect” to seamlessly create a Hex trial
- How to navigate the Hex workspace/notebooks
- How to train an Random forest model and deploy to Snowflake using UDFs

### Resources
- [Hex docs](https://learn.hex.tech/docs)
- [Snowflake Docs](https://docs.Snowflake.com/en/)





