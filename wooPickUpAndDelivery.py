import logging
import traceback

import yaml
from woocommerce import API

from pushTasks import pickUpAndDeliveryTask
from emailErrors import sendMail

order_id = None


def getWooPickUpAndDelivery():
    global order_id

    divider = "-------------------------------------------------------------------------"
    logging.basicConfig(filename="main.log", level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

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
        logging.info("[System] Checking for Pickup & Delivery Orders")
        logging.info(divider)

        print("[System] Checking for Pickup & Delivery Orders")
        print(divider)

        # go through each order in the list
        for x_order in range(len(response)):

            # get the order ID and Status
            order_id = response[x_order]['id']
            order_status = response[x_order]['status']

            # check if status is "Ready to Pickup"
            if order_status == 'ready-for-pickup-':

                # if order_id == 147340:
                # print(order_id)

                #
                #           GET THE CUSTOMER DETAILS FOR DELIVERY
                #
                # get the customer name
                # get the customer Address
                # get the customer phone number
                # get the customer email
                # get the payment method
                # get the shipping type
                customer_name = response[x_order]['shipping']['first_name'] + " " + response[x_order]['shipping'][
                    'last_name']
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
                    #           GET THE VENDOR DETAILS FOR DELIVERY
                    #
                    # get the shop name of the item
                    vendor_shop_name = response[x_order]['line_items'][x]['product_data']['store']['vendor_shop_name']

                    #
                    #           GET THE ITEM DETAILS FOR DELIVERY
                    #
                    # get the item name
                    # get the item quantity
                    # get the item price
                    item_name = response[x_order]['line_items'][x]['name']
                    item_qty = response[x_order]['line_items'][x]['quantity']
                    item_price = response[x_order]['line_items'][x]['price']

                    item_data = [vendor_shop_name, item_name, item_qty, item_price * item_qty]

                    items_list.append(item_data)

                # create the master list [order id, [vendor details, items]]
                vendor_list = []

                # get the product item vendor details of the orders
                for x in range(len(response[x_order]['line_items'])):
                    #
                    #           GET THE VENDOR DETAILS FOR PICKUP
                    #
                    # get the shop name of the item
                    # get the vendor ID
                    # get the vendor Address
                    # get the vendor phone number
                    # get the vendor commission
                    vendor_shop_name = response[x_order]['line_items'][x]['product_data']['store']['vendor_shop_name']
                    vendor_id = response[x_order]['line_items'][x]['product_data']['store']['vendor_id']
                    vendor_address = response[x_order]['line_items'][x]['product_data']['store']['vendor_address']
                    vendor_phone = response[x_order]['line_items'][x]['product_data']['store']["vendor_phone"]
                    try:
                        vendor_commission = \
                            response[x_order]['line_items'][x]['product_data']['store']['settings']['commission'][
                                'commission_percent']
                    except:
                        # Local Commission Percent
                        vendor_commission_meta = response[x_order]['line_items'][x]['product_data']['meta_data']
                        search_key = "_wcfmmp_commission"
                        meta_loc = 0

                        for i, d in enumerate(vendor_commission_meta):
                            if search_key in d:
                                meta_loc = i
                                break

                        vendor_commission = \
                        response[x_order]['line_items'][x]['product_data']['meta_data'][meta_loc]['value'][
                            'commission_percent']

                    vendor_details = [vendor_shop_name, vendor_address, vendor_phone, vendor_commission]

                    if vendor_details not in vendor_list:
                        vendor_list.append(vendor_details)

                # add the products to their specified vendors
                for x in range(len(response[x_order]['line_items'])):
                    #
                    #           GET THE VENDOR DETAILS FOR PICKUP
                    #
                    # get the shop name of the item
                    vendor_shop_name = response[x_order]['line_items'][x]['product_data']['store']['vendor_shop_name']

                    #
                    #           GET THE ITEM DETAILS FOR PICKUP
                    #
                    # get the item name
                    # get the item quantity
                    # get the item price
                    item_name = response[x_order]['line_items'][x]['name']
                    item_qty = response[x_order]['line_items'][x]['quantity']
                    item_price = float(response[x_order]['line_items'][x]['subtotal'])

                    item_data = [item_name, item_qty, item_price]

                    for vendors in vendor_list:
                        vendor_data = vendors
                        if vendor_shop_name in vendor_data:
                            vendors.append(item_data)

                # print(customer_details)
                # print(items_list)
                # print(vendor_list)
                pickUpAndDeliveryTask(customer_details, items_list, vendor_list, logging)
    except:
        logging.error(traceback.format_exc())
        sendMail(traceback.format_exc(), order_id)
        pass

    print(divider)
    logging.info(divider)


#getWooPickUpAndDelivery()
