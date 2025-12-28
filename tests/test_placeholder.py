def test_environment_works():
    """Verify that pytest is running correctly."""
    assert True

def test_package_import():
    """Verify that we can import the package."""
    try:
        import saltshaker
        assert True
    except ImportError:
        # If this fails, it means the package isn't installed in the CI env
        assert False, "Package saltshaker could not be imported"
