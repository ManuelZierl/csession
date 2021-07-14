# CSession

The `csession` package implements a simple wrapper class around the 
[Session](https://github.com/psf/requests/blob/master/requests/sessions.py) class of the 
[requests](https://github.com/psf/requests) module called `CustomSession` that give more freedom to the 
programmer to customize his session by for example setting a default timeout or headers.

## Installation

`pip install csession`

## Usage
 
The core of the package is the `CustomSession` class which mostly acts just like a normal `Session`

```python
from csession import CustomSession

csess = CustomSession()

_ = csess.get("http://myurl.com")
_ = csess.post("http://myurl.com")
```

additionally, the `CustomSesion` accepts all the parameters for a request in the constructor to be set as default

```python
from csession import CustomSession

csess = CustomSession(timeout=30, headers={'Content-type': 'application/json'})

# all upcoming requests will timeout after 30 seconds and have a Content-type json header

...
```

the `CustomSession` can also set a default prepare methode to  manipulate the request
before they are sent. This is for example useful for authentication purposes or url prefixing.
Here is a example for a session that is prefixing every request and also adding a default password an appId
to the json body of a request

```python
from csession import CustomSession

config = {...}

# prepare function accepts methode url and params and also returns those again
# params are formatted as a dict
def prepare_microlog_request(methode, url, params):
    url = "https://my-default-url_prefix"+ url
    params["json"] = dict(params["json"], **{
        'appId': config['APP_ID'],
        'password': config['PASSWORD'],
    })
    return methode, url, params


# Use this Session to make requests to microlog
csess = CustomSession(
    timeout=100,
    headers={'Content-type': 'application/json'},
    prepare=prepare_microlog_request
)

csess.get("/path/to/endpoint")
```

if for a single call the prepare methode should be suppressed you can do:
```python
from csession import CustomSession
csess = CustomSession(prepare=...)

csess.use_prepare = False
csess.get("http://www.url_without_prepare.com")
csess.use_prepare = True
```
or equivalently use the provided context manager:
```python
from csession import CustomSession, without_preparation
csess = CustomSession(prepare=...)

with without_preparation(csess) as sess:
    sess.get("http://www.url_without_prepare.com")
```

The `CustomSession` also provides a simple history function in for of a deque.
History is deactivated by default but can be activated in the constructor by setting 
`save_last_requests=`

```python
from csession import CustomSession, without_preparation

csess = CustomSession(save_last_requests=3) # the last 3 requests are stored

csess.get("http://www.myurl.com")

print(csess.history)

```