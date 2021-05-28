import inspect
import types

f_found = {}


class PickleSerializer:
    @staticmethod
    def is_cls_instance(obj):
        return hasattr(obj, "__dict__") or inspect.isroutine(obj) or inspect.isclass(obj)

    @staticmethod
    def dict_to_module(obj):
        try:
            return __import__(obj)
        except ModuleNotFoundError:
            raise ImportError(str(obj) + " not found")

    @staticmethod
    def dict_to_class(obj):
        return type(obj["name"], obj["bases"], obj["dict"])

    @staticmethod
    def dict_to_code(obj):
        return types.CodeType(
            obj["co_argcount"],
            obj["co_posonlyargcount"],
            obj["co_kwonlyargcount"],
            obj["co_nlocals"],
            obj["co_stacksize"],
            obj["co_flags"],
            obj["co_code"],
            obj["co_consts"],
            obj["co_names"],
            obj["co_varnames"],
            obj["co_filename"],
            obj["co_name"],
            obj["co_firstlineno"],
            obj["co_lnotab"],
            obj["co_freevars"],
            obj["co_cellvars"],
        )

    @staticmethod
    def get_funcs(obj, visited):
        for i in obj.__globals__:
            attr = obj.__globals__[i]
            if inspect.isfunction(attr) and attr.__name__ not in visited:
                visited[attr.__name__] = attr
                visited = PickleSerializer.get_funcs(attr, visited)
        return visited

    @staticmethod
    def set_funcs(gls):
        for gl in gls.values():
            gl.__globals__.update(gls)

    @staticmethod
    def dict_to_func(obj):
        func = types.FunctionType(
            globals=PickleSerializer.parse(obj["__globals__"]),
            code=PickleSerializer.parse(obj["__code__"]),
            name=obj["__name__"],
            argdefs=obj["__defaults__"],
        )

        funcs = PickleSerializer.get_funcs(func, {func.__name__: func})
        PickleSerializer.set_funcs(funcs)
        func.__globals__["__builtins__"] = __import__("builtins")
        return func

    @staticmethod
    def class_to_dict(cls):
        depends = []
        if len(cls.__bases__) != 0:
            for i in cls.__bases__:
                if i.__name__ != "object":
                    depends.append(PickleSerializer.class_to_dict(i))
        args = {}
        cls_dict = dict(cls.__dict__)
        if len(cls_dict) != 0:
            for i in cls_dict:
                if inspect.isclass(cls_dict[i]):
                    args[i] = PickleSerializer.class_to_dict(cls_dict[i])
                elif inspect.isfunction(cls_dict[i]):
                    if cls_dict[i] not in f_found:
                        args[i] = PickleSerializer.function_to_dict(cls_dict[i])
                elif isinstance(cls_dict[i], staticmethod):
                    if cls_dict[i].__func__ not in f_found:
                        args[i] = PickleSerializer.staticmethod_to_dict(cls_dict[i])
                elif isinstance(cls_dict[i], classmethod):
                    if cls_dict[i].__func__ not in f_found:
                        args[i] = PickleSerializer.classmethod_to_dict(cls_dict[i])
                elif inspect.ismodule(cls_dict[i]):
                    args[i] = PickleSerializer.module_to_dict(cls_dict[i])
                elif PickleSerializer.is_cls_instance(cls_dict[i]):
                    args[i] = PickleSerializer.instance_to_dict(cls_dict[i])
                elif isinstance(cls_dict[i], (set, dict, list, int, float, bool, type(None), tuple)):
                    args[i] = cls_dict[i]
        return {"--class_type--": {"name": cls.__name__, "bases": tuple(depends), "dict": args}}

    @staticmethod
    def instance_to_dict(obj):
        return {
            "--instance_type--": {
                "class": PickleSerializer.class_to_dict(obj.__class__),
                "vars": obj.__dict__,
            }
        }

    @staticmethod
    def module_to_dict(obj):
        return {"--module_type--": obj.__name__}

    @staticmethod
    def gather_gls(obj, obj_code):
        global f_found
        f_found[obj] = True
        gls = {}
        for i in obj_code.co_names:
            try:
                if inspect.isclass(obj.__globals__[i]):
                    gls[i] = PickleSerializer.class_to_dict(obj.__globals__[i])
                elif inspect.isfunction(obj.__globals__[i]):
                    if obj.__globals__[i] not in f_found:
                        gls[i] = PickleSerializer.function_to_dict(obj.__globals__[i])
                elif isinstance(obj.__globals__[i], staticmethod):
                    if obj.__globals__[i].__func__ not in f_found:
                        gls[i] = PickleSerializer.staticmethod_to_dict(obj.__globals__[i])
                elif isinstance(obj.__globals__[i], classmethod):
                    if obj.__globals__[i].__func__ not in f_found:
                        gls[i] = PickleSerializer.classmethod_to_dict(obj.__globals__[i])
                elif inspect.ismodule(obj.__globals__[i]):
                    gls[i] = PickleSerializer.module_to_dict(obj.__globals__[i])
                elif PickleSerializer.is_cls_instance(obj.__globals__[i]):
                    gls[i] = PickleSerializer.instance_to_dict(obj.__globals__[i])
                elif isinstance(
                        obj.__globals__[i], (set, dict, list, int, float, bool, type(None), tuple, str)
                ):
                    gls[i] = obj.__globals__[i]
            except KeyError:
                pass
        for i in obj_code.co_consts:
            if isinstance(i, types.CodeType):
                gls.update(PickleSerializer.gather_gls(obj, i))
        return gls

    @staticmethod
    def staticmethod_to_dict(obj):
        return {"--static_method_type--": PickleSerializer.function_to_dict(obj.__func__)}

    @staticmethod
    def classmethod_to_dict(obj):
        return {"--class_method_type--": PickleSerializer.function_to_dict(obj.__func__)}

    @staticmethod
    def function_to_dict(obj):
        gls = PickleSerializer.gather_gls(obj, obj.__code__)

        return {
            "--function_type--": {
                "__globals__": gls,
                "__name__": obj.__name__,
                "__code__": PickleSerializer.code_to_dict(obj.__code__),
                "__defaults__": obj.__defaults__,
            }
        }

    @staticmethod
    def code_to_dict(obj):
        return {
            "--code_type--": {
                "co_argcount": obj.co_argcount,
                "co_posonlyargcount": obj.co_posonlyargcount,
                "co_kwonlyargcount": obj.co_kwonlyargcount,
                "co_nlocals": obj.co_nlocals,
                "co_stacksize": obj.co_stacksize,
                "co_flags": obj.co_flags,
                "co_code": obj.co_code,
                "co_consts": PickleSerializer.convert(obj.co_consts),
                "co_names": obj.co_names,
                "co_varnames": obj.co_varnames,
                "co_filename": obj.co_filename,
                "co_name": obj.co_name,
                "co_firstlineno": obj.co_firstlineno,
                "co_lnotab": obj.co_lnotab,
                "co_freevars": obj.co_freevars,
                "co_cellvars": obj.co_cellvars,
            }
        }

    @staticmethod
    def convert(obj):
        if isinstance(obj, (str, int, float, bool, frozenset)) or obj is None:
            return obj
        elif isinstance(obj, list):
            for i in range(len(obj)):
                obj[i] = PickleSerializer.convert(obj[i])
            return obj
        elif isinstance(obj, set):
            obj = list(obj)
            for i in range(len(obj)):
                obj[i] = PickleSerializer.convert(obj[i])
            return set(obj)
        elif isinstance(obj, tuple):
            obj = list(obj)
            return tuple(obj)
        elif isinstance(obj, dict):
            res = {}
            for i in obj:
                res[i] = PickleSerializer.convert(obj[i])
            return res
        elif inspect.isfunction(obj):
            res = PickleSerializer.function_to_dict(obj)
            return res
        elif isinstance(obj, staticmethod):
            res = PickleSerializer.staticmethod_to_dict(obj)
            return res
        elif isinstance(obj, classmethod):
            res = PickleSerializer.classmethod_to_dict(obj)
            return res
        elif inspect.ismodule(obj):
            return PickleSerializer.module_to_dict(obj)
        elif inspect.isclass(obj):
            return PickleSerializer.class_to_dict(obj)
        elif PickleSerializer.is_cls_instance(obj):
            return PickleSerializer.instance_to_dict(obj)
        elif isinstance(obj, types.CodeType):
            return PickleSerializer.code_to_dict(obj)
        else:
            raise TypeError(obj)

    @staticmethod
    def parse(obj):
        if isinstance(obj, (str, int, float, bool, bytes, set, frozenset, tuple)) or obj is None:
            return obj
        if isinstance(obj, list):
            res = []
            for i in obj:
                res.append(PickleSerializer.parse(i))
            return res
        elif isinstance(obj, dict):
            if "--function_type--" in obj and len(obj.keys()) == 1:
                return PickleSerializer.dict_to_func(obj["--function_type--"])
            if "--class_type--" in obj and len(obj.keys()) == 1:
                return PickleSerializer.dict_to_class(obj["--class_type--"])
            if "--static_method_type--" in obj and len(obj.keys()) == 1:
                return staticmethod(
                    PickleSerializer.dict_to_func(obj["--static_method_type--"]["--function_type--"])
                )
            if "--class_method_type--" in obj and len(obj.keys()) == 1:
                return classmethod(PickleSerializer.dict_to_func(obj["--class_method_type--"]["--function_type--"]))
            if "--module_type--" in obj and len(obj.keys()) == 1:
                return PickleSerializer.dict_to_module(obj["--module_type--"])
            if "--code_type--" in obj and len(obj.keys()) == 1:
                return PickleSerializer.dict_to_code(obj["--code_type--"])
            res = {}
            for i in obj:
                res[i] = PickleSerializer.parse(obj[i])
            return res
        else:
            raise TypeError()

    @staticmethod
    def dumps(obj):
        global f_found
        f_found = {}
        return __import__("pickle").dumps(PickleSerializer.convert(obj))

    @staticmethod
    def loads(obj):
        cur = __import__("pickle").loads(obj)
        return PickleSerializer.parse(cur)

    @staticmethod
    def dump(obj, fp):
        with open(fp, "wb") as file:
            file.write(PickleSerializer.dumps(obj))

    @staticmethod
    def load(fp):
        try:
            with open(fp, "rb") as file:
                data = file.read()
        except FileNotFoundError:
            raise
        else:
            return PickleSerializer.loads(data)
