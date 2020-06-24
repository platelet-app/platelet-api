# Delivery Tracker for Blood Bike Charities

## REST API routes

## Login

### /api/v0.1/login

*POST*

####  Header:
Content-Type: application/json

####  Payload:
username, password

####  Returns:
status code 200 on success

{ access_token }

status code 401 on failure

{ error, message, status_code }

## Sessions

### /api/v0.1/sessions

*POST*

####  Header:
Authorization: Bearer <token\>
Content-Type: application/json (optional)

####  Payload:
{ user (optional), timestamp }

####  Returns:
status code 200 on success

{ uuid, coordinator_uuid, message }

status code 403 on failure

{ message }

####  Description:

Creates a new session for the currently logged in user. If the user is an admin, they can specify creating a session for another user with user: uuid in the json payload.

*GET*

None

*PUT*

None

### /api/v0.1/sessions/<user_id\>/<start\>-<end\>/<order\>

*GET*

####  Header:
Authorization: Bearer <token\>

####  Payload:

None

####  Returns:
status code 200 on success

sessions

-uuid, timestamp, username

####  Description:

Returns a list of sessions of user id <user_id\>, of range <start\> to <end\>, in ascending or descending order. Items are ordered by time creation.

<start\>-<end\> and <order\> are optional.


### /api/v0.1/session/<session_id\>

*GET*

####  Header:
Authorization: Bearer <token\>

####  Payload:

None

####  Returns:

status code 200 on success

{ id, timestamp, user_id }

####  Description:

Returns details of session <session_id\>

### /api/v0.1/session/<session_id\>

*DELETE*

####  Header:
Authorization: Bearer <token\>

#### Payload:

None

#### Returns:
status code 202 on success

{id, message}

#### Description:

Puts session <session_id\> in a queue for deletion.

*PUT*

#### Payload:

user (as uuid), timestamp

## User

### /api/v0.1/users/<start\>-<end\>/<order\>

*GET*

#### Header:
Authorization: Bearer <token\>

#### Payload:

None

#### Returns:
status code 200 on success

[{id, username, links {collection, self}}]

#### Description:

Retrieves a list of all users.

<start\>-<end\> and <order\> are optional.

### /api/v0.1/users

*POST*

####  Payload:

{ username, { address: { country, county, line1, line2, postcode, town },
 password, name, email, dob, patch, roles }


#### Returns:

Status code 200 on success.

#### Description:

Add a new user.

### /api/v0.1/user/<user_id>

*GET*

#### Header:

Authorization: Bearer <token\>

#### Payload:

None

#### Returns:

status code 200 on success

{ address: { country, county, line1, line2, postcode, town } dob, email, links: { collection, self }, name, [ notes: { body, subject } ], patch, roles, username, uuid }

#### Description:

Retrieves details about a user.

*PUT*

####  Payload:

{ username, { address: { country, county, line1, line2, postcode, town },
 password, name, email, dob, patch, roles }

#### Returns:

Status code 200 on success.

#### Description:

Edits an existing user.


## Task

### /api/v0.1/tasks/<session_id\>

*GET*

#### Header:

Authorization: Bearer <token\>

#### Payload:

None

#### Returns:

status code 200 on success

[ { id, username, links { collection, self } } ]

#### Description:

Retrieves a list of all tasks for a specific session.

### /api/v0.1/tasks

*POST*

####  Payload:

{ pickup_address: { country, county, line1, line2, postcode, town },
 dropoff_address: { country, county, line1, line2, postcode, town },
 patch, contact_name, contact_number, priority, session_id, timestamp,
 assigned_rider }


#### Returns:

Status code 200 on success.

#### Description:

Add a new task.

### /api/v0.1/task/<task_id>

*GET*

#### Header:

Authorization: Bearer <token\>

#### Payload:

None

#### Returns:

status code 200 on success

{ address: { country, county, line1, line2, postcode, town }
 dob, email, links: { collection, self },
 name, [ notes: { body, subject } ], patch,
 roles, username, uuid }

#### Description:

Retrieves details about a task.

*PUT*

####  Payload:

{ pickup_address: { country, county, line1, line2, postcode, town },
 dropoff_address: { country, county, line1, line2, postcode, town },
 patch, contact_name, contact_number, priority, session_id, timestamp,
 assigned_rider }

#### Returns:

Status code 200 on success.

#### Description:

Edits an existing task.
