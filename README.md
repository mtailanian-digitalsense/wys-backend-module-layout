# API Endpoints for Layout

Port: 8086

- [API Endpoints for Layout](#api-endpoints-for-layout)
  - [Get the latest configuration of the spaces in the layout by project ID](#get-the-latest-configuration-of-the-spaces-in-the-layout-by-project-id)
    - [Success Response](#success-response)
    - [Error Responses](#error-responses)
    - [Or](#or)
  - [Generate the initial layout with Smart Layout engine by project ID (asynchronous job)](#generate-the-initial-layout-with-smart-layout-engine-by-project-id-asynchronous-job)
    - [Success Response](#success-response-1)
    - [Error Responses](#error-responses-1)
    - [Or](#or-1)
    - [Or](#or-2)
  - [Get the status of asynchronous job by ID](#get-the-status-of-asynchronous-job-by-id)
    - [Success Response](#success-response-2)
    - [Error Responses](#error-responses-2)
    - [Or](#or-3)
  - [Get the result of the asynchronous job.](#get-the-result-of-the-asynchronous-job)
    - [Success Response](#success-response-3)
    - [Error Responses](#error-responses-3)
    - [Or](#or-4)
    - [Or](#or-5)
  - [Generate the initial layout with Smart Layout engine by project ID](#generate-the-initial-layout-with-smart-layout-engine-by-project-id)
    - [Success Response](#success-response-4)
    - [Error Responses](#error-responses-4)
    - [Or](#or-6)
    - [Or](#or-7)
  - [Update the configuration of the spaces in the layout by project ID](#update-the-configuration-of-the-spaces-in-the-layout-by-project-id)
    - [Success Response](#success-response-5)
    - [Error Responses](#error-responses-5)
    - [Or](#or-8)
    - [Or](#or-9)
  - [Get the latest configuration for the Smart Layout engine](#get-the-latest-configuration-for-the-smart-layout-engine)
    - [Success Response](#success-response-6)
    - [Error Responses](#error-responses-6)
    - [Or](#or-10)
  - [Update or create the configuration for the Smart Layout engine](#update-or-create-the-configuration-for-the-smart-layout-engine)
    - [Success Response](#success-response-7)
    - [Error Responses](#error-responses-7)
    - [Or](#or-11)

## Get the latest configuration of the spaces in the layout by project ID

**URL** : `/api/layouts/{project_id}`

**URL Parameters** : 

* `{project_id}=[integer]` where `project_id` is the ID of the Project on the server.

**Method** : `GET`

**Auth required** : YES

### Success Response

**Code** : `200 OK`

**Content example:**
If the building's id is 1, then the response will be: 
````json
{
  "building_id": 7,
  "floor_id": 15,
  "id": 166,
  "selected_floor": {
    "active": true,
    "building_id": 7,
    "elevators_number": 7,
    "id": 15,
    "image_link": "[link-string]",
    "m2": 650,
    "rent_value": 5000,
    "wys_id": "CL15"
  },
  "workspaces": [
    {
      "height": 130.785,
      "id": 1647,
      "image": "[2D-base64-image-string]",
      "layout_gen_id": 166,
      "position_x": 944.355,
      "position_y": 550.85,
      "rotation": "90",
      "space_id": 2,
      "width": 98.2938
    },
    ...
  ]
}
````

### Error Responses

**Condition** : If the project with submitted `project_id`, the layout floor or a layout space was not found.

**Code** : `404 Not Found`

**Content** : `{error_message}`

### Or

**Condition** :  If server or database has some error.

**Code** : `500 Internal Error Server`

**Content** : `{error_message}`

## Generate the initial layout with Smart Layout engine by project ID (asynchronous job)

**URL** : `/api/layouts/{project_id}`

**URL Parameters** : 

* `{project_id}=[integer]` where `project_id` is the ID of the Project on the server.

**Method** : `POST`

**Auth required** : YES

```json
{
    "selected_floor": {
      "active": true,
      "building_id": 6,
      "elevators_number": 2,
      "id": 11,
      "image_link": "{link}",
      "m2": 401.6,
      "rent_value": 10132,
      "wys_id": "CL11"
    },
    "workspaces": [
      {
        "active": true,
        "down_gap": 2,
        "height": 4.05,
        "id": 2,
        "left_gap": 2,
        "name": "WYS_SALAREUNION_RECTA6PERSONAS",
        "points": [],
        "regular": true,
        "right_gap": 2,
        "subcategory_id": 1,
        "up_gap": 2,
        "width": 3,
        "quantity": 2
      },
      ...
    ]
}
```

### Success Response

**Code** : `201 CREATED`

**Content example**

```json

```

### Error Responses

**Condition** : If required field is missing in the body or the submitted body is not a JSON type.

**Code** : `400 Bad Request`

**Content** : `{error_message}`

### Or

**Condition** : If the project with submitted `project_id`, the layout floor or a layout space was not found.

**Code** : `404 Not Found`

**Content** : `{error_message}`

### Or

**Condition** : If an error occurs with the internal server or database connection.

**Code** : `500 Internal Server Error`

**Content** : `{error_message}`

## Get the status of asynchronous job by ID

**URL** : `/api/layouts/v2/job/{job_id}`

**URL Parameters** : 

* `{job_id}=[string]` where `job_id` is the generated ID of the Job by the server.

**Method** : `GET`

**Auth required** : YES

### Success Response

**Code** : `200 OK`

**Content example:**
If the building's id is 1, then the response will be: 
````json

````

### Error Responses

**Condition** : If the project with submitted `project_id`, the layout floor or a layout space was not found.

**Code** : `404 Not Found`

**Content** : `{error_message}`

### Or

**Condition** :  If server or database has some error.

**Code** : `500 Internal Error Server`

**Content** : `{error_message}`

## Get the result of the asynchronous job.

**URL** : `/api/layouts/v2/job`

**URL Parameters** : 

**Method** : `POST`

**Auth required** : YES

**Required body** :
```json
{
  "job_id": "[string]",
  "project_id": 0
}
```

### Success Response

**Code** : `201 CREATED`

**Content example**

```json
{
  "building_id": 7,
  "floor_id": 15,
  "id": 166,
  "selected_floor": {
    "active": true,
    "building_id": 7,
    "elevators_number": 7,
    "id": 15,
    "image_link": "[link-string]",
    "m2": 650,
    "rent_value": 5000,
    "wys_id": "CL15"
  },
  "workspaces": [
    {
      "height": 130.785,
      "id": 1647,
      "image": "[2D-base64-image-string]",
      "layout_gen_id": 166,
      "position_x": 944.355,
      "position_y": 550.85,
      "rotation": "90",
      "space_id": 2,
      "width": 98.2938
    },
    ...
  ]
}
```

### Error Responses

**Condition** : If required field is missing in the body or the submitted body is not a JSON type.

**Code** : `400 Bad Request`

**Content** : `{error_message}`

### Or

**Condition** : If the project with submitted `project_id` or the job was not found.

**Code** : `404 Not Found`

**Content** : `{error_message}`

### Or

**Condition** : If an error occurs with the internal server or database connection.

**Code** : `500 Internal Server Error`

**Content** : `{error_message}`

## Generate the initial layout with Smart Layout engine by project ID

**URL** : `/api/layouts/{project_id}`

**URL Parameters** : 

* `{project_id}=[integer]` where `project_id` is the ID of the Project on the server.

**Method** : `POST`

**Auth required** : YES

**Required body** :
```json
{
  "selected_floor": {
    "active": true,
    "building_id": 6,
    "elevators_number": 2,
    "id": 11,
    "image_link": "[link-string]",
    "m2": 401.6,
    "rent_value": 10132,
    "wys_id": "CL11"
  },
  "workspaces": [
    {
      "active": true,
      "down_gap": 2,
      "height": 4.05,
      "id": 2,
      "left_gap": 2,
      "name": "WYS_SALAREUNION_RECTA6PERSONAS",
      "points": [],
      "regular": true,
      "right_gap": 2,
      "subcategory_id": 1,
      "up_gap": 2,
      "width": 3,
      "quantity": 2
    },
    ...
  ]
}
```

### Success Response

**Code** : `201 CREATED`

**Content example**

```json
{
  "building_id": 7,
  "floor_id": 15,
  "id": 166,
  "selected_floor": {
    "active": true,
    "building_id": 7,
    "elevators_number": 7,
    "id": 15,
    "image_link": "[link-string]",
    "m2": 650,
    "rent_value": 5000,
    "wys_id": "CL15"
  },
  "workspaces": [
    {
      "height": 130.785,
      "id": 1647,
      "image": "[2D-base64-image-string]",
      "layout_gen_id": 166,
      "position_x": 944.355,
      "position_y": 550.85,
      "rotation": "90",
      "space_id": 2,
      "width": 98.2938
    },
    ...
  ]
}
```

### Error Responses

**Condition** : If required field is missing in the body or the submitted body is not a JSON type.

**Code** : `400 Bad Request`

**Content** : `{error_message}`

### Or

**Condition** : If the project with submitted `project_id`, the layout floor or a layout space was not found.

**Code** : `404 Not Found`

**Content** : `{error_message}`

### Or

**Condition** : If an error occurs with the internal server or database connection.

**Code** : `500 Internal Server Error`

**Content** : `{error_message}`

## Update the configuration of the spaces in the layout by project ID

**URL** : `/api/layouts/{project_id}`

**URL Parameters** : 

* `{project_id}=[integer]` where `project_id` is the ID of the Project on the server.

**Method** : `PUT`

**Auth required** : YES

**Required body** :
```json
[
  {
    "height": 130.785,
    "id": 1647,
    "image": "[2D-base64-image-string]",
    "layout_gen_id": 166,
    "position_x": 944.355,
    "position_y": 550.85,
    "rotation": "90",
    "space_id": 2,
    "width": 98.2938
  },
  ...
]
```

### Success Response

**Code** : `200 OK`

**Content example**

```json
{
  "building_id": 7,
  "floor_id": 15,
  "id": 166,
  "selected_floor": {
    "active": true,
    "building_id": 7,
    "elevators_number": 7,
    "id": 15,
    "image_link": "[link-string]",
    "m2": 650,
    "rent_value": 5000,
    "wys_id": "CL15"
  },
  "workspaces": [
    {
      "height": 130.785,
      "id": 1647,
      "image": "[2D-base64-image-string]",
      "layout_gen_id": 166,
      "position_x": 944.355,
      "position_y": 550.85,
      "rotation": "90",
      "space_id": 2,
      "width": 98.2938
    },
    ...
  ]
}
```

### Error Responses

**Condition** : If required field is missing in the body or the submitted body is not a JSON type.

**Code** : `400 Bad Request`

**Content** : `{error_message}`

### Or

**Condition** : If the project with submitted `project_id`, the layout floor or a layout space was not found.

**Code** : `404 Not Found`

**Content** : `{error_message}`

### Or

**Condition** : If an error occurs with the internal server or database connection.

**Code** : `500 Internal Server Error`

**Content** : `{error_message}`

## Get the latest configuration for the Smart Layout engine

**URL** : `/api/layouts/configs`

**Method** : `GET`

**Auth required** : YES

### Success Response

**Code** : `200 OK`

**Content example:**
````json
{
  "generations": 50,
  "id": 1,
  "pop_size": 50
}
````

### Error Responses

**Condition** :  If there is no existing configuration for the Smart Layout.

**Code** : `404 Not Found`

**Content** : `{error_message}`

### Or

**Condition** :  If server or database has some error.

**Code** : `500 Internal Error Server`

**Content** : `{error_message}`

## Update or create the configuration for the Smart Layout engine

**URL** : `/api/layouts/configs`

**Method** : `PUT`

**Auth required** : YES

**Required body** :

**Note: The values of each of the configuration parameters must be greater than 25.**
```json
{
  "generations": 50,
  "pop_size": 50
}
```

### Success Response

**Code** : `200 OK`

**Content example**

```json
{
  "generations": 50,
  "id": 1,
  "pop_size": 50
}
```

### Error Responses

**Condition** : If required field is missing in the body or the submitted body is not a JSON type.

**Code** : `400 Bad Request`

**Content** : `{error_message}`

### Or

**Condition** : If an error occurs with the internal server or database connection.

**Code** : `500 Internal Server Error`

**Content** : `{error_message}`