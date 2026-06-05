"""
tts/__main__.py
Entry point so `python -m tts` starts the TTS HTTP server (equivalent to
`python -m tts.server`). The systemd unit uses `python -m tts.server`; both
work and route through the same main().
"""

from __future__ import annotations

from tts.server import main

if __name__ == "__main__":
    main()
