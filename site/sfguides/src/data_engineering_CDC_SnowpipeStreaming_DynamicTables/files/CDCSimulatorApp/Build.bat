 javac -cp classes;lib/* -d classes src/snowflake/utils/*.java
 javac -cp classes;lib/* -d classes src/snowflake/demo/samples/*.java
 javac -cp classes;lib/* -d classes src/snowflake/demo/*.java


jar cfm CDCSimulatorClient.jar manifest.txt -C classes snowflake src snowflake.properties
