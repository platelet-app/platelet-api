# Delivery Tracker for Blood Bike Charities

## REST API routes

## Login

### /api/<ver\>/login

*POST*

####  Header:
`Content-Type: application/json`

####  Payload:
`{username, password}`

#### Query strings:

None.

####  Returns:
status code 200 on success

`{ access_token, refresh_expiry, login_expiry }`

status code 401 on authentication failure

`{ error, message, status_code }`

### /api/<ver\>/refresh_token

*GET*

#### Header:
Authorization: Bearer <token\>

#### Query strings:

None.

#### Returns:

status code 200 on success

`{ access_token, refresh_expiry, login_expiry }`

status code 401 on failure (typically when the login has expired)

`{ error, message, status_code }`

status code 425 when access permission has not expired yet

`{ error, message, status_code }`

## User

### /api/<ver\>/whoami

*GET*

#### Query strings:

None.

#### Returns:

status code 200 on success

```
{
  "address": {
    "country",
    "county",
    "line1",
    "line2", 
    "postcode", 
    "town", 
    "ward", 
    "what3words", 
  },
  "assigned_vehicles": [], 
  "contact_number", 
  "display_name", 
  "dob", 
  "email", 
  "links": {
    "collection", 
    "self", 
  },
  "login_expiry", 
  "name", 
  "password_reset_on_login", 
  "patch", 
  "patch_id", 
  "profile_picture_thumbnail_url", 
  "profile_picture_url", 
  "refresh_expiry", 
  "roles": [],
  "time_created", 
  "time_modified", 
  "username", 
  "uuid", 
}
```

#### Description:

Returns information about the currently logged in user.

### /api/<ver\>/users

*GET*

#### Header:
Authorization: Bearer <token\>

#### Query strings:

page=<int\>

order=<string\>

"newest" or "oldest"

#### Returns:
status code 200 on success

```
[
    {
        "uuid", 
        "display_name", 
        "time_created", 
        "username", 
        "links", 
            "self", 
            "collection", 
        },
        "name", 
        "patch_id", 
        "patch", 
        "time_modified", 
        "contact_number", 
        "profile_picture_thumbnail_url", 
        "password_reset_on_login", 
        "roles": [],
        "assigned_vehicles": []
    }
]
```

#### Description:

Retrieves a list of registered users.

### /api/<ver\>/users

*POST*

####  Payload:


```
{
    "uuid",
    "username",
    "address",
    "name",
    "email",
    "dob",
    "patch",
    "roles",
    "display_name",
    "patch_id",
    "contact": {
        "name",
        "address": {
           "ward",
           "line1",
           "line2",
           "town",
           "county",
           "country",
           "postcode",
           "what3words
        },
        "telephone_number",
        "mobile_number",
        "email_address"
    },
    "password_reset_on_login",
}
                  
```

#### Returns:

Status code 200 on success.

#### Description:

Adds a new user.

### /api/<ver\>/user/<user_id\>

*GET*

#### Header:

Authorization: Bearer <token\>

#### Returns:

status code 200 on success
```
{
  "address": 
    "country", 
    "county", 
    "line1", 
    "line2", 
    "postcode", 
    "town", 
    "ward", 
    "what3words", 
  },
  "assigned_vehicles": []
  "contact_number",
  "display_name",
  "dob",
  "email",
  "links": 
    "collection",
    "self",
  },
  "name",
  "password_reset_on_login",
  "patch",
  "patch_id",
  "profile_picture_thumbnail_url",
  "profile_picture_url",
  "roles": [],
  "time_created",
  "time_modified",
  "username",
  "uuid",
}

```


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

### /api/<ver\>/tasks/<session_id\>

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

### /api/<ver\>/tasks

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

### /api/<ver\>/task/<task_id>

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
