def error_handled_effect(target, logger, effect_args):
    try:
        target(**effect_args)
    except Exception as e:
        logger.error("Error running effect")
        logger.error(f"Args: {effect_args}")
        logger.exception(e)
