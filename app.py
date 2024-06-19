from enum import Enum

from flask import Flask, jsonify, render_template, make_response
from flask_restful import Resource, Api
import requests
from datetime import datetime, timedelta

app = Flask(__name__, static_folder='static')
api = Api(app)


class COURSES(Enum):
    WILLIS_CASE = 3833


# Constants
DAYS_TO_SEARCH = 13
MAX_TEE_TIME = 390
GOLF_CLUB_IDS = [COURSES.WILLIS_CASE.value]

BOOK_URL = "https://app.membersports.com/tee-times/3833/4932/0/1/0"


class TeeTimes(Resource):
    def get(self):
        url = 'https://api.membersports.com/api/v1/golfclubs/onlineBookingTeeTimes'
        headers = {
            'accept': 'application/json',
            'accept-language': 'en-US,en;q=0.9',
            'content-type': 'application/json; charset=UTF-8',
            'dnt': '1',
            'origin': 'https://app.membersports.com',
            'priority': 'u=1, i',
            'referer': 'https://app.membersports.com/',
            'sec-ch-ua': '"Not/A)Brand";v="8", "Chromium";v="126"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'
        }

        # Start from tomorrow
        start_date = datetime.now() + timedelta(days=1)
        filtered_tee_times = []

        for i in range(DAYS_TO_SEARCH):
            date = start_date + timedelta(days=i)
            date_str = date.strftime('%Y-%m-%d')
            formatted_date = date.strftime('%A, %B %d, %Y')
            data = {
                "configurationTypeId": 0,
                "date": date_str,
                "golfClubGroupId": 1,
                "groupSheetTypeId": 0,
                "memberProfileId": 420662
            }

            response = requests.post(url, headers=headers, json=data)
            tee_times = response.json()

            # filtered_tee_times = []
            for tee_time_group in tee_times:
                for item in tee_time_group['items']:
                    if (
                            item['allowSinglesToBookOnline'] and
                            item['holesRequirementTypeId'] == 1 and
                            item['teeTime'] <= MAX_TEE_TIME and
                            item['golfClubId'] in GOLF_CLUB_IDS
                    ):
                        filtered_tee_times.append({
                            'date': formatted_date,
                            'time': f"{tee_time_group['teeTime'] // 60}:{tee_time_group['teeTime'] % 60:02d}",
                            'course': item['name'],
                            'spotsAvailable': 4 - item['playerCount'],
                            'singleAllowed': item['playerCount'] > 0,
                            'golfClubId': item['golfClubId'],
                            'link': BOOK_URL
                        })

        return jsonify(filtered_tee_times)


class TeeTimesPage(Resource):
    def get(self):
        tee_times = TeeTimes().get().json

        headers = {'Content-Type': 'text/html'}
        return make_response(render_template('tee_times.html', tee_times=tee_times), 200,
                             headers)


api.add_resource(TeeTimes, '/get_tee_times')
api.add_resource(TeeTimesPage, '/tee_times')

if __name__ == '__main__':
    app.run(debug=True)
