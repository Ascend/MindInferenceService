# -*- coding:utf-8 -*-
# Copyright (c) Huawei Technologies Co. Ltd. 2025. All rights reserved.
import unittest


def add(a, b):
    return a + b


class TestAddition(unittest.TestCase):

    def test_add(self):

        self.assertEqual(add(1, 2), 3)


if __name__ == '__main__':
    unittest.main()
