author: 
id: snaketokens
summary: This is a sample Snowflake Guide
categories: Getting Started
environments: web
status: Published 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Getting Started, Data Science, Data Engineering, Twitter 

# Snowflake Snake Tokens Demo Setup Guide
<!-- ------------------------ -->
## Overview 
Duration: 1

The "Snake-Tokens" Guide will show you how to setup FF3 format preserving encryption (tokenization) in a demo database in your Snowflake account as a "minimum viable" prototype. This means that all the functionality needed for FF3 tokenization 
will be functional to test.

### Prerequisites
- Snowflake Enterprise Edition Account

### What You’ll Learn 
- How to install and use the "Snake-Tokens" Python UDFs in order to run FF3 format preserving encrpytion in test setup in your Snowflake account


### What You’ll Need 
- A [Snowflake Enterprise Edition Account](https://signup.snowflake.com/) 

### What You’ll Build 
- A demo that shows how FF3 tokenization can work in your Snowflake account

<!-- ------------------------ -->
## Metadata Configuration
Duration: 2

It is important to set the correct metadata for your Snowflake Guide. The metadata contains all the information required for listing and publishing your guide and includes the following:


- **summary**: Project Snake Tokens aims to give a working MVP for tokenization in Snowflake using Python. The problem this aims to solve is allowing customers to obfuscate (or “mask”) PII while at the same time not losing the ability to use that data in joins and other operations where the consistency of the data through operations is required. Python offers libraries to achieve this using encryption, and through the use of Snowflake Python UDFs we can apply that to information in Snowflake natively. As an MVP, this is not meant to offer a complete solution to the problem. Rather, this is a framework that others can embrace and extend. 
- **id**: sample 
- **categories**: data-governance 
- **environments**: web 
- **status**: Published
- **feedback link**: https://github.com/Snowflake-Labs/sfguides/issues
- **tags**: Getting Started, Data Governance, Tokenization, Encrpytion
- **authors**: [Kevin Keller](mailto:kevin.keller@snowflake.com) 

---



<!-- ------------------------ -->
## Roles, Database, Schema, Warehouse, Stage and Intial Grants Setup
Duration: 2

A single sfguide consists of multiple steps. These steps are defined in Markdown using Header 2 tag `##`. 

```markdown
## Step 1 Title
Duration: 1


---  Create objects for use in the demo. 
-------------------------------------
--- To walk through this we will use manuy objects, and we need to create those and 
--- grant the rights to them. 

--- Create demo roles 
create or replace role ff3_encrypt;
create or replace role ff3_decrypt;
create or replace role data_sc;

--- Grant demo roles to your demo user
--- Replace <USER> with your demo user
grant role ff3_encrypt to user deadpool;
grant role ff3_decrypt to user deadpool;
grant role data_sc to user deadpool;

--- Create warehouse for demo  
create or replace warehouse ff3_testing_wh warehouse_size=medium initially_suspended=true;

--- Grants on warehouse for demo
grant usage, operate on warehouse ff3_testing_wh to role ff3_encrypt;
grant usage, operate on warehouse ff3_testing_wh to role ff3_decrypt;
grant usage, operate on warehouse ff3_testing_wh to role data_sc;
grant usage, operate on warehouse ff3_testing_wh to role accountadmin;
grant usage, operate on warehouse ff3_testing_wh to role sysadmin;

--- Create demo database and schema for demo
create or replace database ff3_testing_db;
create schema ff3_testing_db.ff3_testing_schema;

use database ff3_testing_db;
use schema ff3_testing_db.ff3_testing_schema;

--- Grants on warehouse for demo
grant usage, operate on warehouse ff3_testing_wh to role ff3_encrypt;
grant usage, operate on warehouse ff3_testing_wh to role ff3_decrypt;
grant usage, operate on warehouse ff3_testing_wh to role data_sc;
grant usage, operate on warehouse ff3_testing_wh to role accountadmin;
grant usage, operate on warehouse ff3_testing_wh to role sysadmin;

--- Create internal stage for the FF3 Python library
create stage python_libs;

ls @python_libs; -- should be empty for now, gets "Query produced no results"

--- Here you have to upload the FF3 Python library from here https://github.com/mysto/python-fpe
--- Git clone this library locally, change (cd) into the python-fpe directory, then zip up the ff3 folder, and
--- upload this zip file into the stage.

--- The whole procedure looks like this (substitute in your local values): 
/*
% mkdir ff3-demo-code
% cd ff3-demo-code/
% git clone https://github.com/mysto/python-fpe
% cd python-fpe/
% zip -r ff3.zip ff3/
% pwd
<PATH>
% snowsql -a <ACCOUNT>.<REGION>.<CLOUD> -u <USER>
* SnowSQL * v1.2.23
Type SQL statements or !help
<USER>#ff3_testing_wh@ff3_testing_db.ff3_testing_schema> put file://<PATH>/ff3.zip @python_libs auto_compress=false;
*/

ls @python_libs; -- should now contain the ff3.zip file


```

<!-- ------------------------ -->



## Tags, Source and Target Table Preparation
Duration: 2

A single sfguide consists of multiple steps. These steps are defined in Markdown using Header 2 tag `##`. 

```markdown
## Step 1 Title
Duration: 3

--- Create tags
create or replace tag ff3_data_sc;
create or replace tag ff3_encrypt;
create or replace tag sqljoin;
create or replace tag email;
create or replace tag uspostal;
create or replace tag usphone;

--- Create source table for encrypt, decrypt and data analyst demo
create or replace table ff3_pass3_source1 (
  name varchar(255) default NULL,
  phone varchar(100) default NULL,
  email varchar(255) default NULL,
  postalZip varchar(10) default NULL,
  integernumber integer NULL,
  floatnumber float NULL,
  decimalnumber number(38,8) NULL
);

--- Populate source table with demo data
insert into ff3_pass3_source1 (name,phone,email,postalZip,integernumber,floatnumber,decimalnumber)
values
  ('Keegan Melendez','(0088) 11345912','sapien@protonmail.edu','31242',1,2.754,6.54),
  ('Daniel Black','(0964) 05573972','ullamcorper.viverra@hotmail.org','98-353',4,343.4,45.8),
  ('Malachi Bass','(047) 36000411','dictum@protonmail.net','52545',5,1.7,698.543),
  ('Gabriel Mcknight','(1) 7865551120','duis.elementum@outlook.com','10912',7,884.53,86.987),
  ('Tate Hicks','(079) 44284558','ut.aliquam@outlook.net','26465',4,54545.01,19.2);

--- Create target table 
create or replace table ff3_pass3_target1 (
  keyid varchar(255) default NULL,
  name varchar(255) default NULL,
  phone varchar(255) default NULL,
  email varchar(255) default NULL,
  postalZip varchar(255) default NULL,
  integernumber integer NULL,
  floatnumber float NULL,
  decimalnumber number(38,8) NULL
);

--- Grant access rights to demo database, schema and tables
grant usage on database ff3_testing_db TO ROLE ff3_encrypt;
grant usage on schema ff3_testing_db.ff3_testing_schema TO ROLE ff3_encrypt;

grant usage on database ff3_testing_db TO ROLE ff3_decrypt;
grant usage on schema ff3_testing_db.ff3_testing_schema TO ROLE ff3_decrypt;

grant usage on database ff3_testing_db TO ROLE data_sc;
grant usage on schema ff3_testing_db.ff3_testing_schema TO ROLE data_sc;

grant usage on database ff3_testing_db TO ROLE sysadmin;
grant usage on schema ff3_testing_db.ff3_testing_schema TO ROLE sysadmin;

grant select on all tables in schema ff3_testing_db.ff3_testing_schema to role ff3_encrypt;
grant select on all tables in schema ff3_testing_db.ff3_testing_schema to role ff3_decrypt;
grant select on all tables in schema ff3_testing_db.ff3_testing_schema to role data_sc;
grant select on all tables in schema ff3_testing_db.ff3_testing_schema to role sysadmin;

grant all privileges on schema ff3_testing_db.ff3_testing_schema to role ff3_encrypt;
grant all privileges on schema ff3_testing_db.ff3_testing_schema to role ff3_decrypt;
grant all privileges on schema ff3_testing_db.ff3_testing_schema to role data_sc;
grant all privileges on schema ff3_testing_db.ff3_testing_schema to role sysadmin;

```




<!-- ------------------------ -->
## Keys
Duration: 2

A single sfguide consists of multiple steps. These steps are defined in Markdown using Header 2 tag `##`. 

```markdown
## Step 1 Title
Duration: 3

---  Set the userkeys. 
-------------------------------------
---  For this demo, the keys will be set explicitly. The acutal requirement is that they be present as a session variable. 
---  These keys can be populated any way that is apprpriate. In a real world setting. they may be retrieved programmatically 
---  via External Function from am external KMS or other vault. 

/*
!!!!!!!!!!!!!!! DO NOT EVER USE THESE KEYS IN THE REAL WORLD !!!!!!!!!!!!!!!!!!
!!!!!!!!!!!!!!! NOW THAT THEY ARE PART OF THIS DEMO, THEY ARE DANGEROUS !!!!!!!
*/

set userkeys='''{
    "678901": ["2DE79D232DF5585D68CE47882AE256D6", "CBD09280979564", "56854"],
    "678902": ["c2051e1a93c3fd7f0e4f20b4fb4f7889aeb8d6fd10f68551af659323f42961e9", "CBD09280979841", "85567"]
}'''; -- key can be either in HEX or raw string form

/*
!!!!!!!!!!!!!!! DO NOT EVER USE THESE KEYS IN THE REAL WORLD !!!!!!!!!!!!!!!!!!
!!!!!!!!!!!!!!! NOW THAT THEY ARE PART OF THIS DEMO, THEY ARE DANGEROUS !!!!!!!
*/

select $userkeys; -- check the results


```





<!-- ------------------------ -->
## Python UDF Installation
Duration: 2

A single sfguide consists of multiple steps. These steps are defined in Markdown using Header 2 tag `##`. 

```markdown
## Step 1 Title
Duration: 3

-- Install the string encrypt UDF

create or replace function encrypt_ff3_string_pass3(ff3key string, ff3input string, ff3_user_keys string)
returns string
language python
runtime_version = 3.8
packages = ('pycryptodome')
imports = ('@python_libs/ff3.zip')
handler = 'udf'
as $$

import json
from ff3 import FF3Cipher

def udf(ff3keyinput, ff3input, userkeys):

    if ff3input[0:3] == 'KEY':
        return ff3input

    userkeys=userkeys.replace("'","")
    ff3_userkey_dict=json.loads(userkeys)
    userkeys_list=[]
    userkeyslist=ff3_userkey_dict[ff3keyinput[3:]]
    
    ff3_key=userkeyslist[0]
    ff3_tweak=userkeyslist[1]
    padding=userkeyslist[2]
    
    length=len(ff3input)
   
    c = FF3Cipher.withCustomAlphabet(ff3_key, ff3_tweak, """0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ+-().@ '""")
    
    n =30
    
    chunks = [ff3input[i:i+n] for i in range(0, len(ff3input), n)]

    encrypted_value_list=[]
    result=''
    lengthpadding=[]
    for chunk in chunks:
        lengthchunk=len(chunk)

        if lengthchunk>=4:
                plaintext=chunk
                lengthpadding.append('0')
        if lengthchunk==3:
                plaintext=chunk+padding[0:1]
                lengthpadding.append('1')
        if lengthchunk==2:
                plaintext=chunk+padding[0:2]
                lengthpadding.append('2')
        if lengthchunk==1:
                plaintext=chunk+padding[0:3]
                lengthpadding.append('3')
        
        
        ciphertext = c.encrypt(plaintext)
        encrypted_value_list.append(ciphertext)

    i=0
    x=0
    for encrypted_value in encrypted_value_list:
        i=i+1
        #result = result + '[C' + str(i) +']' + encrypted_value + '[C' + str(i) +']'
        result = result + '[C' + lengthpadding[x] +']' + encrypted_value
        x=x+1

    if length<10:
        result=result+"00"+str(length)
        test=result.split('[C]')
        #print(str(test[-1])[-3:])
        #print(test)
        return result

    if 10 <= length <= 99:
        result=result+'0'+str(length)
        test=result.split('[C]')
        #print(test)
        #print(str(test[-1])[-3:])
        return result

    if length>99 :
        result=result+str(length)
        test=result.split('[C]')
        #print(test)
        #print(str(test[-1])[-3:])
        return result
$$;


-- Test the string encrypt UDF. Result should be: [C0]4Ig8d005
select encrypt_ff3_string_pass3('KEY678901', 'hello', $userkeys);


-- Install the decrypt string UDF

create or replace function decrypt_ff3_string_pass3(ff3key string, ff3input string, ff3_user_keys string)
returns string
language python
runtime_version = 3.8
packages = ('pycryptodome')
imports = ('@python_libs/ff3.zip')
handler = 'udf'
as $$

import json
from ff3 import FF3Cipher


def isDivisibleBy2(num):
    if (num % 2) == 0:
        return True
    else:
        return False


def udf(ff3keyinput, ff3input, userkeys):

    
    
    userkeys=userkeys.replace("'","")
    ff3_userkey_dict=json.loads(userkeys)
    userkeys_list=[]
    userkeyslist=ff3_userkey_dict[ff3keyinput[3:]]
    
    key=userkeyslist[0]
    tweak=userkeyslist[1]
    padding=userkeyslist[2]
    
   

    result=''
    length=len(ff3input)
    #ff3_key_dict=json.loads(ff3key)
    #keyid = str(list(ff3_key_dict.keys())[0])
    #ff3_key=ff3_key_dict[keyid][0]
    #ff3_tweak=ff3_key_dict[keyid][1]
    #ff3_padding=ff3_key_dict[keyid][2]

    c = FF3Cipher.withCustomAlphabet(key, tweak, """0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ+-().@ '""")

    encrypted_value_list=ff3input.split('[C')
    decrypted_value_list=[]
    encryptedvalue=''

    for encrypted_value in encrypted_value_list[1:-1]:
         paddinglength=int(encrypted_value[0])
         encrypted_value=encrypted_value[2:]
         decrypted = c.decrypt(encrypted_value)
         if paddinglength != 0:
            decrypted=decrypted[:-paddinglength]
         decrypted_value_list.append(decrypted)
         encryptedvalue=encryptedvalue+encrypted_value
      

    for decrypted_value in decrypted_value_list:
             result=result+decrypted_value


   


    lastvalue=encrypted_value_list[-1]
    lastvalue = lastvalue[:-3]
    paddinglength=int(lastvalue[0])
    lastvalue = lastvalue[2:]
    lastdecrypt=c.decrypt(lastvalue)
    if paddinglength != 0:
        lastdecrypt=lastdecrypt[:-int(paddinglength)]
    result=result+lastdecrypt
    return result
   

    
    


$$;

-- Test the decrypt string UDF. Result should be "hello"
select decrypt_ff3_string_pass3('KEY678901', '[C0]4Ig8d005', $userkeys);






--Create the float encrypt UDF

create or replace function encrypt_ff3_float_pass3(ff3key string, ff3input float, ff3_user_keys string)
returns float
language python
runtime_version = 3.8
packages = ('pycryptodome')
imports = ('@python_libs/ff3.zip')
handler = 'udf'
as $$

import json
from ff3 import FF3Cipher

def udf(ff3key_input, ff3_input, userkeys):

    userkeys=userkeys.replace("'","")
    ff3_userkey_dict=json.loads(userkeys)
    userkeys_list=[]
    userkeyslist=ff3_userkey_dict[ff3key_input[3:]]
    
    ff3_key=userkeyslist[0]
    ff3_tweak=userkeyslist[1]
    ff3_padding=userkeyslist[2]
    
    c = FF3Cipher(ff3_key, ff3_tweak)

    value = str(ff3_input)
    lengthvalue=len(value)

    if lengthvalue==3:
        ff3_padding=ff3_padding[0:4]
    if lengthvalue==4:
        ff3_padding=ff3_padding[0:3]
    if lengthvalue==5:
        ff3_padding=ff3_padding[0:2]
    if lengthvalue==6:
        ff3_padding=ff3_padding[0:1]
    if lengthvalue >= 7:
        ff3_padding=None

    plaintext_org=value
    commais=value.find('.')
    commais=commais
    detect_float=plaintext_org.split('.')

    #dont try to encode more than 11 digits with float or more than 9 digits before or after the comma

    if len(detect_float[0]) >= 10:
        print ("VALUE BEFORE COMMA TOO BIG NOT MORE THAN 9 DIGITS ALLOWED")
    if len(detect_float[1])>=10:
        print("VALUE AFTER COMMA TOO BIG NOT MORE THAN 9 DIGITS ALLOWED")
    if len(detect_float[1])+len(detect_float[0])>=12:
        print ("VALUE  TOO BIG NOT MORE THAN 11 DIGITS ALLOWED")


    plaintext =  value
    plaintext=plaintext.replace('.','')
    if ff3_padding !=None:
        lengthpadding=len(ff3_padding)+1
        ciphertext = c.encrypt(plaintext+ff3_padding)
    else:
        lengthpadding=1
        ciphertext = c.encrypt(plaintext)
    
    beforecomma=len(detect_float[0])
    aftercomma=len(detect_float[1])
    
    endresult=ciphertext

    endresult=str(commais)+endresult+str(beforecomma)+str(aftercomma)+str(lengthpadding)
    return float(endresult)
    



$$;

-- Test the encrypt float UDF. Result should be : 1417378124
select encrypt_ff3_float_pass3('KEY678901', 9.03, $userkeys);

-- Install the decrypt float UDF
create or replace function decrypt_ff3_float_pass3(ff3key string, ff3input float, ff3_user_keys string)
returns float
language python
runtime_version = 3.8
packages = ('pycryptodome')
imports = ('@python_libs/ff3.zip')
handler = 'udf'
as $$


from ff3 import FF3Cipher
import json

def udf(ff3key_input, ff3_input, userkeys):

    userkeys=userkeys.replace("'","")
    ff3_userkey_dict=json.loads(userkeys)
    userkeys_list=[]
    userkeyslist=ff3_userkey_dict[ff3key_input[3:]]
    
    ff3_key=userkeyslist[0]
    ff3_tweak=userkeyslist[1]
   

    plaintext_org=str(ff3_input)
    plaintext_org=plaintext_org[1:]
    plaintext_org=plaintext_org[:-5]
    
    c = FF3Cipher(ff3_key, ff3_tweak)

    decrypted = c.decrypt(plaintext_org)
    #decrypted=''

    lengthpadding=int(str(ff3_input)[-3])
    commais=int(str(ff3_input)[0])

    
    if lengthpadding==1:
            decrypted=decrypted[:commais] + '.' + decrypted[commais:]
    else:
            decrypted=decrypted[:-lengthpadding+1]
            decrypted=decrypted[:commais] + '.' + decrypted[commais:]


    return float(decrypted)

$$;

-- Test the decrypt float UDF. Result should be 9.03
select decrypt_ff3_float_pass3('KEY678901',1417378124, $userkeys);



-- Install the encrypt number UDF. You can install it as taking integers and returning integers or taking and returning number 38,X)
create or replace function encrypt_ff3_number_pass3(ff3key string, ff3input number(38,8), ff3_user_keys string)
returns number(38,8)
language python
runtime_version = 3.8
packages = ('pycryptodome')
imports = ('@python_libs/ff3.zip')
handler = 'udf'
as $$

from ff3 import FF3Cipher
import json
import re
from decimal import *



def udf(ff3key, ff3input, userkeys):

    userkeys=userkeys.replace("'","")
    ff3_userkey_dict=json.loads(userkeys)
    userkeys_list=[]
    userkeyslist=ff3_userkey_dict[ff3key[3:]]
    
    ff3key=userkeyslist[0]
    tweak=userkeyslist[1]
    padding=userkeyslist[2]
    
    
    checkdecimal="." in str(ff3input)
    
    
    if checkdecimal==False :
        
        length=len(str(ff3input))
        lengthpadding=0
    
        c = FF3Cipher(ff3key, tweak)

        if length<=6:
            plaintext=str(ff3input)
            lengthpadding=1

        if length==5:
            plaintext=str(ff3input)+padding[0:1]
            lengthpadding=2
        
        if length==4:
            plaintext=str(ff3input)+padding[0:2]
            lengthpadding=3

        if length==3:
            plaintext=str(ff3input)+padding[0:3]
            lengthpadding=4
        
        if length==2:
            plaintext=str(ff3input)+padding[0:4]
            lengthpadding=5
        
        if length==1:
            plaintext=str(ff3input)+padding
            lengthpadding=6
        
        ciphertext = c.encrypt(plaintext)
    
        
        if length<10:
            ciphertext=ciphertext+"0"+str(length)
        else:
            ciphertext=ciphertext+str(length)


        ciphertext=str(lengthpadding)+ciphertext
        return int(ciphertext)
        
        
    if checkdecimal==True :
    
       

        c = FF3Cipher(ff3key, tweak)

        value = str(ff3input)
        lengthvalue=len(value)

        if lengthvalue==3:
            ff3_padding=ff3_padding[0:4]
        if lengthvalue==4:
            ff3_padding=ff3_padding[0:3]
        if lengthvalue==5:
            ff3_padding=ff3_padding[0:2]
        if lengthvalue==6:
            ff3_padding=ff3_padding[0:1]
        if lengthvalue >= 7:
            ff3_padding=None

        plaintext_org=value
        commais=value.find('.')
        commais=commais
        detect_float=plaintext_org.split('.')

        #dont try to encode more than 11 digits with float or more than 9 digits before or after the comma

        #if len(detect_float[0]) >= 10:
         #   print ("VALUE BEFORE COMMA TOO BIG NOT MORE THAN 9 DIGITS ALLOWED")
        #if len(detect_float[1])>=10:
        #    print("VALUE AFTER COMMA TOO BIG NOT MORE THAN 9 DIGITS ALLOWED")
        #if len(detect_float[1])+len(detect_float[0])>=12:
        #    print ("VALUE  TOO BIG NOT MORE THAN 11 DIGITS ALLOWED")


        plaintext =  value
        plaintext=plaintext.replace('.','')
        if ff3_padding !=None:
            lengthpadding=len(ff3_padding)+1
            ciphertext = c.encrypt(plaintext+ff3_padding)
        else:
            lengthpadding=1
            ciphertext = c.encrypt(plaintext)

        beforecomma=len(detect_float[0])
        aftercomma=len(detect_float[1])
        
        #d = Decimal(value)
        #aftercomma=int(d.as_tuple().exponent)
        #aftercomma=-aftercomma
        
        aftercommacheck=value
       # before, sep, after = strValue.partition('-')
        #strValue = before
        
        mo = re.match('.+([1-9])[^1-9]*$', aftercommacheck)
        if mo !=  None:
            lastposition=int(mo.start(1))
            aftercommacheck=value[0:lastposition+1]
            aftercommacheck=aftercommacheck.split('.')
            aftercomma=len(aftercommacheck[1])
        else:
            aftercomma=0
            
        
        
        
   
        

        endresult=ciphertext

        endresult=str(commais)+endresult+str(beforecomma)+str(aftercomma)+str(lengthpadding)
        


        
        return Decimal(endresult)




$$;

-- Test the encrypt number UDF. Result for decimal 38,10 should be 4121376945460401.00000000 . Result for integer should be 319241204 .
select encrypt_ff3_number_pass3('KEY678901', 1000, $userkeys);




--Install the decrypt number UDF. Can take and return an integer or decimal like number 38,X


create or replace function decrypt_ff3_number_pass3(ff3key string, ff3input number(38,8), ff3_user_keys string)
returns number(38,8)
language python
runtime_version = 3.8
packages = ('pycryptodome')
imports = ('@python_libs/ff3.zip')
handler = 'udf'
as $$

from ff3 import FF3Cipher
import json
from decimal import *



def udf(ff3key, ff3input, userkeys):


    userkeys=userkeys.replace("'","")
    ff3_userkey_dict=json.loads(userkeys)
    userkeys_list=[]
    userkeyslist=ff3_userkey_dict[ff3key[3:]]
    
    ff3key=userkeyslist[0]
    tweak=userkeyslist[1]
    padding=userkeyslist[2]
    
    checkdecimal="." in str(ff3input)
    
    if checkdecimal==False :
        
        lengthpadding=str(ff3input)[0]
        lengthpadding=int(lengthpadding)
        lengthpadding=lengthpadding-1
    
        c = FF3Cipher(ff3key, tweak)

        
        ciphertext=str(ff3input)[1:]
        ciphertext=ciphertext[:-2]
        decrypted = c.decrypt(ciphertext)
        length=lengthpadding 
 
        if length==5:
            decrypted=decrypted[:-5]
        if length==4:
            decrypted=decrypted[:-4]
        if length==3:
            decrypted=decrypted[:-3]
        if length==2:
            decrypted=decrypted[:-2]
        if length==1:
            decrypted=decrypted[:-1]

    

        return int(decrypted)
        
    if checkdecimal==True :
    
        c = FF3Cipher(ff3key, tweak)

        value=str(ff3input)
        valuesplit=value.split('.')
        
        plaintext_org=valuesplit[0]
        plaintext_org=plaintext_org[1:]
        plaintext_org=plaintext_org[:-3]

        decrypted = c.decrypt(str(plaintext_org))
        value=valuesplit[0]
        lengthpadding=int(value[-1])
        commais=int(value[0])

     
        if lengthpadding==1:
                decrypted=decrypted[:commais] + '.' + decrypted[commais:]
        else:
                decrypted=decrypted[:-lengthpadding+1]
                decrypted=decrypted[:commais] + '.' + decrypted[commais:]


        return Decimal(decrypted)



$$;

-- Test the decrypt number UDF. Decimal (number 38,8) result should be 1,000 (1000.00000000) 
select decrypt_ff3_number_pass3('KEY678901', 4121376945460401.00000000, $userkeys);

--Integer test:  Result should 1,000 (1000)
--select decrypt_ff3_number_pass3('KEY678901', 319241204, $userkeys);


-- Install and test string token formatting UDFs.


create or replace function format_ff3_string_pass3(ff3input string)
returns string
language python
runtime_version = 3.8
handler = 'udf'
as $$




def isDivisibleBy2(num):
    if (num % 2) == 0:
        return True
    else:
        return False


def udf(ff3input):

    
    


    result=''
    encrypted_value_list=ff3input.split('[C')
    decrypted_value_list=[]
    encryptedvalue=''
    i=0
    x=0

    
    for encrypted_value in encrypted_value_list[1:-1]:
     
        if i >= 1:
            x=1
            encrypted_value=encrypted_value[2:]
            encryptedvalue=encryptedvalue+encrypted_value
        
        else:
            encrypted_value=encrypted_value[2:]
            encryptedvalue=encryptedvalue+encrypted_value
        i=i+1


    ## Formatting Block
    lastvalue=encrypted_value_list[-1]
    lastvalue=lastvalue[2:]
    encryptedvalue=encryptedvalue+ lastvalue
    
    howmany = int(encryptedvalue[-3:])
    encryptedvalue=encryptedvalue[:-3]
    
    if x ==1:
        
        #formatted=encryptedvalue[2:]
        formatted=formatted[0:howmany-2]
        formatted=encryptedvalue[2:]
        
        
        
        
    else:
         
        formatted=encryptedvalue
        #formatted=formatted[0:howmany]
        #formatted=encryptedvalue
         
         
    formatted=formatted.replace(' ','')
   
    
    

   
    return formatted


$$;

-- Test the string token formatting. This removes the some metadata from the token and makes sure that the token length matches the intial value that was encrypted. Output should be 4Ig8d .

select format_ff3_string_pass3('[C0]4Ig8d005');
select format_ff3_string_pass3('[C0]D.eaU(5+iijkXsS4@yFULDB58hLTGD[C3]gyYs031'); 



-- Install string token USphone formatting UDFs.
create or replace function format_ff3_string_usphone_pass3(ff3input string)
returns string
language python
runtime_version = 3.8
handler = 'udf'
as $$


def split(word):
    return [char for char in word]

def isDivisibleBy2(num):
    if (num % 2) == 0:
        return True
    else:
        return False


def udf(ff3input):

    
    


    result=''
    encrypted_value_list=ff3input.split('[C')
    decrypted_value_list=[]
    encryptedvalue=''
    i=0
    x=0

    for encrypted_value in encrypted_value_list[1:-1]:
        if i >= 1:
            x=1
            encrypted_value=encrypted_value[2:]
            encryptedvalue=encryptedvalue+encrypted_value
        
        else:
            encrypted_value=encrypted_value[2:]
            encryptedvalue=encryptedvalue+encrypted_value
        i=i+1


    ## Formatting Block
    lastvalue=encrypted_value_list[-1]
    lastvalue=lastvalue[2:]
    encryptedvalue=encryptedvalue+lastvalue

    howmany = int(encryptedvalue[-3:])
    encryptedvalue=encryptedvalue[:-3]
    
    #formatted=encryptedvalue[0:howmany]
    
    if x ==1:
        
        #formatted=encryptedvalue[2:]
        #formatted=formatted[0:howmany-2]
        formatted=encryptedvalue[2:]
        
        
        
        
    else:
         
        formatted=encryptedvalue
        #formatted=formatted[0:howmany]
        #formatted=encryptedvalue
    
    formatted=formatted.replace(' ','')
    
    l = split(formatted)
    #k = [ord(x)-96 for x in l]
    k = [ord(x) for x in l]
    
    for i in k:
        result=result+str(i)
   
    
    

   
    
    result=result[:3] + ") " + result[3:]
    result='('+result
    result = (result[:14] ) if len(result) > 14 else result
    #result=result[:-1]
    return result

    
    


$$;

----  Test string token USphone formatting UDFs. This UDF formats and converts the string token into a string token that is represented by numbers and looks like a US phone number. Output should be (527) 31035610 .
select format_ff3_string_usphone_pass3('[C0]4Ig8d005');

-- Install string token US-postal-code formatting UDFs.
create or replace function format_ff3_string_uspostal_pass3(ff3input string)
returns string
language python
runtime_version = 3.8
handler = 'udf'
as $$


def split(word):
    return [char for char in word]

def isDivisibleBy2(num):
    if (num % 2) == 0:
        return True
    else:
        return False


def udf(ff3input):

    
    


    result=''
    encrypted_value_list=ff3input.split('[C')
    decrypted_value_list=[]
    encryptedvalue=''
    i=0
    x=0

    for encrypted_value in encrypted_value_list[1:-1]:
        if i >= 1:
            x=1
            encrypted_value=encrypted_value[2:]
            encryptedvalue=encryptedvalue+encrypted_value
        
        else:
            encrypted_value=encrypted_value[2:]
            encryptedvalue=encryptedvalue+encrypted_value
        i=i+1


    ## Formatting Block
    lastvalue=encrypted_value_list[-1]
    lastvalue=lastvalue[2:]
    encryptedvalue=encryptedvalue+ lastvalue
    
    howmany = int(encryptedvalue[-3:])
    encryptedvalue=encryptedvalue[:-3]
    #formatted=encryptedvalue[0:howmany]
    
    if x ==1:
        
        #formatted=encryptedvalue[2:]
        #formatted=formatted[0:howmany-2]
        formatted=encryptedvalue[2:]
        
        
        
        
    else:
         
        formatted=encryptedvalue
        #formatted=formatted[0:howmany]
        #formatted=encryptedvalue
    
    formatted=formatted.replace(' ','')
    
    l = split(formatted)
    #k = [ord(x)-96 for x in l]
    k = [ord(x) for x in l]
    
    for i in k:
        result=result+str(i)
   
    
    

   
    
    result = (result[:5] ) if len(result) > 5 else result
    #result=result[:-1]
    return result

    
    


$$;

----  Test string token USpostal-code formatting UDFs. This UDF formats and converts the string token into a string token that is represented by numbers and looks like a US post code number. Output should be 52731 .
select format_ff3_string_uspostal_pass3('[C0]4Ig8d005');




-- Install string token email formatting UDFs.
create or replace function format_email_ff3_string_pass3(ff3input string)
returns string
language python
runtime_version = 3.8
handler = 'udf'
as $$


def isDivisibleBy2(num):
    if (num % 2) == 0:
        return True
    else:
        return False


def udf(ff3input):


    result=''
    encrypted_value_list=ff3input.split('[C')
    decrypted_value_list=[]
    encryptedvalue=''
    i=0
    x=0

    for encrypted_value in encrypted_value_list[1:-1]:
        if i >= 1:
            x=1
            encrypted_value=encrypted_value[2:]
            encryptedvalue=encryptedvalue+encrypted_value
        
        else:
            encrypted_value=encrypted_value[2:]
            encryptedvalue=encryptedvalue+encrypted_value
        i=i+1


    ## Formatting Block
    lastvalue=encrypted_value_list[-1]
    lastvalue=lastvalue[2:]
    encryptedvalue=encryptedvalue+ lastvalue
    howmany = int(encryptedvalue[-3:])
    encryptedvalue=encryptedvalue[:-3]
   
   
    
    #email=encryptedvalue[0:howmany]
    
    if x ==1:
        
        #formatted=encryptedvalue[2:]
        #formatted=formatted[0:howmany-2]
        email=encryptedvalue[2:]
        
        
        
        
    else:
         
        email=encryptedvalue
        #formatted=formatted[0:howmany]
        #formatted=encryptedvalue
    
    howlongemail=len(email)
    positionemail=howlongemail/2
    if isDivisibleBy2(positionemail)==True:
       positionemail=int(positionemail)
    else:
       positionemail=int(positionemail+1)
    email=email.replace('@','')
    email = email[:positionemail] + "@" + email[positionemail:]
    email=email[0:howmany]
    email=email+".com"
    email=email.replace(' ','')
    
    #temporary fix
    #email=email.replace('0]','')
    email=email.replace('@@','@')
    


   
    return email

$$;


----  Test string token email formatting UDFs. This UDF formats and converts the string token into a string token that looks like an email . Output should be 4Ig@8d.com .

select format_email_ff3_string_pass3('[C0]4Ig8d005');
select format_email_ff3_string_pass3('[C0]D.eaU(5+iijkXsS4@yFULDB58hLTGD[C3]gyYs031');


-- Install string token sqljoin formatting UDFs.
create or replace function sqljoin_ff3_string_pass3(ff3input string)
returns string
language python
runtime_version = 3.8
handler = 'udf'
as $$

def udf(ff3input):


    result=''
    encrypted_value_list=ff3input.split('[C')
 
    encryptedvalue=''

    for encrypted_value in encrypted_value_list[1:-1]:
        encryptedvalue=encryptedvalue+encrypted_value[2:]


    ## Formatting Block
    lastvalue=encrypted_value_list[-1]
    encryptedvalue=encryptedvalue+lastvalue[2:]
    #howmany = int(encryptedvalue[-3:])
    encryptedvalue=encryptedvalue[:-3]

    
   
    return encryptedvalue

$$;

----  Test string token sqljoin formatting UDFs. This UDF removes metadata and just gives the plain token back. This insures that sql joins can be done with token values that are guaranteed to be unique. This essentially removes any token 
-- formatting however. Output should be 4Ig8d .

select sqljoin_ff3_string_pass3('[C0]4Ig8d005');


-- Install the float token formatting UDF

create or replace function format_ff3_float_pass3(ff3input float)
returns float
language python
runtime_version = 3.8
packages = ('pycryptodome')
imports = ('@python_libs/ff3.zip')
handler = 'udf'
as $$



def udf(ff3_input):

    

    #lengthpadding=int(str(ff3_input)[-3])
    #commais=int(str(ff3_input)[0])
    
    formatting=str(ff3_input)[-5:]
    formatting = formatting[:-3]
   

    beforecomma=int(formatting[0])
    aftercomma=int(formatting[-1])
    numberofdigits=beforecomma+aftercomma
    

    formatted=str(ff3_input)[0:numberofdigits]
    formatted=formatted[:beforecomma] + '.' + formatted[beforecomma:]

    checkformatted=int(formatted[-1])
    if checkformatted==0:
            formatted = formatted[:-1] + '1'



    return float(formatted)

$$;

-- Test the float token formatting. This formatter reads the metadata from the token and gives back a float number that has the same length and the comma at the same place as the original float number that was encrypted.
-- Output should be: 1.41

select format_ff3_float_pass3 (1417378124);


-- Install  float token formatting for sql joins UDF
create or replace function sqljoin_ff3_float_pass3(ff3input float)
returns float
language python
runtime_version = 3.8
packages = ('pycryptodome')
imports = ('@python_libs/ff3.zip')
handler = 'udf'
as $$



def udf(ff3_input):

    

    
    #formatting=str(ff3_input)[1:]
    #formatting = formatting[:-4]
   

    return float(ff3_input)

$$;

-- Test the float token sqljoin formatting. This just passes through the token and returns it as is in order to make sure this value is unique for sql joins. Output should be: 1760531124 .

select sqljoin_ff3_float_pass3(1760531124);


-- Install the number token formatting UDF


create or replace function format_ff3_number_pass3(ff3input number(38,8))
returns number(38,8)
language python
runtime_version = 3.8
handler = 'udf'
as $$


from decimal import *



def udf(ff3input):

    
    checkdecimal="." in str(ff3input)
    
    if checkdecimal==False :
    
        value=str(ff3input)
        length=int(value[-2:])
        
        formatted=''
        formatted=value[1:]
        formatted=formatted[:-2]
        formatted=formatted[0:length]
        #formatted='1'+formatted
        final=''
        addition=0
        numberofzeros=0
        nullen=''
        result=0
        
        
        if formatted[0]=='0':
            numberofzeros=length-1
            addition=length-numberofzeros
            for zeros in range(numberofzeros):
                nullen=nullen+'0'
            final=str(addition)+nullen
            result=int(formatted)+int(final)
            return result
            

        return int(formatted)
        
    if checkdecimal==True :
    
    #1114907569131.00000000 = 9.021
    #str(commais)+endresult+str(beforecomma)+str(aftercomma)+str(lengthpadding)
    
        value=str(ff3input).split('.')
        result=value[0]
        result=result[1:]
        result=result[:-1]
        commas=result[-2:]
        result=result[:-2]
        
        beforecomma=int(commas[0])
        aftercomma=int(commas[-1])
        
        bcdigits=result[0:beforecomma]
        
        if aftercomma!=0: 
            acdigits=result[-aftercomma:]
        else:
            acdigits=0
        
        endresult=str(bcdigits)+'.'+str(acdigits)
        
        
        
      
        return Decimal(endresult)



$$;



--  Test number token formatting UDFs if used number(38.X) for input/output. This gives back the value in the same length and form as it was before it was encrypted. Output should be 1,213 (1213.00000000)
select format_ff3_number_pass3('4121376945460401.00000000');

--  Test number token formatting UDF if used integer for input/output. This gives back the value in the same length and form as it was before it was encrypted. Output should be 1924 .
--select format_ff3_number_pass3('319241204');


-- Install the sql join formatting UDF for numbers. 

create or replace function sqljoin_ff3_number_pass3(ff3input number(38,8))
returns number(38,8)
language python
runtime_version = 3.8
handler = 'udf'
as $$


from decimal import *



def udf(ff3input):

    
    checkdecimal="." in str(ff3input)
    
    if checkdecimal==False :
    
        value=str(ff3input)
        #length=int(value[-2:])
        
        formatted=''
        formatted=value[1:]
        formatted=formatted[:-2]
        #formatted=formatted[0:length]
        #formatted='1'+formatted
        #final=''
        #addition=0
        #numberofzeros=0
        #nullen=''
        #result=0
        
        
        #if formatted[0]=='0':
        #    numberofzeros=length-1
        #    addition=length-numberofzeros
        #    for zeros in range(numberofzeros):
        #        nullen=nullen+'0'
        #    final=str(addition)+nullen
        #    result=int(formatted)+int(final)
        #    return result
            
        return int(formatted)
        
    if checkdecimal==True :
    
    #1114907569131.00000000 = 9.021
    #str(commais)+endresult+str(beforecomma)+str(aftercomma)+str(lengthpadding)
    
        value=str(ff3input).split('.')
        result=value[0]
        result=result[1:]
        result=result[:-1]
        commas=result[-2:]
        result=result[:-2]
        
        #beforecomma=int(commas[0])
        #aftercomma=int(commas[-1])
        
        bcdigits=result
        
        acdigits=0
        
        endresult=str(bcdigits)+'.'+str(acdigits)
        
        
        
      
        return Decimal(endresult)

$$;




--  Test number token formatting UDF if used with number(38.X) for input/output. This gives back a unique simplified token to guarantee uniqueness for sql joins. Output should be 121376945460.00000000 with number 38,8.
select sqljoin_ff3_number_pass3('4121376945460401.00000000');

--  Test number token formatting UDF if used with integer for input/output. This gives back a unique simplified token to guarantee uniqueness for sql joins. Output should be 192412 with integer. 
--select sqljoin_ff3_number_pass3('319241204');





```



<!-- ------------------------ -->


## Policy Setup
Duration: 2

A single sfguide consists of multiple steps. These steps are defined in Markdown using Header 2 tag `##`. 

```markdown
## Step 1 Title
Duration: 3

--Create encrypt polices 


create or replace masking policy ff3_encrypt_string_pass3 as (val string, keyid string)  returns string ->
  case
    when  current_role() in ('ACCOUNTADMIN') 
     then val
   when  current_role() in ('FF3_ENCRYPT')
     then encrypt_ff3_string_pass3(keyid,val, $userkeys)
    else '** masked **'
  end;
  
  create or replace masking policy ff3_encrypt_float_pass3 as (val float,keyid string)  returns float ->
  case
   when  current_role() in ('ACCOUNTADMIN') 
     then val
    when  current_role() in ('FF3_ENCRYPT') 
     then encrypt_ff3_float_pass3(keyid,val, $userkeys)
    else -999
  end;
  
 create or replace masking policy ff3_encrypt_number_pass3_integer as (val integer,keyid string)  returns integer ->
  case
   when  current_role() in ('ACCOUNTADMIN') 
     then val
    when  current_role() in ('FF3_ENCRYPT') 
     then encrypt_ff3_number_pass3(keyid,val, $userkeys)
    else -999
  end;


 create or replace masking policy ff3_encrypt_number_pass3_decimal as (val number(38,8),keyid string)  returns number(38,8) ->
  case
   when  current_role() in ('ACCOUNTADMIN') 
     then val
    when  current_role() in ('FF3_ENCRYPT') 
     then encrypt_ff3_number_pass3(keyid,val, $userkeys)
    else -999
  end;
  
  

--  Create decrypt and format policies 4x 


create or replace masking policy ff3_decrypt_format_string_pass3 as (val string, keyid string)  returns string ->
  case
    when  current_role() in ('FF3_DECRYPT')
     then decrypt_ff3_string_pass3(keyid,val, $userkeys)
     
     when  current_role() in ('DATA_SC') AND system$get_tag_on_current_column('sqljoin')=''
     then sqljoin_ff3_string_pass3(val)  
    
    when  current_role() in ('DATA_SC') AND system$get_tag_on_current_column('email')=''
     then format_email_ff3_string_pass3(val)
     
    when  current_role() in ('DATA_SC') AND system$get_tag_on_current_column('uspostal')=''
     then format_ff3_string_uspostal_pass3(val)
     
     when  current_role() in ('DATA_SC') AND system$get_tag_on_current_column('usphone')=''
     then format_ff3_string_usphone_pass3(val)
     
    when  current_role() in ('DATA_SC')
     then format_ff3_string_pass3(val) 
    when  current_role() in ('ACCOUNTADMIN') 
     then val
    else '** masked **'
  end;
  
  
  create or replace masking policy ff3_decrypt_format_float_pass3 as (val float, keyid string)  returns float ->
  case
    when  current_role() in ('FF3_DECRYPT')
     then decrypt_ff3_float_pass3(keyid,val, $userkeys)
    when  current_role() in ('DATA_SC') AND system$get_tag_on_current_column('sqljoin')=''
     then sqljoin_ff3_float_pass3(val)
    when  current_role() in ('DATA_SC')
     then format_ff3_float_pass3(val)
    when  current_role() in ('ACCOUNTADMIN') 
     then val
    else -999
  end;
  
 create or replace masking policy ff3_decrypt_format_pass3_integer as (val integer, keyid string)  returns integer ->
  case
    when  current_role() in ('FF3_DECRYPT')
     then decrypt_ff3_number_pass3(keyid,val, $userkeys)
     when  current_role() in ('DATA_SC') AND system$get_tag_on_current_column('sqljoin')=''
     then sqljoin_ff3_number_pass3(val)
    when  current_role() in ('DATA_SC')
     then format_ff3_number_pass3(val)
    when  current_role() in ('ACCOUNTADMIN') 
     then val
    else -999
  end;


 create or replace masking policy ff3_decrypt_format_pass3_decimal as (val number(38,8), keyid string)  returns number(38,8) ->
  case
    when  current_role() in ('FF3_DECRYPT')
     then decrypt_ff3_number_pass3(keyid,val, $userkeys)
     when  current_role() in ('DATA_SC') AND system$get_tag_on_current_column('sqljoin')=''
     then sqljoin_ff3_number_pass3(val)
    when  current_role() in ('DATA_SC')
     then format_ff3_number_pass3(val)
    when  current_role() in ('ACCOUNTADMIN') 
     then val
    else -999
  end;
  








```




<!-- ------------------------ -->


## Test
Duration: 2

A single sfguide consists of multiple steps. These steps are defined in Markdown using Header 2 tag `##`. 

```markdown
## Step 1 Title
Duration: 3

All the content for the step goes here.

## Step 2 Title
Duration: 1

All the content for the step goes here.
```

To indicate how long each step will take, set the `Duration` under the step title (i.e. `##`) to an integer. The integers refer to minutes. If you set `Duration: 4` then a particular step will take 4 minutes to complete. 

The total sfguide completion time is calculated automatically for you and will be displayed on the landing page. 


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