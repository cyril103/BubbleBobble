from dataclasses import dataclass

import pygame

from src.settings import HEIGHT, VECTOR_FIELD_CELL_SIZE, VECTOR_FIELD_DEFAULT_DIRECTION, WIDTH


@dataclass
class VectorField:
    cell_size: int
    columns: int
    rows: int
    vectors: list[list[pygame.Vector2]]

    @classmethod
    def upward(cls) -> "VectorField":
        columns = WIDTH // VECTOR_FIELD_CELL_SIZE
        rows = HEIGHT // VECTOR_FIELD_CELL_SIZE
        default_vector = pygame.Vector2(VECTOR_FIELD_DEFAULT_DIRECTION)
        vectors = [[default_vector.copy() for _column in range(columns)] for _row in range(rows)]
        return cls(VECTOR_FIELD_CELL_SIZE, columns, rows, vectors)

    @classmethod
    def from_json_data(cls, data: object) -> "VectorField":
        field = cls.upward()
        if not isinstance(data, dict):
            return field

        vectors = data.get("vectors")
        if not isinstance(vectors, list):
            return field

        for row_index, row in enumerate(vectors[: field.rows]):
            if not isinstance(row, list):
                continue
            for column_index, value in enumerate(row[: field.columns]):
                if not isinstance(value, list | tuple) or len(value) < 2:
                    continue
                x, y = value[:2]
                if not isinstance(x, int | float) or not isinstance(y, int | float):
                    continue
                field.set_cell_direction(column_index, row_index, pygame.Vector2(float(x), float(y)))
        return field

    def to_json_data(self) -> dict[str, object]:
        return {
            "cell_size": self.cell_size,
            "vectors": [
                [[round(vector.x, 3), round(vector.y, 3)] for vector in row]
                for row in self.vectors
            ],
        }

    def cell_at(self, point: pygame.Vector2 | tuple[float, float]) -> tuple[int, int]:
        x, y = point
        column = max(0, min(int(x // self.cell_size), self.columns - 1))
        row = max(0, min(int(y // self.cell_size), self.rows - 1))
        return column, row

    def cell_center(self, column: int, row: int) -> pygame.Vector2:
        return pygame.Vector2(
            column * self.cell_size + self.cell_size / 2,
            row * self.cell_size + self.cell_size / 2,
        )

    def set_cell_direction(self, column: int, row: int, direction: pygame.Vector2) -> None:
        if not 0 <= column < self.columns or not 0 <= row < self.rows:
            return
        if direction.length_squared() <= 0.001:
            direction = pygame.Vector2(VECTOR_FIELD_DEFAULT_DIRECTION)
        self.vectors[row][column] = direction.normalize()

    def direction_at(self, point: pygame.Vector2 | tuple[float, float]) -> pygame.Vector2:
        column, row = self.cell_at(point)
        direction = self.vectors[row][column]
        if direction.length_squared() <= 0:
            return pygame.Vector2()
        return direction.normalize()
