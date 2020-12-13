"""
    Author: Reza Karami
    Date: 12/12/20 11:08 PM
    Description: ``
"""
import json
import logging
from typing import Union, Mapping, Any, List

import requests
from celery import shared_task

from request_.models import Request

logger = logging.getLogger(__name__)

JSON = Union[str, int, float, bool, None, Mapping[str, Any], List[Any]], dict


def get_json_resp(url: str, method: str = 'get', **kwargs) -> JSON:
    try:
        resp = getattr(requests, method)(url, **kwargs)

        if not resp.ok:
            logger.warning('failed to fetch data from api endpoint, reason=%s', resp.content)
            try:
                return resp.status_code, resp.json()
            except json.JSONDecodeError:
                return resp.status_code, None

        try:
            if resp.status_code != 204:
                return resp.status_code, resp.json()
            return 204, None
        except json.JSONDecodeError as e:
            logger.warning('failed to decode response from api endpoint, error=%s', e)
            return None, None
    except requests.RequestException as e:
        logger.warning('failed to connect to api endpoint, error=%s', e)
        return None, None
    except Exception as e:
        logger.warning('unknown error calling api endpoint, reason=%s', e)
        return None, None


@shared_task
def execute_request(request_id: int):
    try:
        request = Request.objects.get(id=request_id, status=Request.STATUS_TYPE_PENDING)
    except Request.DoesNotExist:
        logger.warning('A pending request with request_id=%d was not found!', request_id)
        return

    http_status, response_body = get_json_resp(request.url, request.method, data=request.data, params=request.params)

    if http_status is None:
        request.status = Request.STATUS_TYPE_FAILED
        request.save(update_fields=['status'])
    else:
        request.status = Request.STATUS_TYPE_SUCCESSFUL
        request.response_http_status = http_status
        request.response_body = response_body
        request.save(update_fields=['status', 'response_http_status', 'response_body'])