import firebase_admin
import base64
import asyncio
import firebase_admin.db
import websockets
import json
from firebase_admin import credentials, firestore, db
from energy_monitor_server.setting import Setting


async def main():
    cred = credentials.Certificate("service_account_key.json")
    app = firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://energy-monitor-63cd4-default-rtdb.europe-west1.firebasedatabase.app',
    })
    print(f'initialize firebase app {app.project_id}')

    settings_collection = firestore.client(app).collection('settings')
    settings_docs = settings_collection.get()
    for setting_doc in settings_docs:
        setting = Setting.from_dict({"user_id": setting_doc.id, **setting_doc.to_dict()})
        user_metadata: dict = json.loads(base64.b64decode(
            setting.shelly_cloud.access_token.split('.')[1]).decode('utf-8'))

        shelly_server = str(user_metadata['user_api_url']).replace('https://', '')
        websocket_url = f"wss://{shelly_server}:6113/shelly/wss/hk_sock?t={setting.shelly_cloud.access_token}"
        print(f"connecting to {shelly_server} for user {setting.user_id}")
        async for websocket in websockets.connect(websocket_url):
            print(f"connected to shelly cloud")
            try:
                async for message in websocket:
                    parsed_message = json.loads(message)
                    print("received message:", parsed_message, "user_id:", setting.user_id)
                    if "emeters" in parsed_message["status"]:
                        power = parsed_message["status"]["emeters"][0]["power"]
                        print("save data to firebase, power:", power, "user_id:", setting.user_id)
                        db.reference("states").child(setting.user_id).set({"power": power})
            except websockets.ConnectionClosed as err:
                print(f"error on websocket: {err}, reconnecting...")
                continue


if __name__ == '__main__':
    asyncio.run(main())
