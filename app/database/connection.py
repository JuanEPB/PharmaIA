from contextlib import contextmanager

import mysql.connector

from mysql.connector import Error

from app.config.settings import settings


class DatabaseConnection:

    @staticmethod
    def connect():

        try:

            connection = mysql.connector.connect(

                host=settings.DB_HOST,

                port=settings.DB_PORT,

                database=settings.DB_NAME,

                user=settings.DB_USER,

                password=settings.DB_PASSWORD,

                charset="utf8mb4",

                autocommit=False,

            )

            return connection

        except Error as error:

            raise ConnectionError(error)


@contextmanager
def get_connection():

    connection = DatabaseConnection.connect()

    try:

        yield connection

    finally:

        if connection.is_connected():

            connection.close()


def test_connection():

    try:

        with get_connection() as connection:

            cursor = connection.cursor()

            cursor.execute(
                "SELECT DATABASE(), VERSION()"
            )

            database, version = cursor.fetchone()

            cursor.close()

            return {

                "status":"ok",

                "database":database,

                "mysql":version,

            }

    except Exception as error:

        return {

            "status":"error",

            "message":str(error),

        }
