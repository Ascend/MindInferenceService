/*
Copyright 2025 Huawei Technologies Co., Ltd.
*/

package utils

// MapEqual used to judge equalization between maps
func MapEqual[T comparable](a, b map[string]T) bool {
	if len(a) != len(b) {
		return false
	}

	for key, aValue := range a {
		if bValue, exist := b[key]; !exist || bValue != aValue {
			return false
		}
	}

	return true
}
