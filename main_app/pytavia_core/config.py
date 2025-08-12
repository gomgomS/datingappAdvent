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
# IF RESPON 400 AND CSRF MISSING MAKESURE FIRST YOUR RUN USING http://localhost:50011 it will works 
# why using http://localhost:50011 IDONT FKING KNOW 
MAIN_APP_URL                = "http://localhost:50011"
                        
# DATABASE
mainDB                      = "datingapp"
mainDB_string               = "mongodb://127.0.0.1:27017/"  + mainDB

# Local Storage
G_BASE_S3_URL               = "http://127.0.0.1:50012"
G_IMAGE_URL_DISPATCH        = G_BASE_S3_URL + "/v1/cfs/get-file?"

G_IMAGE_BUCKET              = "ADVENT-MATCH"
G_IMAGE_LABEL               = "ADVENT-MATCH"
G_IMAGE_DEFAULT_URL         = "key=/placeholder/02-01-2021/placeholder_1609559601948_7656949&bucket=ADVENT-MATCH"


# IMAGE SERVER
G_CHAT_URL_DISPATCH         = "http://127.0.0.1:50013"




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

CITY_LIST = [
          "Jakarta", "Surabaya", "Bandung", "Medan", "Semarang",
          "Palembang", "Makassar", "Bogor", "Depok", "Bekasi",
          "Yogyakarta", "Malang", "Padang", "Pekanbaru", "Banjarmasin",
          "Samarinda", "Pontianak", "Manado", "Denpasar", "Batam",
          "Tangerang", "South Tangerang", "Bandar Lampung", "Cimahi", "Tasikmalaya",
          "Serang", "Balikpapan", "Jambi", "Cirebon", "Surakarta",
          "Kupang", "Mataram", "Jayapura", "Bengkulu", "Palu",
          "Ambon", "Kendari", "Dumai", "Pekalongan", "Palangka Raya",
          "Binjai", "Kediri", "Sorong", "Tegal", "Banda Aceh",
          "Tarakan", "Probolinggo", "Singkawang", "Lubuklinggau", "Tanjungpinang",
          "Bitung", "Pangkalpinang", "Batu", "Pasuruan", "Banjar",
          "Gorontalo", "Ternate", "Madiun", "Salatiga", "Prabumulih",
          "Lhokseumawe", "Langsa", "Bontang", "Tanjungbalai", "Tebing Tinggi",
          "Metro", "Palopo", "Bima", "Baubau", "Parepare",
          "Blitar", "Pagar Alam", "Payakumbuh", "Gunungsitoli", "Mojokerto",
          "Bukittinggi", "Kotamobagu", "Magelang", "Tidore", "Tomohon",
          "Sungai Penuh", "Subulussalam", "Pariaman", "Sibolga", "Tual",
          "Solok", "Sawahlunto", "Padang Panjang", "Sabang","Timika"
        ]

MIN_USER_SWIPE_ACCESSABLE = 200
########################### PREMIUM CONFIGURATION ###########################
SUBSCRIPTION_CONFIG = {
    "premium": {
        "DAILY_SWIPE": 8,
        "CAN_UNDO_LAST_DISLIKE": True,
        "CAN_SEE_WHO_LIKE_USER": True,
        "CAN_UPLOAD_ALBUM": True,
        "MORE_OFTEN_SEEN": True,
        "GET_INFO_TOTAL_NEW_USER": True,
        "CAN_FILTER": True
    },
    "free": {
        "DAILY_SWIPE": 70,
        "CAN_UNDO_LAST_DISLIKE": False,
        "CAN_SEE_WHO_LIKE_USER": False,
        "CAN_UPLOAD_ALBUM": False,
        "MORE_OFTEN_SEEN": False,
        "GET_INFO_TOTAL_NEW_USER": False,
        "CAN_FILTER": False
    }
}


superadmin_username = "gomgom" 
password = 1
