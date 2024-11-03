import ydb
import ydb.iam
import uuid
import datetime
import os
import json

UserStatuses = {
    'INITIAL': 1,
    'LOCATION_SET': 2,
    'MATCHING_STARTED': 3
}

class Repository:
    def __init__(self):
        driver_config = ydb.DriverConfig(
             endpoint=os.getenv("YDB_ENDPOINT"),
            database=os.getenv("YDB_DATABASE"),
             #  metadata url credentials.
            credentials=ydb.iam.MetadataUrlCredentials(),
        )

        driver = ydb.Driver(driver_config)
        # Wait for the driver to become active for requests.
        driver.wait(fail_fast=True, timeout=5)
        # Create the session pool instance to manage YDB sessions.
        pool = ydb.SessionPool(driver)
        self.pool = pool
        self.USERS_TABLE = 'users'
        self.REQUESTS_TABLE = 'requests'
    
    def add_user(self, chat_id):
        text = f"INSERT INTO {self.USERS_TABLE} SELECT '{str(uuid.uuid1().hex)}' as id, {chat_id} as chat_id, {UserStatuses['INITIAL']} as status, '{str(datetime.datetime.utcnow())}' as createdAt;"
        return self.pool.retry_operation_sync(lambda s: s.transaction().execute(
        text,
        commit_tx=True,
        settings=ydb.BaseRequestSettings().with_timeout(3).with_operation_timeout(2)
    ))

    def set_user_geo_info(self, chat_id, lat, long):
        text = f"UPDATE {self.USERS_TABLE} SET long = {long}, lat = {lat}, status = {UserStatuses['LOCATION_SET']} WHERE chat_id = {chat_id};"
        return self.pool.retry_operation_sync(lambda s: s.transaction().execute(
            text,
            commit_tx=True,
            settings=ydb.BaseRequestSettings().with_timeout(3).with_operation_timeout(2)
        ))

    def get_user(self, chat_id):
        text = f"SELECT * FROM {self.USERS_TABLE} WHERE chat_id == {chat_id};"
        arr = self.pool.retry_operation_sync(lambda s: s.transaction().execute(
            text,
            commit_tx=True,
            settings=ydb.BaseRequestSettings().with_timeout(3).with_operation_timeout(2)
        ))[0].rows
        
        if len(arr) > 0:
            return arr[0]
        return None

    def get_user_last_prediction(self, chat_id):
        text = f"SELECT * FROM {self.REQUESTS_TABLE} WHERE chat_id == {chat_id} ORDER BY pageNumber DESC LIMIT 1;"
        arr = self.pool.retry_operation_sync(lambda s: s.transaction().execute(
            text,
            commit_tx=True,
            settings=ydb.BaseRequestSettings().with_timeout(3).with_operation_timeout(2)
        ))[0].rows

        if len(arr) > 0:
            return arr[0]
        return None

    def set_user_prediction(self, chat_id, count, distance, pageNumber, altitudeDifference, isLoop, category, routeId):
        prediction_id = str(uuid.uuid1().hex)
        
        text = f"INSERT INTO {self.REQUESTS_TABLE} SELECT '{prediction_id}' as id, {chat_id} as chat_id, {count} as count, '{str(datetime.datetime.utcnow())}' as createdAt, {distance} as distance, False as isUserLike, {pageNumber} as pageNumber, {altitudeDifference} as altitudeDifference, {isLoop} as isLoop, {category} as category, {routeId} as routeId;"
        
        self.pool.retry_operation_sync(lambda s: s.transaction().execute(
            text,
            commit_tx=True,
            settings=ydb.BaseRequestSettings().with_timeout(3).with_operation_timeout(2)
        ))

        return prediction_id

    def set_prediction_result(self, prediction_id, is_like):
        text = f"UPDATE {self.REQUESTS_TABLE} SET isUserLike = {is_like} WHERE id == '{prediction_id}';"
        return self.pool.retry_operation_sync(lambda s: s.transaction().execute(
            text,
            commit_tx=True,
            settings=ydb.BaseRequestSettings().with_timeout(3).with_operation_timeout(2)
        ))
    
    def set_user_matching_status(self, chat_id):
        text = f"UPDATE {self.USERS_TABLE} SET status = {UserStatuses['MATCHING_STARTED']} WHERE chat_id = {chat_id};"
        return self.pool.retry_operation_sync(lambda s: s.transaction().execute(
            text,
            commit_tx=True,
            settings=ydb.BaseRequestSettings().with_timeout(3).with_operation_timeout(2)
        )) 

    def find_users_with_locations(self):
        text = f"SELECT * FROM {self.USERS_TABLE} WHERE status == {UserStatuses['MATCHING_STARTED']};"
        arr = self.pool.retry_operation_sync(lambda s: s.transaction().execute(
            text,
            commit_tx=True,
            settings=ydb.BaseRequestSettings().with_timeout(3).with_operation_timeout(2)
        ))[0].rows

        if len(arr) > 0:
            return arr
        return None    
    
    def get_user_predictions(self, chat_id):
        text = f"SELECT * FROM {self.REQUESTS_TABLE} WHERE chat_id == {chat_id} ORDER BY pageNumber;"
        arr = self.pool.retry_operation_sync(lambda s: s.transaction().execute(
            text,
            commit_tx=True,
            settings=ydb.BaseRequestSettings().with_timeout(3).with_operation_timeout(2)
        ))[0].rows
        
        return arr
