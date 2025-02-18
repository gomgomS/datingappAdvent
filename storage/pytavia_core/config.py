import os
import  urllib.parse



G_FLASK_SECRET=b'_5#y2L"F4Q8z\n\xec]/'
G_WALLET_ID_SUFFIX = 6


# This is the home path for the home of this project
G_HOME_PATH=os.getcwd()

# This is where all the cookies are stored
G_SESSION_STORAGE = G_HOME_PATH + "/settings/storage"
G_STATIC_URL_PATH = G_HOME_PATH + "/static"
G_STATIC_URL_PATH = "/static"
G_UPLOAD_PATH     = G_HOME_PATH + G_STATIC_URL_PATH + "/upload"
G_UPLOAD_URL_PATH = G_STATIC_URL_PATH + "/upload"
G_UPLOAD_DOCO_URL_PATH      = G_UPLOAD_URL_PATH + "/documents"
G_UPLOAD_ADV_URL_PATH       = G_UPLOAD_URL_PATH + "/advertising"


####################################################################################################################################################


# Development

# Database
mainDB                    = "datingapp"
mainDB_string             = "mongodb://127.0.0.1:27017/"  + mainDB


####################################################################################################################################################


# This is where we have all the databases we want to connect to
G_DATABASE_CONNECT=[
    {"dbname" : mainDB    , "dbstring"  : mainDB_string    }
]

# HTML TEMPLATE TRANSITION
G_TICKBOX = {
        1 : "checked",
        0 : ""
}

G_STATUS = {
    1 : "ACTIVE",
    0 : "NO ACTIVE"
}

G_PAGINATE_START=0
G_PAGINATE_LENGTH=10

# SECURITY
G_VERIFIED_SUCCESS="VERIFY_SUCCESS"

