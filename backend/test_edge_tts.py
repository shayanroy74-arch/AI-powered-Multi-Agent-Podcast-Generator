import asyncio
import edge_tts


async def generate_voice(text, voice, output_file):

    communicate = edge_tts.Communicate(
        text,
        voice
    )

    await communicate.save(output_file)

    print(f"Generated: {output_file}")


async def main():

    await generate_voice(
        "Hello and welcome to our podcast. Today we are discussing the future of artificial intelligence.",
        "en-US-GuyNeural",
        "host_edge.wav"
    )

    await generate_voice(
        "Thanks for having me. Artificial intelligence is developing rapidly and changing many industries.",
        "en-US-JennyNeural",
        "guest_edge.wav"
    )


if __name__ == "__main__":
    asyncio.run(main())