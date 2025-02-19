import os
import  urllib.parse
G_FLASK_SECRET=b'_5#y2L"F4Q8z\n\xec]/'
G_WALLET_ID_SUFFIX = 6

# This is the
G_HOME_PATH=os.getcwd()

# This is where all the cookies are stored
G_STATIC_URL_PATH           = "/static"
G_UPLOAD_PATH               = G_HOME_PATH + G_STATIC_URL_PATH + "/upload"
G_UPLOAD_URL_PATH           = G_STATIC_URL_PATH + "/upload"



############################################################################################################################################################

# DEVELOPMENT

MAIN_APP_URL                = "http://0.0.0.0:50011"
                        
# DATABASE
mainDB                      = "datingapp"
mainDB_string               = "mongodb://127.0.0.1:27017/"  + mainDB

# Local Storage
G_BASE_S3_URL               = "http://0.0.0.0:50012"
G_IMAGE_URL_DISPATCH        = G_BASE_S3_URL + "/v1/cfs/get-file?"

G_IMAGE_BUCKET              = "ADVENT-MATCH"
G_IMAGE_LABEL               = "ADVENT-MATCH"
G_IMAGE_DEFAULT_URL         = "key=/placeholder/02-01-2021/placeholder_1609559601948_7656949&bucket=ADVENT-MATCH"


# IMAGE SERVER
G_CHAT_URL_DISPATCH         = "http://0.0.0.0:50013"




############################################################################################################################################################


# This is where we have all the databases we want to connect to
G_DATABASE_CONNECT=[
    {"dbname" : mainDB    , "dbstring"  : mainDB_string    }
]

JKTA_TZ = 7
MS_24_HOURS = 86399999

MAIL_SERVER ="smtp.gmail.com"
MAIL_PORT  = 465
MAIL_USERNAME  = "bersihinyabang@gmail.com"
MAIL_PASSWORD  = "mxfk ezha kgjh sixk"
MAIL_USE_TLS  = False
MAIL_USE_SSL  = True

