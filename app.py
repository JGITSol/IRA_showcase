"""Streamlit entry point delegating to the internal UI module."""

from app.streamlit_ui import main  # noqa: F401


if __name__ == "__main__":  # pragma: no cover
    main()