from src.editor import LevelEditor


def main() -> int:
    editor = LevelEditor()
    return editor.run()


if __name__ == "__main__":
    raise SystemExit(main())
