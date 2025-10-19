from dataclasses import dataclass

@dataclass
class AudioTag:
    language: str
    title: str = "Unknown"

@dataclass
class AudioTrack:
    index: int
    codec_name: str
    tags: AudioTag
    channels: int = 2

    @classmethod
    def from_dict(cls, data: dict) -> "AudioTrack":
        tags_data = data.get("tags", {})
        return cls(
            index=data["index"],
            codec_name=data["codec_name"],
            tags=AudioTag(**tags_data),
            channels=data.get("channels", 2)
        )

@dataclass
class AudioStream:
    index: int
    channels: int = 2
    bitrate: str = "192"
    is_aac: bool = False
    title: str = "Unknown"
    lang: str = "UNK"
