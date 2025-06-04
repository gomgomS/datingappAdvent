import time
import copy
import pymongo
import os
import sys

from bson.objectid import ObjectId

class mongo_model:

    def __init__(self, record, lookup, db_handle):
        self._mongo_record  = copy.deepcopy(record)
        self._lookup_record = copy.deepcopy(lookup)
        self._db_handle     = db_handle
    # end def

    def put(self, key, value):
        if not (key in self._lookup_record):
            raise ValueError('SETTING_NON_EXISTING_FIELD', key, value)
        # end if
        self._mongo_record[key] = value
    # end def

    def get(self):
        return self._mongo_record
    # end def   

    def delete(self , query):
        collection_name = self._lookup_record["__db__name__"]
        self._db_handle[collection_name].remove( query )
    # end def

    def insert(self, lock=None):
        collection_name = self._lookup_record["__db__name__"]
        del self._mongo_record["__db__name__"]
        # if 
        #if not(collection_name in self._db_handle.list_collection_names()):
        #    self._db_handle.create_collection( collection_name )
        # end if
        if lock == None:
            self._db_handle[collection_name].insert_one(  
                self._mongo_record
            )
        else:
            self._db_handle[collection_name].insert_one(  
                self._mongo_record,
                session=lock
            )
        # end if
    # end def

    def update(self, query):
        collection_name = self._lookup_record["__db__name__"]
        self._db_handle[collection_name].update(
            query, 
            { "$set" : self._mongo_record }
        )
    # end def
# end class
#
#
# Define the models/collections here for the mongo db
#
db = {
    
    "db_config_all" : {
        "name"                  : "",
        "add_url"               : "",
        "edit_url"              : "",
        "value"                 : "",
        "count"                 : 0 ,
        "desc"                  : "",
        "type"                  : "", # MENU PERMISSION | ETC
        # additional
        "misc"                  : "",
        "bo_access"             : "FALSE", # TRUE | FALSE  | give access to back office
        "bo_access_2"           : "FALSE"  # TRUE | FALSE  | give access to back office
    },

    "db_config_general" : {
        "name"                  : "",
        "value"                 : "",
        "order"                 : 0 ,
        "status"                : "ENABLE",
        "desc"                  : "",
        "misc"                  : "",
    },

    "db_config_menu_webapp_handler" : {
        "name"                  : "",
        "value"                 : "",
        "href"                  : "",
        "status"                : "ENABLE",
        "fk_menu_id"            : "CONFIGURATION"
    },

    "db_config_menu_webapp_item_all" : {
        "name"                  : "",
        "value"                 : "",
        "order"                 : 0 ,
        "href"                  : "",
        "status"                : "ENABLE",
        "icon"                  : "",
        "description"           : ""
    },

    "db_config_privilege" : {
        "name"                  : "",
        "value"                 : "",
        "order"                 : 0 ,
        "status"                : "ENABLE",
        "misc"                  : "",
        "desc"                  : ""
    },

    "db_config_role" : {
        "name"                  : "",
        "value"                 : "",
        "order"                 : 0 ,
        "status"                : "ENABLE",
        "user_type"             : "BO", # additional for user type
        "misc"                  : "",
        "desc"                  : ""
    },

    "db_config_webapp_menu_privilege" : {
        "name"                  : "",
        "value"                 : "",
        "order"                 : 0 ,
        "status"                : "ENABLE",
        "fk_privilege_id"       : "SELECT PRIVILEGE",
        "fk_menu_id"            : "SELECT MENU",
        "desc"                  : ""
    },

    "db_config_webapp_role_privilege" : {
        "name"                  : "",
        "value"                 : "",
        "order"                 : 0 ,
        "status"                : "ENABLE",
        "fk_privilege_id"       : "SELECT PRIVILEGE",
        "fk_role_id"            : "SELECT ROLE"
    },

    "db_config_webapp_route_privileges" : {
        "name"                  : "", # this for route action name (for logging), display as privilege text
        "value"                 : "", # this value as ROUTE_NAME, should be Unique
        "href"                  : "", # route url
        "order"                 : 0 , # use order to sort side menu list
        "route_type"            : "", # MENU | PAGE | PROCESS ( PROCESS UPDATE, PROCESS EDIT, PROCESS DELETE, etc  )
        "status"                : "ENABLE",
        "misc"                  : "",
        "desc"                  : "" ,
        # for route_type MENU only
        "display_text"          : "", # display as MENU text
        "icon"                  : "", # icon for MENU
        "bo_access"             : "TRUE", # give privilege to Back Office, default TRUE, update in CMS
    },

    "db_cookies" : {
        "fk_user_id"            : "",
        "cookie_id"             : "",
        "user_agent"            : {},
        "referrer"              : "",
        "x_forward_for"         : "",
        "username"              : "",
        "expire_time"           : "",
        "active"                : "", # TRUE | FALSE  
    },

    "db_log_login_auth" : {
        "fk_user_id"            : "" ,
        "usernmae"              : "",
        "desc"                  : "",
        "state"                 : "LOGIN_FAILED", # LOGIN_FAILED | LOGIN_SUCCESS,
    },

    "db_role_parent_to_child_mapping" : {
        "name"                  : "",
        "value"                 : "",
        "status"                : "ENABLE",
        "parent_role_val"       : "",
        "child_role_val"        : "",
        "desc"                  : "",
    },

    "db_security_api_core" : {
        "api_key"               : "",
        "api_secret"            : "",
        "active"                : "TRUE",
        "description"           : ""
    },
    
    "db_security_cfs" : {
        "token_value"           : "",
        "username"              : "",
        "password"              : "",
        "expire_time"           : "",
        "active"                : "TRUE"
    }, 
    
    "db_security_user" : {
        "token_value"           : "",
        "username"              : "",
        "password"              : "",
        "expire_time"           : "",
        "active"                : "TRUE"
    },

    "db_session" : {
        "fk_user_id"            : "",
        "login_time"            : 0 
    },

    "db_setting_app" : {
        "idle_account"          : "",
        "force_change_password" : "",
        "password_history"      : "",
        "password_length"       : "",
        "variable_password"     : { 
            "numeric"               : "FALSE",  # <TRUE> | <FALSE>
            "lower_case"            : "FALSE",  # <TRUE> | <FALSE>
            "upper_case"            : "FALSE",  # <TRUE> | <FALSE>
            "symbol"                : "FALSE",  # <TRUE> | <FALSE>
            "symbol_str"            : ""
        },
        "wrong_counter"         : "",
        "limit_history_password": 0,
        "screen_timeout"        : 0,
        "tran_timeout"          : 0,
    },

    "db_system_activity_logging" : {
        "client_type"           : "",
        "action"                : "",
        "description"           : "",
        "action_time"           : "",
        "call_id"               : "",
        "request"               : "",
        "response"              : "",
        "fk_user_id"            : "",
        "portal_type"           : "",
        "merchant_id"           : "",
        "user_role"             : "",
        "username"              : "",
        "activity_data"         : "",
    },

    "db_unique_counter" : {
        "counter"               : 0,
    },

    "db_random_config" : {
        "config_name"           : "check_gapeka_api_status",
        "check_gpk_api_status"  : "off",
    },

    "db_config"                    : {
        "_id"                   : ObjectId(),
        "name"                  : "",
        "value"                 : "",
        "desc"                  : "",
        "config_type"           : "",
        "misc"                  : "",
        "data"                  : {}
    },

    "db_menu"                   : {
        "_id"                   : ObjectId(),
        "menu_name"             : "",
        "value"                 : "",
        "icon_class"            : "",
        "url"                   : "",
        "position"              : "",
        "desc"                  : "",
        "rec_timestamp"         : ""
    },

    "db_starter"                   : {
        "_id"                   : ObjectId(),
        "menu_value"            : "",
        "name"                  : "",
        "value"                 : "",
        "icon_class"            : "",
        "url"                   : "",
        "position"              : "",
        "desc"                  : "",
        "rec_timestamp"         : ""
    },

    "db_menu_permission"        : {
        "_id"                   : ObjectId(),
        "role_position_value"   : "",
        "menu_value"            : "",
        "desc"                  : "",
        "rec_timestamp"         : ""
    },

    "db_super_user" : {
        "username"              : "",
        "password"              : "",
        "role"                  : "ADMIN",
    },

    # USER
    "db_users": {
        "user_id"                     : "",
        "email"                       : "",
        "password"                    : "",
        "is_premium"                  : "FALSE",
        "subscription_type"           : "", # "free" or "premium"
        "premium_expiry"              : "",
        "name"                        : "",
        "username"                    : "",
        "verify_email"                : "",
        "dob"                         : "", #day of birth
        "otp_4_number"                : "",        
        "sex"                         : "", # male or female
        "hobbies"                     : "", 
        "city"                        : "", 
        "tribe"                       : "", 
        "congregation"                : "",
        "marital_status"              : "",
        "job"                         : "",
        "about"                       : "",
        "advent_status"               : "",
        "profile_intro"               : "FALSE",
        "profile_photo"               : "",
        "location"                    : {},
        "fk_user_id_like"             : [],
        "fk_user_id_dislike"          : [],
        "image"                       : [], # max 5 image //gallery photo
        "preferences": {
            "age_range"               : { "min": 18, "max": 50 },
            "distance_range_km"       : 50,
        },
        "total_swipe_daily"           : "",
        "created_at"                  : "",
        "updated_at"                  : ""
    },
    # CONFIG
    "db_subscription_plans": {
        "plan_id"                     : "",
        "plan_name"                   : "",
        "price"                       : 0.0,
        "features"                    : ["feature1", "feature2"],
        "created_at"                  : "",
        "updated_at"                  : ""
    },
    "db_adsense": {
        "ads_id"                      : "",
        "client_id"                   : "",
        "ads_title"                   : "",
        "ads_url"                     : "",
        "ads_image"                   : "",
        "target_audience"             : { "location": "", "age_range": { "min": 18, "max": 50 } },
        "created_at"                  : "",
        "updated_at"                  : ""
    },
    # ADMIN
    "db_admins": {
        "admin_id"                    : "",
        "name"                        : "",
        "email"                       : "",
        "password"                    : "",
        "role"                        : "moderator", # "superadmin" or "moderator"
        "created_at"                  : "",
        "updated_at"                  : ""
    },
    # MESSAGING
    "db_messages": {
        "message_id"                  : "",
        "sender_id"                   : "", # FK from db_users
        "receiver_id"                 : "", # FK from db_users
        "message_content"             : "",
        "is_read"                     : "FALSE",
        "created_at"                  : ""
    },
    # MATCHES
    "db_matches": {
        "match_id"                    : "",
        "user_id_1"                   : "", # FK from db_users
        "user_id_2"                   : "", # FK from db_users
        "is_mutual"                   : "TRUE",
        "created_at"                  : ""
    },

    # CHAT
    "db_chat": {
        "chat_id"                     : "",        
        "match_id"                    : "",
        "sender_user_id"              : "",
        "receiver_user_id"            : "",
        "message"                     : "",
        "type"                        : "",
        "timestamp"                   : "",
        "is_read"                     : "false",        
        "is_deleted"                  : "false",   
        "sequence"                    : 0,     
    },  

    # PAYMENTS
    "db_payments": {
        "payment_id"                  : "",
        "user_id"                     : "", # FK from db_users
        "subscription_plan_id"        : "", # FK from db_subscription_plans
        "amount"                      : 0.0,
        "payment_status"              : "", # "pending", "completed", "failed"
        "payment_method"              : "",
        "created_at"                  : ""
    },
    # REPORTS
    "db_reports": {
        "report_id"                   : "",
        "reported_by"                 : "", # FK from db_users
        "reported_user"               : "", # FK from db_users
        "reason"                      : "",
        "status"                      : "", # "pending", "resolved"
        "created_at"                  : "",
        "resolved_at"                 : ""
    },

    "db_premium_logs": {
        "log_premium_id"              : "",  # unique ID
        "user_id"                     : "",  # FK ke db_users
        "type"                        : "",  # "1_month" atau "3_month"
        "start_at"                    : "",  # datetime mulai premium
        "end_at"                      : "",  # datetime akhir premium (auto dihitung)
        "created_at"                  : ""   # kapan log ini dicatat (biasanya == start_at)
    }


}
