import asyncio
import sys

from src.game import Game


async def main() -> int:
    game = Game()
    await game.run_async()
    return 0


if __name__ == "__main__":
    if "--editor" in sys.argv:
        from src.editor import LevelEditor

        raise SystemExit(LevelEditor().run())

    asyncio.run(main())
