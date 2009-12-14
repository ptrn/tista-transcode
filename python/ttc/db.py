#! /usr/bin/python
# -*- coding: utf-8; -*-

"""

This module contains various utility functions for connecting to Postgres.

IMPORTANT:

  * NEVER INCLUDE ARGUMENTS IN SQL STATEMENT ITSELF. USE args INSTEAD,
    THUS PROTECTING US AGAINST SQL INJECTION ATTACKS.

  * ALWAYS USE THE PsE FUNCTION WHEN EXECUTING SQL STATEMENTS. IT
    ENSURES THAT EXCEPTIONS ARE APPROPRIATELY CAUGHT.

"""

import os, re
import psycopg2

def PsE(cursor, cmd, args = None):
    """
    Executes an SQL command just like cursor.execute, but tries to
    handle exceptions a bit more intelligently.

      * cursor: Postgres cursor

      * cmd: SQL command

      * args: SQL arguments

    """
    
    if args == None:
        cursor.execute(cmd)
    else:
        cursor.execute(cmd, args)
