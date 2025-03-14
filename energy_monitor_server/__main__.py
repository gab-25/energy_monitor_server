import firebase_admin
import base64
import asyncio
import firebase_admin.db
import websockets
import json
from firebase_admin import credentials, firestore, db
from energy_monitor_server.setting import Setting


async def connection_manager(connection: dict):
    user_id = connection["user_id"]
    uri = connection["uri"]
    device_id = connection["device_id"]

    db_states_ref = db.reference("states").child(user_id)
    print(f"connecting to {uri} for user {user_id}")

    async with websockets.connect(uri) as websocket:
        print(f"connected to shelly cloud for user {user_id}")
        db_states_ref.child("shelly_cloud_connected").set(True)
        while True:
            try:
                message = await websocket.recv()
                parsed_message = json.loads(message)
                if parsed_message['status']['mac'] == device_id:
                    power = parsed_message["status"]["emeters"][0]["power"]
                    print("save data to firebase, power:", power, "user_id:", user_id)
                    db_states_ref.child("power").set(power)
            except websockets.ConnectionClosed as err:
                print(f"error on websocket: {err}, reconnecting...")
                db_states_ref.child("shelly_cloud_connected").set(False)
                await asyncio.sleep(10)


async def main():
    cred = credentials.Certificate("service_account_key.json")
    app = firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://energy-monitor-63cd4-default-rtdb.europe-west1.firebasedatabase.app',
    })
    print(f'initialize firebase app {app.project_id}')

    settings_collection = firestore.client(app).collection('settings')
    settings_docs = settings_collection.get()

    connections = []
    for setting_doc in settings_docs:
        setting = Setting.from_dict({"user_id": setting_doc.id, **setting_doc.to_dict()})
        shelly_server = setting.shelly_cloud.url.replace('https://', '')
        websocket_uri = f"wss://{shelly_server}:6113/shelly/wss/hk_sock?t={setting.shelly_cloud.access_token}"
        connections.append({
            "user_id": setting.user_id,
            "uri": websocket_uri,
            "device_id": setting.shelly_cloud.device_id
        })

    tasks = [connection_manager(connection) for connection in connections]
    await asyncio.gather(*tasks)


if __name__ == '__main__':
    asyncio.run(main())
