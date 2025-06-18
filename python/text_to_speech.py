import asyncio
import tempfile
import os

from loguru import logger
from decouple import config
import boto3
from botocore.response import StreamingBody
from mypy_boto3_polly import PollyClient  # Type hints for Polly client from boto3-stubs
from mypy_boto3_polly.type_defs import SynthesizeSpeechOutputTypeDef
import playsound3
from playsound3.playsound3 import Sound


AWS_TOKEN = config("AWS_TOKEN")
AWS_PRIVATE_TOKEN = config("AWS_PRIVATE_TOKEN")


def _aws_text_to_speech(
        text: str,
        aws_token: str = AWS_TOKEN,
        aws_private_token: str = AWS_PRIVATE_TOKEN,
) -> bytes:
    """
    Convert text to speech using AWS Polly and return audio bytes.
    Args:
        text (str): The text to convert to speech.
    Returns:
        bytes: The audio data as bytes, in MP3 format.
    Raises:
        ValueError: If the audio stream is empty.
    """

    if not text:
        raise ValueError("Input text cannot be empty.")
    if not aws_token or not aws_private_token:
        raise ValueError("AWS credentials are not set. Please check your environment variables.")

    logger.debug(f"Converting text to audio:\t{text}")

    # Create a session with AWS credentials, and initialize the Polly client
    session = boto3.Session(
        aws_access_key_id=aws_token,
        aws_secret_access_key=aws_private_token,
        region_name="us-east-1",
    )
    polly: PollyClient = session.client("polly")

    # Synthesize speech from the text via AWS Polly
    response: SynthesizeSpeechOutputTypeDef = polly.synthesize_speech(
        Text=text, OutputFormat="mp3", VoiceId="Justin", Engine="neural"
    )

    # Check if the response contains an audio stream
    audio_stream: StreamingBody = response.get("AudioStream")
    if audio_stream is None:
        raise ValueError("Audio stream is empty. Please check the input text.")
    audio_bytes = audio_stream.read()
    logger.debug(f"Received audio data of length: {len(audio_bytes)} bytes")

    return audio_bytes


async def _aws_text_to_speech_async(text: str) -> bytes:
    """
    Asynchronous wrapper for aws_text_to_speech to allow for non-blocking calls.
    Args:
        text (str): The text to convert to speech.
    Returns:
        bytes: The audio data as bytes, in MP3 format.
    """
    loop = asyncio.get_event_loop()
    # Use run_in_executor, which defaults to ThreadPoolExecutor, to run the blocking function in a separate thread
    return await loop.run_in_executor(None, _aws_text_to_speech, text)


async def _write_audio_to_file(audio_bytes: bytes, file_path: str) -> None:
    """
    Write audio bytes to a file.
    Args:
        audio_bytes (bytes): The audio data to write.
        file_path (str): The path where the audio file will be saved.
    """
    try:
        with open(file_path, "wb") as audio_file:
            audio_file.write(audio_bytes)
        logger.debug(f"Audio data written to {file_path}")
    except Exception as e:
        logger.error(f"Failed to write audio to file: {e}")
        raise


async def _play_audio(audio_bytes: bytes) -> None:
    """
    Play audio bytes using a temporary file.
    Args:
        audio_bytes (bytes): The audio data to play.
    Raises:
        ValueError: If the audio bytes are empty.
        Exception: If playback fails.
    """
    temp_file_path = None
    if not audio_bytes:
        raise ValueError("Audio bytes cannot be empty.")
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_file:
            temp_file.write(audio_bytes)
            temp_file_path = temp_file.name

        playback_controller: Sound = playsound3.playsound(temp_file_path, block=False)
        while playback_controller.is_alive():
            await asyncio.sleep(0.1)
    except Exception as e:
        logger.error(f"Audio playback failed: {e}")
        raise
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)


async def text_to_speech_and_save(text: str, file_path: str) -> None:
    """
    Convert text to speech and save the audio to a file.
    Args:
        text (str): The text to convert to speech.
        file_path (str): The path where the audio file will be saved.
    """
    try:
        if not text:
            raise ValueError("Input text cannot be empty.")
        if not file_path.endswith(".mp3"):
            raise ValueError("File path must end with .mp3 extension.")

        audio_data = await _aws_text_to_speech_async(text)
        await _write_audio_to_file(audio_data, file_path)
    except Exception as e:  # Broad exceptions are not great but we're oversimplifying
        logger.error(f"Failed to convert text to speech and save to file: {e}")
        raise


async def text_to_speech_and_play(text: str) -> None:
    """
    Convert text to speech and play the audio.
    Args:
        text (str): The text to convert to speech.
    """
    try:
        if not text:
            raise ValueError("Input text cannot be empty.")
        audio_data = await _aws_text_to_speech_async(text)
        await _play_audio(audio_data)
    except Exception as e:
        logger.error(f"Failed to convert text to speech and play audio: {e}")
        raise



if __name__ == "__main__":
    # Example usage
    example_text = "Hello, this is a test of the AWS Polly text-to-speech service."
    asyncio.run(text_to_speech_and_play(example_text))
