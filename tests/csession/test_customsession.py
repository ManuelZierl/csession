from collections import deque

import pytest
import requests
from requests import ReadTimeout, Timeout

from csession import CustomSession, without_preparation


def test_custom_session_init(mocker):
    mocker.patch("requests.Session.request")
    spy_request = mocker.spy(requests.Session, "request")

    sess = CustomSession(headers={'Content-type': 'application/json'}, timeout=42, save_last_requests=3)
    assert sess.default_kwargs == {'headers': {'Content-type': 'application/json'}, 'timeout': 42}
    assert sess.prepare is None
    assert sess.use_prepare is True
    assert sess.save_last_requests == 3
    assert isinstance(sess.history, deque)
    assert sess.history.maxlen == 3
    assert list(sess.history) == []

    _ = sess.post("https://httpbin.org/delay/10", json={"my": "request"})
    spy_request.assert_called_once()
    spy_request.assert_called_with('POST', 'https://httpbin.org/delay/10',
                                   headers={'Content-type': 'application/json'},
                                   timeout=42, data=None, json={'my': 'request'})


def test_custom_session_prepare(mocker):
    mocker.patch("requests.Session.request")
    spy_request = mocker.spy(requests.Session, "request")

    def prepare(methode, url, params):
        assert methode == "POST"
        assert url == "https://httpbin.org/delay/10"
        assert params == {'data': None, 'json': {'my': 'request'}}
        return methode, url, params

    sess = CustomSession(
        headers={'Content-type': 'application/json'},
        timeout=42,
        save_last_requests=3,
        prepare=prepare
    )
    _ = sess.post("https://httpbin.org/delay/10", json={"my": "request"})
    spy_request.assert_called_once()
    spy_request.assert_called_with('POST', 'https://httpbin.org/delay/10',
                                   headers={'Content-type': 'application/json'},
                                   timeout=42, data=None, json={'my': 'request'})


def test_custom_session_request(mocker):
    mocker.patch("requests.Session.request")
    spy_request = mocker.spy(requests.Session, "request")

    sess = CustomSession(
        headers={'Content-type': 'application/json'},
        timeout=42,
        save_last_requests=3,
    )

    _ = sess.post("https://httpbin.org/delay/10", json={"my": "request"})
    spy_request.assert_called_once()
    spy_request.assert_called_with('POST', 'https://httpbin.org/delay/10',
                                   headers={'Content-type': 'application/json'},
                                   timeout=42, data=None, json={'my': 'request'})
    spy_request.reset_mock()

    _ = sess.get("https://httpbin.org/delay/10")
    spy_request.assert_called_once()
    spy_request.assert_called_with('GET', 'https://httpbin.org/delay/10', headers={'Content-type': 'application/json'},
                                   timeout=42, allow_redirects=True)
    spy_request.reset_mock()

    _ = sess.options("https://httpbin.org/delay/10")
    spy_request.assert_called_once()
    spy_request.assert_called_with('OPTIONS', 'https://httpbin.org/delay/10',
                                   headers={'Content-type': 'application/json'},
                                   timeout=42, allow_redirects=True)


def test_custom_session_timeout(httpbin):
    # test a real request to a local httbin server
    sess = CustomSession(headers={'Content-type': 'application/json'}, timeout=2, save_last_requests=3)
    _ = sess.get(f"{httpbin.url}/delay/1")

    with pytest.raises(ReadTimeout):
        _ = sess.get(f"{httpbin.url}/delay/3")

    with pytest.raises(Timeout):
        _ = sess.get(f"{httpbin.url}/delay/3")

    new_sess = CustomSession(headers={'Content-type': 'application/json'}, timeout=6)
    _ = new_sess.get(f"{httpbin.url}/delay/3")


def test_deactivate_preparation_context(mocker):
    mocker.patch("requests.Session.request")
    spy_request = mocker.spy(requests.Session, "request")

    def prepare(methode, url, params):
        assert False  # this methode should never be called

    sess = CustomSession(
        headers={'Content-type': 'application/json'},
        timeout=42,
        save_last_requests=3,
        prepare=prepare
    )
    sess.use_prepare = False
    _ = sess.post("https://httpbin.org/delay/10", json={"my": "request"})
    spy_request.assert_called_once()
    spy_request.assert_called_with('POST', 'https://httpbin.org/delay/10',
                                   headers={'Content-type': 'application/json'},
                                   timeout=42, data=None, json={'my': 'request'})
    spy_request.reset_mock()
    sess.use_prepare = True

    with pytest.raises(AssertionError):
        _ = sess.post("https://httpbin.org/delay/10", json={"my": "request"})
        spy_request.assert_called_once()
        spy_request.assert_called_with('POST', 'https://httpbin.org/delay/10',
                                       headers={'Content-type': 'application/json'},
                                       timeout=42, data=None, json={'my': 'request'})

    spy_request.reset_mock()
    with without_preparation(sess) as s:
        _ = s.post("https://httpbin.org/delay/10", json={"my": "request"})
        spy_request.assert_called_once()
        spy_request.assert_called_with('POST', 'https://httpbin.org/delay/10',
                                       headers={'Content-type': 'application/json'},
                                       timeout=42, data=None, json={'my': 'request'})

    # check if context manger properly resets
    assert sess.use_prepare is True
    with pytest.raises(AssertionError):
        _ = sess.post("https://httpbin.org/delay/10", json={"my": "request"})
        spy_request.assert_called_once()
        spy_request.assert_called_with('POST', 'https://httpbin.org/delay/10',
                                       headers={'Content-type': 'application/json'},
                                       timeout=42, data=None, json={'my': 'request'})


def test_custom_session_history(mocker):
    mocker.patch("requests.Session.request")
    sess = CustomSession(
        headers={'Content-type': 'application/json'},
        timeout=42,
        save_last_requests=3,
    )
    _ = sess.post("https://httpbin.org/delay/1", json={"my": 1})
    _ = sess.post("https://httpbin.org/delay/2", json={"my": 2})
    _ = sess.post("https://httpbin.org/delay/3", json={"my": 3})
    _ = sess.post("https://httpbin.org/delay/4", json={"my": 4})
    assert list(sess.history) == [{
        'methode': 'POST',
        'url': f'https://httpbin.org/delay/{i}',
        'params': {
            'headers': {'Content-type': 'application/json'},
            'timeout': 42,
            'data': None,
            'json': {'my': i}
        }
    } for i in range(2, 5)]
    assert sess.last_json_body() == {"my": 4}



def test_prepare_args(mocker):
    mocker.patch("requests.Session.request")
    spy_request = mocker.spy(requests.Session, "request")

    def prepare_42(methode, url, params, foo=43):
        assert foo == 42
        return methode, url, params

    sess = CustomSession(
        headers={'Content-type': 'application/json'},
        timeout=42,
        save_last_requests=3,
        prepare=prepare_42
    )
    _ = sess.post("https://httpbin.org/", json={"my": "request"}, prepare_args={"foo": 42})

    def prepare_43(methode, url, params, foo=43):
        assert foo == 43
        return methode, url, params

    sess = CustomSession(
        headers={'Content-type': 'application/json'},
        timeout=42,
        save_last_requests=3,
        prepare=prepare_43
    )
    _ = sess.post("https://httpbin.org/", json={"my": "request"})
