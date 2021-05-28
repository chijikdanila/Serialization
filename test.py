import unittest
from fabric_method import Fabric
import test_objects as test

serializer = Fabric.create_serializer("Json")
# serializer = Fabric.create_serializer("Pickle")


class TestSerializer(unittest.TestCase):
    def test_bool(self):
        self.assertEqual(test.bool_variable, serializer.loads(serializer.dumps(test.bool_variable)))

    def test_int(self):
        self.assertEqual(test.int_variable, serializer.loads(serializer.dumps(test.int_variable)))

    def test_float(self):
        self.assertEqual(test.float_variable, serializer.loads(serializer.dumps(test.float_variable)))

    def test_string(self):
        self.assertEqual(test.string, serializer.loads(serializer.dumps(test.string)))

    def test_list(self):
        self.assertEqual(test.lst, serializer.loads(serializer.dumps(test.lst)))

    def test_dict(self):
        self.assertEqual(test.dct, serializer.loads(serializer.dumps(test.dct)))

    def test_simple_function(self):
        self.assertEqual(test.func_simple.__code__, serializer.loads(serializer.dumps(test.func_simple.__code__)))
        self.assertEqual(test.func_simple(1, 2), serializer.loads(serializer.dumps(test.func_simple(1, 2))))

    def test_recursive_function(self):
        self.assertEqual(test.func_recursive.__code__, serializer.loads(serializer.dumps(test.func_recursive.__code__)))
        self.assertEqual(test.func_recursive(3), serializer.loads(serializer.dumps(test.func_recursive(3))))

    def test_function_with_defaults(self):
        self.assertEqual(test.func_with_default.__code__,
                         serializer.loads(serializer.dumps(test.func_with_default.__code__)))
        self.assertEqual(test.func_with_default(),
                         serializer.loads(serializer.dumps(test.func_with_default())))

    def test_function_with_tuple(self):
        self.assertEqual(test.func_with_tuple.__code__,
                         serializer.loads(serializer.dumps(test.func_with_tuple.__code__)))

    def test_function_with_set(self):
        self.assertEqual(test.func_with_set.__code__,
                         serializer.loads(serializer.dumps(test.func_with_set.__code__)))

    def test_class_method(self):
        self.assertEqual(test.Class1.class_method.__code__,
                         serializer.loads(serializer.dumps(test.Class1.class_method.__code__)))

    def test_class(self):
        serializer.dump(test.Class1, "test_class.json", False, 4)
        class_after_des = serializer.load("test_class.json")
        self.assertEqual(class_after_des.class_method(class_after_des), test.Class1.class_method(test.Class1))
        self.assertEqual(class_after_des.a, test.Class1.a)

    def test_class_static_method(self):
        serializer.dump(test.ClassWithStaticMethod, "test_class_static.json", True, 4)
        class_after_des = serializer.load("test_class_static.json")
        self.assertEqual(class_after_des.static_method(), test.ClassWithStaticMethod.static_method())