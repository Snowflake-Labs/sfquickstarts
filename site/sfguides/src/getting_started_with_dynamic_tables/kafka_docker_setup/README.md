# Use this README file for Streaming data into Snowflake using Kafka connect

## Alternatively you can use the instruction to simulate streaming with the Python UDF functions defined in the setup step of this [Quickstart guide](https://quickstarts.snowflake.com/guide/getting_started_with_dynamic_tables/index.html?index=..%2F..index#1).

## OR

## Use Docker to create Kafka streaming enviroment on your local computer and connect it with Snowflake for the Snowpipe Streaming and Dynamic Table Hands on Lab/Demo

## Docker Installation in Windows

### Prerequisites
- Ensure that your system is running a 64-bit version of Windows 10 Pro, Enterprise, or Education. Docker for Windows requires Microsoft Hyper-V to run.
- Make sure that virtualization is enabled in BIOS settings if not already enabled.

### Steps
1. Download Docker Desktop for Windows from the official Docker website: [Docker Desktop for Windows](https://hub.docker.com/editions/community/docker-ce-desktop-windows).
2. Run the installer and follow the installation wizard.
3. During installation, Docker Desktop prompts to enable Hyper-V if it's not enabled. Allow Docker to enable Hyper-V if prompted.
4. After installation, Docker Desktop launches automatically. You'll see the Docker whale icon in the system tray when it's running.

## macOS Installation

### Prerequisites
- Docker Desktop for Mac runs on macOS 10.14 Mojave or newer versions.
- Ensure that your system supports HyperKit.

### Steps
1. Download Docker Desktop for Mac from the official Docker website: [Docker Desktop for Mac](https://hub.docker.com/editions/community/docker-ce-desktop-mac).
2. Open the downloaded `.dmg` file.
3. Drag the Docker icon to the Applications folder to install it.
4. Once installed, launch Docker Desktop from the Applications folder.
5. You may be prompted to provide your system password to install networking components and allow Docker to make changes. Enter your password to proceed.
6. Docker Desktop starts and is running when the whale icon in the status menu is displayed with a green dot.

## Verification
- After installation, you can verify that Docker is installed correctly by opening a terminal or command prompt and running the following command: 
`docker --version`

This command should display the installed Docker version.

## Steps to start the kafka environment
- Download [this zip file on your local desktop or laptop](https://github.com/sfc-gh-pjain/sfguides/tree/master/site/sfguides/src/getting_started_with_dynamic_tables/kafka_docker_setup/kc-demo-shared.zip) and unzip it into a folder called `kc-demo-shared`.
- Go to the new unzipped folder
- Open Snowflake worksheet and copy below code and run it in your Snowflake account to create necessary Database objects required for this demo

```
CREATE DATABASE IF NOT EXISTS DEMO;
CREATE SCHEMA IF NOT EXISTS DEMO.DT_DEMO;
USE SCHEMA DEMO.DT_DEMO;

CREATE WAREHOUSE XSMALL_WH 
WAREHOUSE_TYPE = STANDARD
  WAREHOUSE_SIZE = XSMALL
  AUTO_SUSPEND = 300
  AUTO_RESUME = TRUE;

```

- Generate private and public key. Follow [these instructions and click here](https://docs.snowflake.com/user-guide/kafka-connector-install#using-key-pair-authentication-key-rotation) to create keys and store public key in Snowflake 
- Open the `consumer/sf_streaming.properties` in a text editor and update your Snowflake account and credentials and then save it. The Kafka connector relies on key pair authentication rather than basic authentication (i.e. username and password). For [Account URL look here](https://docs.snowflake.com/en/user-guide/admin-account-identifier)
- Open a terminal or command promt and change dir to the folder called `kc-demo-shared`
- Run `docker compose up` command from this folder. This will take some time to download and deploy the server for the very first run.
- Note that this command will download open source Kafka and necessary libraries from the internet. The hands on lab is for demonstration purpose only and you should check for necessary license and compliance with your own administration team. This demo is not meant for production use.

## After the first run you can simply start and stop the demo by using below commands

### Start Kafka streaming to Snowflake

`docker compose up`


### Stop Kafka streaming to Snowflake

`docker compose down`

### Reset and remove tables created in Snowflake

`drop table IF EXISTS cust_info;`

`drop table IF EXISTS prod_stock_inv;`

`drop table IF EXISTS salesdata;`