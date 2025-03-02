import firebase_admin
import websocket
from firebase_admin import credentials, firestore
from energy_monitor_server.setting import Setting


def main():
    cred = credentials.Certificate("service_account_key.json")
    app = firebase_admin.initialize_app(cred)
    print(f'initialize firebase app {app.project_id}')

    settings_collection = firestore.client(app).collection('settings')
    settings_doc = settings_collection.get()
    for setting_doc in settings_doc:
        setting = Setting.from_dict(setting_doc.to_dict())


if __name__ == '__main__':
    main()
