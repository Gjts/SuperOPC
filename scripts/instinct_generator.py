"""Compatibility wrapper for the v2 instinct generator."""

from engine.instinct_generator import Instinct, InstinctGenerator, main

__all__ = ["Instinct", "InstinctGenerator", "main"]


if __name__ == "__main__":
    main()
