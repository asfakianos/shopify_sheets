from keys import *
import shopify
import gspread
import time

# NOTE: To add a field to the excel sheet, simply edit the headers and then add the respective header here and to the product_meta dict in update_sheet_from_shopify()

HEADERS = {"product_id":"A",
           "sku":"B",
           "name":"C",
           "specifications":"D",
           "features":"E",
           "dimensions":"F",
           "tags":"G",
           "vendor":"H",
           "edited":"I"
          }
HEAD_INDEX = {"product_id":"0",
              "sku":"1",
              "title":"2",
              "features":"3",
              "dimensions":"4",
              "specifications":"5",
              "tags":"6",
              "vendor":"7",
              "edited":"8"
             }

# Unique key for product spreadsheet
SHEET_KEY = "1UQmcZX09yK8HsagccECYNRngRZCklU3-x6o7BWDgxMw"

# Loop delay in seconds. (Checks for EDIT every iteration, pulls from Shopify every 5th iteration)
LOOP_DELAY = 5


# Acquire a shopify session to interact with the shop
def shop_session():
    shop_url = "https://%s:%s@greenstar-test.myshopify.com/admin/api/%s" % (API_KEY, PASSWORD, API_VERSION) 
    shopify.ShopifyResource.set_site(shop_url)
    print("shopify handshake success")
    return shopify.Shop.current()


# Acquire a gspread session to use the google drive API
def gspread_session():
    gc = gspread.service_account()
    sh = gc.open_by_key(SHEET_KEY)
    print("sheet loaded successfully")
    return sh


# Returns all the products of a given shop
def get_products(shop):
    # NOTE: Eventually we want to shift towards getting ALL products, not just the first page...not sure what this does quite yet...
    return shopify.Product.find()


# Updates the 'shopify products' sheet1 with up-to-date info on all Shopify Products and metadata
def update_sheet_from_shopify(shop, worksheet):
    first_prod_page = get_products(shop)

    # If we were to add async, this system would have to change an be indexed by name or id
    product_meta = {}

    # Add each of the products to a dictionary, key=product_id, and fill with product metadata
    # NOTE: we are using a dictionary to service as a system for "promising" a field, even if none exists (resulting in a stored empty string)
    for product in first_prod_page:

        # NOTE RE product.to_dict(): Since we don't need all of the data from it, it's simpler just to clean like this
        # initialize a new product with empty meta fields (for now ignoring regular fields
        product_meta[product.id] = {
                                    'sku':product.variants[0].sku,
                                    'title':product.title,
                                    'features':'', 
                                    'dimensions':'', 
                                    'specifications':'', 
                                    'tags':product.tags,
                                    'vendor':product.vendor,
                                    'edited':False
                                   }
        # populate the list
        for field in product.metafields():
            product_meta[product.id][field.key] = field.value

    # Using list comprehension to update because batch_update() uses a single API write request.
    worksheet.batch_update([{'range':f'A{id[0]+2}:{HEADERS["edited"]}{id[0]+2}',
                             'values':[[id[1]]+list(product_meta[id[1]].values())]}
                            for id in list(enumerate(list(product_meta.keys())))])


# Fetches updates from a given worksheet, assuming that it is formatted correctly, via the 'edited' row checkboxes
def fetch_sheet_updates(worksheet):
    # Retrieving the edited column to check if a user has reported any units and isolate the row numbers:
    updated_rows = worksheet.batch_get([f'{HEADERS["edited"]}:{HEADERS["edited"]}'])[0][1:]
    rows_to_check = [row[0] + 2 for row in enumerate(updated_rows) if row[1][0] == 'TRUE']
    if len(rows_to_check) > 0:
        changes = worksheet.batch_get([f'{HEADERS["product_id"]}{row_num}:{HEADERS["edited"]}{row_num}' for row_num in rows_to_check])
        return changes
    return None # If there are no changes to make


# Updates products in a given shop based on the items in the list provided. 
def send_to_shopify(shop, items):
    for item in items:
        # Find the item in question and update all fields
        item = item[0]
        product = shopify.Product.find(item[int(HEAD_INDEX['product_id'])])
       
        # Updating standard props before meta
        product.title = item[int(HEAD_INDEX['title'])]
        product.tags = item[int(HEAD_INDEX['tags'])]
        product.vendor = item[int(HEAD_INDEX['vendor'])]
        product.variants[0].sku = item[int(HEAD_INDEX['sku'])]

        product.save()

        # While it would be great to loop this part, we don't know what has been edited, and we have to assign specific field var names:
        # Metafields save themselves, so no need for a product.save()
        product.add_metafield(shopify.Metafield({
            'key':'features',
            'value_type':'string',
            'namespace':'global',
            'value':item[int(HEAD_INDEX['features'])]
        }))

        product.add_metafield(shopify.Metafield({
            'key':'dimensions',
            'value_type':'string',
            'namespace':'global',
            'value':item[int(HEAD_INDEX['dimensions'])]
        }))

        product.add_metafield(shopify.Metafield({
            'key':'specifications',
            'value_type':'string',
            'namespace':'global',
            'value':item[int(HEAD_INDEX['specifications'])]
        }))


# Checks the google sheet for any edits and then sends them to shopify if they exist.
def generate_and_apply_edits(shop, worksheet):
    to_shopify = fetch_sheet_updates(worksheet)
    if to_shopify:
        send_to_shopify(shop, to_shopify)


def main():
    # Initialize access/session
    sh = gspread_session()
    shop = shop_session()
    # Accessing the product-management worksheet
    worksheet = sh.worksheet("Product-Management")

    # Run through one initial iteration of the full loop to "catch up"
    generate_and_apply_edits(shop, worksheet)
    # Replace data with shopify source data
    update_sheet_from_shopify(shop, worksheet)

    # Main loop (forever)
    i = 0 # Iterator
    while True:
        time.sleep(LOOP_DELAY)
        i += 1
        generate_and_apply_edits(shop, worksheet)
        # Every 5th iteration, check back with shopify.
        if i >= 5:
            update_sheet_from_shopify(shop, worksheet)
            i = 0


if __name__ == '__main__':
    main()


