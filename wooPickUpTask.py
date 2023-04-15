import logging
import traceback

from woocommerce import API
import yaml

from pushTasks import pickUpTask
from emailErrors import sendMail

order_id = None


def getWooPickUp():
    global order_id
    logging.basicConfig(filename="main.log", level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    divider = "-------------------------------------------------------------------------"
    try:
        # woocommerce REST api connection details
        wcapi = API(
            url="https://quickee.com/",
            consumer_key="ck_c709b40b9b71cdc04465b086abeb730aabf056a3",
            consumer_secret="cs_89ae560751ac23a34abfa4fa08078740b8086a64",
            timeout=50,
        )

        # get the data from the woocommerce API - latest 20 orders
        response = wcapi.get("orders", params={'per_page': 20}).json()

        logging.info("[System] Checking for Pickup Orders")
        logging.info(divider)

        print("[System] Checking for Pickup Orders")
        print(divider)

        # go through each order in the list
        for x_order in range(len(response)):

            # get the order ID and Status
            order_id = response[x_order]['id']
            order_status = response[x_order]['status']

            # check if status is "Ready to Pickup"
            # if order_id == 147340:
            if order_status == 'ready-to-pickup':

                # create the master list [order id, [vendor details, items]]
                vendor_list = []

                # get the product item vendor details of the orders
                for x in range(len(response[x_order]['line_items'])):
                    #
                    #           GET THE VENDOR DETAILS
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
                        # Global Commission Percent
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

                    item_data = [item_name, item_qty, item_price]

                    for vendors in vendor_list:
                        vendor_data = vendors
                        if vendor_shop_name in vendor_data:
                            vendors.append(item_data)

                # print(vendor_list)
                pickUpTask(order_id, vendor_list, logging)
    except:
        logging.error(traceback.format_exc())
        sendMail(traceback.format_exc(), order_id)
        pass

    print(divider)
    logging.info(divider)

# getWooPickUp()
