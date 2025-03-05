import config_core
import sys
import traceback
from   datetime import datetime
import random
import time

sys.path.append("pytavia_core"    )
sys.path.append("pytavia_modules" )
sys.path.append("pytavia_settings")
sys.path.append("pytavia_stdlib"  )
sys.path.append("pytavia_storage" )

from pytavia_stdlib   import idgen
from pytavia_stdlib   import utils
from pytavia_core     import database
from pytavia_core     import helper
from pytavia_core     import config
from pytavia_stdlib   import cfs_lib
from xml.sax            import saxutils as su

class profile_proc:

    mgdDB = database.get_db_conn(config.mainDB)

    def __init__(self, app):
        self.webapp = app
    # end def

    def validate_username(self, params) :
        username = params["add_username"]

        check_username = self.mgdDB.db_user.find_one({ "username" : username, "type" : "BO" })
        if check_username != None :
            return False
        else :
            return True


    # end def

    def update(self, params):
        response = helper.response_msg(
            "UPDATE_PROFILE_SUCCESS", "UPDATE PROFILE SUCCESS", {} , "0000"
        )
        try:     

            update_fields = {
                # "is_premium"              : params.get("is_premium", "FALSE"),
                # "subscription_type"       : params.get("subscription_type", "free"),
                "name"                    : params.get("name", ""),
                "dob"                     : params.get("dob", ""),
                "sex"                     : params.get("sex", ""),
                # "hobbies"                 : params.get("hobbies", ""),
                "city"                    : params.get("city", ""),
                "tribe"                   : params.get("tribe", ""),
                "congregation"            : params.get("congregation", ""),
                # "marital_status"          : params.get("marital_status", ""),
                "job"                     : params.get("job", ""),
                "about"                   : params.get("about", ""),
                # "advent_status"           : params.get("advent_status", ""),
                "profile_intro"           : "TRUE",                
                "location"                : params.get("location", {"latitude": 0.0, "longitude": 0.0}),
                # "preferences": params.get("preferences", {
                #     "age_range"           : {"min": 18, "max": 50},
                #     "distance_range_km"   : 50
                # }),
                "updated_at"              : datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            if params['hobbies'] != '':
                update_fields["hobbies"] = params['hobbies']

            if params['marital_status'] != '':
                update_fields["marital_status"] = params['marital_status']
            
            if params['advent_status'] != '':
                update_fields["advent_status"] = params['advent_status']
            
            image_profile           = params["files"]["image_profile"]
            file_image_profile      = ""
            file_name               = ""

            if image_profile.filename != "":
                try:    
                    now_time        = int(time.time() * 1000)
                    random_int      = random.randint(1000000,9999999)
                    file_name       = "file_" + str( now_time ) + "_" + str(random_int)
                    created_time    = time.strftime("%d-%m-%Y", time.localtime(int(time.time())))
                    file_resp       = cfs_lib.store_file_to_cfs({
                        "bucket"     : config.G_IMAGE_BUCKET,
                        "label"      : config.G_IMAGE_LABEL,
                        "file_data"  : image_profile,
                        "extension"  : "DEFAULT",
                        "allow_type" : ["DEFAULT"],
                        "file_name"  : "/profile_photo/"  + created_time + "/" + file_name
                    })
                    
                    self.webapp.logger.debug( "------------------------------------------" )
                    self.webapp.logger.debug( file_resp )
                    self.webapp.logger.debug( "------------------------------------------" )
                    
                    action_file     = file_resp["message_action"]
                    desc_file       = file_resp["message_desc"  ]
                    data_file       = file_resp["message_data"  ]
                    
                    if action_file != "ADD_CFS_FILE_SUCCES":
                        response.put( "status"      , "ADD_PROFILE_FAILED" )
                        response.put( "desc"        , "Upload Image Failed" )
                        response.put( "status_code" , "1001" )
                        response.put( "data"        , { "error_message" : desc_file })
                        return response
                    #endif

                    file_image_profile = data_file["path"]
                    file_name          = data_file["key"] 

                    update_fields["profile_photo"] = file_image_profile                   

                except:
                    self.webapp.logger.debug(traceback.format_exc())
                    file_image_profile      = ""

                #end try                        
            

            #process image
            removed_img = params.get("img_removed", None)            
            
            if removed_img:
                removed_img_clean = su.unescape(removed_img)
                removed_img_arr = removed_img_clean.split(",")
                if len(removed_img_arr) > 0:
                    for img in removed_img_arr:
                        self.mgdDB.db_users.update({"user_id"   : params.get("user_id", "")},
                                {"$pull": {"image" : img }})
                    # end for
                # end if
              
            #for looping multiple image save to cfs 
            if params.get("image"):
                for image_data in params["image"]:                                       
                    image           = image_data
                    file_name       = ""
                    if image.filename != "":
                        try:    
                            now_time        = int(time.time() * 1000)
                            random_int      = random.randint(1000000,9999999)
                            file_name       = "file_" + str( now_time ) + "_" + str(random_int)
                            created_time    = time.strftime("%d-%m-%Y", time.localtime(int(time.time())))
                            file_resp       = cfs_lib.store_file_to_cfs({
                                "bucket"     : config.G_IMAGE_BUCKET,
                                "label"      : config.G_IMAGE_LABEL,
                                "file_data"  : image,
                                "extension"  : "DEFAULT",
                                "allow_type" : ["DEFAULT"],
                                "file_name"  : "/gallery/"  + created_time + "/" + file_name
                            })
                            
                            self.webapp.logger.debug( "------------------------------------------" )
                            self.webapp.logger.debug( file_resp )
                            self.webapp.logger.debug( "------------------------------------------" )
                            
                            action_file     = file_resp["message_action"]
                            desc_file       = file_resp["message_desc"  ]
                            data_file       = file_resp["message_data"  ]
                            
                            if action_file != "ADD_CFS_FILE_SUCCES":
                                response.put( "status"      , "ADD_PENGELOLAAN_HUNIAN_FAILED" )
                                response.put( "desc"        , "Upload Image Failed" )
                                response.put( "status_code" , "1001" )
                                response.put( "data"        , { "error_message" : desc_file })
                                return response
                            #endif                                                        
                                                                                    
                            self.mgdDB.db_users.update(
                                {
                                    "user_id"   : params.get("user_id", "")
                                },
                                {"$push": {"image" : data_file["path"] }}
                            )
                 
                        except:
                            self.webapp.logger.debug(traceback.format_exc())

                        #end try
                    #end if
                #end for
            #end if

            self.mgdDB.db_users.update(
                {"user_id"               : params.get("user_id", "")},
                {"$set"                   : update_fields}
            )

            user_rec = self.mgdDB.db_users.find_one(
                {"user_id"               : params.get("user_id", "")},                
            )

            response.put( "data"        , user_rec)
        
        except :
            trace_back_msg = traceback.format_exc()
            self.webapp.logger.debug(traceback.format_exc())

            response.put( "status"      , "EDIT_PROFILE_FAILED" )
            response.put( "desc"        , "EDIT PROFILE FAILED" )
            response.put( "status_code" , "9999" )
            response.put( "data"        , { "error_message" : trace_back_msg })
        # end try
        return response


    def activate(self, params):
        call_id  = idgen._get_api_call_id()
        response = {
            "message_id"     : call_id,
            "message_action" : "ACTIVE_USER_SUCCESS",
            "message_code"   : "0",
            "message_title"  : "",
            "message_desc"   : "",
            "message_data"   : {}
        }

        try:
            modif_user_id = params["pkey"  ]
            set_active    = params["active"]
            notes         = params["notes" ]

            active_status = config.G_STATUS_INACTIVE[ set_active ]

            #self.webapp.logger.debug( "active_status---------------------------------------------" )
            #self.webapp.logger.debug( active_status )
            #self.webapp.logger.debug( "---------------------------------------------" )

            self.mgdDB.db_user.update(
                { "pkey" : modif_user_id },
                { "$set"       : { 
                    "status"   : active_status["status"],
                    
                }}
            )

            self.mgdDB.db_user_auth.update(
                { "fk_user_id" : modif_user_id },
                { "$set"       : { 
                    "inactive_status" : active_status["value" ],
                    "inactive_note"   : notes
                }}
            )
        except:
            self.webapp.logger.debug(traceback.format_exc())
            response["message_action"] = "ACTIVE_USER_FAILED"
            response["message_action"] = "ACTIVE_USER_FAILED: " + str(sys.exc_info())
        # end try

        

        return response

    # end def

    def edit(self, params):
        call_id  = idgen._get_api_call_id()
        response = {
            "message_id"     : call_id,
            "message_action" : "EDIT_USER_SUCCESS",
            "message_code"   : "0",
            "message_title"  : "",
            "message_desc"   : "",
            "message_data"   : {}
        }
        #self.webapp.logger.debug( "user_proc params--------------------------------------------------" )
        #self.webapp.logger.debug( params )
        #self.webapp.logger.debug( "------------------------------------------------------------------" )
        try:
            modif_user_id = params["edit_pkey_id"   ]
            username      = params["edit_username"  ]
            name          = params["edit_fullname"  ]
            password      = params["edit_password"  ]
            role          = params["edit_role"      ]
            


            self.mgdDB.db_user.update(
                { 
                    "pkey"      : modif_user_id,
                    "username"  : username,
                },
                { "$set"       : { 
                    "role" : role, 
                    "name" : name,
                    }
                }
            )

            if password != "" :
                hashed_password = utils._get_passwd_hash({
                    "id" : username, "password" : password
                })
                self.mgdDB.db_user_auth.update(
                    { 
                        "fk_user_id" : modif_user_id,
                        "username"   : username,
                    },
                    { "$set"       : { 
                        "password" : hashed_password,
                        }
                    }
                )
            #end if update password


        except:
            self.webapp.logger.debug(traceback.format_exc())
            response["message_action"] = "EDIT_USER_FAILED"
            response["message_action"] = "EDIT_USER_FAILED: " + str(sys.exc_info())
        # end try
        return response
    # end def

    def remove(self, params):
        call_id  = idgen._get_api_call_id()
        response = {
            "message_id"     : call_id,
            "message_action" : "REMOVE_USER_SUCCESS",
            "message_code"   : "0",
            "message_title"  : "",
            "message_desc"   : "",
            "message_data"   : {}
        }
        try:
            pkey_user = params["del_pkey_id"]
            self.mgdDB.db_user.remove      ({ "pkey"       : pkey_user })
            self.mgdDB.db_user_auth.remove ({ "fk_user_id" : pkey_user })
        except:
            self.webapp.logger.debug(traceback.format_exc())
            response["message_action"] = "REMOVE_USER_FAILED"
            response["message_action"] = "REMOVE_USER_FAILED: " + str(sys.exc_info())
        # end try


        self.webapp.logger.debug( "remove user response ---------------------------------------------" )
        self.webapp.logger.debug( response )
        self.webapp.logger.debug( "---------------------------------------------" )

        return response
    # end def
# end class
