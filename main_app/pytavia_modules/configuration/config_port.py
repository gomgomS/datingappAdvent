import config_core
import sys
import traceback

sys.path.append("pytavia_core"    )
sys.path.append("pytavia_modules" )
sys.path.append("pytavia_settings")
sys.path.append("pytavia_stdlib"  )
sys.path.append("pytavia_storage" )

from pytavia_stdlib   import idgen
from pytavia_stdlib   import utils
from pytavia_core     import database
from pytavia_core     import config

class config_port:

    mgdDB = database.get_db_conn(config.mainDB)

    def __init__(self, app):
        self.webapp = app
    # end def

    def upsert(self, params):
        call_id  = idgen._get_api_call_id()
        response = {
            "message_id"     : call_id,
            "message_action" : "ADD_PORT_SUCCESS",
            "message_code"   : "0",
            "message_title"  : "",
            "message_desc"   : "",
            "message_data"   : {}
        }
        try:

            pkey        = params["pkey"]
            city_id     = params["city"]
            name        = params["name"]
            desc        = params["desc"]
            misc        = params["misc"]
            context     = params["context"]
            
            doc = self.mgdDB.db_config_port.find_one({ "pkey" : pkey})
            if doc:
                self.mgdDB.db_config_port.update(
                    { 
                        "pkey"      : doc['pkey'],
                    },
                    {
                        "$set":
                        { 
                            "fk_city_id": city_id,
                            "name" : name,
                            "desc" : desc,
                            "misc" : misc,
                            "context" : context, 
                        }
                    }
                )
                response["message_action"] = "UPDATE_PORT_SUCCESS"
            else:

                doc = database.get_record("db_config_port")
                doc["fk_user_id"] = params['fk_user_id']   
                doc["fk_city_id"] = city_id  
                doc["name"] = name
                doc["desc"] = desc      
                doc["misc"] = misc
                doc["context"] = context
                self.mgdDB.db_config_port.insert( doc )

                response["message_action"] = "ADD_PORT_SUCCESS"
            #endif

            #update item
            item_count = self.mgdDB.db_config_port.find({}).count()
            self.mgdDB.db_config_all.update(
                {"value" : "CONFIG_PORT"},
                {"$set"  : {"count" : item_count }}
            )
        except :
            self.webapp.logger.debug(traceback.format_exc())
            response["message_action"   ] = "ADD_PORT_FAILED"
            response["message_action"   ] = "ADD_PORT_FAILED: " + str(sys.exc_info())
        # end try
        return response
    # end def

    def remove(self, params):
        call_id  = idgen._get_api_call_id()
        response = {
            "message_id"     : call_id,
            "message_action" : "REMOVE_PORT_SUCCESS",
            "message_code"   : "0",
            "message_title"  : "",
            "message_desc"   : "",
            "message_data"   : {}
        }
        try:
            pkey = params["pkey"]
            self.mgdDB.db_config_port.remove({ "pkey": pkey })
        except:
            self.webapp.logger.debug(traceback.format_exc())
            response["message_action"] = "REMOVE_PORT_FAILED"
            response["message_action"] = "REMOVE_PORT_FAILED: " + str(sys.exc_info())
        # end try

        return response
    # end def
# end class
