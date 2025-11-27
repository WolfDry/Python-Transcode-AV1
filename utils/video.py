""" Module for video-related utilities."""
from dataclasses import dataclass, fields
from typing import Optional

@dataclass
class VideoTrack:
    """Class representing video track."""
    pix_fmt: str
    width: int
    height: int
    r_frame_rate: str
    avg_frame_rate: str
    color_space: Optional[str] = None
    color_primaries: Optional[str] = None
    color_transfer: Optional[str] = None
    bit_rate: Optional[str] = None
    content_light_metadata: Optional[str] = None
    side_data_list: Optional[list] = None
    mastering_display_metadata: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> "VideoTrack":
        """Create a VideoTrack instance from a dictionary.

        Args:
            data (dict): dictionary containing video track information.

        Returns:
            VideoTrack: instance of VideoTrack
        """
        allowed_keys = {f.name for f in fields(cls)}
        filtered = {k: v for k, v in data.items() if k in allowed_keys}
        return cls(**filtered)

@dataclass
class TranscodeData:
    """Class representing transcoding data."""
    pix_fmt: str
    color_primaries: str
    color_transfer: str
    is_hdr: bool
    resolution: str
    framerate: float
    cq: str
    b_v: str
    maxrate: str
    bufsize: str
    tile_columns: str
    bitrate: int
    duration: float
    mastering_display_metadata: Optional[str]
