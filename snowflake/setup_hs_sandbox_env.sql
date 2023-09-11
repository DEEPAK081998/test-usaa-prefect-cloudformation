-- HS SANDBOX env
set environment = 'HS_SANDBOX';

set database_name = $environment || '_DATABASE';
set schema_name = $database_name || '_SCHEMA';

set datapipeline_standard_warehouse_name = $environment || '_STANDARD_WAREHOUSE';
set qs_adhoc_warehouse_name = $environment || '_QS_ADHOC_WAREHOUSE';

set standard_resource_monitor = $environment || '_STANDARD_RESOURCE_MONITOR';
set adhoc_resource_monitor = $environment || '_ADHOC_RESOURCE_MONITOR';

set ownership_role = $environment || '_OWNERSHIP_ROLE';
set read_role = $environment || '_READ_ROLE';
set reporting_dev_role = $environment || '_REPORTING_DEV_ROLE';
set airbyte_source_role = $environment || '_AIRBYTE_SOURCE_ROLE';

set airbyte_username = 'AIRBYTE_USER_' || $environment;
set airbyte_password = '?';
set airbyte_source_username = 'AIRBYTE_SOURCE_USER_' || $environment;
set airbyte_source_password = '?';

set dbt_username = 'DBT_USER_' || $environment;
set dbt_password = '?';

set qs_username = 'QS_USER_' || $environment;
set qs_password = '?';
set qs_adhoc_username = 'QS_ADHOC_USER_' || $environment;
set qs_adhoc_password = '?';

begin;

use role SECURITYADMIN;

-- create needed roles
create role if not exists identifier($ownership_role);
grant role identifier($ownership_role) to role SYSADMIN;

create role if not exists identifier($read_role);
grant role identifier($read_role) to role SYSADMIN;

create role if not exists identifier($reporting_dev_role);
grant role identifier($reporting_dev_role) to role SYSADMIN;

create role if not exists identifier($airbyte_source_role);
grant role identifier($airbyte_source_role) to role SYSADMIN;

-- create Airbyte user
create user if not exists identifier($airbyte_username)
password = $airbyte_password
default_role = $ownership_role
default_warehouse = $datapipeline_standard_warehouse_name;

grant role identifier($ownership_role) to user identifier($airbyte_username);

-- create Airbyte Source user
create user if not exists identifier($airbyte_source_username)
password = $airbyte_source_password
default_role = $airbyte_source_role
default_warehouse = $datapipeline_standard_warehouse_name;

grant role identifier($airbyte_source_role) to user identifier($airbyte_source_username);

-- create DBT user
create user if not exists identifier($dbt_username)
password = $dbt_password
default_role = $ownership_role
default_warehouse = $datapipeline_standard_warehouse_name;

grant role identifier($ownership_role) to user identifier($dbt_username);

-- create Quicksight standard user
create user if not exists identifier($qs_username)
password = $qs_password
default_role = $read_role
default_warehouse = $datapipeline_standard_warehouse_name;

grant role identifier($read_role) to user identifier($qs_username);

-- create Quicksight Ad hoc user
create user if not exists identifier($qs_adhoc_username)
password = $qs_adhoc_password
default_role = $read_role
default_warehouse = $qs_adhoc_warehouse_name;

grant role identifier($read_role) to user identifier($qs_adhoc_username);

-- change role to sysadmin for warehouse / database steps
use role SYSADMIN;

-- create Datapipeline database
create database if not exists identifier($database_name);

-- grant database access
grant OWNERSHIP
on database identifier($database_name)
to role identifier($ownership_role);

grant USAGE
on database identifier($database_name)
to role identifier($ownership_role);

grant USAGE
on database identifier($database_name)
to role identifier($read_role);

grant USAGE
on database identifier($database_name)
to role identifier($reporting_dev_role);

grant USAGE
on database identifier($database_name)
to role identifier($airbyte_source_role);

-- create Standard warehouse
create warehouse if not exists identifier($datapipeline_standard_warehouse_name)
warehouse_size = xsmall
warehouse_type = standard
auto_suspend = 10
auto_resume = true
initially_suspended = true;

-- grant Datapipeline standard warehouse access
grant USAGE
on warehouse identifier($datapipeline_standard_warehouse_name)
to role identifier($ownership_role);

grant USAGE
on warehouse identifier($datapipeline_standard_warehouse_name)
to role identifier($read_role);

grant USAGE
on warehouse identifier($datapipeline_standard_warehouse_name)
to role identifier($reporting_dev_role);

grant USAGE
on warehouse identifier($datapipeline_standard_warehouse_name)
to role identifier($airbyte_source_role);

-- create Ad hoc warehouse
create warehouse if not exists identifier($qs_adhoc_warehouse_name)
warehouse_size = xsmall
warehouse_type = standard
auto_suspend = 10
auto_resume = true
initially_suspended = true;

--grant Ad hoc warehouse access
grant USAGE
on warehouse identifier($qs_adhoc_warehouse_name)
to role identifier($read_role);

commit;

begin;

USE DATABASE identifier($database_name);

-- create schema for Datapipeline data
CREATE SCHEMA IF NOT EXISTS identifier($schema_name);

commit;

begin;

-- grant schema access
grant OWNERSHIP
on schema identifier($schema_name)
to role identifier($ownership_role);
grant USAGE
on schema identifier($schema_name)
to role identifier($ownership_role);
grant OWNERSHIP
on schema identifier('PUBLIC')
to role identifier($ownership_role);
grant OWNERSHIP
on schema identifier('OUTBOUND')
to role identifier($ownership_role);


grant USAGE
on schema identifier('PUBLIC')
to role identifier($reporting_dev_role);

grant USAGE
on schema identifier('OUTBOUND')
to role identifier($reporting_dev_role);

grant USAGE
on schema identifier($schema_name)
to role identifier($read_role);

grant USAGE
on schema identifier('PUBLIC')
to role identifier($read_role);

grant USAGE
on schema identifier('OUTBOUND')
to role identifier($read_role);

grant USAGE
on schema identifier('PUBLIC')
to role identifier($airbyte_source_role);

commit;

begin;

use role ACCOUNTADMIN;

GRANT CREATE SCHEMA
ON DATABASE identifier($database_name)
TO ROLE identifier($reporting_dev_role);

GRANT CREATE TABLE
ON FUTURE SCHEMAS IN DATABASE identifier($database_name)
TO ROLE identifier($reporting_dev_role);

GRANT CREATE VIEW
ON FUTURE SCHEMAS IN DATABASE identifier($database_name)
TO ROLE identifier($reporting_dev_role);

GRANT SELECT ON ALL TABLES
IN SCHEMA identifier('PUBLIC')
TO ROLE identifier($reporting_dev_role);
GRANT SELECT ON FUTURE TABLES
IN SCHEMA identifier('PUBLIC')
TO ROLE identifier($reporting_dev_role);

GRANT SELECT ON ALL VIEWS
IN SCHEMA identifier('PUBLIC')
TO ROLE identifier($reporting_dev_role);
GRANT SELECT ON FUTURE VIEWS
IN SCHEMA identifier('PUBLIC')
TO ROLE identifier($reporting_dev_role);

GRANT SELECT ON ALL TABLES
IN SCHEMA identifier('OUTBOUND')
TO ROLE identifier($reporting_dev_role);
GRANT SELECT ON FUTURE TABLES
IN SCHEMA identifier('OUTBOUND')
TO ROLE identifier($reporting_dev_role);

GRANT SELECT ON ALL VIEWS
IN SCHEMA identifier('OUTBOUND')
TO ROLE identifier($reporting_dev_role);
GRANT SELECT ON FUTURE VIEWS
IN SCHEMA identifier('OUTBOUND')
TO ROLE identifier($reporting_dev_role);

GRANT SELECT ON ALL TABLES
IN SCHEMA identifier('PUBLIC')
TO ROLE identifier($read_role);
GRANT SELECT ON FUTURE TABLES
IN SCHEMA identifier('PUBLIC')
TO ROLE identifier($read_role);

GRANT SELECT ON ALL VIEWS
IN SCHEMA identifier('PUBLIC')
TO ROLE identifier($read_role);
GRANT SELECT ON FUTURE VIEWS
IN SCHEMA identifier('PUBLIC')
TO ROLE identifier($read_role);

GRANT SELECT ON ALL TABLES
IN SCHEMA identifier('OUTBOUND')
TO ROLE identifier($read_role);
GRANT SELECT ON FUTURE TABLES
IN SCHEMA identifier('OUTBOUND')
TO ROLE identifier($read_role);

GRANT SELECT ON ALL VIEWS
IN SCHEMA identifier('OUTBOUND')
TO ROLE identifier($read_role);
GRANT SELECT ON FUTURE VIEWS
IN SCHEMA identifier('OUTBOUND')
TO ROLE identifier($read_role);

GRANT SELECT ON TABLE identifier('PUBLIC.FCT_ROUTING_SCORES')
TO ROLE identifier($airbyte_source_role);

commit;

begin;

use role ACCOUNTADMIN;

create RESOURCE MONITOR if not exists identifier($standard_resource_monitor) with
CREDIT_QUOTA = 4
FREQUENCY = DAILY
START_TIMESTAMP = IMMEDIATELY
NOTIFY_USERS = (SNOWFLAKEADMIN)
TRIGGERS ON 70 PERCENT DO NOTIFY
         ON 80 PERCENT DO SUSPEND
         ON 90 PERCENT DO SUSPEND_IMMEDIATE;

ALTER WAREHOUSE identifier($datapipeline_standard_warehouse_name) SET RESOURCE_MONITOR = $standard_resource_monitor;

create RESOURCE MONITOR if not exists identifier($adhoc_resource_monitor) with
CREDIT_QUOTA = 4
FREQUENCY = DAILY
START_TIMESTAMP = IMMEDIATELY
NOTIFY_USERS = (SNOWFLAKEADMIN)
TRIGGERS ON 70 PERCENT DO NOTIFY
         ON 80 PERCENT DO SUSPEND
         ON 90 PERCENT DO SUSPEND_IMMEDIATE;

ALTER WAREHOUSE identifier($qs_adhoc_warehouse_name) SET RESOURCE_MONITOR = $adhoc_resource_monitor;

commit;
--------------------------------------------------------------------