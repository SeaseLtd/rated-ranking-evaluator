## Code Quality Tools

This project uses:

* [Ruff](https://github.com/astral-sh/ruff) for linting.
* [Mypy](https://mypy.readthedocs.io/) for static type checking.

### Linting with Ruff

```bash
# Check for issues
uv run ruff check .

# Auto-fix fixable issues
uv run ruff check --fix .

# Format code (if enabled)
uv run ruff format .
```

### Type Checking with Mypy

```bash
# Run type checking
uv run mypy .
```

**Config Files**

* `ruff.toml`: Ruff linting rules and settings.
* `mypy.ini`: Mypy type checking rules and settings.

---