from keys import *
import shopify
import gspread
import time

HEADERS = {"product_id":"A",
           "name":"B",
           "specifications":"C",
           "features":"D",
           "dimensions":"E",
           "edited":"F"
          }

HEAD_INDEX = {"product_id":"0",
              "name":"1",
              "specifications":"2",
              "features":"3",
              "dimensions":"4",
              "edited":"5"
          }
# Unique key for product spreadsheet
SHEET_KEY = "1UQmcZX09yK8HsagccECYNRngRZCklU3-x6o7BWDgxMw"

def get_products():
    shop_url = "https://%s:%s@greenstar-test.myshopify.com/admin/api/%s" % (API_KEY, PASSWORD, API_VERSION) 
    shopify.ShopifyResource.set_site(shop_url)
    shop = shopify.Shop.current()
    print(shop)
    # NOTE: Eventually we want to shift towards getting ALL products, not just the first page
    page1 = shopify.Product.find()
    return page1


def gspread_session():
    gc = gspread.service_account()
    sh = gc.open_by_key(SHEET_KEY)
    return sh

# Updates the 'shopify products' sheet1 with up-to-date info on all Shopify Products and metadata
def update_sheet_from_shopify(worksheet):
    first_prod_page = get_products()

    # If we were to add async, this system would have to change an be indexed by name or id
    product_meta = {}

    # Add each of the products to a dictionary, key=product_id, and fill with product metadata
    # NOTE: we are using a dictionary to service as a system for "promising" a field, even if none exists (resulting in a stored empty string)
    for product in first_prod_page:

        # initialize a new product with empty meta fields (for now ignoring regular fields
        product_meta[product.id] = {'name':product.title, 'features':'', 'dimensions':'', 'specifications':'', 'edited':False}
        
        # populate the list
        for field in product.metafields():
            product_meta[product.id][field.key] = field.value

    # Using list comprehension to update because batch_update() uses a single API write request.
    worksheet.batch_update([{'range':f'A{id[0]+2}:{HEADERS["edited"]}{id[0]+2}',
                             'values':[[id[1]]+list(product_meta[id[1]].values())]}
                            for id in list(enumerate(list(product_meta.keys())))])

    return worksheet.get_all_values()


def get_sheet_updates(last_records):
    for row in last_records:
        if row[-1] == 'TRUE':
            print(row)

def main():
    # Initialize access/session
    sh = gspread_session()
    last = update_sheet_from_shopify(sh.sheet1)
    get_sheet_updates(last)


if __name__ == '__main__':
    main()


