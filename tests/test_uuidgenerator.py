# -*- coding: utf-8 -*-
"""Test configs."""
from uuid import uuid4

from kunin.utils.uuidgenerator import UUIDGenerator


def test_generate_uuid():
    """Generate uuid."""
    uuid1 = UUIDGenerator()
    assert len(str(uuid1.uuid)) == 36

def test_unique_uuids_generated():
    """Generate unique uuids."""
    uuid1 = UUIDGenerator()
    assert uuid1 != UUIDGenerator()

def test_check_uuid_is_new_version():
    """Check that uuids are new version"""
    # we don't test general UUIDs as they may or may not conform, so no need to check
    uuid_good = UUIDGenerator().uuid
    assert bool(UUIDGenerator.new_version(uuid_good))

def test_id_to_uuid():
    """Check that ints can convert well to uuid"""
    id = 1000
    assert len(str(UUIDGenerator.int_to_uuid(id))) == 36

def test_uuid_to_int_id():
    """Check that ints can convert well to uuid"""
    int_id = UUIDGenerator.uuid_to_int(str(UUIDGenerator().uuid))
    assert isinstance(int_id, int)
    id = 1000
    uuid_from_id = UUIDGenerator.int_to_uuid(id)
    assert UUIDGenerator.uuid_to_int(str(uuid_from_id)) == id

def test_str_to_uuid():
    """Check that str representations of UUID can be turned to a true UUID"""
    test_uuid = uuid4()
    str_uuid = str(test_uuid)
    assert UUIDGenerator.str_to_uuid(str_uuid) == test_uuid

def test_invalid_str_to_uuid():
    """Check that str representations of UUID can be turned to a true UUID"""
    import pytest
    with pytest.raises(ValueError) as excinfo:
        test_uuid = uuid4()
        bad_str_uuid = str(test_uuid)[:-2]
        expected_bad_result = UUIDGenerator.str_to_uuid(bad_str_uuid)
    assert 'is NOT a proper uuid' in str(excinfo.value)

def test_format_hex_to_dashed_representation():
    """Check that a UUID hex can be reformatted into a UUID compatible string"""
    str_uuid_no_dashes = uuid4().hex
    new_uuid = UUIDGenerator.format_uuid_hex(str_uuid_no_dashes)
    assert len(new_uuid) == 36

def test_format_hex_throws_exception():
    """Check that a BAD UUID hex can throws an error"""
    import pytest
    with pytest.raises(ValueError) as excinfo:
        str_uuid_no_dashes = uuid4().hex[:-2]
        new_uuid = UUIDGenerator.format_uuid_hex(str_uuid_no_dashes)
    assert 'provided is NOT a proper uuid' in str(excinfo.value)
