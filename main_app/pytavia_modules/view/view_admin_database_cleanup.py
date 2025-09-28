from pytavia_core import config
from pytavia_core import database
from flask import render_template
import json

class view_admin_database_cleanup:
    
    mgdDB = database.get_db_conn(config.mainDB)

    def __init__(self, app):
        self.webapp = app
    # end def

    def html(self, params):
        try:
            # Get counts for each collection
            users_count = self.mgdDB.db_users.count_documents({})
            matches_count = self.mgdDB.db_matches.count_documents({})
            chat_count = self.mgdDB.db_chat.count_documents({})
            swipe_logs_count = self.mgdDB.db_swipe_logs_daily.count_documents({})
            
            # Get users with likes/dislikes
            users_with_likes = self.mgdDB.db_users.count_documents({"fk_user_id_like": {"$exists": True, "$ne": []}})
            users_with_dislikes = self.mgdDB.db_users.count_documents({"fk_user_id_dislike": {"$exists": True, "$ne": []}})
            
            data = {
                "users_count": users_count,
                "matches_count": matches_count,
                "chat_count": chat_count,
                "swipe_logs_count": swipe_logs_count,
                "users_with_likes": users_with_likes,
                "users_with_dislikes": users_with_dislikes
            }
            
            return render_template(
                "admin/database_cleanup.html",
                data=data,
                image_base_url=config.G_IMAGE_URL_DISPATCH
            )
            
        except Exception as e:
            return render_template(
                "admin/database_cleanup.html",
                error=f"Error loading database cleanup page: {str(e)}",
                data={},
                image_base_url=config.G_IMAGE_URL_DISPATCH
            )
    # end def
