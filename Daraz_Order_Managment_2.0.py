from datetime import datetime, timedelta
import urllib.parse as urlparse
from urllib.parse import urlencode
import requests
import datetime
import hmac
import hashlib
import xmlrpc.client
import json
from csv import writer

from datetime import datetime, timedelta
curr_dt = datetime.now()


url_live = 'http://116.203.171.209:8069'
db_live = 'AES_Live'
username_live = 'syed.kumail@affinitysuite.net'
password_live = 'Allied@786'
common_live = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url_live))
common_live.version()
uid_live = common_live.authenticate(db_live, username_live, password_live, {})
models_live = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url_live))


# get sign algorithm

def sign(secret, api, parameters):
    sort_dict = sorted(parameters)

    parameters_str = "%s%s" % (api,
                               str().join('%s%s' % (key, parameters[key]) for key in sort_dict))

    h = hmac.new(secret.encode(encoding="utf-8"),
                 parameters_str.encode(encoding="utf-8"), digestmod=hashlib.sha256)

    return h.hexdigest().upper()


Seacrh_Daraz_instance = models_live.execute_kw(db_live, uid_live, password_live,
                                               'token.model', 'search_read',
                                               [[]])

for daraz_instance in Seacrh_Daraz_instance:
    print(str(daraz_instance['name']))
    # get Orders
    print("Current datetime: ", curr_dt)
    timestamp = int(curr_dt.timestamp())

    print("Integer timestamp of current datetime: ",
          timestamp)
    timestamp_new = str(int(timestamp))+'000'

    hours_minus = 4
    newDate = curr_dt - timedelta(hours=hours_minus)
    print(newDate)

    url = '/orders/get?'
    datecheck = datetime.now().astimezone().replace(microsecond=0).timestamp()
    print(datecheck)
    endpoint = 'http://api.daraz.pk/rest'
    urlWithEndpoint = 'http://api.daraz.pk/rest/order/get'

    parameters = {
        'app_key': daraz_instance['app_key'],
        # 'app_key' : '500054',
        'timestamp': timestamp_new,
        'sign_method': 'sha256',
        # 'code': '4_500590_aHr8yra8rx6LOu2O9nt9S7K33317',
        'access_token': daraz_instance['access_token'],
        # 'access_token' : '50000500b31fz8iBRwRvECdmVhqwE0ogfCDpdNUyfod10f1a07fNG4kUTrj04',
        'created_after': str(newDate.isoformat()),
        # 'created_after': '2023-02-06T21:20:00',
        # 'created_before': '2023-02-06T21:08:00',
        'status': 'pending',
        # 'limit': 10

        # 'order_id':	128622891664963,
    }
    concatenated = urlencode(sorted(parameters.items()))
    parameters['sign'] = sign(
        str(daraz_instance['app_secret']), '/orders/get', parameters)
    concatenated = urlencode(sorted(parameters.items()))
    final_url = endpoint+url+concatenated
    print(final_url)
    response = requests.request('GET', final_url)

    order_ids = []
    all_orders = response.json()
    print(all_orders)

    for rec in all_orders["data"]['orders']:
        order_ids.append(rec['order_number'])

    # get orderlines

    print("Current datetime: ", curr_dt)
    timestamp = int(curr_dt.timestamp())

    print("Integer timestamp of current datetime: ",
          timestamp)
    timestamp_new = str(int(timestamp))+'000'

    url = '/orders/items/get?'
    datecheck = datetime.now().astimezone().replace(microsecond=0).timestamp()
    print(datecheck)
    endpoint = 'http://api.daraz.pk/rest'
    urlWithEndpoint = 'http://api.daraz.pk/rest/order/get'

    parameters = {
        'app_key': daraz_instance['app_key'],
        # 'app_key' : '500054',
        'timestamp': timestamp_new,
        'sign_method': 'sha256',
        # 'code': '4_500590_aHr8yra8rx6LOu2O9nt9S7K33317',
        'access_token': daraz_instance['access_token'],
        # 'access_token' : '50000500b31fz8iBRwRvECdmVhqwE0ogfCDpdNUyfod10f1a07fNG4kUTrj04',
        'order_ids': order_ids
    }
    concatenated = urlencode(sorted(parameters.items()))
    parameters['sign'] = sign(
        str(daraz_instance['app_secret']), '/orders/items/get', parameters)
    concatenated = urlencode(sorted(parameters.items()))
    final_url = endpoint+url+concatenated
    print(final_url)
    response = requests.request('GET', final_url)

    all_order_lines = response.json()
    print(all_order_lines)
    order_lines = []
    warehouse = []
    pricelist = []
    vendor = []
    if order_ids:
        # Create Customer
        for customers in all_orders["data"]['orders']:
            try:
                existing_customer = []
                existing_customer = models_live.execute_kw(db_live, uid_live, password_live,
                                                           'res.partner', 'search',
                                                           [[['phone', '=', customers['address_shipping']['phone']]]])

                if len(existing_customer) == 0:
                    models_live.execute_kw(db_live, uid_live, password_live, 'res.partner', 'create', [{
                        'name': str(customers['address_shipping']['first_name']),
                        'phone': str(customers['address_shipping']['phone']),
                        'street': str(customers['address_shipping']['address1']) if customers['address_shipping']['address1'] else False,
                        'city': str(customers['address_shipping']['city']) if customers['address_shipping']['city'] else False
                    }])
                    print('Customer Created')
                else:
                    print('Customer Already Created ' +
                          str(customers['address_shipping']['first_name']))

                customer = models_live.execute_kw(db_live, uid_live, password_live,
                                                  'res.partner', 'search_read',
                                                  [[['phone', '=', customers['address_shipping']['phone']]]])

            except Exception as ex:
                print("Cannot Create Customer", ex)

        for sale_order in all_orders["data"]['orders']:
            try:
                product_found_check = " "
                existing_order = []
                existing_order = models_live.execute_kw(db_live, uid_live, password_live,
                                                        'sale.order', 'search',
                                                        [[['x_studio_daraz_order_id', '=', str(sale_order['order_number'])]]])

                for line_data in all_order_lines['data']:
                    for line in line_data['order_items']:
                        product_found_check = models_live.execute_kw(db_live, uid_live, password_live,
                                                                     'product.product', 'search_read',
                                                                     [[['default_code', '=', line['sku']]]])
                        product_hold_exp = line['sku']

                if len(existing_order) == 0:
                    if len(product_found_check) != 0:

                        customer_order = models_live.execute_kw(db_live, uid_live, password_live,
                                                                'res.partner', 'search_read',
                                                                [[['phone', '=', sale_order['address_shipping']['phone']]]])
                        for customer_ in customer_order:
                            get_customer_id = customer_['id']

                        # get_store_name =
                        get_warehouse = models_live.execute_kw(db_live, uid_live, password_live,
                                                               'daraz.setting', 'search_read',
                                                               [[['select_instance', '=', str(daraz_instance['name'])]]])

                        for warehouse_id in get_warehouse:
                            warehouse = warehouse_id['select_warehouse'][0]
                            print(warehouse)

                        # get_price_list
                        get_pricelist = models_live.execute_kw(db_live, uid_live, password_live,
                                                               'daraz.setting', 'search_read',
                                                               [[['select_instance', '=', str(daraz_instance['name'])]]])

                        for pricelist_id in get_pricelist:
                            pricelist = pricelist_id['pricelist'][0]
                            print(pricelist)

                        # get_vendor
                        get_vendor = models_live.execute_kw(db_live, uid_live, password_live,
                                                            'daraz.setting', 'search_read',
                                                            [[['select_instance', '=', str(daraz_instance['name'])]]])

                        for vendor_id in get_vendor:
                            vendor = vendor_id['x_studio_vendor'][0]
                            print(vendor)

                        daraz_cou = ' '
                        daraz_tracking = ' '
                        for line_data in all_order_lines['data']:
                            for line in line_data['order_items']:
                                daraz_cou = str(line['shipment_provider'])
                                daraz_tracking = str(line['tracking_code'])
                        # paymentMode
                        paymentmode = ' '
                        if str((sale_order['payment_method'])) == 'COD':
                            paymentmode = 'COD'
                        else:
                            paymentmode = 'Prepaid'

                        print(paymentmode)

                        # datetimesplit

                        if sale_order['created_at']:
                            datetime_with_timezone = sale_order['created_at']
                            datetime_without_timezone = datetime_with_timezone.split(
                                "+")
                            z = datetime_without_timezone[0]
                            y = z.split(" ")
                            print(y[0])
                            print(y[1])

                            datetime_ = y[0] + ' ' + y[1]
                            hours_plus = 8
                            abc = datetime.strptime(
                                datetime_, '%Y-%m-%d %H:%M:%S')
                            newDate = abc - timedelta(hours=hours_plus)
                            hold = str(newDate)
                            date_order_time = hold.replace("-", "-")
                            print(str(date_order_time))

                        shipping_type = ' '
                        for line_data in all_order_lines['data']:
                            for line in line_data['order_items']:
                                shipping_type = str(line['shipping_type'])

                        try:
                            sale_order_daraz_id = models_live.execute_kw(db_live, uid_live, password_live, 'sale.order', 'create', [{
                                'state': 'draft',
                                'sale_order_type': 'fulfillment',
                                'sale_order_sub_type': 'daraz',
                                'partner_id': get_customer_id,
                                'x_studio_platform_1': vendor,
                                'x_studio_daraz_order_id': str(sale_order['order_number']),
                                'x_studio_payment_mode': str(paymentmode),
                                'x_studio_daraz_order_creation_date': date_order_time,
                                'daraz_store_name': str(daraz_instance['name']),
                                'x_studio_daraz_shipping_type': str(shipping_type),
                                'warehouse_id': warehouse,
                                'x_studio_daraz_order_status': str(sale_order['statuses']),
                                'x_studio_daraz_payment_method':str((sale_order['payment_method'])),
                                'pricelist_id': pricelist,
                                'x_studio_daraz_courier': daraz_cou,
                                'x_studio_daraz_tracking_no': daraz_tracking,
                                'x_studio_shipping_amount': float(sale_order['shipping_fee'])

                            }])
                            print('Sale Order Created: ' +
                                  str((sale_order['order_number'])))
                        except Exception as Ex:
                            daraz_order_number = str(
                                sale_order['order_number'])
                            print(str(Ex))
                        for line_data in all_order_lines['data']:
                            for line in line_data['order_items']:

                                product = models_live.execute_kw(db_live, uid_live, password_live,
                                                                 'product.product', 'search_read',
                                                                 [[['default_code', '=', line['sku']]]])

                                sale_order_search = models_live.execute_kw(db_live, uid_live, password_live,
                                                                           'sale.order', 'search_read',
                                                                           [[['x_studio_daraz_order_id', '=', str(line['order_id'])]]])

                                for sale_order_data in sale_order_search:
                                    if str(sale_order['order_number']) == str(line['order_id']):

                                        if product:
                                            order_lines = []
                                            shipping_amount = 0
                                            order_lines.append((0, 0, {
                                                'name': product[0]['name'],
                                                'product_id': product[0]['id'],
                                                'product_uom_qty': float(1),
                                                'product_uom': 1,
                                                'price_unit': float(line['paid_price']),
                                                'tax_id': False,
                                                'x_studio_daraz_voucher': float(line['voucher_seller']),
                                                'x_daraz_order_item_id': str(line['order_item_id'])
                                                # 'x_studio_shipping_amount': float(all_order_lines['SuccessResponse']['Body']['OrderItems'][i]['ShippingAmount']),
                                                # 'x_studio_daraz_order_item_id': str(all_order_lines['SuccessResponse']['Body']['OrderItems'][i]['OrderItemId']),
                                            }))
                                            shipping_amount += float(
                                                line['shipping_amount'])

                                            checkValid = True
                                            try:
                                                models_live.execute_kw(db_live, uid_live, password_live, 'sale.order', 'write', [[sale_order_data['id']], {
                                                    'order_line': order_lines,
                                                }])
                                                print('orderline inserted')
                                            except Exception as Ex:
                                                print(

                                                    str(line['order_id']), 'orderline not inserted: ', str(Ex))

                    else:

                        print('Product Not found for Sale Order No: ' + str(
                            sale_order['order_number']) + " and Product " + str(product_hold_exp))
                        # List_data = ('Product Not found for Sale Order No: ' + str(sale_order['order_number']) + " and Product " +str(product_hold_exp))
                        with open(r"C:\Users\Administrator\Desktop\Daraz Order API Logs\Daraz_Order_Logs_.txt", 'a') as f_object:

                            writer_object = writer(f_object)
                            writer_object.writerow('Product Not found for Sale Order No: ' + str(
                                sale_order['order_number']) + " and Product " + str(product_hold_exp))
                            f_object.close()

                else:
                    print('Sale Order Already Created: ' +
                          str(sale_order['order_number']))
                    # print(sale_order_search)
            except Exception as ex:
                print('Cant Create Sale Order: ' +
                      str(sale_order['order_number']))
                print(ex)
