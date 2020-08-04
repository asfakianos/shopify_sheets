import gspread
from oauth2client.service_account import ServiceAccountCredentials

gc = gspread.service_account()
sh = gc.open('test')
print(sh.sheet1.get_all_records())
worksheet = sh.sheet1
worksheet.update('A1:B2', [[1, 2], [3, 4]])
