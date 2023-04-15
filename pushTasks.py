import traceback
import requests
import yaml

from woocommerce import API
from datetime import datetime, timedelta

# ----------------------------------------------------------------------------------------------------------------------
#                                         LOAD CONFIGURATION FILE AND API SETTINGS
# ----------------------------------------------------------------------------------------------------------------------
from emailErrors import sendMail

order_id = None

# load configuration file
with open("config.yaml", "r") as file:
    data = yaml.safe_load(file)

api_key = data["api_key"]
site_url = data["url"]
consumer_key = data["consumer_key"]
consumer_secret = data["consumer_secret"]

wcapi = API(
    url=site_url,
    consumer_key=consumer_key,
    consumer_secret=consumer_secret,
    timeout=50,
)

headers = {'Content-Type': 'application/json'}


# ----------------------------------------------------------------------------------------------------------------------
#                                             CREATE ORDER NOTE WITH TRACKER LINK
# ----------------------------------------------------------------------------------------------------------------------
def createOrderNote(order_id, tracking_link):
    data = {"note": tracking_link}

    print(wcapi.post("orders/" + str(order_id) + "/notes", data).json())


# ----------------------------------------------------------------------------------------------------------------------
#                                                    CHECK TASK STATUS
# ----------------------------------------------------------------------------------------------------------------------

def getOrderStatus(order_id):
    info_url = "https://api.tookanapp.com/v2/get_job_details_by_order_id"

    get_order_exists = {"api_key": api_key,
                        "order_ids": [
                            order_id
                        ],
                        "include_task_history": "1"
                        }

    info = requests.post(info_url, json=get_order_exists, headers=headers)

    get_data = info.json()

    if get_data["status"] == 404:
        pass
    else:

        # check if it is a delivery task
        is_delivery_task = get_data['data'][-1]['has_delivery']

        # if it's a delivery task return the job status
        if is_delivery_task == 1:
            return get_data['data'][-1]['job_status']
        else:
            return "not delivery"


# ----------------------------------------------------------------------------------------------------------------------
#                                              CHECK IF TASK EXISTS ON TOOKAN
# ----------------------------------------------------------------------------------------------------------------------

def getOrderExists(order_id):
    print("[System] Checking if Order ID " + str(order_id) + " Exists")
    info_url = "https://api.tookanapp.com/v2/get_job_details_by_order_id"

    get_order_exists = {"api_key": api_key,
                        "order_ids": [order_id],
                        "include_task_history": 0
                        }

    info = requests.post(info_url, json=get_order_exists, headers=headers)

    get_data = info.json()
    # print(get_data)

    # If status is 404 order does not exist
    if get_data["status"] == 404:
        return False
    else:
        return True


# ----------------------------------------------------------------------------------------------------------------------
#                                                   PUSH PICKUP TASKS
# ----------------------------------------------------------------------------------------------------------------------
def pickUpTask(order_id, data_list, logging):
    try:
        current_time = datetime.now()
        formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")

        # loop through the list of items
        for x in range(len(data_list)):
            vendor_name = data_list[x][0]
            vendor_address = data_list[x][1]
            vendor_phone = data_list[x][2]
            vendor_commission = data_list[x][3]

            new_order_id = str(order_id) + "_" + str(x)

            if getOrderExists(new_order_id):

                logging.info("[Pick Up Task] Order ID " + new_order_id + " Already Exists - Skipping")
                print("[Pick Up Task] Order ID " + new_order_id + " Already Exists - Skipping")
            else:
                # print("-----------------------")
                # print(new_order_id)
                # print(vendor_name)
                # print(vendor_address)
                # print(vendor_phone)
                # print(vendor_commission)

                # remove vendor details and keep the items only
                data_list[x] = data_list[x][4:]
                # print(str(data_list[x]))

                total_payment = 0
                for items in data_list[x]:
                    total_payment = total_payment + items[2]

                total_payment = total_payment - (total_payment * (int(vendor_commission) / 100))
                # print(total_payment)

                pickup_data = {
                    "api_key": api_key,
                    "order_id": new_order_id,
                    "job_description": "Pick Up Task",
                    "job_pickup_phone": vendor_phone,
                    "job_pickup_name": vendor_name,
                    "job_pickup_address": vendor_address,
                    "job_pickup_datetime": formatted_time,
                    "pickup_custom_field_template": "pickupTaskAPI",
                    "pickup_meta_data": [{"label": "Details", "data": data_list[x]},
                                         {"label": "Total_Payment", "data": total_payment}],
                    "has_pickup": "1",
                    "has_delivery": "0",
                    "layout_type": "0",
                    "tracking_link": "0",
                    "timezone": "-330",
                    "auto_assignment": "0"

                }

                url = 'https://api.tookanapp.com/v2/create_task'

                response = requests.post(url, json=pickup_data, headers=headers)

                task_data = response.json()

                logging.info("[Pick Up Task] Task Created with id " + new_order_id)
                logging.info(task_data)

                print("[Pick Up Task] Task Created with id " + new_order_id)
                print(task_data)
    except:
        sendMail(traceback.format_exc(), order_id)
        logging.error(traceback.format_exc())
        pass


# ----------------------------------------------------------------------------------------------------------------------
#                                               PUSH DELIVERY TASKS
# ----------------------------------------------------------------------------------------------------------------------

def deliveryTask(customer_details, items_list, logging):
    global order_id
    try:
        # get the order id
        order_id = customer_details[0]

        if getOrderExists(order_id):
            logging.info("[Delivery Task] Order ID " + str(order_id) + " Already Exists - Skipping")
            print("[Delivery Task] Order ID " + str(order_id) + " Already Exists - Skipping")
            pass
        else:
            # get the customer name
            customer_name = customer_details[1]
            # get the customer Address
            customer_address = customer_details[2]
            # get the customer phone number
            customer_phone = customer_details[3]
            # get the customer email
            customer_email = customer_details[4]
            # get the payment method
            payment_method = customer_details[5]
            # get the shipping type
            shipping_type = customer_details[6]
            # get the shipping fee
            shipping_cost = customer_details[7]
            for ships in shipping_type:
                shipping_type = ships['method_title']

            # Get the current time
            current_time = datetime.now()
            # Add 2 hours to the current time

            if shipping_type == 'Rapid Express (30 Minutes)':
                new_time = current_time + timedelta(minutes=30)
            if shipping_type == 'Express Delivery (30 – 120 Minutes)' \
                    or shipping_type == 'Rapid Express 30-120 min' \
                    or shipping_type == "Express Delivery (30 \u2013 120 Minutes)":
                new_time = current_time + timedelta(hours=2)
            else:
                new_time = current_time

            # Format the new time to a string
            formatted_time = new_time.strftime("%Y-%m-%d %H:%M:%S")

            total_payment = float(shipping_cost)

            for items in items_list:
                total_payment = total_payment + items[3]

            # print("-----------------------")
            # print(str(order_id))
            # print(customer_name)
            # print(customer_address)
            # print(customer_phone)
            # print(customer_email)
            # print(payment_method)
            # print(shipping_type)
            # print(new_time)
            # print(items_list)

            delivery_data = {
                "api_key": api_key,
                "order_id": order_id,
                "job_description": "Delivery Task",
                "customer_email": customer_email,
                "customer_username": customer_name,
                "customer_phone": customer_phone,
                "customer_address": customer_address,
                "job_delivery_datetime": formatted_time,
                "custom_field_template": "deliveryTaskAPI",
                "meta_data": [{"label": "Details", "data": items_list},
                              {"label": "Delivery_Charge", "data": shipping_cost},
                              {"label": "Payment_Method", "data": payment_method},
                              {"label": "Total_Customer_Payment", "data": total_payment}],
                "team_id": "",
                "auto_assignment": "0",
                "has_pickup": "0",
                "has_delivery": "1",
                "layout_type": "0",
                "tracking_link": "0",
                "timezone": "-330",
                "notify": 1,
            }

            url = 'https://api.tookanapp.com/v2/create_task'

            response = requests.post(url, json=delivery_data, headers=headers)

            task_data = response.json()
            tracking_link = task_data['data']['tracking_link']
            createOrderNote(order_id, tracking_link)

            logging.info("[Delivery Task] Task Created with id " + str(order_id))
            logging.info(task_data)
            logging.info("Got Tracking Link: " + tracking_link)

            print("[Delivery Task] Task Created with id " + str(order_id))
            print("Got Tracking Link: " + tracking_link)
            print(task_data)
    except:
        logging.error(traceback.format_exc())
        sendMail(traceback.format_exc(), order_id)
        pass


# ----------------------------------------------------------------------------------------------------------------------
#                                               PUSH PICKUP & DELIVERY TASKS
# ----------------------------------------------------------------------------------------------------------------------

def pickUpAndDeliveryTask(customer_details, items_list, data_list, logging):
    # print(data_list)
    global order_id
    try:
        current_time = datetime.now()
        pickup_time = current_time.strftime("%Y-%m-%d %H:%M:%S")

        # get the order id
        order_id = customer_details[0]

        if getOrderExists(order_id):
            logging.info("[Pick Up & Delivery Task] Order ID " + str(order_id) + " Already Exists - Skipping")
            print("[Pick Up & Delivery Task] Order ID " + str(order_id) + " Already Exists - Skipping")
            pass
        else:
            # get the customer name
            customer_name = customer_details[1]
            # get the customer Address
            customer_address = customer_details[2]
            # get the customer phone number
            customer_phone = customer_details[3]
            # get the customer email
            customer_email = customer_details[4]
            # get the payment method
            payment_method = customer_details[5]
            # get the shipping type
            shipping_type = customer_details[6]
            # get the shipping cost
            shipping_cost = customer_details[7]

            for ships in shipping_type:
                shipping_type = ships['method_title']

            # Get the current time
            current_time = datetime.now()
            # Add 2 hours to the current time

            if shipping_type == 'Rapid Express (30 Minutes)':
                new_time = current_time + timedelta(minutes=30)

            if shipping_type == 'Express Delivery (30 – 120 Minutes)' \
                    or shipping_type == 'Rapid Express 30-120 min' \
                    or shipping_type == "Express Delivery (30 \u2013 120 Minutes)":
                new_time = current_time + timedelta(hours=2)
            else:
                new_time = current_time

            # Format the new time to a string
            formatted_time = new_time.strftime("%Y-%m-%d %H:%M:%S")

            total_customer_payment = float(shipping_cost)
            for items in items_list:
                total_customer_payment = total_customer_payment + items[3]

            print(total_customer_payment)

            # print("-----------------------")
            # print(str(order_id))
            # print(customer_name)
            # print(customer_address)
            # print(customer_phone)
            # print(customer_email)
            # print(payment_method)
            # print(shipping_type)
            # print(new_time)
            # print(items_list)

            vendor_name = data_list[0][0]
            vendor_address = data_list[0][1]
            vendor_phone = data_list[0][2]
            vendor_commission = data_list[0][3]

            # print("-----------------------")
            # print(order_id)
            # print(vendor_name)
            # print(vendor_address)
            # print(vendor_phone)
            # print(vendor_commission)

            # remove vendor details and keep the items only
            data_list = data_list[0][4:]
            # print(data_list)

            total_payment = 0
            for items in data_list:
                total_payment = total_payment + items[2]

            total_payment = total_payment - (total_payment * (int(vendor_commission) / 100))
            # print(total_payment)

            pickup_delivery_data = {
                "api_key": api_key,
                "order_id": order_id,
                "team_id": "",
                "auto_assignment": "0",
                "job_description": "Pickup & Delivery",
                "job_pickup_phone": vendor_phone,
                "job_pickup_name": vendor_name,
                "job_pickup_email": "",
                "job_pickup_address": vendor_address,
                "job_pickup_datetime": pickup_time,
                "customer_email": customer_email,
                "customer_username": customer_name,
                "customer_phone": customer_phone,
                "customer_address": customer_address,
                "job_delivery_datetime": formatted_time,
                "has_pickup": "1",
                "has_delivery": "1",
                "layout_type": "0",
                "tracking_link": "0",
                "timezone": "-330",
                "custom_field_template": "deliveryTaskAPI",
                "meta_data": [{"label": "Details", "data": items_list},
                              {"label": "Payment_Method", "data": payment_method},
                              {"label": "Delivery_Charge", "data": shipping_cost},
                              {"label": "Total_Customer_Payment", "data": total_customer_payment}],
                "pickup_custom_field_template": "pickupTaskAPI",
                "pickup_meta_data": [{"label": "Details", "data": data_list},
                                     {"label": "Total_Payment", "data": total_payment}],
                "notify": 1,
            }

            url = 'https://api.tookanapp.com/v2/create_task'

            response = requests.post(url, json=pickup_delivery_data, headers=headers)

            task_data = response.json()
            tracking_link = task_data['data']['delivery_tracing_link']
            createOrderNote(order_id, tracking_link)

            print("[Pick Up & Delivery Task] Task Created with id " + str(order_id))
            print("Got Tracking Link: " + tracking_link)
            print(task_data)

            logging.info("[Pick Up & Delivery Task] Task Created with id " + str(order_id))
            logging.info(task_data)
            logging.info("Got Tracking Link: " + tracking_link)
    except:
        logging.error(traceback.format_exc())
        sendMail(traceback.format_exc(), order_id)
        pass
