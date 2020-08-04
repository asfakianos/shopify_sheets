from keys import *
import shopify
import gspread

HEADERS = {"product_id":"A",
           "name":"B",
           "specifications":"C",
           "features":"D",
           "dimensions":"E"
          }

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
    #sh = gc.open('test')
    #print(sh.sheet1.get_all_records())
    #worksheet = sh.sheet1
    return gc


def main():
    # Initialize access/session
    gc = gspread_session()
    sh = gc.open('test') # Using a test sheet to test out update() features from gspread
    worksheet = sh.sheet1
    first_prod_page = get_products()

    # If we were to add async, this system would have to change an be indexed by name or id
    meta_data = {'name':[],'features':[], 'dimensions':[], 'specifications':[]}
    product_meta = {}

    # Add each of the products to a dictionary, key=product_id, and fill with product metadata
    # NOTE: we are using a dictionary to service as a system for "promising" a field, even if none exists (resulting in a stored empty string)
    for product in first_prod_page:
        # initialize a new product with empty meta fields (for now ignoring regular fields
        product_meta[product.id] = {'name':product.title, 'features':'', 'dimensions':'', 'specifications':''}
        # populate the list
        for field in product.metafields():
            product_meta[product.id][field.key] = field.value
    # Add each product in the dict to the sheet
    last_updated = 2 # Keeping track of the last row that we populated with data
    for key in meta_data.keys():
        cell_list = worksheet.range(f"{HEADERS['product_id']}{last_updated}:{HEADERS['dimensions']}{last_updated}")

    for product_id in product_meta:
        worksheet.update(f"{HEADERS['product_id']}{last_updated}",product_id)
        for meta_key,meta_value in product_meta[product_id].items():
            worksheet.update(f"{HEADERS[meta_key]}{last_updated}",meta_value)
        last_updated += 1


if __name__ == '__main__':
    print(API_KEY)
    main()
