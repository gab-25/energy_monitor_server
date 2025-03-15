import firebase_admin
import asyncio
import firebase_admin.db
import websockets
import json
import requests
from firebase_admin import credentials, firestore, db, messaging
from energy_monitor_server.setting import Setting


class Connection:
    def __init__(self, uri: str, device_id: str, power_limit: int):
        self.uri = uri
        self.device_id = device_id
        self.power_limit = power_limit


def get_settings_by_user_id(user_id: str) -> Setting:
    settings_doc = settings_coll.document(user_id).get()
    return Setting.from_dict({"user_id": settings_doc.id, **settings_doc.to_dict()})


def refresh_token(user_id: str):
    settings = get_settings_by_user_id(user_id)
    try:
        response = requests.post(f"{settings.shelly_cloud.url}/oauth/auth", {
            "client_id": "shelly-diy",
            "grant_types":
            "code", "code": settings.shelly_cloud.refresh_token
        })
        if response.status_code == 200:
            response_json = response.json()
            settings.shelly_cloud.access_token = response_json['access_token']
            settings.shelly_cloud.refresh_token = response_json['refresh_token']
            settings.shelly_cloud.token_type = response_json['token_type']
            settings.shelly_cloud.expires_in = response_json['expires_in']
            print(f"update settings with new token, user_id: {user_id}", settings)
            settings_coll.document(user_id).set(settings.to_dict())
    except Exception as e:
        print(f"error on refresh token, user_id: {user_id}", e)


def send_notification_to_user(user_id, power):
    fcm_token = get_settings_by_user_id(user_id).fcm_token
    if fcm_token:
        print("send fcm message to user", user_id, "fcm_token", fcm_token)
        message = messaging.Message(
            notification=messaging.Notification(
                title="Attention",
                body=f"Power limit exceeded, current power: {power}W",
            ),
            token=fcm_token,
        )
        messaging.send(message)


async def connection_manager(user_id: str):
    connection: Connection = connections[user_id]
    db_states_ref = db.reference("states").child(user_id)

    print(f"connecting to {connection.uri} for user {user_id}")
    async with websockets.connect(connection.uri) as websocket:
        print(f"connected to shelly cloud for user {user_id}")
        db_states_ref.child("shelly_cloud_connected").set(True)
        while True:
            try:
                message = await websocket.recv()
                parsed_message = json.loads(message)
                if parsed_message['status']['mac'] == connection.device_id:
                    power: float = parsed_message["status"]["emeters"][0]["power"]
                    print("save data to firebase, power:", power, "user_id:", user_id)
                    db_states_ref.child("power").set(power)
                    if power > connection.power_limit:
                        send_notification_to_user(user_id, power)
            except websockets.ConnectionClosed as err:
                print(f"error on websocket: {err}, try refresh token and reconnecting...")
                db_states_ref.child("shelly_cloud_connected").set(False)
                await asyncio.sleep(10)
                refresh_token(user_id)


async def main():
    connections.clear()
    settings_docs = settings_coll.get()
    for setting_doc in settings_docs:
        setting = Setting.from_dict({"user_id": setting_doc.id, **setting_doc.to_dict()})
        shelly_server = setting.shelly_cloud.url.replace('https://', '')
        websocket_uri = f"wss://{shelly_server}:6113/shelly/wss/hk_sock?t={setting.shelly_cloud.access_token}"
        connections[setting.user_id] = Connection(
            uri=websocket_uri,
            device_id=setting.shelly_cloud.device_id,
            power_limit=setting.power.limit_value,
        )

    tasks = [connection_manager(user_id) for user_id in connections.keys()]
    await asyncio.gather(*tasks)


cred = credentials.Certificate("service_account_key.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://energy-monitor-63cd4-default-rtdb.europe-west1.firebasedatabase.app',
})
print(f'initialize firebase app')

settings_coll = firestore.client().collection('settings')
connections: dict[str, Connection] = {}

if __name__ == '__main__':
    asyncio.run(main())
