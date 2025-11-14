"""
Data classes for representing audio stream and track information.
"""

from dataclasses import dataclass

@dataclass
class AudioTag:
    """Class representing audio track tags."""
    language: str
    title: str = "Unknown"

@dataclass
class AudioTrack:
    """Class representing an audio track."""
    index: int
    codec_name: str
    tags: AudioTag
    channels: int = 2
    bit_rate: int = 0

    @classmethod
    def from_dict(cls, data: dict) -> "AudioTrack":
        """Create an AudioTrack instance from a dictionary.

        Args:
            data (dict): dictionary containing audio track information.

        Returns:
            AudioTrack: instance of AudioTrack
        """
        tags_data = data.get("tags", {})
        return cls(
            index=data["index"],
            codec_name=data["codec_name"],
            tags=AudioTag(**tags_data),
            channels=data.get("channels", 2),
            bit_rate=data.get("bit_rate", 0)
        )

@dataclass
class AudioStream:
    """Class representing an audio stream."""
    index: int
    channels: int = 2
    bitrate: str = "192"
    is_aac: bool = False
    title: str = "Unknown"
    lang: str = "UNK"
