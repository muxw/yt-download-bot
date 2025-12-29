#!/usr/bin/env python3
# coding: utf-8

# ytdlbot - cache.py


import logging

import fakeredis
import redis

from config import REDIS_HOST


class Redis:
    def __init__(self):
        try:
            self.r = redis.StrictRedis(host=REDIS_HOST, db=1, decode_responses=True)
            self.r.ping()
        except Exception:
            logging.warning("Redis connection failed, using fake redis instead.")
            self.r = fakeredis.FakeStrictRedis(host=REDIS_HOST, db=1, decode_responses=True)

    def __del__(self):
        self.r.close()

    def add_cache(self, key, mapping):
        self.r.hset(key, mapping=mapping)

    def get_cache(self, k: str):
        return self.r.hgetall(k)

    def store_pending_download(self, chat_id: int, msg_id: int, url: str):
        """存储待选择格式的下载URL，5分钟过期"""
        key = f"pending:{chat_id}:{msg_id}"
        self.r.setex(key, 300, url)

    def get_pending_download(self, chat_id: int, msg_id: int) -> str | None:
        """获取待处理的下载URL"""
        key = f"pending:{chat_id}:{msg_id}"
        return self.r.get(key)

    def delete_pending_download(self, chat_id: int, msg_id: int):
        """删除待处理的下载记录"""
        key = f"pending:{chat_id}:{msg_id}"
        self.r.delete(key)
