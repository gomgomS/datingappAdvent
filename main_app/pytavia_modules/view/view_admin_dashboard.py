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

class view_admin_dashboard:

    mgdDB = database.get_db_conn(config.mainDB)

    def __init__(self, app):
        self.webapp = app
    # end def

    def html(self, params):
        # Get dashboard statistics
        stats = self._get_dashboard_stats()
        
        return render_template(
            "admin/dashboard.html",
            stats=stats,
            image_base_url=config.G_IMAGE_URL_DISPATCH
        )             
    # end def   

    def _get_dashboard_stats(self):
        """
        Get dashboard statistics
        """
        stats = {}
        
        # Total users count
        stats['total_users'] = self.mgdDB.db_users.count_documents({})
        
        # Verified users count
        stats['verified_users'] = self.mgdDB.db_users.count_documents({'verify_email': 'TRUE'})
        
        # Not verified users count
        stats['not_verified_users'] = self.mgdDB.db_users.count_documents({'verify_email': {'$ne': 'TRUE'}})
        
        # Premium users count
        stats['premium_users'] = self.mgdDB.db_users.count_documents({'is_premium': 'TRUE'})
        
        # Free users count
        stats['free_users'] = self.mgdDB.db_users.count_documents({'is_premium': {'$ne': 'TRUE'}})
        
        # Total matches count
        stats['total_matches'] = self.mgdDB.db_matches.count_documents({})
        
        # Mutual matches count
        stats['mutual_matches'] = self.mgdDB.db_matches.count_documents({'is_mutual': True})
        
        # Non-mutual matches count
        stats['non_mutual_matches'] = self.mgdDB.db_matches.count_documents({'is_mutual': {'$ne': True}})
        
        # Recent activity (last 7 days)
        seven_days_ago = datetime.now() - timedelta(days=7)
        stats['recent_users'] = self.mgdDB.db_users.count_documents({
            'rec_timestamp': {'$gte': seven_days_ago.strftime('%Y-%m-%d')}
        })
        
        stats['recent_matches'] = self.mgdDB.db_matches.count_documents({
            'created_at': {'$gte': seven_days_ago.strftime('%Y-%m-%d')}
        })
        
        # Calculate percentages
        if stats['total_users'] > 0:
            stats['verified_percentage'] = round((stats['verified_users'] / stats['total_users']) * 100, 1)
            stats['premium_percentage'] = round((stats['premium_users'] / stats['total_users']) * 100, 1)
        else:
            stats['verified_percentage'] = 0
            stats['premium_percentage'] = 0
            
        if stats['total_matches'] > 0:
            stats['mutual_percentage'] = round((stats['mutual_matches'] / stats['total_matches']) * 100, 1)
        else:
            stats['mutual_percentage'] = 0
        
        return stats

# end class
