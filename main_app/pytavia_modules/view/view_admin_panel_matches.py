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

class view_admin_panel_matches:

    mgdDB = database.get_db_conn(config.mainDB)

    def __init__(self, app):
        self.webapp = app
    # end def

    def html(self, params):
        page = int(params.get('page', 1))
        per_page = int(params.get('per_page', 10))
        keyword = params.get('keyword')
        
        # Get all matches with user details
        matches_data = self._get_all_matches(page, per_page, keyword)
        
        # Get total count for pagination
        total_matches = self._get_total_matches_count(keyword)
        total_page = (total_matches // per_page) + (1 if total_matches % per_page != 0 else 0)

        return render_template(
            "admin/matches.html",
            data=matches_data,
            page=page,
            per_page=per_page,
            total_page=total_page,
            total_matches=total_matches,
            image_base_url=config.G_IMAGE_URL_DISPATCH
        )             
    # end def   

    def _get_all_matches(self, page, per_page, keyword=None):
        """
        Get all matches with user details for admin panel
        """
        skip = (page - 1) * per_page
        
        # Aggregation pipeline to get matches with user details
        pipeline = [
            {
                '$lookup': {
                    'from': 'db_users',
                    'localField': 'user_id_1',
                    'foreignField': 'user_id',
                    'as': 'user_1_details'
                }
            },
            {
                '$lookup': {
                    'from': 'db_users',
                    'localField': 'user_id_2',
                    'foreignField': 'user_id',
                    'as': 'user_2_details'
                }
            },
            {
                '$unwind': '$user_1_details'
            },
            {
                '$unwind': '$user_2_details'
            },
            {
                '$project': {
                    '_id': 0,
                    'match_id': 1,
                    'is_mutual': 1,
                    'created_at': 1,
                    'user_1': {
                        'user_id': '$user_1_details.user_id',
                        'name': '$user_1_details.name',
                        'email': '$user_1_details.email',
                        'username': '$user_1_details.username',
                        'profile_photo': '$user_1_details.profile_photo',
                        'city': '$user_1_details.city',
                        'sex': '$user_1_details.sex'
                    },
                    'user_2': {
                        'user_id': '$user_2_details.user_id',
                        'name': '$user_2_details.name',
                        'email': '$user_2_details.email',
                        'username': '$user_2_details.username',
                        'profile_photo': '$user_2_details.profile_photo',
                        'city': '$user_2_details.city',
                        'sex': '$user_2_details.sex'
                    }
                }
            },
            {
                '$sort': {'created_at': -1}
            }
        ]
        
        # Add keyword search if provided (after lookups and projection)
        if keyword:
            rgx = re.compile(f'.*{keyword}.*', re.IGNORECASE)
            pipeline.append({
                '$match': {
                    '$or': [
                        {'user_1.name': rgx},
                        {'user_1.email': rgx},
                        {'user_1.username': rgx},
                        {'user_2.name': rgx},
                        {'user_2.email': rgx},
                        {'user_2.username': rgx}
                    ]
                }
            })
        
        # Add pagination
        pipeline.extend([
            {'$skip': skip},
            {'$limit': per_page}
        ])
        
        # Execute aggregation
        matches = list(self.mgdDB.db_matches.aggregate(pipeline))
        
        return matches

    def _get_total_matches_count(self, keyword=None):
        """
        Get total count of matches for pagination
        """
        pipeline = [
            {
                '$lookup': {
                    'from': 'db_users',
                    'localField': 'user_id_1',
                    'foreignField': 'user_id',
                    'as': 'user_1_details'
                }
            },
            {
                '$lookup': {
                    'from': 'db_users',
                    'localField': 'user_id_2',
                    'foreignField': 'user_id',
                    'as': 'user_2_details'
                }
            },
            {
                '$unwind': '$user_1_details'
            },
            {
                '$unwind': '$user_2_details'
            },
            {
                '$project': {
                    '_id': 0,
                    'user_1': {
                        'name': '$user_1_details.name',
                        'email': '$user_1_details.email',
                        'username': '$user_1_details.username'
                    },
                    'user_2': {
                        'name': '$user_2_details.name',
                        'email': '$user_2_details.email',
                        'username': '$user_2_details.username'
                    }
                }
            }
        ]
        
        # Add keyword search if provided (after lookups and projection)
        if keyword:
            rgx = re.compile(f'.*{keyword}.*', re.IGNORECASE)
            pipeline.append({
                '$match': {
                    '$or': [
                        {'user_1.name': rgx},
                        {'user_1.email': rgx},
                        {'user_1.username': rgx},
                        {'user_2.name': rgx},
                        {'user_2.email': rgx},
                        {'user_2.username': rgx}
                    ]
                }
            })
        
        # Add count stage
        pipeline.append({'$count': 'total'})
        
        result = list(self.mgdDB.db_matches.aggregate(pipeline))
        return result[0]['total'] if result else 0

# end class
