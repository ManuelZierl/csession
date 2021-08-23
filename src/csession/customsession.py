import collections
from typing import Optional

import requests
from requests import Response


class without_preparation:
    """
    a context manger for code blocks that shouldn't use preparation
    """
    def __init__(self, custom_session):
        assert isinstance(custom_session, CustomSession)
        self.custom_session = custom_session

    def __enter__(self):
        self.custom_session.use_prepare = False
        return self.custom_session

    def __exit__(self, *args, **kwargs):
        self.custom_session.use_prepare = True


class CustomSession(requests.Session):
    """ This is a Wrapper Class for the request.Session class

    This Class inherits all functionality from the request.Session class with the additional feature that
    all kwargs that can be passed to an request are configurable as default in the constructor of this class

    For more information about this parameters pleas refer to the Session class in <your-packages>/requests/session.py
    The default parameters can be overwritten by parameters in the direct call of an request methode.

    There are also additional arguments:
    :param prepare: prepare is a (optional) function 'def prepare(methode, url, params) -> methode, url, params'
        which is called before every request of this session. You are therefore able to edit the request
        everytime before its made. You need to ensure that the function returns methode, url, params, where params
        is a dict.
        If you want to do a exemption request with this session (not using the prepare methode) you can do the following:
        ```python
        custom_session.use_prepare = False
        custom_session.get("http://www.url_without_prepare.com")
        custom_session.use_prepare = True
        ```
        or alternatively you could use an context manager like:
        ```python
        with without_preparation(custom_session) as sess:
            custom_session.get("http://www.url_without_prepare.com")
        ```
        # todo: explain prepare_args: how to pass arguments to the prepare function
        # todo: explain handle_exception: ...
    :param save_last_requests: int defining the last how many requests get stores in the self.history variable. This is
        useful if you for example want to know the content of a request after it was done (with al the changes this
        class as made). Default is set to 0
    """

    def __init__(self, params=None, data=None, headers=None, cookies=None, files=None,
                 auth=None, timeout=None, allow_redirects=None, proxies=None,
                 hooks=None, stream=None, verify=None, cert=None, json=None,
                 prepare=None, save_last_requests=0, handle_exception=None):
        self.default_kwargs = {
            "params": params, "data": data, "headers": headers, "cookies": cookies, "files": files, "auth": auth,
            "timeout": timeout, "allow_redirects": allow_redirects, "proxies": proxies, "hooks": hooks,
            "stream": stream, "verify": verify, "cert": cert, "json": json
        }
        assert prepare is None or isinstance(prepare, collections.Callable)
        self.handle_exception = handle_exception
        self.prepare = prepare
        self.use_prepare = True
        self.save_last_requests = save_last_requests
        self.history = collections.deque(maxlen=self.save_last_requests)
        self.default_kwargs = {key: val for key, val in self.default_kwargs.items() if val is not None}
        super().__init__()

    def request(self, method: str, url, prepare_args=None, handle_exception_args=None, **kwargs) -> Optional[Response]:
        if prepare_args is None:
            prepare_args = {}
        if self.use_prepare and self.prepare:
            method, url, kwargs = self.prepare(method, url, kwargs, **prepare_args)
        kwargs = dict(self.default_kwargs, **kwargs)

        self.history.append({
            "methode": method,
            "url": url,
            "params": kwargs
        })

        if self.handle_exception is not None:
            try:
                r = super().request(method, url, **kwargs)
                return r
            except requests.RequestException as exc:
                if handle_exception_args is None:
                    handle_exception_args = {}
                handle_args = dict(
                    method=method,
                    url=url,
                    params=kwargs,
                    **handle_exception_args
                )
                return self.handle_exception(exc, **handle_args)
        return super().request(method, url, **kwargs)

    def last_json_body(self):
        """
        Gets the json body of the last request that was done.
        WARNING: save_last_requests must be > 0
        """
        assert len(self.history) > 0, "last_json_body() called but history is empty, you might have forgotten  to " \
                                      "set 'save_last_requests' or called the function before doing a request"
        return self.history[-1]["params"]["json"]
