import asyncio

from src.game import Game


async def main() -> int:
    game = Game()
    await game.run_async()
    return 0


if __name__ == "__main__":
    asyncio.run(main())
