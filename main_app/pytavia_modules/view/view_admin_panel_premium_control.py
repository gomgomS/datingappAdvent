import sys
import traceback
import time
import json
import datetime
import statistics
from bson import Int64
from datetime import datetime, timedelta
import re

sys.path.append("pytavia_core"    )
sys.path.append("pytavia_modules" )
sys.path.append("pytavia_settings")
sys.path.append("pytavia_stdlib"  )
sys.path.append("pytavia_storage" )
sys.path.append("pytavia_modules/view" )

from flask          import render_template
from flask          import session
from pytavia_stdlib import idgen
from pytavia_stdlib import utils
from pytavia_core   import database
from pytavia_core   import config

from view import view_core_menu
from view import view_core_display
from view import view_core_header
from view import view_core_footer
from view import view_core_script
from view import view_core_css
from view import view_core_dialog_message

class view_admin_panel_premium_control:

    mgdDB = database.get_db_conn(config.mainDB)

    def __init__(self, app):
        self.webapp = app
    # end def

    def html(self, params):
        page = int(params.get('page', 1))
        per_page = int(params.get('per_page', 10))
        keyword = params.get('keyword')
        query = {}

        if keyword:
            rgx = re.compile(f'.*{keyword}.*', re.IGNORECASE)
            query['$or'] = [
                {'username': rgx},
                {'name': rgx},
                {'email': rgx}
            ]
        
        exec_command = self.mgdDB.db_users.find(query)
        numb_recs = exec_command.count()
        user_records = exec_command.skip((page - 1) * per_page).limit(per_page)
        
        result = []
        for user in user_records:
            expiry_str = user.get("premium_expiry", "")
            expiry_date = None
            countdown_days = ""
            formatted_expiry = ""

            if expiry_str:
                try:
                    expiry_date = datetime.strptime(expiry_str, "%Y-%m-%d %H:%M:%S")
                    now = datetime.now()
                    days_left = (expiry_date - now).days
                    countdown_days = f"{days_left} day(s)" if days_left >= 0 else "expired"
                    formatted_expiry = expiry_date.strftime("%d %B %Y")  # 29 June 2025
                except:
                    countdown_days = "invalid date"
                    formatted_expiry = expiry_str

            i = {
                'user_id': user.get('user_id'),
                'username': user.get('username', ''),
                'email': user.get('email', ''),                
                'is_premium': user.get('is_premium', ''),
                'name': user.get('name', ''),
                'premium_expiry': formatted_expiry,
                'premium_countdown': countdown_days,
                'subscription_type': user.get('subscription_type', ''),
            }
            result.append(i)


        total_page = (numb_recs // per_page) + (1 if numb_recs % per_page != 0 else 0)

        return render_template(
            "admin/premium_control.html",
            data=result,
            page=page,
            per_page=per_page,
            total_page=total_page,
            image_base_url=config.G_IMAGE_URL_DISPATCH
        )             
    # end def   

# end class
