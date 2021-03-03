# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals


def error_handled_effect(target, logger, effect_args):
    try:
        target(**effect_args)
    except Exception as e:
        logger.error("Error running effect")
        logger.error("Args: {}".format(effect_args))
        logger.exception(e)
