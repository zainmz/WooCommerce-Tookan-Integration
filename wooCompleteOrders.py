import logging
import traceback

import yaml
from woocommerce import API

from emailErrors import sendMail
from pushTasks import getOrderStatus

order_id = None


# ----------------------------------------------------------------------------------------------------------------------
#                           FUNCTION TO COMPLETE ORDERS WHEN TOOKAN DELIVERY TASK IS COMPLETED
# ----------------------------------------------------------------------------------------------------------------------
def getCompleteOrders(log):
    global order_id
    logger = log

    divider = "-------------------------------------------------------------------------"
    # woocommerce REST api connection details
    try:
        # load configuration file
        with open("config.yaml", "r") as file:
            data = yaml.safe_load(file)

        site_url = data["url"]
        consumer_key = data["consumer_key"]
        consumer_secret = data["consumer_secret"]

        wcapi = API(
            url=site_url,
            consumer_key=consumer_key,
            consumer_secret=consumer_secret,
            timeout=50,
        )

        # get the data from the woocommerce API - latest 20 orders
        response = wcapi.get("orders", params={'per_page': 20}).json()

        print("[Update Orders] Checking for Orders that can be completed")
        print(divider)

        logger.info("[Update Orders] Checking for Orders that can be completed")
        logger.info(divider)

        # go through each order in the list
        for x_order in range(len(response)):
            # get the order ID and Status
            order_id = response[x_order]['id']
            order_status = response[x_order]['status']

            # check if status is "Ready to Pickup"
            if order_status == 'completed':
                continue

            print("[Update Orders] Checking if Order " + str(order_id) + " is completed on Tookan")
            logger.info("[Update Orders] Checking if Order " + str(order_id) + " is completed on Tookan")

            tookan_status = getOrderStatus(order_id)

            if tookan_status != 'not delivery':

                if tookan_status == 2:
                    data = {
                        "status": "completed"
                    }
                    wcapi.put("orders/" + str(order_id), data).json()
                    print("[Update Orders] Order " + str(order_id) + " is now completed")
                    logger.info("[Update Orders] Order " + str(order_id) + " is now completed")
    except:
        logging.error(traceback.format_exc())
        sendMail(traceback.format_exc(), order_id)
        pass

    print(divider)
    logger.info(divider)

# getCompleteOrders()
