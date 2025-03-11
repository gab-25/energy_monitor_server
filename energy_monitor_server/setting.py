import dataclasses


@dataclasses.dataclass
class ShellyCloud:
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int

    @staticmethod
    def from_dict(data: dict):
        return ShellyCloud(
            access_token=data['access_token'],
            refresh_token=data['refresh_token'],
            token_type=data['token_type'],
            expires_in=data['expires_in'],
        )


@dataclasses.dataclass
class Setting:
    user_id: str
    shelly_cloud: ShellyCloud

    @staticmethod
    def from_dict(data: dict):
        return Setting(
            user_id=data['user_id'],
            shelly_cloud=ShellyCloud.from_dict(data['shelly_cloud'])
        )
