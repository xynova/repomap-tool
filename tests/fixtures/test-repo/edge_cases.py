"""
Edge cases and special characters for testing.
"""

# Unicode strings
unicode_string = "Hello 世界 🌍"
emoji_string = "🚀 Python is awesome! 🐍"
special_chars = "!@#$%^&*()_+-=[]{}|;':\",./<>?"


# Empty functions
def empty_function():
    pass


def function_with_docstring():
    """This function has a docstring but no body."""
    pass


# Functions with special characters in names
def function_with_underscores():
    return "underscores"


def functionWithCamelCase():
    return "camelCase"


def function_with_numbers_123():
    return "numbers"


# Functions with unicode names
def función_con_acentos():
    return "español"


def 函数名():
    return "中文"


# Empty class
class EmptyClass:
    pass


# Class with only docstring
class DocstringOnlyClass:
    """This class has only a docstring."""

    pass


# Class with special characters
class Class_With_Underscores:
    def method_with_underscores(self):
        return "method"


class ClassWithCamelCase:
    def methodWithCamelCase(self):
        return "method"


# Variables with special names
变量名 = "variable"
変数名 = "variable"
변수명 = "variable"
