import dataclasses


@dataclasses.dataclass
class ShellyCloud:
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    url: str
    device_id: str

    @staticmethod
    def from_dict(data: dict):
        return ShellyCloud(
            access_token=data['access_token'],
            refresh_token=data['refresh_token'],
            token_type=data['token_type'],
            expires_in=data['expires_in'],
            url=data['url'],
            device_id=data['device_id'],
        )


@dataclasses.dataclass
class Power:
    limit_value: int
    max_value: int

    @staticmethod
    def from_dict(data: dict):
        return Power(
            limit_value=data['limit_value'],
            max_value=data['max_value']
        )


@dataclasses.dataclass
class Setting:
    user_id: str
    shelly_cloud: ShellyCloud
    power: Power

    @staticmethod
    def from_dict(data: dict):
        return Setting(
            user_id=data['user_id'],
            shelly_cloud=ShellyCloud.from_dict(data['shelly_cloud']),
            power=Power.from_dict(data['power'])
        )
