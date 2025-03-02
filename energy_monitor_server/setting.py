import dataclasses


@dataclasses.dataclass
class Shelly:
    url: str
    api_key: str

    @staticmethod
    def from_dict(data: dict):
        return Shelly(
            url=data['url'],
            api_key=data['api_key']
        )


@dataclasses.dataclass
class Setting:
    user_id: str
    shelly: Shelly

    @staticmethod
    def from_dict(data: dict):
        return Setting(
            user_id=data['user_id'],
            shelly=Shelly.from_dict(data['shelly'])
        )
