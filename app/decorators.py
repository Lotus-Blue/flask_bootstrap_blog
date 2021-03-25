#-*- coding:utf-8 -*-

from functools import wraps
from flask import abort
from flask_login import current_user
from .models import Permission, AnonymousUser

from app import redis_client
import time

def mark_online(user):
    user_id = str(user.id).encode('utf-8')
    now = int(time.time())
    expires = now + (5 * 60) + 10
    all_users_key = "online-users/%d" % (now // 60)
    user_key = "user-activity/%s" % user_id
    p = redis_client.pipeline()
    p.sadd(all_users_key, user_id)
    p.set(user_key, now)
    p.expireat(all_users_key, expires)
    p.expireat(user_key, expires)
    p.execute()

def permission_required(permission):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.can(permission):
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    return permission_required(Permission.ADMINISTER)(f)

def push_online(user):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user = current_user._get_current_object()
            isAnonymousUser = isinstance(user,AnonymousUser)#没登陆的话值为True
            if not isAnonymousUser:
                mark_online(user)#记录在线信息
            return f(*args, **kwargs)
        return decorated_function
    return decorator
