CREATE OR REPLACE DATABASE nature_clips_db;
CREATE SCHEMA nature_clips_schema;
-- |----------|----------------------------------------------------|
-- | Table    | Columns                                            |
-- |----------|----------------------------------------------------|
-- | videos   | video_id, title, topic, url, length                |
-- | visitors | visitor_id, name, email, gender, zip_code, interest|
-- | activity | visit_id, visitor_id, visit_timestamp, video_id    |
-- |----------|----------------------------------------------------|

CREATE OR REPLACE TABLE videos (
  video_id STRING PRIMARY KEY,
  title STRING,
  topic STRING,
  url STRING,
  length INT); -- length of video in seconds

CREATE OR REPLACE TABLE visitors(
  visitor_id STRING PRIMARY KEY,
  name STRING,
  email STRING,
  gender STRING,
  zip_code INT,
  interest STRING); -- camping, riding, or paddling
  
CREATE OR REPLACE TABLE activity (
  visit_id STRING PRIMARY KEY,
  visitor_id STRING FOREIGN KEY REFERENCES visitors(visitor_id),
  video_id STRING FOREIGN KEY REFERENCES videos(video_id),
  duration_sec INT,
  visit_timestamp TIMESTAMP);

USE DATABASE nature_clips_db;
USE SCHEMA nature_clips_schema;

CREATE OR REPLACE PROCEDURE generate_NC_data(
    GROUP_PREFIX STRING,
    USER_COUNT DOUBLE,
    INTEREST STRING,
    MAX_EVENT_PER_USER DOUBLE,
    MIN_SPENT_TIME DOUBLE,
    MAX_SPENT_TIME DOUBLE,
    TOPIC STRING,
    VIDEO_ID STRING,
    VIDEO_COUNT DOUBLE,
    GENERATE_VIDEO BOOLEAN
) 
  RETURNS STRING
  LANGUAGE JAVASCRIPT
  EXECUTE AS caller
AS $$
if (GENERATE_VIDEO) {
  var command = ''
  let video_id = '';
  
  command = `INSERT INTO videos VALUES ` 
  let video_num = 0;
  while (video_num < VIDEO_COUNT) {
    let v_id = `${VIDEO_ID}.${video_num}`
    var v_len = Math.floor(Math.random() * 400) + 20;
    if (TOPIC.includes("kayak") || TOPIC.includes("raft")) 
      v_len += 120;
    command += `('${v_id}', 'video_${v_id}', '${TOPIC}', 'http://nature_clips.com/${v_id}', '${v_len}')`; 
    video_num += 1;
    if (video_num < VIDEO_COUNT)
      command += `,`
    else 
      command += `;`
  }
  snowflake.execute({sqlText: command});
}

is_first_activity = true;
total_act_count = 0
is_first_user = true;
activity_cmd = `INSERT INTO activity VALUES `
user_cmd = `INSERT INTO visitors VALUES `;

let user_num = 0;
while (user_num < USER_COUNT) {
    let user_id = `u${GROUP_PREFIX}${user_num} `;
    let email = `email_${GROUP_PREFIX}${user_num}@mail.com`;
    user_num = user_num + 1;
    let zipcode = `9404${user_num % 9}` 
    gender = Math.random() > .55 ? 'F' : 'M';
    if(!is_first_user) {
      user_cmd += ', '
    }
    is_first_user = false;
    user_cmd += `('${user_id}', 'Name ${user_id}', '${email}', '${gender}', '${zipcode}', '${INTEREST}')`;
    
    // Creating Activity data for each user.
    let avtivity_num = 0;
    let rand_visit = Math.floor(Math.random()*10000)
    var activity_count = Math.random() * MAX_EVENT_PER_USER + 1 
    while (avtivity_num < activity_count) {
        let activity_id = `v_${GROUP_PREFIX}${avtivity_num}${rand_visit}`;
        avtivity_num += 1;
        let v_id = `${VIDEO_ID}.${Math.floor(Math.random()*VIDEO_COUNT)}`;
        let time_spent = Math.floor(Math.random() * (MAX_SPENT_TIME - MIN_SPENT_TIME) + MIN_SPENT_TIME) ;
        let timestamp = 1672531200 + Math.floor(Math.random() * 15552000); // Random between 2023-01-01 and 2023-06-26
        // Making a spike for Fathers day
        if (Math.random()< 0.01) { 
          timestamp = 1687016400 + Math.floor(Math.random() * 12000); // Random time on 2023-06-18
        }
        if(!is_first_activity) {
          activity_cmd += ', '
        }
        is_first_activity = false;
        activity_cmd += `('${activity_id}', '${user_id}', '${v_id}', ${time_spent}, TO_TIMESTAMP(${timestamp}))`;
        total_act_count += 1
        // Kind of flushing if things get too large
        if (total_act_count % 5000 == 0) {
            activity_cmd += ';'
            snowflake.execute({sqlText: activity_cmd});
            activity_cmd = 'INSERT INTO activity VALUES ';
            is_first_activity = true;
        }
    }
}
activity_cmd += ';'
user_cmd += ';'
if (!is_first_user) {
  snowflake.execute({sqlText: user_cmd});
}
if (!is_first_activity) {
   snowflake.execute({sqlText: activity_cmd});
}
total_videos = 0
if (GENERATE_VIDEO) {
  total_videos = VIDEO_COUNT
} 
return `generated ${USER_COUNT} users, ${total_videos} videos, and ${total_act_count} activities`
$$;


------------------------------------------------------------------------
----- Generate data for Nature Clips.
------------------------------------------------------------------------
USE DATABASE nature_clips_db;
USE SCHEMA nature_clips_schema;

-------------------------------------------------------------------------------------------------
--------------------- User Groups        Max Eng      Video Topic          Video Groups
---------------------    User#               min time                             Video #
---------------------          Interest          max time                              store videos
CALL generate_NC_data(1, 1811, 'hiker',  24, 24, 120, 'camping in Nature', 'v_1', 237, true);
CALL generate_NC_data(2, 4245, 'camper', 42, 55, 200, 'camping in Nature', 'v_1', 237, false);
CALL generate_NC_data(3, 468,  'paddler',18, 20, 40,  'camping in Nature', 'v_1', 237, false);

CALL generate_NC_data(4, 2978, 'hiker',  55, 55, 200, 'hiking in cities',  'v_2', 103, true);
CALL generate_NC_data(5, 1435, 'camper', 29, 35, 150, 'hiking in cities',  'v_2', 103, false);
CALL generate_NC_data(6, 997,  'paddler',21, 12, 103, 'hiking in cities',  'v_2', 103, false);
-- Kayayking videos
CALL generate_NC_data(7, 2122, 'hiker',  32, 34, 85,  'kayaking',          'v_3', 278, true);
CALL generate_NC_data(8, 3164, 'camper', 45, 53, 89,  'kayaking',          'v_3', 278, false);
CALL generate_NC_data(9, 9427, 'paddler',63, 100, 300,'kayaking',          'v_3', 278, false);

-- Low view-count videos
CALL generate_NC_data(11, 181, 'hiker',  2, 24, 120, 'camping in Nature', 'v_4', 3438, true);
CALL generate_NC_data(12, 445, 'camper', 4, 55, 200, 'camping in Nature', 'v_4', 3438, false);
CALL generate_NC_data(13, 168, 'paddler',1, 20, 40,  'camping in Nature', 'v_4', 3438, false);
CALL generate_NC_data(14, 278, 'hiker',  3, 55, 200, 'hiking in cities',  'v_5', 5103, true);
CALL generate_NC_data(15, 135, 'camper', 2, 35, 150, 'hiking in cities',  'v_5', 5103, false);
CALL generate_NC_data(16, 297, 'paddler',1, 12, 103, 'hiking in cities',  'v_5', 5103, false);
CALL generate_NC_data(17, 122, 'hiker',  1, 34, 85,  'kayaking',          'v_6', 4278, true);
CALL generate_NC_data(18, 164, 'camper', 1, 53, 89,  'kayaking',          'v_6', 4278, false);
CALL generate_NC_data(19, 427, 'paddler',2, 100, 300,'kayaking',          'v_6', 4278, false);

-- Users that are only in NatureClip
CALL generate_NC_data(101, 528, 'hiker',  4, 24, 120, 'camping in Nature', 'v_1', 237, false);
CALL generate_NC_data(102, 3119,'camper', 8, 55, 200, 'camping in Nature', 'v_1', 237, false);
CALL generate_NC_data(103, 275, 'paddler',2, 20, 40,  'camping in Nature', 'v_1', 237, false);
CALL generate_NC_data(101, 476, 'hiker',  3, 5, 34,   'rafting at home',   'v_4', 168, true);
CALL generate_NC_data(102, 652, 'camper', 4, 5, 100,  'rafting at home',   'v_4', 168, false);
CALL generate_NC_data(103, 4306,'paddler',18, 20, 400,'rafting at home',   'v_4', 168, false);

SELECT * FROM VISITORS SAMPLE(5 ROWS);
SELECT * FROM videos SAMPLE(5 ROWS);
SELECT * FROM activity SAMPLE(5 ROWS);

SELECT COUNT(*) FROM activity;
SELECT COUNT(*) FROM videos;
SELECT COUNT(*) FROM visitors;