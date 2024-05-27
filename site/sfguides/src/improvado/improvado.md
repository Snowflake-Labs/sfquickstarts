author:
id: improvado
summary: Improvado to Snowflake
categories: Getting-Started,partner-integrations
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Getting Started

# Improvado Guide

<!-- ------------------------ -->

## Overview

Duration: 1

This guide will show how to connect Improvado and your Snowflake Destination.

### What Is Improvado?

Improvado is AI-powered marketing analytics & intelligence

### What You’ll Learn

- How to connect Snowflake Destination to your Improvado account

### Prerequisites

- A [Snowflake](https://signup.snowflake.com/) Account
- Access to an Improvado instance. Please reach out to your Improvado Customer Success Manager or [Book a demo](https://improvado.io/register/talk-to-an-expert)

<!-- ------------------------ -->

## Connect Snowflake to Improvado

Duration: 2

### Step 1. Permissions

Grant the following permissions:

- `CREATE`
- `ALTER TABLE`
- `DELETE`
- `INSERT`

### Step 2. Select a destination

This tile menu shows all the Destinations that you can use for data loading.

![Catalog](assets/add_a_new_destination.png)

Click on the **Snowflake** tile.

### Step 3. Complete configuration

On the Snowflake connection page, fill in the following fields:

1. Enter a name for your Destination connection in the Title.
2. Enter the Account.
3. Enter the User Name.
4. Enter the Password.
5. Enter the Database Name.
6. Enter the Warehouse.
7. Specify the Schema of your database.
8. Enter the Role.
   - The `SYSADMIN` role should be granted to the specified user. Make sure you use not a public role because it doesn’t have enough permissions for the load process.
9. Select the necessary Use static IP option from the dropdown.

## Conclusion

You can learn more about Improvado on [official website](https://improvado.io).

You can learn more about the Snowflake partnership with Improvado at [Improvado-Snowflake Partnership](https://improvado.io/blog)
