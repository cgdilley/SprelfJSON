from __future__ import annotations

import functools
import io
from typing import TextIO
from SprelfJSON.JSONDefinitions import JSONType, JSONable

YAMLError: type[Exception] | None = None


@functools.cache
def yaml():
    global YAMLError
    try:
        from ruamel.yaml import YAML, YAMLError as ye
        YAMLError = ye
        y = YAML(typ="safe")
        y.indent = 4
        y.encoding = "utf-8"
        y.default_flow_style = False
        return y
    except ImportError:
        raise ImportError("ruamel.yaml is required for YAML support.  Try install sprelf-json[yaml].")


def dumps(obj: JSONType | JSONable) -> str:
    with io.StringIO() as f:
        yaml().dump(jsonify(obj), f)
        return f.getvalue()


def dump(f: TextIO, obj: JSONType | JSONable) -> None:
    yaml().dump(jsonify(obj), f)


def load(s: str | TextIO, default: JSONType, raise_errors: bool = False) -> JSONType:
    try:
        return yaml().load(s)
    except YAMLError:
        if raise_errors:
            raise
        return default if default is not None else dict()


def loads(s: str | TextIO, default: JSONType, raise_errors: bool = False) -> JSONType:
    return load(s, default, raise_errors)


def jsonify(obj: JSONType | JSONable) -> JSONType:
    return obj.to_json() if isinstance(obj, JSONable) else obj
