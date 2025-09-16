def str_to_bool(s):
    return s.lower() in ("yes", "true", "t", "1")
print(str_to_bool('1'))