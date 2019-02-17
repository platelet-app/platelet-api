#Delivery Tracker for Blood Bike Charities

##REST API routes

##Login

###/api/v0.1/login

*POST*

####Header:
Content-Type: application/json

####Payload:
username, password

####Returns:
status code 200 on success
access_token

status code 401 on failure
error, message, status_code

##Sessions

###/api/v0.1/sessions

*POST*

####Header:
Authorization: Bearer <token\>
Content-Type: application/json (optional)

####Payload:
user (as integer id) (optional)

####Returns:
status code 200 on success
id, user_id, message

status code 403 on failure
message

####Description:

Creates a new session for the currently logged in user. If the user is an admin, they can specify creating a session for another user with user: id in the json payload.

*GET*

None

###/api/v0.1/sessions/<user_id\>/<start\>-<end\>/<order\>

*GET*

####Header:
Authorization: Bearer <token\>

####Payload:

None

####Returns:
status code 200 on success
sessions
-id, timestamp, username

####Description:

Returns a list of sessions of user id <user_id\>, of range <start\> to <end\>, in ascending or descending order. Items are ordered by time creation.

<start\>-<end\> and <order\> are optional.


###/api/v0.1/session/<session_id\>

*GET*

####Header:
Authorization: Bearer <token\>

####Payload:

None

####Returns:
status code 200 on success
id, timestamp, user_id

####Description:

Returns details of session <session_id\>

###/api/v0.1/session/<session_id\>

*DELETE*

####Header:
Authorization: Bearer <token\>

####Payload:

None

####Returns:
status code 202 on success
id, message

####Description:

Puts session <session_id\> in a queue for deletion.

##User

###/api/v0.1/users

*GET*

####Header:
Authorization: Bearer <token\>

####Payload:

None

####Returns:
status code 200 on success
users
-id, username

####Description:

Puts session <session_id\> in a queue for deletion.
