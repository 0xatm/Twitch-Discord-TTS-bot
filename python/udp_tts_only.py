import asyncio
import socketserver
import string
from typing import Optional

from loguru import logger

from python.profanity_filter import nonowords
from python.text_to_speech import text_to_speech_and_play


# Checks the filtered list to sort out words that you wish not to be said
def check_filter(text) -> Optional[str]:
    msg = text.translate(str.maketrans("", "", string.punctuation)).lower().split()

    if not msg:
        logger.warning("Received empty message.")
        return None

    detected_words = [word for word in msg if word in nonowords]

    if detected_words:
        logger.warning(f"Detected profanity:\t{', '.join(detected_words)}")
        return "Let's not say that."
    else:
        logger.debug(f"Message passed filter:\t'{text}'")
        return text


# The UDP Handler for interfacing with streamer.bot
class MyUDPHandler(socketserver.DatagramRequestHandler):
    def handle(self):
        msgRecvd = self.rfile.readline().strip()
        msg = msgRecvd.decode("utf-8").lower()
        logger.info(f"Message received:\t'{msgRecvd.decode('utf-8')}'")
        text = check_filter(msg)
        asyncio.run(text_to_speech_and_play(text))


def main():
    listen_addr = ("0.0.0.0", 414)
    socketserver.UDPServer.allow_reuse_address = True
    serverUDP = socketserver.UDPServer(listen_addr, MyUDPHandler)
    logger.info("UDP server running. Waiting for messages...")
    serverUDP.serve_forever()


if __name__ == "__main__":
    # You can test the UDP server by sending messages to it using a tool like netcat:
    # echo "Hello, world!" | nc -u 127.0.0.1 414
    main()
