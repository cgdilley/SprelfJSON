# # This is largely based on implementation of standard library's namedtuple:
# # https://gist.github.com/malcolmgreaves/a8ff32e814053f805ba9c0aae380771c
#
# MODEL_TEMPLATE = \
# """
# class {typename}({parent}{opt_generic}):
#     '{typename}({annotated_args})'
#
#     __slots__ = ()
#
#     _fields = {field_names!r}
#
#     def __init__(self, {annotated_args}):
#         'Create a new instance of {typename}'
#         return JSONModel.__init__(self, **{args_as_dict})
#
#     def __repr__(self):
#         return "{typename}(" + {parts} + ")"
# """