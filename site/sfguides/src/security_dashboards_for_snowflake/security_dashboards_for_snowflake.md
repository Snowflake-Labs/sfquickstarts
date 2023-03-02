author: 
id: security_dashboards_for_snowflake
summary: This is a sample Snowflake Guide
categories: Getting-Started
environments: web
status: Published 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Security, SnowSight, Dashboards

# Snowflake Security Dashboards
<!-- ------------------------ -->
## Why Make Security Dashboards?
Duration: 2

The Security Field CTO team at Snowflake has talked with thousands of Snowflake customers over the years. Most of them have a simple request. "Tell us how to do security well for Snowflake, please." It's a reasonbale thing to ask. We've tried many ways to deliver the answer to this question from checklists and tutorials to documents and slides. In 2021, we started a project (code named "Snow Sentry") which aimed to take much of that advice and make it into code. We created a set of sample tiles contained in a single dashboard to act as an MVP for monitoring security items in Snowflake. You will build a replica of that MVP during this quickstart. 

### Who Should Use These Dashboards?

These dashboards are for any Snowflake customer who wants gain deeper understanding of Snowflake account in the following areas:

- Configuration drift: Deviations from baseline normal to network policies, security integrations, replication, and failback-enabled Snowflake Accounts
- Authentication patterns: Failed login attempts organized by user and reason and account-wide visibility of authentication types in use
- Roles: RBAC maturity ratings, AccountAdmin usage monitoring, least-used roles for users
- Users: Most dangerous user, disabled users not yet dropped, and users with stale passwords

### Prerequisites
- Familiarity with Snowflake's Snowsight tile creation and management
- Basic SQL skills
- Accountadmin role for the Snowflake Account where you will work

### What You’ll Learn 
- How to use SQL to explore Snowflake's security auditing and configuration metadata
- The items the Security Field CTO team thinks are the right starting point for understanding the security posture of your Snowflake Account(s)

### What You’ll Need 
- A Snowflake Account

### What You’ll Build 
- A set of Security dashboards for Snowflake

<!-- ------------------------ -->
## Getting Started with Snowflake's SnowSight Tiles
Duration: 1

Throughout this quickstart we will be creating tiles (i.e. charts, graphs) that will be part of dashboards to display the information we want to see. The steps to create thse tiles are not the core part of this, but without the ability to do the basics here, you will get lost pretty quickly. So we will spend the time to step through how to do this in detail for the first tile, but then all the following tiles will assume you know how to do what's needed and only give basic guidance and sample end results. 

The majority of what you should need to know is in the documentation here:
- [Visualizing Data With Dashboards](https://docs.snowflake.com/en/user-guide/ui-snowsight-dashboards)



<!-- ------------------------ -->
## Create the Dashboard and the First Tile
Duration: 10

First, you will need to set up some background items to prepare. We will create a special role, grant it rights, and then grant that role to the user you are using during this work. You can do this in whatever UI or other tool you want at this point. 

```
use role accountadmin; 
create role secdashboards;
grant imported privileges on database snowflake to role secdashboards;
grant usage on warehouse <YOURWAREHOUSE> to role secdashboards;
grant role secdashboards to user <YOURUSER>;
```

Now we have a role named `secdashboards` that has access to the proper resources. Each time you want to use these dashboards, you would set your context to use these resources, like so: 

```
use role secdashboards;
use warehouse <YOURWAREHOUSE>;
use database snowflake;
use schema account_usage;
```

This will ensure you are using the right resources to make the SQL we will write in the next sections function correctly. It also means that all you will need to do in order to give people access to this information is grant them access to that role or a role with equivalent access to the equivalent resources. 

Now you will log into the Snowflake UI, [Snowsight](https://docs.snowflake.com/en/user-guide/ui-snowsight). Then you will navigate to the "Dashboards" section on the left menu:

![Dashboards Menu](assets/snowsight_dashboards_menu.png)

Then you will set your role context to the role create earlier:

![Set Role](assets/snowsight_set_role.png)

Click the big, blue "+ Dashboard" button on the top, right of the screen to start a new dashboard, and name it "Security Dashboard Quickstart." You may see that there is no warehouse selected for the dashboard at this point depending on how you arrived here. If so, set the warehouse to the one you granted to the role in the earlier steps:

![Set Warehouse](assets/dashboard_select_warehouse.png)

To complete this step, we will create a single tile that we will go through step by step. First, let's look at what the completed tile will look like:

![First Complete Tile](assets/login_failures_full_chart_config.png)

Let's go through how to create this tile step by step.
1. Click the big, blue "+ New Tile" button at the center of your blank dashboard. 
2. Your context here should be set to `SNOWFLAKE.ACCOUNT_USAGE` in the upper, right hand corner of the editing area. If not, use the drop down to set it to that.
![Set Tile Context](assets/firstTile_set_context.png)
3. Add the SQL for our first tile, which is: 
```sql 
select
    user_name,
    error_message,
    count(*) num_of_failures
from
    login_history
where
    is_success = 'NO'
group by
    user_name,
    error_message
order by
    num_of_failures desc;
```
4. After pasting the code into the editing area, running it, and clicking the "Chart" button at the divider between the editing area and the results area, you should see something that looks like this:
![Set Tile Context](assets/firstTile_first_chart.png)
5. In the Chart area, click on the date in the upper, left hand corner and edit this to be the name "`Authentication: Failures, by User and Reason`".
6. On the right hand side, change the "Chart Type" to "Bar."
7. Continuing on the right hand side, use the drop down to the left of "X-Axis" to change the "Column" to "USER_NAME".
8. Under that "USER_NAME" clikc the "+ Add column" button, and select the "ERROR_MESSAGE" Column. It should then appear above the "USER_NAME" as a "Series", like so:
![Set Tile Data Columns](assets/firstTile_data_set.png)
9. Continuing on the right hand side, under the Appearance heading click the icon on the right to the right of "Grouping" which will change the chart. You will know you have the right one if the "Stretching" label appears beneath it (though you do not need to adjust that new setting). 
10. Continuing on the right hand side, click the check box next to "Label X-Axis" and make the input box read "User". Then click the checkbox next to "Label Y-Axis" and make the input box read "Login Failures".

At this point, your chart should look very close to the final result shared above. The size of the bars, names, and errors you may see woudl be different because of the actual data, of course. The labels, title text, type of bars, and other details should be the same. 

Now you can click the blue "- Return to Security Dashboa..." link in the upper left hand corner of the tile editing widget, and you should end up in a dashboard with a single tile like so:
![Final state of first tile](assets/firstTile_final.png)

As an FYI, the black bars appearing in these screen shots are simply to block out information specific to our testing area where these screens came from. You do not need to see those in your tiles.

From this point on, Tiles will be presented in their final form and the instructions will focus on what SQL and other details you will use. Hopefully, this walkthrough has given you a thurough idea of how to manipulate the Tile editor well enough to make the rest that follow.

<!-- ------------------------ -->
## Authentication Tiles
Duration: 5

Our Security Dashboard will have two tiles focusing on authentication data. The first is the "`Authentication: Failures, by User and Reason`" tile we made in the last section to assist in Tile editing. This shows that the Snowflake audit trail is capturing all the information you need to track the health of authentication events.

The second will be named "`Authentication: Breakdown by Method`", and it will appear like so:
![Final state of authn breakdown tile](assets/tile_authn_by_method.png)

The SQL for this tile is:
```sql
select
   first_authentication_factor || ' ' ||nvl(second_authentication_factor, '') as authentication_method
   , count(*)
    from login_history
    where is_success = 'YES'
    and user_name != 'WORKSHEETS_APP_USER'
    group by authentication_method
    order by count(*) desc;
```
Similar to the failure tracking, ensuring that people are using the right authenitcation methods is crucial. This tile shows how to break down what methods are being used and by whom.

By default, these tiles will now be side by side. But you can drag them so they appear one under the other if you wish. We find that makes this information dense visual easier to read, but you can arrange it how you see fit. 

Since this dashboard only aims to be an MVP, this is a chance to ask yourself what else you may want to know about authentication. Now you will know where to find it. That is a theme that will repeat through the other sections, too.


<!-- ------------------------ -->
## Privileged Access Tiles
Duration: 6

Keeping and eye on those with Privileged Access to any system is a must for good security practice. These tiles show you how you can do that with the audit trail Snowflake is providing to you. There are two tiles in this category. 

First is the "`Privileged Access: ACCOUNTADMIN Grants`" tile. This will be a simple table, and will look like this:
![AA grants tile final state](assets/tile_aa_grnats.png)
The SQL for this tile is:
```sql
select
    user_name || ' granted the ' || role_name || ' role on ' || end_time as Description, query_text as Statement
from
    query_history
where
    execution_status = 'SUCCESS'
    and query_type = 'GRANT'
    and query_text ilike '%grant%accountadmin%to%'
order by
    end_time desc;
```

The second tile is the "`Privileged Access: ACCOUNTADMIN's that do not use MFA`" tile. The name says it all. Here we're looking for people that have elevated access, but are not using the powerful protection that MFA (Multi-Factor Authentication) provides. The tile will look like this:
![AA without MFA tile final state](assets/tile_aa_no_mfa.png)
The SQL for this tile is:
```sql
select u.name, 
timediff(days, last_success_login, current_timestamp()) || ' days ago' last_login ,
timediff(days, password_last_set_time,current_timestamp(6)) || ' days ago' password_age
from users u
join grants_to_users g on grantee_name = name and role = 'ACCOUNTADMIN' and g.deleted_on is null
where ext_authn_duo = false and u.deleted_on is null and has_password = true
order by last_success_login desc;
```
An obvious extention to these tiles would be to include other built in roles like `SYSADMIN` and `SECURITYADMIN` in addition to the `ACCOUNTADMIN` role. Less obvious but similarly powerful would be to include roles that have these roles granted to them. Perhaps you can even include roles that you have created which you know to have a great deal of power for reasons only obviousl to your orgnaization. 

<!-- ------------------------ -->
## Identity Management Tiles
Duration: 6

Governing users well is arguably the most important thing one can do to have healthy security outcomes. These three tiles will look at some of the basics everyone should be watching in every system. 

First is the "`Identity Management: Users by oldest Passwords`" tile. It's worth pointing out that you can use [Password Policies](https://docs.snowflake.com/en/sql-reference/sql/create-password-policy) in Snowflake to proactively control the age of passwords for users. However, many organization have not yet applied these policies or have exceptions for service accounts or other types of users. So this will keep an eye on compliance to your policies even when it can't be limited proactively. The tile will look like this:
![Old Passwords tile final state](assets/tile_iam_old_passwords.png)
The SQL for this tile is:
```sql
select name, datediff('day', password_last_set_time, current_timestamp()) || ' days ago' as password_last_changed from users 
where deleted_on is null and 
password_last_set_time is not null
order by password_last_set_time;
```

Next is the "`Identity Management: Stale Users`" tile. Here we're looking to see the last login for each user principal. The tile will look like this:
![Stale Users tile final state](assets/tile_iam_stale_users.png)
The SQL for this tile is:
```sql
select name, datediff("day", nvl(last_success_login, created_on), current_timestamp()) || ' days ago' Last_Login from users 
where deleted_on is null
order by datediff("day", nvl(last_success_login, created_on), current_timestamp()) desc;
```

The third and final is the "`Identity Management: SCIM Token Lifecycle`" tile. [SCIM (System for Cross-domain Identity Management)](https://docs.snowflake.com/en/user-guide/scim) is an open specification to help facilitate the automated management of user identities and groups (i.e. roles) in cloud applications using RESTful APIs. Since it's doing such sensitive work, the token used by the SCIM provider system making these changes is very powerful, and making sure it's healthy and well managed is imperative. The tile will look like this:
![SCIM Token tile final state](assets/tile_scim_tokens.png)
The SQL for this tile is:
```sql
select
    user_name as by_whom,
    datediff('day', start_time, current_timestamp()) || ' days ago' as created_on,
    ADD_MONTHS(start_time, 6) as expires_on,
    datediff(
        'day',
        current_timestamp(),
        ADD_MONTHS(end_time, 6)
    ) as expires_in_days
from
    query_history
where
    execution_status = 'SUCCESS'
    and query_text ilike 'select%SYSTEM$GENERATE_SCIM_ACCESS_TOKEN%'
    and query_text not ilike 'select%where%SYSTEM$GENERATE_SCIM_ACCESS_TOKEN%'
order by
    expires_in_days;
```

Again, there are many more aspects to Identity Management which deserve to be plunged into. The goal here is to create an MVP, and leave you with the tools to take that plunge now that you know where the pool is and which side is the deep end so you don't hurt yourself diving into the wrong places. 

<!-- ------------------------ -->
## Least Privileged Access Tiles
Duration: 5

A close second to Identity Management is Entitlement Management. The ideal for this is achiving Least Privileged Access, the state where user and roles have only exactly the entitlements required to accomplish their authorized business goals. There are two tiles we have created to help with that. 

First there is the "`Least Privileged Access: Most Dangerous Person`" tile. The cheeky title does relate to a real idea of technical risk. To rise to the top of this someone must have the most entitlements granted in the system overall. The tile will look like this:
![Most Dangerous Person tile final state](assets/tile_most_danger_person.png)
The SQL for this tile is:
```sql
with role_hier as (
    --Extract all Roles
    select
        grantee_name,
        name
    from
        grants_to_roles
    where
        granted_on = 'ROLE'
        and privilege = 'USAGE'
        and deleted_on is null
    union all
        --Adding in dummy records for "root" roles
    select
        'root',
        r.name
    from
        roles r
    where
        deleted_on is null
        and not exists (
            select
                1
            from
                grants_to_roles gtr
            where
                gtr.granted_on = 'ROLE'
                and gtr.privilege = 'USAGE'
                and gtr.name = r.name
                and deleted_on is null
        )
) --CONNECT BY to create the polyarchy and SYS_CONNECT_BY_PATH to flatten it
,
role_path_pre as(
    select
        name,
        level,
        sys_connect_by_path(name, ' -> ') as path
    from
        role_hier connect by grantee_name = prior name start with grantee_name = 'root'
    order by
        path
) --Removing leading delimiter separately since there is some issue with how it interacted with sys_connect_by_path
,
role_path as (
    select
        name,
        level,
        substr(path, len(' -> ')) as path
    from
        role_path_pre
) --Joining in privileges from GRANT_TO_ROLES
,
role_path_privs as (
    select
        path,
        rp.name as role_name,
        privs.privilege,
        granted_on,
        privs.name as priv_name,
        'Role ' || path || ' has ' || privilege || ' on ' || granted_on || ' ' || privs.name as Description
    from
        role_path rp
        left join grants_to_roles privs on rp.name = privs.grantee_name
        and privs.granted_on != 'ROLE'
        and deleted_on is null
    order by
        path
) --Aggregate total number of priv's per role, including hierarchy
,
role_path_privs_agg as (
    select
        trim(split(path, ' -> ') [0]) role,
        count(*) num_of_privs
    from
        role_path_privs
    group by
        trim(split(path, ' -> ') [0])
    order by
        count(*) desc
) --Most Dangerous Man - final query
select
    grantee_name as user,
    count(a.role) num_of_roles,
    sum(num_of_privs) num_of_privs
from
    grants_to_users u
    join role_path_privs_agg a on a.role = u.role
where
    u.deleted_on is null
group by
    user
order by
    num_of_privs desc;
```

Second is the "`Least Privileged Access: Most Bloated Roles`" tile. This is the sister to the most dangerous person. The most bloated role is the role that has the most entitlements. A user with several of these would easily start rising to the top of the last tile. The tile will look like this:
![Most Bloated Role tile final state](assets/tile_bloated_role.png)
The SQL for this tile is:
```sql
--Role Hierarchy
with role_hier as (
    --Extract all Roles
    select
        grantee_name,
        name
    from
        grants_to_roles
    where
        granted_on = 'ROLE'
        and privilege = 'USAGE'
        and deleted_on is null
    union all
        --Adding in dummy records for "root" roles
    select
        'root',
        r.name
    from
        roles r
    where
        deleted_on is null
        and not exists (
            select
                1
            from
                grants_to_roles gtr
            where
                gtr.granted_on = 'ROLE'
                and gtr.privilege = 'USAGE'
                and gtr.name = r.name
                and deleted_on is null
        )
) --CONNECT BY to create the polyarchy and SYS_CONNECT_BY_PATH to flatten it
,
role_path_pre as(
    select
        name,
        level,
        sys_connect_by_path(name, ' -> ') as path
    from
        role_hier connect by grantee_name = prior name start with grantee_name = 'root'
    order by
        path
) --Removing leading delimiter separately since there is some issue with how it interacted with sys_connect_by_path
,
role_path as (
    select
        name,
        level,
        substr(path, len(' -> ')) as path
    from
        role_path_pre
) --Joining in privileges from GRANT_TO_ROLES
,
role_path_privs as (
    select
        path,
        rp.name as role_name,
        privs.privilege,
        granted_on,
        privs.name as priv_name,
        'Role ' || path || ' has ' || privilege || ' on ' || granted_on || ' ' || privs.name as Description
    from
        role_path rp
        left join grants_to_roles privs on rp.name = privs.grantee_name
        and privs.granted_on != 'ROLE'
        and deleted_on is null
    order by
        path
) --Aggregate total number of priv's per role, including hierarchy
,
role_path_privs_agg as (
    select
        trim(split(path, ' -> ') [0]) role,
        count(*) num_of_privs
    from
        role_path_privs
    group by
        trim(split(path, ' -> ') [0])
    order by
        count(*) desc
) 
select * from role_path_privs_agg order by num_of_privs desc
```

Since these tiles are doing a deeper level of analysis, the SQL is much more complex. Even with that complexity, there are likely areas to imagine pulling in more information, or aiming similar analysis at other aspects of the system like user that have the most code deployed in the form of SnowPark or stored procedures. 

<!-- ------------------------ -->
## Network Policy Tile
Duration: 2

There are many types of policy that control security properties of your Snowflake Accounts. One of the most crucial is the Network Policy, which decides what network origination points will be allowed to connect to your Snowflake Accounts. This will help you track when any changes are made to these policies. The tile will look like this:
![Network POlicy changes tile final state](assets/tile_net_policy_changes.png)
The SQL for this tile is:
```sql
select user_name || ' made the following Network Policy change on ' || end_time || ' [' ||  query_text || ']' as Events
   from query_history where execution_status = 'SUCCESS'
   and query_type in ('CREATE_NETWORK_POLICY', 'ALTER_NETWORK_POLICY', 'DROP_NETWORK_POLICY')
   or (query_text ilike '% set network_policy%' or
       query_text ilike '% unset network_policy%')
       and query_type != 'SELECT' and query_type != 'UNKNOWN'
   order by end_time desc;
```

You can easily modify this to watch for modifications for any of the policies controling access to your Snowflake Accounts.

<!-- ------------------------ -->
## Conclusion
Duration: 2

The Security Dashboard you've built here is a starting point. The hope is you've seen that all the information you would likely want to use is available, and we make it relatively easy to get that information displayed in a useful way. 

If you want to learn more about Snowflake security, checkout the official documentation here: [Summary of Security Features (Docs)](https://docs.snowflake.com/user-guide/admin-security). There is also a lot more information about Security at Snowflake here: [Snowflake Security & Trust Center](https://www.snowflake.com/product/security-and-trust-center/). 

### What we've covered
- How to use Snowsight to create dashboard tiles
- Using the Snowflake audit trail to find security data
- Building tiles to explore your Snowflake security data