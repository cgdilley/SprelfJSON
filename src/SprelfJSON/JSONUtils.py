from SprelfJSON.JSONDefinitions import JSONObject, JSONValue, JSONType, JSONArray, JSONContainer, FieldPath


def get(o: JSONValue, path: FieldPath, default: JSONType = None):
    """
    Retrieves the value at the specified field path in the given JSON object, if it exists.  If not
    found, will return the given default value instead.  Components of the field path can either be
    strings (to get keys from an object) or integers (to get elements from an array).  Field path
    may be given either as a tuple of fields to navigate, or a single string where each field
    is separated by a (.) period.

    :param o: The JSON value to extract the value from.
    :param path: The path at which to extract the value.
    :param default: Optional.  The default value to return if unsuccessful in finding the specified field.
    Defaults to None.
    :return: The extract value, or the default value if not successful.
    """
    if isinstance(path, str):
        path = tuple(path.split("."))
    if len(path) == 0:
        return o
    if isinstance(o, JSONValue):
        return default
    curr, *rest = path
    if isinstance(o, list):
        if not isinstance(curr, int):
            try:
                curr = int(curr)
            except ValueError:
                return default
        if not (0 <= curr < len(o)):
            return default
        return get(o[curr], rest, default)
    elif isinstance(o, dict):
        if not isinstance(curr, str):
            return default
        if curr not in o:
            return default
        return get(o[curr], rest, default)
