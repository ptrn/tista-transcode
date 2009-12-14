#! /usr/bin/python
# -*- coding: utf-8 -*-

"""

This module contains a function used to read configuration files

"""

def Load(path):
    """
    Reads config file and returns dictionariy of settings.

      * path: Path to config file
      
    """
    
    d = {
        "network":  {},
        "path":     {},
        "database": {},
        "debug":    {},
        }

    execfile(path, globals(), d)

    return d
