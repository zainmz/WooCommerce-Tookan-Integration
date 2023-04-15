import logging
import traceback

import yaml
from woocommerce import API

from emailErrors import sendMail
from pushTasks import deliveryTask

order_id = None


def getWooDelivery():
    global order_id

    logging.basicConfig(filename="main.log", level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
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

        logging.info("[System] Checking for Delivery Orders")
        logging.info(divider)

        print("[System] Checking for Delivery Orders")
        print(divider)

        # go through each order in the list
        for x_order in range(len(response)):

            # get the order ID and Status
            order_id = response[x_order]['id']
            order_status = response[x_order]['status']

            # check if status is "Ready to Pickup"
            if order_status == 'ready-to-dispatch':
                # if order_id == 147340:

                # create the master list [name, address, phone, email, payment method, payment amnt, items]
                customer_details = []

                #
                #           GET THE CUSTOMER DETAILS
                #
                # get the customer name
                customer_name = response[x_order]['shipping']['first_name'] + " " + response[x_order]['shipping'][
                    'last_name']
                # get the customer Address
                # get the customer phone number
                # get the customer email
                # get the payment method
                # get the payment method
                # get the shipping type
                customer_address = response[x_order]['shipping']['address_1']
                customer_phone = response[x_order]['shipping']['phone']
                customer_email = response[x_order]['billing']['email']
                payment_method = response[x_order]['payment_method_title']
                shipping_type = response[x_order]['shipping_lines']
                shipping_total = response[x_order]['shipping_total']

                customer_details = [order_id, customer_name, customer_address, customer_phone, customer_email,
                                    payment_method, shipping_type, shipping_total]

                items_list = []
                # consolidate all the products
                for x in range(len(response[x_order]['line_items'])):
                    #
                    #           GET THE VENDOR DETAILS
                    #
                    # get the shop name of the item
                    vendor_shop_name = response[x_order]['line_items'][x]['product_data']['store']['vendor_shop_name']

                    #
                    #           GET THE ITEM DETAILS
                    #
                    # get the item name
                    # get the item quantity
                    # get the item price
                    item_name = response[x_order]['line_items'][x]['name']
                    item_qty = response[x_order]['line_items'][x]['quantity']
                    item_price = float(response[x_order]['line_items'][x]['subtotal'])

                    item_data = [vendor_shop_name, item_name, item_qty, item_price]

                    items_list.append(item_data)

                # print(customer_details)
                # print(items_list)

                deliveryTask(customer_details, items_list, logging)
    except:
        logging.error(traceback.format_exc())
        sendMail(traceback.format_exc(), order_id)
        pass

    logging.info(divider)
    print(divider)
