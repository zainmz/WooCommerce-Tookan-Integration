import logging
import traceback

import requests
import yaml
from woocommerce import API

from emailErrors import sendMail
from pushTasks import getOrderExists

order_id = None


# ----------------------------------------------------------------------------------------------------------------------
#                              FUNCTION TO CANCEL TOOKAN TASK IF ORDER CANCELLED IN WOOCOMMERCE
# ----------------------------------------------------------------------------------------------------------------------
def cancelTookanTask(order_id, vendor_list, logger):

    def cancelJob(job_id, order_id, logger):
        # cancel the job
        info_url = "https://api.tookanapp.com/v2/cancel_task"

        get_order_exists = {"api_key": api_key,
                            "job_id": job_id,
                            "job_status": "9"
                            }

        info = requests.post(info_url, json=get_order_exists, headers=headers)
        # print(info.json())
        logger.info("[System] Cancelled Task - " + str(order_id))
        logger.info("-------------------------------------------------------------------------")

        print("[System] Cancelled Task - " + str(order_id))
        print("-------------------------------------------------------------------------")

    # ------------------------------------------------------------------------------------------------------------------
    #                              FUNCTION TO GET TOOKAN JOB STATUS FROM TOOKAN JOB ID
    # ------------------------------------------------------------------------------------------------------------------
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

    # ------------------------------------------------------------------------------------------------------------------
    #                            FUNCTION TO GET TOOKAN JOB ID FROM WOOCOMMERCE ORDER ID
    # ------------------------------------------------------------------------------------------------------------------

    def getJobID(new_order_id):
        # get the job ID
        info_url = "https://api.tookanapp.com/v2/get_job_details_by_order_id"

        get_order_exists = {"api_key": api_key,
                            "order_ids": [
                                new_order_id
                            ],
                            "include_task_history": "0"
                            }

        info = requests.post(info_url, json=get_order_exists, headers=headers)
        get_data = info.json()

        try:
            # check if delivery task exists
            if getJobStatus(new_order_id) != 9:
                cancelJob(get_data['data'][1]['job_id'], new_order_id)
        except:
            pass

        return get_data['data'][0]['job_id']

    # ------------------------------------------------------------------------------------------------------------------
    #                                         LOAD CONFIGURATION FILE AND API SETTINGS
    # ------------------------------------------------------------------------------------------------------------------

    # load configuration file
    with open("config.yaml", "r") as file:
        data = yaml.safe_load(file)

    api_key = data["api_key"]
    headers = {'Content-Type': 'application/json'}

    # check if multiple vendors are available or not
    if len(vendor_list) > 1:
        for i, item in enumerate(vendor_list):

            # check if the order is in the system
            new_order_id = str(order_id) + "_" + str(i)

            if getOrderExists(new_order_id):
                # if exists get the job id and cancel the Tookan task
                job_id = getJobID(new_order_id)
                if getJobStatus(job_id) == 9:
                    logger.info("[System] Already Completed")
                    print("[System] Already Completed")
                    return
                else:
                    cancelJob(job_id, new_order_id, logging)
                    logger.info("[System] Cancelled Task - " + str(new_order_id))
                    print("[System] Cancelled Task - " + str(new_order_id))
    else:
        if getOrderExists(order_id):
            job_id = getJobID(order_id)
            if getJobStatus(job_id) == 9:
                logger.info("[System] Already Completed")
                print("[System] Already Completed")
                pass
            else:
                cancelJob(job_id, order_id, logging)
                logger.info("[System] Cancelled Task - " + str(order_id))
                print("[System] Cancelled Task - " + str(order_id))


# ----------------------------------------------------------------------------------------------------------------------
#                  FUNCTION TO CANCEL GET WOOCOMMERCE CANCELLED ORDERS AND CANCEL RELATED TOOKAN TASKS
# ----------------------------------------------------------------------------------------------------------------------
def getCancelledOrders(log):
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
        response = wcapi.get("orders", params={'per_page': 20}).json()

        print("[System] Checking for Cancelled Orders")
        print(divider)

        logger.info("[System] Checking for Cancelled Orders")
        logger.info(divider)

        # go through each order in the list
        for x_order in range(len(response)):

            # get the order ID and Status
            order_id = response[x_order]['id']
            order_status = response[x_order]['status']

            # check if status is "Ready to Pickup"
            if order_status == 'cancelled':

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

                cancelTookanTask(order_id, vendor_list, logger)
    except:
        logging.error(traceback.format_exc())
        sendMail(traceback.format_exc(), order_id)
        pass

    print("-------------------------------------------------------------------------")
    logger.info(divider)

