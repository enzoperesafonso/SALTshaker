import saltshaker


def test_public_api_is_importable():
    for name in saltshaker.__all__:
        assert hasattr(saltshaker, name), name


def test_version_is_a_string():
    assert isinstance(saltshaker.__version__, str)
