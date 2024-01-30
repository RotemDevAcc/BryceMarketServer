USELOGGING = True
if USELOGGING:
    import logging

    logging.basicConfig(
        level=logging.DEBUG,          # Set the minimum log level to display
        format='%(asctime)s [%(levelname)s]: %(message)s',
        filename='my_app.log',        # Log messages to a file (optional)
    )



def log_action(message,case):
    if(not USELOGGING):
        print("\033[91m LOG: " + message + "\033[0m")
        return
    
    if(case is None or case == ""):
        case = "DEBUG"
    
    if(message == "" or message is None):
        logging.debug("log_action received an empty message")
        return

    case = case.upper()

    if(case == "DEBUG"):
        logging.debug(message, exc_info=True)
    elif(case == "INFO"):
        logging.info(message, exc_info=True)
    elif(case == "WARNING"):
        logging.warning(message, exc_info=True)
    elif(case == "ERROR"):
        logging.error(message, exc_info=True)
    elif(case == "CRITICAL"):
        logging.critical(message, exc_info=True)
    elif(case == "EXCEPTION"):
        logging.exception(message, exc_info=True)
    else:
        logging.debug("log_action was not used properly case non-existent")