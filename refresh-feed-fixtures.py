"""Replace fixtures/model-feeds from the current engine.

Tests never run this. Review the resulting diff before keeping it.

    python refresh-feed-fixtures.py
"""
import test_model_feeds


def main():
    test_model_feeds.write_fixtures(test_model_feeds.load_engine())
    print(f"wrote {test_model_feeds.FIXTURES}")


if __name__ == "__main__":
    main()
