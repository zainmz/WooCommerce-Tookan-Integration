import logging
import traceback

import requests
from woocommerce import API
import yaml

from emailErrors import sendMail
from pushTasks import getOrderExists

# ----------------------------------------------------------------------------------------------------------------------
#                                         LOAD CONFIGURATION FILE AND API SETTINGS
# ----------------------------------------------------------------------------------------------------------------------
order_id = None
# load configuration file
with open("config.yaml", "r") as file:
    data = yaml.safe_load(file)

api_key = data["api_key"]
headers = {'Content-Type': 'application/json'}


# get the orders from WooCommerce
# get the job id and check if the order status is 9
# then update the order on WooCommerce

# ----------------------------------------------------------------------------------------------------------------------
#                                    FUNCTION TO GET JOB ID OF TOOKAN TASK RELATED TO ORDER ID
# ----------------------------------------------------------------------------------------------------------------------

def getJobID(order_id):
    # get the job ID
    info_url = "https://api.tookanapp.com/v2/get_job_details_by_order_id"

    get_order_exists = {"api_key": api_key,
                        "order_ids": [
                            order_id
                        ],
                        "include_task_history": "0"
                        }

    info = requests.post(info_url, json=get_order_exists, headers=headers)
    get_data = info.json()
    return get_data['data'][0]['job_id']


# ----------------------------------------------------------------------------------------------------------------------
#                                   FUNCTION TO GET STATUS OF TOOKAN JOB FROM TOOKAN JOB ID
# ----------------------------------------------------------------------------------------------------------------------
def getJobStatus(job_id):
    # get current job status
    info_url = "https://api.tookanapp.com/v2/get_job_details"

    get_order_exists = {"api_key": api_key,
                        "job_ids": [job_id],
                        "include_task_history": 0,
                        "job_additional_info": 1
                        }

    info = requests.post(info_url, json=get_order_exists, headers=headers)
    get_data = info.json()
    job_status = get_data['data'][0]['job_status']
    return job_status


# ----------------------------------------------------------------------------------------------------------------------
#                                      FUNCTION TO CHECK IF ORDER HAS MULTIPLE VENDORS
# ----------------------------------------------------------------------------------------------------------------------
def checkMultipleVendors(response, x_order):
    # create the master list [order id, [vendor details, items]]
    vendor_list = []

    # get the product item vendor details of the orders
    for x in range(len(response[x_order]['line_items'])):
        #
        #           GET THE VENDOR DETAILS
        #
        # get the shop name of the item
        vendor_shop_name = response[x_order]['line_items'][x]['product_data']['store']['vendor_shop_name']

        vendor_details = [vendor_shop_name]

        if vendor_details not in vendor_list:
            vendor_list.append(vendor_details)

    return len(vendor_list)


# ----------------------------------------------------------------------------------------------------------------------
#                             FUNCTION TO CANCEL WOOCOMMERCE ORDERS WHEN TOOKAN TASK IS CANCELLED
# ----------------------------------------------------------------------------------------------------------------------
def cancelWooCommerceOrders(log):
    global order_id

    logger = log
    divider = "-------------------------------------------------------------------------"

    try:

        # woocommerce REST api connection details
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
        response = wcapi.get("orders", params={'per_page': 40}).json()
        print(divider)
        print("[Update Orders] Checking for Orders to Cancel")
        logger.info(divider)
        logger.info("[Update Orders] Checking for Orders to Cancel")

        # go through each order in the list
        for x_order in range(len(response)):

            # get the order ID and Status
            order_id = response[x_order]['id']
            order_status = response[x_order]['status']
            print("[System] Checking if Order " + str(order_id) + " Cancelled on Tookan")

            # check if status is not cancelled
            if order_status == 'cancelled':
                continue

            count = checkMultipleVendors(response, x_order)
            if count > 1:
                order_id = str(order_id) + "_" + str("0")

            if getOrderExists(order_id):
                job_id = getJobID(order_id)
                job_status = getJobStatus(job_id)

                if job_status == 9:
                    data = {
                        "status": "cancelled"
                    }
                    print(wcapi.put("orders/" + str(order_id), data).json())
                    logger.info("[Update Orders] Order " + str(order_id) + " is now cancelled")
                    print("[Update Orders] Order " + str(order_id) + " is now cancelled")
            else:
                logger.info("[System] Order " + str(order_id) + " does not exist on Tookan")
    except:
        logging.error(traceback.format_exc())
        sendMail(traceback.format_exc(), order_id)
        print(divider)
        logger.info(divider)
        pass

