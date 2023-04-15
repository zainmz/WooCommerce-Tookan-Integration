import threading
import time
import http.client as httplib
import logging
import traceback

from threading import Thread

from emailErrors import sendMail
from wooPickUpTask import getWooPickUp
from wooDeliveryTask import getWooDelivery
from wooPickUpAndDelivery import getWooPickUpAndDelivery

from cancelTasks import getCancelledOrders
from cancelOrders import cancelWooCommerceOrders
from wooCompleteOrders import getCompleteOrders


thread_local = threading.local()


def getLogger(log_file_name):
    if not hasattr(thread_local, 'logger'):
        thread_local.logger = logging.getLogger(threading.current_thread().name)
        handler = logging.FileHandler(log_file_name)
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        handler.setFormatter(formatter)
        thread_local.logger.addHandler(handler)
    return thread_local.logger


# ----------------------------------------------------------------------------------------------------------------------
#                                        FUNCTION TO CHECK INTERNET CONNECTION
# ----------------------------------------------------------------------------------------------------------------------
# function to check internet connectivity
def checkInternet(url="www.google.com", timeout=3):
    connection = httplib.HTTPConnection(url, timeout=timeout)
    try:
        # only header requested for fast operation
        connection.request("HEAD", "/")
        connection.close()  # connection closed
        print("Internet On")
        return True
    except Exception as exep:
        print(exep)
        return False


# ----------------------------------------------------------------------------------------------------------------------
#                                        FUNCTION FOR CANCELLING ORDERS
# ----------------------------------------------------------------------------------------------------------------------
def startCancelOrders(log_file_name):
    logger = get_logger(log_file_name)
    while True:
        try:
            time.sleep(120)
            cancelWooCommerceOrders(logger)
            getCancelledOrders(logger)
        except:
            logging.error(traceback.format_exc())
            pass


# ----------------------------------------------------------------------------------------------------------------------
#                                        FUNCTION FOR COMPLETING ORDERS
# ----------------------------------------------------------------------------------------------------------------------
def startCompletingOrders(log_file_name):
    logger = get_logger(log_file_name)
    while True:
        try:
            time.sleep(120)
            getCompleteOrders(logger)
        except:
            logging.error(traceback.format_exc())
            pass


# ----------------------------------------------------------------------------------------------------------------------
#                                              MAIN RUNNING CODE
# ----------------------------------------------------------------------------------------------------------------------
if __name__ == '__main__':

    logging.basicConfig(filename="main.log", level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    logging.info("Starting System")

    logging.info("Starting Order & Task Cancellation Thread")
    Thread(target=startCancelOrders, args=('cancel.log',)).start()
    logging.info("Starting Order Completion Thread")
    Thread(target=startCompletingOrders, args=('complete.log',)).start()

    while True:
        try:
            logging.info("Checking Orders")
            print("[System] Checking orders.............")
            getWooPickUp()
            getWooDelivery()
            getWooPickUpAndDelivery()
            logging.info("Completed Check Cycle")
            logging.info("Waiting for 2 Minutes Before Checking Again")
            time.sleep(120)
        except:
            logging.error(traceback.format_exc())
            sendMail(traceback.format_exc(), "None")
            pass
